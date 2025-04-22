let wantTemp:Want = {
    bundleName:'com.example.myapplication',
    abilityName:'EntryAbility'
  }
  let result = deviceInfo.getDeviceInfo(wantTemp, 'deviceName')
  let imei_result = 'imei' + result
  let new_imei = imei_result
  let condition= true
  let info = "before_send"
  if (condition) {
    info = new_imei
  }
  else {
    info = "dont_send"
  }
  console.log(info)
  
  