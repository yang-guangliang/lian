if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface Index_Params {
    message?: string;
    context?: Context | undefined;
}
import backgroundTaskManager from "@ohos:resourceschedule.backgroundTaskManager";
import type { BusinessError as BusinessError } from "@ohos:base";
import deviceInfo from "@ohos:deviceInfo";
import wantAgent from "@ohos:app.ability.wantAgent";
import type { WantAgent as WantAgent } from "@ohos:app.ability.wantAgent";
import hilog from "@ohos:hilog";
import taskpool from "@ohos:taskpool";
// 在元服务中，请删除WantAgent导入
const DOMAIN = 0x0000;
function callback(info: backgroundTaskManager.ContinuousTaskCancelInfo) {
    // 长时任务id
    console.info('OnContinuousTaskCancel callback id ' + info.id);
    // 长时任务取消原因
    console.info('OnContinuousTaskCancel callback reason ' + info.reason);
}
class Index extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__message = new ObservedPropertySimplePU('ContinuousTask', this, "message");
        this.context = this.getUIContext().getHostContext();
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: Index_Params) {
        if (params.message !== undefined) {
            this.message = params.message;
        }
        if (params.context !== undefined) {
            this.context = params.context;
        }
    }
    updateStateVars(params: Index_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__message.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__message.aboutToBeDeleted();
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
    // 通过getUIContext().getHostContext()方法，来获取page所在的UIAbility上下文
    private context: Context | undefined;
    OnContinuousTaskCancel() {
        try {
            backgroundTaskManager.on("continuousTaskCancel", callback);
            console.info(`Succeeded in operationing OnContinuousTaskCancel.`);
        }
        catch (error) {
            console.error(`Operation OnContinuousTaskCancel failed. code is ${(error as BusinessError).code} message is ${(error as BusinessError).message}`);
        }
    }
    OffContinuousTaskCancel() {
        try {
            // callback参数不传，则取消所有已注册的回调
            backgroundTaskManager.off("continuousTaskCancel", callback);
            console.info(`Succeeded in operationing OffContinuousTaskCancel.`);
        }
        catch (error) {
            console.error(`Operation OffContinuousTaskCancel failed. code is ${(error as BusinessError).code} message is ${(error as BusinessError).message}`);
        }
    }
    // 申请长时任务.then()写法
    startContinuousTask() {
        let wantAgentInfo: wantAgent.WantAgentInfo = {
            // 点击通知后，将要执行的动作列表
            // 添加需要被拉起应用的bundleName和abilityName
            wants: [
                {
                    bundleName: "com.example.myapplication",
                    abilityName: "MainAbility"
                }
            ],
            // 指定点击通知栏消息后的动作是拉起ability
            actionType: wantAgent.OperationType.START_ABILITY,
            // 使用者自定义的一个私有值
            requestCode: 0,
            // 点击通知后，动作执行属性
            actionFlags: [wantAgent.WantAgentFlags.UPDATE_PRESENT_FLAG],
            // 车钥匙长时任务子类型，从API version 16开始支持。只有申请bluetoothInteraction类型的长时任务，车钥匙子类型才能生效。
            // 确保extraInfo参数中的Key值为backgroundTaskManager.BackgroundModeType.SUB_MODE，否则子类型不生效。
            // extraInfo: { [backgroundTaskManager.BackgroundModeType.SUB_MODE] : backgroundTaskManager.BackgroundSubMode.CAR_KEY }
        };
        try {
            // 通过wantAgent模块下getWantAgent方法获取WantAgent对象
            // 在元服务中，使用wantAgent.getWantAgent(wantAgentInfo).then((wantAgentObj: object) => {替换下面一行代码
            wantAgent.getWantAgent(wantAgentInfo).then((wantAgentObj: WantAgent) => {
                try {
                    let list: Array<string> = ["audioRecording"];
                    // let list: Array<string> = ["bluetoothInteraction"]; 长时任务类型包含bluetoothInteraction，CAR_KEY子类型合法
                    // 在元服务中，let list: Array<string> = ["audioPlayback"];
                    backgroundTaskManager.startBackgroundRunning(this.context, list, wantAgentObj).then((res: backgroundTaskManager.ContinuousTaskNotification) => {
                        console.info("Operation startBackgroundRunning succeeded");
                        hilog.info(DOMAIN, 'testTag', deviceInfo.brand);
                        // 此处执行具体的长时任务逻辑，如录音，录制等。
                        // 系统会对业务场景的真实性进行检测，如果没有实际执行对应的业务，系统可能会取消对应的长时任务并挂起应用。
                    }).catch((error: BusinessError) => {
                        console.error(`Failed to Operation startBackgroundRunning. code is ${error.code} message is ${error.message}`);
                    });
                }
                catch (error) {
                    console.error(`Failed to Operation startBackgroundRunning. code is ${(error as BusinessError).code} message is ${(error as BusinessError).message}`);
                }
            });
        }
        catch (error) {
            console.error(`Failed to Operation getWantAgent. code is ${(error as BusinessError).code} message is ${(error as BusinessError).message}`);
        }
    }
    // 取消长时任务.then()写法
    stopContinuousTask() {
        backgroundTaskManager.stopBackgroundRunning(this.context).then(() => {
            console.info(`Succeeded in operationing stopBackgroundRunning.`);
        }).catch((err: BusinessError) => {
            console.error(`Failed to operation stopBackgroundRunning. Code is ${err.code}, message is ${err.message}`);
        });
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.height('100%');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.width('100%');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create("Index");
            Text.fontSize(50);
            Text.fontWeight(FontWeight.Bold);
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithChild();
            Button.type(ButtonType.Capsule);
            Button.margin({ top: 10 });
            Button.backgroundColor('#0D9FFB');
            Button.width(250);
            Button.height(40);
            Button.onClick(() => {
                // 通过按钮申请长时任务
                this.startContinuousTask();
            });
        }, Button);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('申请长时任务');
            Text.fontSize(25);
            Text.fontWeight(FontWeight.Bold);
        }, Text);
        Text.pop();
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithChild();
            Button.type(ButtonType.Capsule);
            Button.margin({ top: 10 });
            Button.backgroundColor('#0D9FFB');
            Button.width(250);
            Button.height(40);
            Button.onClick(() => {
                // 此处结束具体的长时任务的执行
                // 通过按钮取消长时任务
                this.stopContinuousTask();
            });
        }, Button);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('取消长时任务');
            Text.fontSize(25);
            Text.fontWeight(FontWeight.Bold);
        }, Text);
        Text.pop();
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithChild();
            Button.type(ButtonType.Capsule);
            Button.margin({ top: 10 });
            Button.backgroundColor('#0D9FFB');
            Button.width(250);
            Button.height(40);
            Button.onClick(() => {
                // 通过按钮注册长时任务取消回调
                this.OnContinuousTaskCancel();
            });
        }, Button);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('注册长时任务取消回调');
            Text.fontSize(25);
            Text.fontWeight(FontWeight.Bold);
        }, Text);
        Text.pop();
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithChild();
            Button.type(ButtonType.Capsule);
            Button.margin({ top: 10 });
            Button.backgroundColor('#0D9FFB');
            Button.width(250);
            Button.height(40);
            Button.onClick(() => {
                // 通过按钮取消注册长时任务取消回调
                this.OffContinuousTaskCancel();
                testArrayBuffer();
            });
        }, Button);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('取消注册长时任务取消回调');
            Text.fontSize(25);
            Text.fontWeight(FontWeight.Bold);
        }, Text);
        Text.pop();
        Button.pop();
        Column.pop();
        Row.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "Index";
    }
}
function printArrayBuffer(buffer: ArrayBuffer) {
    "use concurrent";
    let brand = deviceInfo.brand;
    let DOMAIN = 0x000;
    hilog.info(DOMAIN, 'testTag', brand);
    return buffer;
}
function testArrayBuffer() {
    const buffer = new ArrayBuffer(1);
    const group = new taskpool.TaskGroup();
    const task = new taskpool.Task(printArrayBuffer, buffer);
    group.addTask(task);
    task.setCloneList([buffer]);
    for (let i = 0; i < 5; i++) {
        taskpool.execute(group).then(() => {
            console.info('execute group success');
        }).catch((e: BusinessError) => {
            console.error(`execute group error: ${e.message}`);
        });
    }
}
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.background_task_long", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
