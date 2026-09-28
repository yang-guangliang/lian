import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
class BrandStore {
    private inner: string = '';
    set brand(value: string) {
        this.inner = value;
    }
    get brand(): string {
        return this.inner;
    }
}
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void { }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        windowStage.loadContent('pages/Index');
        let store = new BrandStore();
        store.brand = deviceInfo.brand; // TAINT_SOURCE
        hilog.info(DOMAIN, 'benchmark', 'accessor %{public}s', store.brand); // TAINT_SINK
    }
}
