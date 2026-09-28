import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
interface Holder {
    nested?: BrandNode;
}
interface BrandNode {
    value?: string;
}
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let holder: Holder = { nested: { value: deviceInfo.brand } }; // TAINT_SOURCE
        let value = holder.nested?.value ?? '';
        hilog.info(DOMAIN, 'benchmark', 'optional %{public}s', value); // TAINT_SINK
    }
}
