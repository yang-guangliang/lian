if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    record?: DeviceRecord;
}
interface BrandChild_Params {
    record?: DeviceRecord;
}
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
const DOMAIN = 0x0000;
@Observed
class DeviceRecord {
    brand: string = '';
}
class BrandChild extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__record = new SynchedPropertyNesedObjectPU(params.record, this, "record");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: BrandChild_Params) {
        this.__record.set(params.record);
    }
    updateStateVars(params: BrandChild_Params) {
        this.__record.set(params.record);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__record.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__record.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __record: SynchedPropertyNesedObjectPU<DeviceRecord>;
    get record() {
        return this.__record.get();
    }
    aboutToAppear(): void {
        hilog.info(DOMAIN, 'benchmark', 'object link %{public}s', this.record.brand); // TAINT_SINK
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.record.brand);
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
        this.__record = new ObservedPropertyObjectPU(new DeviceRecord(), this, "record");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.record !== undefined) {
            this.record = params.record;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__record.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__record.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __record: ObservedPropertyObjectPU<DeviceRecord>;
    get record() {
        return this.__record.get();
    }
    set record(newValue: DeviceRecord) {
        this.__record.set(newValue);
    }
    aboutToAppear(): void {
        this.record.brand = deviceInfo.brand; // TAINT_SOURCE
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
                    let componentCall = new BrandChild(this, { record: this.record }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/Index.ets", line: 35, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            record: this.record
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        record: this.record
                    });
                }
            }, { name: "BrandChild" });
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
