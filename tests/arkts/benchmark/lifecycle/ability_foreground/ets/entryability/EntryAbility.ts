import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    private brand: string = '';
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
        this.brand = deviceInfo.brand; // TAINT_SOURCE
    }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
    }
    onForeground(): void {
        hilog.info(DOMAIN, 'benchmark', 'foreground %{public}s', this.brand); // TAINT_SINK
    }
}
