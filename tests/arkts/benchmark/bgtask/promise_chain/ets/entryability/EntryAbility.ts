import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let brand = deviceInfo.brand; // TAINT_SOURCE
        Promise.resolve(brand)
            .then((value: string) => value + ':p1')
            .then((value: string) => {
            hilog.info(DOMAIN, 'benchmark', 'promise %{public}s', value); // TAINT_SINK
        });
    }
}
