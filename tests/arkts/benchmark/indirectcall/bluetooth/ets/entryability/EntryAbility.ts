import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import ConfigurationConstant from "@ohos:app.ability.ConfigurationConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
import access from "@ohos:bluetooth.access";
import type { BusinessError as BusinessError } from "@ohos:base";
import deviceInfo from "@ohos:deviceInfo";
const DOMAIN = 0x0000;
export function enable(): void {
    access.enableBluetooth();
    access.on('stateChange', (data) => {
        let btStateMessage = '';
        switch (data) {
            case 0:
                btStateMessage += 'STATE_OFF';
                break;
            case 1:
                btStateMessage += 'STATE_TURNING_ON';
                break;
            case 2:
                btStateMessage += 'STATE_ON';
                break;
            default:
                btStateMessage += 'unknown status';
                break;
        }
        if (btStateMessage == 'STATE_ON') {
            access.off('stateChange');
        }
        console.info('bluetooth statues: ' + btStateMessage);
    });
}
// 关闭蓝牙
export function disable(): void {
    try {
        access.disableBluetooth();
    }
    catch (err) {
        hilog.error(DOMAIN, "blutooth", 'errCode: ' + (err as BusinessError).code + ', errMessage: ' + (err as BusinessError).message);
    }
    // statechange是固定的
    access.on('stateChange', (data) => {
        hilog.info(0x0000, 'testTag', deviceInfo.brand);
        let btStateMessage = '';
        switch (data) {
            case 0:
                btStateMessage += 'STATE_OFF';
                break;
            case 1:
                btStateMessage += 'STATE_TURNING_ON';
                break;
            case 2:
                btStateMessage += 'STATE_ON';
                break;
            case 3:
                btStateMessage += 'STATE_TURNING_OFF';
                break;
            case 4:
                btStateMessage += 'STATE_BLE_TURNING_ON';
                break;
            case 5:
                btStateMessage += 'STATE_BLE_ON';
                break;
            case 6:
                btStateMessage += 'STATE_BLE_TURNING_OFF';
                break;
            default:
                btStateMessage += 'unknown status';
                break;
        }
        if (btStateMessage == 'STATE_OFF') {
            access.off('stateChange');
        }
        console.info("bluetooth statues: " + btStateMessage);
    });
}
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
        this.context.getApplicationContext().setColorMode(ConfigurationConstant.ColorMode.COLOR_MODE_NOT_SET);
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onCreate');
    }
    onDestroy(): void {
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onDestroy');
    }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        // Main window is created, set main page for this ability
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onWindowStageCreate');
        windowStage.loadContent('pages/Index', (err) => {
            if (err.code) {
                hilog.error(DOMAIN, 'testTag', 'Failed to load the content. Cause: %{public}s', JSON.stringify(err));
                return;
            }
            hilog.info(DOMAIN, 'testTag', 'Succeeded in loading the content.');
        });
        disable();
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
