if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    tmsg?: string;
}
import deviceInfo from "@ohos:deviceInfo";
import { CountDownComponent } from "@normalized:N&&&entry/src/main/ets/pages/CountDownComponent&";
const DOMAIN = 0x0000;
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__tmsg = new ObservedPropertySimplePU("10", this, "tmsg");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.tmsg !== undefined) {
            this.tmsg = params.tmsg;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__tmsg.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__tmsg.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __tmsg: ObservedPropertySimplePU<string>;
    get tmsg() {
        return this.__tmsg.get();
    }
    set tmsg(newValue: string) {
        this.__tmsg.set(newValue);
    }
    onPageShow(): void {
        this.tmsg = deviceInfo.brand;
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(`Grant ${this.tmsg} nuggets to play.`);
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 父组件的数据源的修改会同步给子组件
            Button.createWithLabel(`+1 - Nuggets in New Game`);
            // 父组件的数据源的修改会同步给子组件
            Button.onClick(() => {
                this.tmsg = deviceInfo.brand;
            });
        }, Button);
        // 父组件的数据源的修改会同步给子组件
        Button.pop();
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new CountDownComponent(this, { count: this.tmsg, costOfOneAttempt: 2 }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/Index.ets", line: 22, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            count: this.tmsg,
                            costOfOneAttempt: 2
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {});
                }
            }, { name: "CountDownComponent" });
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
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.propstate", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
