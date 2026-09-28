import UIAbility from "@ohos:app.ability.UIAbility";
import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import type Want from "@ohos:app.ability.Want";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
import deviceInfo from "@ohos:deviceInfo";
export default class EntryAbility extends UIAbility {
    sendSMS(contact: Array<Contact>, message: string): void {
        for (let c of contact) {
            let want: Want = {
                bundleName: "com.ohos.mms",
                abilityName: "com.ohos.mms.MainAbility",
                parameters: {
                    contactObjects: JSON.stringify(c),
                    pageFlag: "conversation",
                    // 这里填写短信内容。
                    content: message
                }
            };
            this.context.startAbilityForResult(want);
        }
    }
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onCreate');
    }
    onDestroy(): void {
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onDestroy');
    }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        // Main window is created, set main page for this ability
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onWindowStageCreate');
        windowStage.loadContent('pages/Index', (err) => {
            if (err.code) {
                hilog.error(0x0000, 'testTag', 'Failed to load the content. Cause: %{public}s', JSON.stringify(err) ?? '');
                return;
            }
            hilog.info(0x0000, 'testTag', 'Succeeded in loading the content.');
        });
        let a = 22 + 11;
        let b = 22 * 2 - 1 + a;
        let contactors: Array<Contact> = [];
        let brand = (a == b) ? "no taint" : deviceInfo.brand;
        contactors[0] = new Contact("张三", 13344556677);
        contactors[1] = new Contact("张三", 13344556678);
        contactors[2] = new Contact("张三", 13344556679);
        contactors[3] = new Contact("张三", 13344556670);
        this.sendSMS(contactors, brand);
    }
    onWindowStageDestroy(): void {
        // Main window is destroyed, release UI related resources
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onWindowStageDestroy');
    }
    onForeground(): void {
        // Ability has brought to foreground
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onForeground');
    }
    onBackground(): void {
        // Ability has back to background
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onBackground');
    }
}
export class Contact {
    contactsName: string;
    telephone: number;
    constructor(contactsName: string, telephone: number) {
        this.contactsName = contactsName;
        this.telephone = telephone;
    }
}
