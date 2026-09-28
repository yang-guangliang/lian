if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    brand?: string;
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
        this.__brand = new ObservedPropertySimplePU('Hello World', this, "brand");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.brand !== undefined) {
            this.brand = params.brand;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__brand.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__brand.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __brand: ObservedPropertySimplePU<string>;
    get brand() {
        return this.__brand.get();
    }
    set brand(newValue: string) {
        this.__brand.set(newValue);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.height('100%');
            Column.width('100%');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel("1234546");
            Button.onClick(() => {
                this.brand = deviceInfo.brand;
            });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel("2");
            Button.onClick(() => {
                let context: common.UIAbilityContext = getContext(this) as common.UIAbilityContext;
                let params: Array<Object> = [new Contact("张三", 13344556677)];
                let imei = "imei";
                let want: Want = {
                    bundleName: "com.ohos.mms",
                    abilityName: "com.ohos.mms.MainAbility",
                    parameters: {
                        contactObjects: JSON.stringify(params),
                        pageFlag: "conversation",
                        // 这里填写短信内容。
                        content: this.brand
                    }
                };
                console.log("Success" + JSON.stringify(want));
                context.startAbilityForResult(want);
            });
        }, Button);
        Button.pop();
        Column.pop();
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
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.button2", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
