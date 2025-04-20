import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { window } from '@kit.ArkUI';
import { deviceInfo } from '@kit.BasicServicesKit';
import { healthStore } from '@kit.HealthServiceKit';
import { abilityAccessCtrl, common, Permissions,  } from '@kit.AbilityKit';
import { BusinessError } from '@kit.BasicServicesKit';


const permissions: Record<string, string> = {
  LOCATION: 'ohos.permission.LOCATION',
  APPROXIMATELY_LOCATION: 'ohos.permission.APPROXIMATELY_LOCATION'
};

// 使用UIExtensionAbility：将common.UIAbilityContext 替换为common.UIExtensionContext
function reqPermissionsFromUser(permissions: Record, context: common.UIAbilityContext): void {
  let atManager: abilityAccessCtrl.AtManager = abilityAccessCtrl.createAtManager();
  // requestPermissionsFromUser会判断权限的授权状态来决定是否唤起弹窗
  let permission = permissions['LOCATION'];
  atManager.requestPermissionsFromUser(context, permission).then((data) => {
    let grantStatus: Array<number> = data.authResults;
    let length: number = grantStatus.length;
    for (let i = 0; i < length; i++) {
      if (grantStatus[i] === 0) {
        // 用户授权，可以继续访问目标操作
      } else {
        // 用户拒绝授权，提示用户必须授权才能访问当前页面的功能，并引导用户到系统设置中打开相应的权限
        return;
      }
    }
    // 授权成功
  }).catch((err: BusinessError) => {
    console.error(`Failed to request permissions from user. Code is ${err.code}, message is ${err.message}`);
  })
}

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
    getDeviceInfo("brand")
    windowStage.loadContent('pages/Index', (err) => {
      reqPermissionsFromUser(permissions, this.context)
    });
  }


}

EntryAbility.onWindowStageCreate()