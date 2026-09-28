import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import ConfigurationConstant from "@ohos:app.ability.ConfigurationConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
import deviceInfo from "@ohos:deviceInfo";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
        try {
            this.context.getApplicationContext().setColorMode(ConfigurationConstant.ColorMode.COLOR_MODE_NOT_SET);
        }
        catch (err) {
            hilog.error(DOMAIN, 'testTag', 'Failed to set colorMode. Cause: %{public}s', JSON.stringify(err));
        }
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onCreate');
    }
    onDestroy(): void {
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onDestroy');
    }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onWindowStageCreate');
        // Taint source: device brand info
        let brand: string = deviceInfo.brand;
        // Dispatch variable — only one case leaks the taint
        let caseValue: number = 2;
        switch (caseValue) {
            case 0:
                hilog.info(DOMAIN, 'testTag', 'Case 0: processing request, no sensitive data logged');
                break;
            case 1:
                hilog.info(DOMAIN, 'testTag', 'Case 1: normal operation, no leak');
                break;
            case 2:
                // TAINT LEAK: only this branch passes brand (source) to hilog.info (sink)
                hilog.info(DOMAIN, 'testTag', 'Device brand: %{public}s', brand);
                break;
            case 3:
                hilog.info(DOMAIN, 'testTag', 'Case 3: fallback path, no leak');
                break;
            default:
                hilog.info(DOMAIN, 'testTag', 'Default: unknown case, no leak');
                break;
        }
        windowStage.loadContent('pages/Index', (err) => {
            if (err.code) {
                hilog.error(DOMAIN, 'testTag', 'Failed to load the content. Cause: %{public}s', JSON.stringify(err));
                return;
            }
            hilog.info(DOMAIN, 'testTag', 'Succeeded in loading the content.');
        });
    }
    onWindowStageDestroy(): void {
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onWindowStageDestroy');
    }
    onForeground(): void {
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onForeground');
    }
    onBackground(): void {
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onBackground');
    }
}
