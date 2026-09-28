import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import emitter from "@ohos:events.emitter";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        emitter.once('benchEmitterBrand', (event: emitter.EventData) => {
            let data = event.data as Record<string, string>;
            hilog.info(DOMAIN, 'benchmark', 'emitter %{public}s', data['brand']); // TAINT_SINK
        });
        let brand = deviceInfo.brand; // TAINT_SOURCE
        emitter.emit('benchEmitterBrand', { data: { brand: brand } });
    }
}
