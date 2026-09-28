if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    message?: string;
}
import type common from "@ohos:app.ability.common";
import type Want from "@ohos:app.ability.Want";
import deviceInfo from "@ohos:deviceInfo";
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__message = new ObservedPropertySimplePU('Hello World', this, "message");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.message !== undefined) {
            this.message = params.message;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__message.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__message.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __message: ObservedPropertySimplePU<string>;
    get message() {
        return this.__message.get();
    }
    set message(newValue: string) {
        this.__message.set(newValue);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            RelativeContainer.create();
            RelativeContainer.height('100%');
            RelativeContainer.width('100%');
        }, RelativeContainer);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel("123");
            Button.onClick(() => {
                let context: common.UIAbilityContext = getContext(this) as common.UIAbilityContext;
                let params: Array<Object> = [new Contact("张三", 13344556677)];
                this.message = deviceInfo.brand;
                let want: Want = {
                    bundleName: "com.ohos.mms",
                    abilityName: "com.ohos.mms.MainAbility",
                    parameters: {
                        contactObjects: JSON.stringify(params),
                        pageFlag: "conversation",
                        // 这里填写短信内容。
                        content: this.message
                    }
                };
                context.startAbilityForResult(want).then((data) => {
                    console.log("Success" + JSON.stringify(data));
                }).catch(() => {
                    console.log("error");
                });
            });
        }, Button);
        Button.pop();
        RelativeContainer.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "Index";
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
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.button1", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
