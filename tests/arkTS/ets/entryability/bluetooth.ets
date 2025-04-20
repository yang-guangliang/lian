import { access } from '@kit.ConnectivityKit';
import { AsyncCallback, BusinessError } from '@kit.BasicServicesKit';

// 开启蓝牙
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
  if (btStateMessage == 'STATE_ON') {
    access.off('stateChange');
  }
  console.info('bluetooth statues: ' + btStateMessage);
})

// 关闭蓝牙
access.disableBluetooth();
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
})

// TextReader.on('stateChange', (state: TextReader.ReadState) => {
//   this.onStateChanged(state)
// });