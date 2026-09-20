/**
 * 百度地图浏览器端能力封装。
 *
 * 这里负责加载 JS API、浏览器定位和逆地理编码。浏览器端 AK 会公开，正式部署
 * 必须依靠 Referer 白名单保护。
 */

let loaderPromise

/** 异步加载百度地图 WebGL JS API，同一页面只会加载一次。 */
export function loadBaiduMap() {
  if (window.BMapGL) return Promise.resolve(window.BMapGL)
  if (loaderPromise) return loaderPromise

  const ak = import.meta.env.VITE_BAIDU_MAP_AK
  if (!ak) return Promise.reject(new Error('尚未配置浏览器端百度地图 AK'))

  loaderPromise = new Promise((resolve, reject) => {
    const callbackName = `initBaiduMap_${Date.now()}`
    const script = document.createElement('script')
    const timeout = window.setTimeout(() => reject(new Error('百度地图加载超时')), 15000)

    window[callbackName] = () => {
      window.clearTimeout(timeout)
      delete window[callbackName]
      resolve(window.BMapGL)
    }
    script.onerror = () => {
      window.clearTimeout(timeout)
      delete window[callbackName]
      loaderPromise = null
      reject(new Error('百度地图加载失败，请检查 AK 和 Referer 白名单'))
    }
    script.src = `https://api.map.baidu.com/api?v=1.0&type=webgl&ak=${encodeURIComponent(ak)}&callback=${callbackName}`
    document.head.appendChild(script)
  })
  return loaderPromise
}

/** 请求浏览器定位；必须由用户点击触发，浏览器可能弹出权限询问。 */
export function getBrowserPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error('当前浏览器不支持定位'))
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude }),
      (error) => reject(new Error(error.code === 1 ? '定位权限未开启' : '暂时无法获取当前位置')),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 },
    )
  })
}

/** 使用浏览器端 JS 地理编码服务，把坐标转换为中文地址。 */
export async function reverseGeocode(latitude, longitude) {
  const BMapGL = await loadBaiduMap()
  return new Promise((resolve, reject) => {
    const geocoder = new BMapGL.Geocoder()
    geocoder.getLocation(new BMapGL.Point(longitude, latitude), (result) => {
      if (!result) return reject(new Error('未能解析当前位置'))
      resolve({
        name: result.surroundingPois?.[0]?.title || result.address,
        address: result.address,
        point: result.point,
      })
    })
  })
}

/** 完成“浏览器定位 → 百度逆地理编码”的完整位置打卡流程。 */
export async function locateTravelMoment() {
  const coordinate = await getBrowserPosition()
  const address = await reverseGeocode(coordinate.latitude, coordinate.longitude)
  return { ...coordinate, ...address }
}
