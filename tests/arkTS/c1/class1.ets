class EntryAbility {
  getDeviceInfo(infoName:string):string{
    const deviceInfoRecord:Record<string, string> = {
      "manufacture":deviceInfo.manufacture,
      "deviceType":deviceInfo.deviceType,
      "brand":deviceInfo.brand,
      "marketName":deviceInfo.marketName,
      "productSeries":deviceInfo.productSeries
    }
    let info = deviceInfoRecord[infoName]
    return info;
  }
  onWindowStageCreate(windowStage: window.WindowStage): void {
    let b = "brand"
    getDeviceInfo(b)
  }
}
EntryAbility.onWindowStageCreate()