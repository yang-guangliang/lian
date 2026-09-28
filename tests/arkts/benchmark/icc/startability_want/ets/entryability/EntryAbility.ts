import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import type window from "@ohos:window";
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let brand = deviceInfo.brand; // TAINT_SOURCE
        let target: Want = {
            bundleName: 'com.example.receiver',
            abilityName: 'EntryAbility',
            parameters: { brand: brand }
        };
        this.context.startAbility(target); // TAINT_SINK
    }
}
