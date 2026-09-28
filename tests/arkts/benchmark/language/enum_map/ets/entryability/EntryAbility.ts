import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
enum DeviceKey {
    Brand = "brand"
}
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let values: Map<DeviceKey, string> = new Map<DeviceKey, string>();
        values.set(DeviceKey.Brand, deviceInfo.brand); // TAINT_SOURCE
        let brand = values.get(DeviceKey.Brand) ?? '';
        hilog.info(DOMAIN, 'benchmark', 'enum map %{public}s', brand); // TAINT_SINK
    }
}
