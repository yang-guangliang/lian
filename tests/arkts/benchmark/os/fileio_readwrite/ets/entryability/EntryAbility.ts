import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import fileIo from "@ohos:file.fs";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let brand = deviceInfo.brand; // TAINT_SOURCE
        let path = this.context.filesDir + '/bench_brand.txt';
        let file = fileIo.openSync(path, fileIo.OpenMode.READ_WRITE | fileIo.OpenMode.CREATE | fileIo.OpenMode.TRUNC);
        fileIo.writeSync(file.fd, brand);
        fileIo.closeSync(file);
        let value = fileIo.readTextSync(path);
        hilog.info(DOMAIN, 'benchmark', 'fileio %{public}s', value); // TAINT_SINK
    }
}
