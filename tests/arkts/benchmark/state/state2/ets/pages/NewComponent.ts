if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface NewComponent_Params {
    text?: string | Resource;
    method?: (event?: ClickEvent) => void;
}
export class NewComponent extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.text = '';
        this.method = (): void => {
        };
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: NewComponent_Params) {
        if (params.text !== undefined) {
            this.text = params.text;
        }
        if (params.method !== undefined) {
            this.method = params.method;
        }
    }
    updateStateVars(params: NewComponent_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
    }
    aboutToBeDeleted() {
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private text: string | Resource;
    private method: (event?: ClickEvent) => void;
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel(this.text);
            Button.fontSize(20);
            Button.fontWeight(FontWeight.Normal);
            Button.align(Alignment.Center);
            Button.type(ButtonType.Capsule);
            Button.width('90%');
            Button.margin({ top: 10, bottom: 5 });
            Button.onClick(this.method);
        }, Button);
        Button.pop();
        Column.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
