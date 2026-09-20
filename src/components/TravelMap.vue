<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LocateFixed, MapPin, Navigation, Route, Search, ZoomIn, ZoomOut } from 'lucide-vue-next'
import { getBrowserPosition, loadBaiduMap, reverseGeocode } from '../services/baiduMap'

const props = defineProps({ trip: { type: Object, required: true } })
const emit = defineEmits(['notify', 'located', 'route-info'])
const mapElement = ref()
const keyword = ref('')
const loading = ref(true)
const error = ref('')
const routeMode = ref('driving')
let map
let BMapGL
let routeService

/** 使用所选行程的真实坐标绘制标记和手账路线。 */
function renderTrip() {
  if (!map || !props.trip) return
  map.clearOverlays()
  const points = (props.trip.route || []).map(([lng, lat]) => new BMapGL.Point(lng, lat))
  const center = new BMapGL.Point(props.trip.longitude, props.trip.latitude)
  map.centerAndZoom(center, props.trip.zoom || 11)
  points.forEach((point, index) => {
    const marker = new BMapGL.Marker(point)
    marker.setTitle(props.trip.places?.[index] || `${props.trip.city}足迹`)
    map.addOverlay(marker)
    if (props.trip.places?.[index]) {
      const label = new BMapGL.Label(props.trip.places[index], {
        position: point, offset: new BMapGL.Size(13, -24),
      })
      label.setStyle({ color: '#40584c', border: '0', padding: '4px 7px', fontSize: '11px' })
      map.addOverlay(label)
    }
  })
  if (points.length > 1) {
    map.addOverlay(new BMapGL.Polyline(points, {
      strokeColor: '#bf6b4c', strokeWeight: 4, strokeOpacity: 0.9,
    }))
    map.setViewport(points, { margins: [70, 70, 70, 70] })
  } else {
    map.addOverlay(new BMapGL.Marker(center))
  }
}

/** 初始化地图底图、比例尺和所选行程。 */
async function initializeMap() {
  try {
    BMapGL = await loadBaiduMap()
    await nextTick()
    map = new BMapGL.Map(mapElement.value)
    map.enableScrollWheelZoom(true)
    map.enableInertialDragging()
    map.addControl(new BMapGL.ScaleControl())
    renderTrip()
    loading.value = false
  } catch (reason) {
    error.value = reason.message
    loading.value = false
  }
}

/** 使用已开通的 JS 地点检索服务，在当前地图内搜索。 */
function searchPlace() {
  if (!map || !keyword.value.trim()) return
  const local = new BMapGL.LocalSearch(map, {
    renderOptions: { map, autoViewport: true, selectFirstResult: true },
    pageCapacity: 8,
    onSearchComplete(results) {
      const count = results?.getCurrentNumPois?.() || 0
      emit('notify', count ? `找到 ${count} 个相关地点` : '没有找到相关地点')
    },
  })
  local.search(keyword.value.trim())
}

/** 用浏览器定位服务显示当前地点并返回地址给手账页面。 */
async function locateMe() {
  try {
    emit('notify', '正在获取当前位置…')
    const position = await getBrowserPosition()
    const address = await reverseGeocode(position.latitude, position.longitude)
    const point = new BMapGL.Point(position.longitude, position.latitude)
    map.addOverlay(new BMapGL.Marker(point))
    map.panTo(point)
    map.setZoom(16)
    emit('located', { ...position, ...address })
    emit('notify', `已定位：${address.name}`)
  } catch (reason) {
    emit('notify', reason.message)
  }
}

/** 在首尾足迹之间切换并绘制驾车、步行或骑行路线。 */
function planRoute() {
  const points = props.trip.route || []
  if (!map || points.length < 2) return emit('notify', '至少需要两个足迹才能规划路线')
  routeService?.clearResults?.()
  const constructors = {
    driving: BMapGL.DrivingRoute,
    walking: BMapGL.WalkingRoute,
    riding: BMapGL.RidingRoute,
  }
  const start = new BMapGL.Point(...points[0])
  const end = new BMapGL.Point(...points.at(-1))
  routeService = new constructors[routeMode.value](map, {
    renderOptions: { map, autoViewport: true },
    onSearchComplete(results) {
      if (routeService.getStatus() !== window.BMAP_STATUS_SUCCESS) {
        return emit('notify', '路线规划失败，请稍后再试')
      }
      const plan = results.getPlan(0)
      const info = { duration: plan.getDuration(true), distance: plan.getDistance(true) }
      emit('route-info', info)
      emit('notify', `路线已生成：${info.distance} · ${info.duration}`)
    },
  })
  routeService.search(start, end)
}

watch(() => props.trip, renderTrip, { deep: true })
onMounted(initializeMap)
onBeforeUnmount(() => { map = null; routeService = null })
</script>

<template>
  <section class="real-map-shell">
    <div ref="mapElement" class="real-map"></div>
    <div v-if="loading" class="map-status"><span class="spinner dark"></span>正在加载百度地图…</div>
    <div v-else-if="error" class="map-status error"><MapPin :size="23" />{{ error }}</div>
    <form class="map-search" @submit.prevent="searchPlace">
      <Search :size="17" /><input v-model="keyword" placeholder="搜索景点、咖啡馆或地址" /><button>搜索</button>
    </form>
    <div class="map-route-tools">
      <select v-model="routeMode" aria-label="出行方式"><option value="driving">驾车</option><option value="walking">步行</option><option value="riding">骑行</option></select>
      <button @click="planRoute"><Route :size="16" />规划路线</button>
    </div>
    <div class="map-controls">
      <button aria-label="放大" @click="map?.zoomIn()"><ZoomIn :size="18" /></button>
      <button aria-label="缩小" @click="map?.zoomOut()"><ZoomOut :size="18" /></button>
      <button aria-label="定位" @click="locateMe"><LocateFixed :size="18" /></button>
    </div>
    <div class="map-brand-note"><Navigation :size="13" /> 百度地图实时服务</div>
  </section>
</template>
