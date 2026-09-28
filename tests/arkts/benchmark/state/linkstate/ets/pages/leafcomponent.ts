if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface leafcomponent_Params {
    tmp?: string;
    func?: (msg: string) => void;
}
export class leafcomponent extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__tmp = new ObservedPropertySimplePU('Hello World', this, "tmp");
        this.func = (): void => {
        };
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: leafcomponent_Params) {
        if (params.tmp !== undefined) {
            this.tmp = params.tmp;
        }
        if (params.func !== undefined) {
            this.func = params.func;
        }
    }
    updateStateVars(params: leafcomponent_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__tmp.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__tmp.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __tmp: ObservedPropertySimplePU<string>;
    get tmp() {
        return this.__tmp.get();
    }
    set tmp(newValue: string) {
        this.__tmp.set(newValue);
    }
    private func: (msg: string) => void;
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            RelativeContainer.create();
            RelativeContainer.height('100%');
            RelativeContainer.width('100%');
        }, RelativeContainer);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.tmp);
            Text.id('HelloWorld');
            Text.fontSize({ "id": 16777224, "type": 10002, params: [], "bundleName": "com.example.linkstate", "moduleName": "entry" });
            Text.fontWeight(FontWeight.Bold);
            Text.alignRules({
                center: { anchor: '__container__', align: VerticalAlign.Center },
                middle: { anchor: '__container__', align: HorizontalAlign.Center }
            });
            Text.onClick(() => {
                this.func(this.tmp);
            });
        }, Text);
        Text.pop();
        RelativeContainer.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
