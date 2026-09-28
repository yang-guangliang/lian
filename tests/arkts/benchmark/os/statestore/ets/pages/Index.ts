if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    leakedBrand?: string;
}
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
import { StateStore } from "@normalized:N&&&entry/src/main/ets/store/StateStore&";
const DOMAIN: number = 0x0001;
const TAG: string = 'StateStoreBenchmark';
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__leakedBrand = new ObservedPropertySimplePU('', this, "leakedBrand");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.leakedBrand !== undefined) {
            this.leakedBrand = params.leakedBrand;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__leakedBrand.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__leakedBrand.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __leakedBrand: ObservedPropertySimplePU<string>;
    get leakedBrand() {
        return this.__leakedBrand.get();
    }
    set leakedBrand(newValue: string) {
        this.__leakedBrand.set(newValue);
    }
    aboutToAppear(): void {
        // Source: 从 deviceInfo 获取设备品牌信息（污点源）
        const brand: string = deviceInfo.brand;
        // Dispatch: 通过 StateStore 全局状态管理传递污点数据
        const store: StateStore = StateStore.getInstance();
        store.dispatch('SET_BRAND', brand);
        // Sink: 从 StateStore 取出污点数据，通过 hilog.info 泄露
        this.leakedBrand = store.getState().brand;
        hilog.info(DOMAIN, TAG, 'Leaked device brand: %{public}s', this.leakedBrand);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            RelativeContainer.create();
            RelativeContainer.height('100%');
            RelativeContainer.width('100%');
        }, RelativeContainer);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(`Device Brand: ${this.leakedBrand}`);
            Text.id('BrandDisplay');
            Text.fontSize({ "id": 16777224, "type": 10002, params: [], "bundleName": "com.example.statestore", "moduleName": "entry" });
            Text.fontWeight(FontWeight.Bold);
            Text.alignRules({
                center: { anchor: '__container__', align: VerticalAlign.Center },
                middle: { anchor: '__container__', align: HorizontalAlign.Center }
            });
        }, Text);
        Text.pop();
        RelativeContainer.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "Index";
    }
}
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.statestore", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
