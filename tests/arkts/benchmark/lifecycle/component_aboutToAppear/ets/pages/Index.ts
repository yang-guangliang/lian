if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    brand?: string;
}
interface LifecycleChild_Params {
    brand?: string;
}
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
const DOMAIN = 0x0000;
class LifecycleChild extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__brand = new SynchedPropertySimpleOneWayPU(params.brand, this, "brand");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: LifecycleChild_Params) {
    }
    updateStateVars(params: LifecycleChild_Params) {
        this.__brand.reset(params.brand);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__brand.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__brand.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __brand: SynchedPropertySimpleOneWayPU<string>;
    get brand() {
        return this.__brand.get();
    }
    set brand(newValue: string) {
        this.__brand.set(newValue);
    }
    aboutToAppear(): void {
        hilog.info(DOMAIN, 'benchmark', 'child lifecycle %{public}s', this.brand); // TAINT_SINK
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.brand);
            Text.fontSize(24);
        }, Text);
        Text.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__brand = new ObservedPropertySimplePU('', this, "brand");
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
    aboutToAppear(): void {
        this.brand = deviceInfo.brand; // TAINT_SOURCE
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.width('100%');
            Column.height('100%');
            Column.justifyContent(FlexAlign.Center);
        }, Column);
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new LifecycleChild(this, { brand: this.brand }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/Index.ets", line: 29, col: 16 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            brand: this.brand
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        brand: this.brand
                    });
                }
            }, { name: "LifecycleChild" });
        }
        Column.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "Index";
    }
}
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.loop1", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
