if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface CountDownComponent_Params {
    count?: string;
    costOfOneAttempt?: number;
}
import hilog from "@ohos:hilog";
const DOMAIN = 0x0000;
export class CountDownComponent extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.count = "123";
        this.costOfOneAttempt = 1;
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: CountDownComponent_Params) {
        if (params.count !== undefined) {
            this.count = params.count;
        }
        if (params.costOfOneAttempt !== undefined) {
            this.costOfOneAttempt = params.costOfOneAttempt;
        }
    }
    updateStateVars(params: CountDownComponent_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
    }
    aboutToBeDeleted() {
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private count: string;
    private costOfOneAttempt: number;
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.costOfOneAttempt > 0) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(`You have ${this.count} Nuggets left`);
                    }, Text);
                    Text.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('Game over!');
                    }, Text);
                    Text.pop();
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // @Prop装饰的变量不会同步给父组件
            Button.createWithLabel(`Try again`);
            // @Prop装饰的变量不会同步给父组件
            Button.onClick(() => {
                hilog.info(DOMAIN, 'testTag', this.count);
            });
        }, Button);
        // @Prop装饰的变量不会同步给父组件
        Button.pop();
        Column.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
