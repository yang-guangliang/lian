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
        let brand = deviceInfo.brand; // TAINT_SOURCE
        windowStage.loadContent('pages/Index', () => {
            hilog.info(DOMAIN, 'benchmark', 'window callback %{public}s', brand); // TAINT_SINK
        });
    }
}
