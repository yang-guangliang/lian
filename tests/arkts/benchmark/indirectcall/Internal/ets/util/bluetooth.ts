import type { BusinessError as BusinessError } from "@ohos:base";
import hilog from "@ohos:hilog";
import access from "@ohos:bluetooth.access";
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
const DOMAIN = 0x0000;
export function disable(): void {
    try {
        access.disableBluetooth();
    }
    catch (err) {
        hilog.error(DOMAIN, "blutooth", 'errCode: ' + (err as BusinessError).code + ', errMessage: ' + (err as BusinessError).message);
    }
    // statechange是固定的
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
