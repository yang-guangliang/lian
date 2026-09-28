import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
async function loadBrand(): Promise<string> {
    return deviceInfo.brand; // TAINT_SOURCE
}
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    async onWindowStageCreate(windowStage: window.WindowStage): Promise<void> {
        windowStage.loadContent('pages/Index');
        let brand = await loadBrand();
        hilog.info(DOMAIN, 'benchmark', 'async await %{public}s', brand); // TAINT_SINK
    }
}
