function getDeviceInfo(infoName) {

    const deviceInfoRecord = {
      "manufacture":deviceInfo.manufacture,
      "deviceType":deviceInfo.deviceType,
      "brand":deviceInfo.brand,
      "marketName":deviceInfo.marketName,
      "productSeries":deviceInfo.productSeries
    }
   let info = deviceInfoRecord[infoName]
   return info          
 }