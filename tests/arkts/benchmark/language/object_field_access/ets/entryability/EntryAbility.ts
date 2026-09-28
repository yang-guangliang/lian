import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
interface DevicePayload {
    brand: string;
    label: string;
}
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let payload: DevicePayload = { brand: deviceInfo.brand, label: 'device' }; // TAINT_SOURCE
        let brand = payload.brand;
        hilog.info(DOMAIN, 'benchmark', 'object field %{public}s', brand); // TAINT_SINK
    }
}
