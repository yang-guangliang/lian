if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    dataList?: DataItem[];
    deviceBrand?: string;
}
import deviceInfo from "@ohos:deviceInfo";
import hilog from "@ohos:hilog";
const DOMAIN = 0x0001;
const TAG = 'ForEachTaintLeak';
class DataItem {
    id: number;
    label: string;
    constructor(id: number, label: string) {
        this.id = id;
        this.label = label;
    }
}
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__dataList = new ObservedPropertyObjectPU([
            new DataItem(1, 'Item One'),
            new DataItem(2, 'Item Two'),
            new DataItem(3, 'Item Three'),
            new DataItem(4, 'Item Four'),
            new DataItem(5, 'Item Five')
        ], this, "dataList");
        this.deviceBrand = '';
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.dataList !== undefined) {
            this.dataList = params.dataList;
        }
        if (params.deviceBrand !== undefined) {
            this.deviceBrand = params.deviceBrand;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__dataList.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__dataList.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __dataList: ObservedPropertyObjectPU<DataItem[]>;
    get dataList() {
        return this.__dataList.get();
    }
    set dataList(newValue: DataItem[]) {
        this.__dataList.set(newValue);
    }
    // Taint source: device brand information
    private deviceBrand: string;
    aboutToAppear(): void {
        // Source: read sensitive device info
        this.deviceBrand = deviceInfo.brand;
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.height('100%');
            Column.width('100%');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('ForEach Taint Leak Benchmark');
            Text.fontSize(20);
            Text.fontWeight(FontWeight.Bold);
            Text.margin({ top: 20, bottom: 10 });
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            List.create();
            List.width('100%');
            List.layoutWeight(1);
        }, List);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // ForEach loop rendering - taint propagates through itemGenerator callback
            ForEach.create();
            const forEachItemGenFunction = (_item, index: number) => {
                const item = _item;
                {
                    const itemCreation = (elmtId, isInitialRender) => {
                        ViewStackProcessor.StartGetAccessRecordingFor(elmtId);
                        ListItem.create(deepRenderFunction, true);
                        if (!isInitialRender) {
                            ListItem.pop();
                        }
                        ViewStackProcessor.StopGetAccessRecording();
                    };
                    const itemCreation2 = (elmtId, isInitialRender) => {
                        ListItem.create(deepRenderFunction, true);
                    };
                    const deepRenderFunction = (elmtId, isInitialRender) => {
                        itemCreation(elmtId, isInitialRender);
                        this.observeComponentCreation2((elmtId, isInitialRender) => {
                            Row.create();
                            Row.width('100%');
                            Row.onClick(() => {
                                // Sink: tainted data leaked via hilog.info inside ForEach callback
                                hilog.info(DOMAIN, TAG, 'Item clicked: %{public}s, Device Brand: %{public}s', item.label, this.deviceBrand);
                            });
                        }, Row);
                        this.observeComponentCreation2((elmtId, isInitialRender) => {
                            Text.create(`${item.id}. ${item.label}`);
                            Text.fontSize(16);
                            Text.padding(12);
                        }, Text);
                        Text.pop();
                        Row.pop();
                        ListItem.pop();
                    };
                    this.observeComponentCreation2(itemCreation2, ListItem);
                    ListItem.pop();
                }
            };
            this.forEachUpdateFunction(elmtId, this.dataList, forEachItemGenFunction, (item: DataItem) => item.id.toString(), true, false);
        }, ForEach);
        // ForEach loop rendering - taint propagates through itemGenerator callback
        ForEach.pop();
        List.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('Add Item & Trigger Leak');
            Button.width('90%');
            Button.margin({ bottom: 20 });
            Button.onClick(() => {
                const newId = this.dataList.length + 1;
                this.dataList.push(new DataItem(newId, `Item ${this.dataList.length + 1}`));
                // Sink: tainted data leaked via hilog.info when modifying ForEach data source
                hilog.info(DOMAIN, TAG, 'List updated, total: %{public}d, Device Brand: %{public}s', this.dataList.length, this.deviceBrand);
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
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.foreach", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
