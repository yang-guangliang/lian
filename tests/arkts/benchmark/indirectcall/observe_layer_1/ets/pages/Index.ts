if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    message?: string;
    cls1?: Child;
}
@Observed
class cc {
    public st: string;
    constructor(st: string) {
        this.st = st;
    }
}
@Observed
class Child {
    public c: cc;
    constructor(c: cc) {
        this.c = c;
    }
}
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__message = new ObservedPropertySimplePU('Hello World', this, "message");
        this.__cls1 = new ObservedPropertyObjectPU(new Child(new cc("9")), this, "cls1");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.message !== undefined) {
            this.message = params.message;
        }
        if (params.cls1 !== undefined) {
            this.cls1 = params.cls1;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__message.purgeDependencyOnElmtId(rmElmtId);
        this.__cls1.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__message.aboutToBeDeleted();
        this.__cls1.aboutToBeDeleted();
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
    private __cls1: ObservedPropertyObjectPU<Child>;
    get cls1() {
        return this.__cls1.get();
    }
    set cls1(newValue: Child) {
        this.__cls1.set(newValue);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.height('100%');
            Column.width('100%');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(`BookCard: ${this.cls1.c.st}`);
            Text.width(320);
            Text.margin(10);
            Text.textAlign(TextAlign.Center);
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel(this.message);
            Button.id('HelloWorld');
            Button.fontSize({ "id": 16777224, "type": 10002, params: [], "bundleName": "com.example.observe_layer_1", "moduleName": "entry" });
            Button.fontWeight(FontWeight.Bold);
            Button.alignRules({
                center: { anchor: '__container__', align: VerticalAlign.Center },
                middle: { anchor: '__container__', align: HorizontalAlign.Center }
            });
            Button.onClick(() => {
                this.message = 'Welcome';
                this.cls1.c.st = "6";
            });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel(this.cls1.c.st);
            Button.id('HelloWorld');
            Button.fontSize({ "id": 16777224, "type": 10002, params: [], "bundleName": "com.example.observe_layer_1", "moduleName": "entry" });
            Button.fontWeight(FontWeight.Bold);
            Button.alignRules({
                center: { anchor: '__container__', align: VerticalAlign.Center },
                middle: { anchor: '__container__', align: HorizontalAlign.Center }
            });
            Button.onClick(() => {
                this.message = 'Welcome';
                this.cls1.c.st = "6";
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
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.observe_layer_1", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
