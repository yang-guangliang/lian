if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    message?: string;
    counter?: number;
}
import hilog from "@ohos:hilog";
import deviceInfo from "@ohos:deviceInfo";
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__message = new ObservedPropertySimplePU('Hello World', this, "message");
        this.__counter = new ObservedPropertySimplePU(0, this, "counter");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.message !== undefined) {
            this.message = params.message;
        }
        if (params.counter !== undefined) {
            this.counter = params.counter;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__message.purgeDependencyOnElmtId(rmElmtId);
        this.__counter.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__message.aboutToBeDeleted();
        this.__counter.aboutToBeDeleted();
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
    private __counter: ObservedPropertySimplePU<number>;
    get counter() {
        return this.__counter.get();
    }
    set counter(newValue: number) {
        this.__counter.set(newValue);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            RelativeContainer.create();
            RelativeContainer.height('100%');
            RelativeContainer.width('100%');
        }, RelativeContainer);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel("click to leak");
            Button.onClick(() => {
                ++this.counter;
                let imei = deviceInfo.brand;
                let data: NoDataLeak;
                if (this.counter % 2 == 0)
                    data = new NoDataLeak("no leak");
                else
                    data = new DataLeak(imei);
                data.logData();
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
export class NoDataLeak {
    data: string;
    constructor(data: string) {
        this.data = data;
    }
    getData(): string {
        return this.data;
    }
    logData(): void {
        hilog.info(0x0000, 'testTag0', '%{public}s', this.data);
    }
}
export class DataLeak extends NoDataLeak {
    constructor(data: string) {
        super(data);
    }
    logData(): void {
        hilog.info(0x0000, 'testTag1', '%{public}s', super.getData());
    }
}
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.virtualdispatch", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
