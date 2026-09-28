import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import preferences from "@ohos:data.preferences";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    async onWindowStageCreate(windowStage: window.WindowStage): Promise<void> {
        windowStage.loadContent('pages/Index');
        let store = await preferences.getPreferences(this.context, 'bench_preferences');
        let brand = deviceInfo.brand; // TAINT_SOURCE
        await store.put('brand', brand);
        let value = await store.get('brand', '');
        hilog.info(DOMAIN, 'benchmark', 'preferences %{public}s', value as string); // TAINT_SINK
    }
}
