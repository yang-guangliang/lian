if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
import deviceInfo from "@ohos:deviceInfo";
import { PersonalInfoViewVM } from "@normalized:N&&&entry/src/main/ets/viewmodels/PersonalInfoViewVM&";
import type { ApiHandler, PersonalInfo, SwitchInfo } from "@normalized:N&&&entry/src/main/ets/viewmodels/PersonalInfoViewVM&";
class PersonalInfoView extends ViewV2 {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda, extraInfo) {
        super(parent, elmtId, extraInfo);
        this.initParam("switchInfo", (params && "switchInfo" in params) ? params.switchInfo : {});
        this.initParam("personalInfo", (params && "personalInfo" in params) ? params.personalInfo : {});
        this.initParam("apiInfo", (params && "apiInfo" in params) ? params.apiInfo : {});
        this.vm = new PersonalInfoViewVM();
        this.finalizeConstruction();
    }
    public resetStateVarsOnReuse(params: Object): void {
        this.resetParam("switchInfo", (params && "switchInfo" in params) ? params.switchInfo : {});
        this.resetParam("personalInfo", (params && "personalInfo" in params) ? params.personalInfo : {});
        this.resetParam("apiInfo", (params && "apiInfo" in params) ? params.apiInfo : {});
        this.vm = new PersonalInfoViewVM();
        this.resetMonitorsOnReuse();
    }
    @Param
    readonly switchInfo: SwitchInfo;
    @Param
    readonly personalInfo: PersonalInfo;
    @Param
    readonly apiInfo: ApiHandler;
    @Local
    vm: PersonalInfoViewVM;
    aboutToAppear(): void {
        this.vm.assignSwitchInfo(this.switchInfo);
        this.vm.assignPersonalInfo(this.personalInfo);
        this.vm.assignApiInfo(this.apiInfo);
        this.vm.collectList();
    }
    @Monitor('personalInfo')
    onPersonalInfoChanged(monitor: IMonitor): void {
        const personalInfoValue = monitor.value<PersonalInfo>('personalInfo');
        if (personalInfoValue === undefined) {
            return;
        }
        this.vm.assignPersonalInfo(personalInfoValue.now);
        const changedData = this.vm.buildChangedData();
        if ((changedData.nickName ?? '').length > 0) {
            console.log('personal info auto sync, all data: ' + JSON.stringify(changedData)); // TAINT_SINK
        }
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.width('100%');
            Column.alignItems(HorizontalAlign.Center);
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.vm.personalData.nickName ?? '');
            Text.fontSize(20);
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.vm.personalData.phoneNumber ?? '');
            Text.fontSize(16);
        }, Text);
        Text.pop();
        Column.pop();
    }
    public updateStateVars(params) {
        if (params === undefined) {
            return;
        }
        if ("switchInfo" in params) {
            this.updateParam("switchInfo", params.switchInfo);
        }
        if ("personalInfo" in params) {
            this.updateParam("personalInfo", params.personalInfo);
        }
        if ("apiInfo" in params) {
            this.updateParam("apiInfo", params.apiInfo);
        }
    }
    rerender() {
        this.updateDirtyElements();
    }
}
class Index extends ViewV2 {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda, extraInfo) {
        super(parent, elmtId, extraInfo);
        this.personalInfo = {
            avatar: 'avatar://local/profile.png',
            nickName: 'guest user',
            phoneNumber: '13800138000',
            introDesc: 'driver license exam user profile'
        };
        this.switchInfo = {
            showAvatar: true,
            showNickName: true,
            showPhoneNumber: true,
            showIntroDesc: true
        };
        this.apiInfo = {
            updateNickName: (param: Object): Promise<void> => {
                return Promise.resolve();
            }
        };
        this.finalizeConstruction();
    }
    public resetStateVarsOnReuse(params: Object): void {
        this.personalInfo = {
            avatar: 'avatar://local/profile.png',
            nickName: 'guest user',
            phoneNumber: '13800138000',
            introDesc: 'driver license exam user profile'
        };
        this.switchInfo = {
            showAvatar: true,
            showNickName: true,
            showPhoneNumber: true,
            showIntroDesc: true
        };
        this.apiInfo = {
            updateNickName: (param: Object): Promise<void> => {
                return Promise.resolve();
            }
        };
    }
    @Local
    personalInfo: PersonalInfo;
    @Local
    switchInfo: SwitchInfo;
    @Local
    apiInfo: ApiHandler;
    refreshPersonalInfo(): void {
        const updatedInfo: PersonalInfo = {};
        updatedInfo.avatar = this.personalInfo.avatar ?? '';
        updatedInfo.nickName = deviceInfo.brand; // TAINT_SOURCE
        updatedInfo.phoneNumber = this.personalInfo.phoneNumber ?? '';
        updatedInfo.introDesc = this.personalInfo.introDesc ?? '';
        this.personalInfo = updatedInfo;
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 12 });
            Column.width('100%');
            Column.height('100%');
            Column.justifyContent(FlexAlign.Center);
            Column.alignItems(HorizontalAlign.Center);
        }, Column);
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new PersonalInfoView(this, {
                        switchInfo: this.switchInfo,
                        personalInfo: this.personalInfo,
                        apiInfo: this.apiInfo
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/Index.ets", line: 76, col: 7 });
                    ViewV2.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            switchInfo: this.switchInfo,
                            personalInfo: this.personalInfo,
                            apiInfo: this.apiInfo
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        switchInfo: this.switchInfo,
                        personalInfo: this.personalInfo,
                        apiInfo: this.apiInfo
                    });
                }
            }, { name: "PersonalInfoView" });
        }
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('Load Profile');
            Button.onClick(() => {
                this.refreshPersonalInfo();
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
registerNamedRoute(() => new Index(undefined, {}), "", { bundleName: "com.example.loop1", moduleName: "entry", pagePath: "pages/Index", pageFullPath: "entry/src/main/ets/pages/Index", integratedHsp: "false", moduleType: "followWithHap" });
