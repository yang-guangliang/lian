import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import ConfigurationConstant from "@ohos:app.ability.ConfigurationConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
const DOMAIN = 0x0000;
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
        this.context.getApplicationContext().setColorMode(ConfigurationConstant.ColorMode.COLOR_MODE_NOT_SET);
        hilog.info(DOMAIN, 'testTag', '%{public}s', 'Ability onCreate');
    }
    dynamicImport() {
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
        import("@normalized:N&&&entry/src/main/ets/util/Calc&").then((ns: any) => {
            ns.Calc1.staticAdd(8, 9); // 调用静态成员函数staticAdd()
            let calc: any = new ns.Calc1(); // 实例化类Calc
            calc.instanceAdd(10, 11); // 调用成员函数instanceAdd()
            ns.addHarlibrary(6, 7); // 调用全局方法addHarlibrary()
            // 使用类、成员函数和方法的字符串名字进行反射调用
            let className = 'Calc1';
            let methodName = 'instanceAdd';
            let staticMethod = 'staticAdd';
            let functionName = 'addHarlibrary';
            ns[className][staticMethod](12, 13); // 调用静态成员函数staticAdd()
            let calc1: any = new ns[className](); // 实例化类Calc
            calc1[methodName](14, 15); // 调用成员函数instanceAdd()
            ns[functionName](16, 17); // 调用全局方法addHarlibrary()
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
