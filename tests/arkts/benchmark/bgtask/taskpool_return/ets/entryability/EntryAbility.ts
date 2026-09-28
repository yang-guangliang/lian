import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import taskpool from "@ohos:taskpool";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
function passBrand(value: string): string {
    "use concurrent";
    return value;
}
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let brand = deviceInfo.brand; // TAINT_SOURCE
        let task = new taskpool.Task(passBrand, brand);
        taskpool.execute(task).then((value: Object) => {
            hilog.info(DOMAIN, 'benchmark', 'taskpool %{public}s', value as string); // TAINT_SINK
        });
    }
}
