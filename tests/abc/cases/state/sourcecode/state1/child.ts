if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Child_Params {
    taint?: string;
}
import hilog from "@ohos:hilog";
export class Child extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__taint = new ObservedPropertySimplePU('Hello World', this, "taint");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Child_Params) {
        if (params.taint !== undefined) {
            this.taint = params.taint;
        }
    }
    updateStateVars(params: Child_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__taint.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__taint.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __taint: ObservedPropertySimplePU<string>;
    get taint() {
        return this.__taint.get();
    }
    set taint(newValue: string) {
        this.__taint.set(newValue);
    }
    func1() {
        hilog.info(0x0000, 'testTag', this.taint);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            RelativeContainer.create();
            RelativeContainer.height('100%');
            RelativeContainer.width('100%');
        }, RelativeContainer);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.taint);
            Text.id('HelloWorld');
            Text.fontSize({ "id": 16777224, "type": 10002, params: [], "bundleName": "com.example.state1", "moduleName": "entry" });
            Text.fontWeight(FontWeight.Bold);
            Text.alignRules({
                center: { anchor: '__container__', align: VerticalAlign.Center },
                middle: { anchor: '__container__', align: HorizontalAlign.Center }
            });
            Text.onClick(() => {
                this.func1();
            });
        }, Text);
        Text.pop();
        RelativeContainer.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
