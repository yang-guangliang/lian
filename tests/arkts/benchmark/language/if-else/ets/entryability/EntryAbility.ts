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
        // Multi-layer nested if-else taint benchmark
        // Source: deviceInfo.brand, Sink: hilog.info
        // Leak only occurs when ALL conditions are satisfied
        const condA: boolean = true;
        const condB: boolean = true;
        const condC: boolean = true;
        const condD: boolean = true;
        const condE: boolean = true;
        if (condA) {
            if (condB) {
                if (condC) {
                    if (condD) {
                        if (condE) {
                            // All conditions satisfied: taint sink — leaks deviceInfo.brand
                            hilog.info(DOMAIN, 'testTag', 'Brand: %{public}s', deviceInfo.brand);
                        }
                        else {
                            hilog.info(DOMAIN, 'testTag', '%{public}s', 'condE not met');
                        }
                    }
                    else {
                        hilog.info(DOMAIN, 'testTag', '%{public}s', 'condD not met');
                    }
                }
                else {
                    hilog.info(DOMAIN, 'testTag', '%{public}s', 'condC not met');
                }
            }
            else {
                hilog.info(DOMAIN, 'testTag', '%{public}s', 'condB not met');
            }
        }
        else {
            hilog.info(DOMAIN, 'testTag', '%{public}s', 'condA not met');
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
        // Main window is destroyed, release UI related resources
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onWindowStageDestroy');
    }
    onForeground(): void {
        // Ability has brought to foreground
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onForeground');
    }
    onBackground(): void {
        // Ability has back to background
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onBackground');
    }
}
