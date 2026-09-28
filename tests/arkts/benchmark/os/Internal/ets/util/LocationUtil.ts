import bundleManager from "@ohos:bundle.bundleManager";
import type common from "@ohos:app.ability.common";
import abilityAccessCtrl from "@ohos:abilityAccessCtrl";
import type { PermissionRequestResult as PermissionRequestResult } from "@ohos:abilityAccessCtrl";
import type { Permissions as Permissions } from "@ohos:abilityAccessCtrl";
import type { BusinessError as BusinessError } from "@ohos:base";
const TAG: string = 'ScanKit Permission';
let context = getContext(this) as common.UIAbilityContext;
export class LocationUtil {
    public static async checkAccessToken(permission: Permissions): Promise<abilityAccessCtrl.GrantStatus> {
        let atManager: abilityAccessCtrl.AtManager = abilityAccessCtrl.createAtManager();
        let grantStatus: abilityAccessCtrl.GrantStatus = abilityAccessCtrl.GrantStatus.PERMISSION_DENIED;
        // 获取应用程序的accessTokenID
        let tokenId: number = 0;
        try {
            let bundleInfo: bundleManager.BundleInfo = await bundleManager.getBundleInfoForSelf(bundleManager.BundleFlag.GET_BUNDLE_INFO_WITH_APPLICATION);
            let appInfo: bundleManager.ApplicationInfo = bundleInfo.appInfo;
            tokenId = appInfo.accessTokenId;
        }
        catch (error) {
            const err: BusinessError = error as BusinessError;
            console.error(`Failed to get bundle info for self. Code is ${err.code}, message is ${err.message}`);
        }
        // 校验应用是否被授予权限
        try {
            grantStatus = await atManager.checkAccessToken(tokenId, permission);
        }
        catch (error) {
            const err: BusinessError = error as BusinessError;
            console.error(`Failed to check access token. Code is ${err.code}, message is ${err.message}`);
        }
        return grantStatus;
    }
    public static async reqPermissionsFromUser(): Promise<number[]> {
        const permissions: Array<Permissions> = ['ohos.permission.LOCATION', 'ohos.permission.APPROXIMATELY_LOCATION'];
        let atManager: abilityAccessCtrl.AtManager = abilityAccessCtrl.createAtManager();
        // requestPermissionsFromUser会判断权限的授权状态来决定是否唤起弹窗
        let grantStatus: PermissionRequestResult = { permissions: [], authResults: [] };
        grantStatus = await atManager.requestPermissionsFromUser(context, permissions); // .then((data) => {
        //   let grantStatus: Array<number> = data.authResults;
        //   let length: number = grantStatus.length;
        //   for (let i = 0; i < length; i++) {
        //     if (grantStatus[i] === 0) {
        //       // 用户授权，可以继续访问目标操作
        //     } else {
        //       // 用户拒绝授权，提示用户必须授权才能访问当前页面的功能，并引导用户到系统设置中打开相应的权限
        //       return;
        //     }
        //   }
        //   // 授权成功
        // }).catch((err: BusinessError) => {
        //   console.error(`Failed to request permissions from user. Code is ${err.code}, message is ${err.message}`);
        // })
        return grantStatus.authResults;
    }
}
export default new LocationUtil();
