import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import pasteboard from "@ohos:pasteboard";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let brand = deviceInfo.brand; // TAINT_SOURCE
        let board = pasteboard.getSystemPasteboard();
        board.setData(pasteboard.createPlainTextData(brand)).then(() => {
            board.getData().then((data: pasteboard.PasteData) => {
                hilog.info(DOMAIN, 'benchmark', 'pasteboard %{public}s', data.getPrimaryText()); // TAINT_SINK
            });
        });
    }
}
