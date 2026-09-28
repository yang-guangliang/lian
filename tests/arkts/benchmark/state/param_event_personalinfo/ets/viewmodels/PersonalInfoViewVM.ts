export enum DataType {
    AVATAR = "avatar",
    NICK_NAME = "nickName",
    PHONE_NUMBER = "phoneNumber",
    INTRO_DESC = "introDesc"
}
export interface PersonalInfo {
    avatar?: string;
    nickName?: string;
    phoneNumber?: string;
    introDesc?: string;
}
export interface SwitchInfo {
    showAvatar?: boolean;
    showNickName?: boolean;
    showPhoneNumber?: boolean;
    showIntroDesc?: boolean;
}
export interface ApiHandler {
    updateAvatar?: (param: Object) => Promise<void>;
    updateNickName?: (param: Object) => Promise<void>;
    updatePhoneNumber?: (param: Object) => Promise<void>;
    updateIntro?: (param: Object) => Promise<void>;
}
export class ObservedInfoItem {
    value: string = '';
    onChange: (param?: Object) => void = () => { };
    constructor(value: string, onChange: (param?: Object) => void) {
        this.value = value;
        this.onChange = onChange;
    }
}
export class PersonalInfoViewVM {
    switchInfo: SwitchInfo = {};
    personalData: PersonalInfo = {};
    apiInfo: ApiHandler = {};
    nickNameItem: ObservedInfoItem = new ObservedInfoItem('', () => { });
    assignSwitchInfo(data: SwitchInfo): void {
        this.switchInfo.showAvatar = data.showAvatar ?? true;
        this.switchInfo.showNickName = data.showNickName ?? true;
        this.switchInfo.showPhoneNumber = data.showPhoneNumber ?? true;
        this.switchInfo.showIntroDesc = data.showIntroDesc ?? true;
    }
    assignPersonalInfo(data: PersonalInfo): void {
        this.personalData.avatar = data.avatar ?? '';
        this.personalData.nickName = data.nickName ?? '';
        this.personalData.phoneNumber = data.phoneNumber ?? '';
        this.personalData.introDesc = data.introDesc ?? '';
    }
    assignApiInfo(apiInfo: ApiHandler): void {
        this.apiInfo.updateAvatar = apiInfo.updateAvatar ?? (() => Promise.resolve());
        this.apiInfo.updateNickName = apiInfo.updateNickName ?? (() => Promise.resolve());
        this.apiInfo.updatePhoneNumber = apiInfo.updatePhoneNumber ?? (() => Promise.resolve());
        this.apiInfo.updateIntro = apiInfo.updateIntro ?? (() => Promise.resolve());
    }
    buildChangedData(): PersonalInfo {
        const fields: DataType[] = [DataType.AVATAR, DataType.NICK_NAME, DataType.PHONE_NUMBER, DataType.INTRO_DESC];
        const changedData: PersonalInfo = {};
        for (let index = 0; index < fields.length; index++) {
            switch (fields[index]) {
                case DataType.AVATAR:
                    if (this.switchInfo.showAvatar) {
                        changedData.avatar = this.personalData.avatar ?? '';
                    }
                    break;
                case DataType.NICK_NAME:
                    if (this.switchInfo.showNickName) {
                        changedData.nickName = this.personalData.nickName ?? '';
                    }
                    break;
                case DataType.PHONE_NUMBER:
                    if (this.switchInfo.showPhoneNumber) {
                        changedData.phoneNumber = this.personalData.phoneNumber ?? '';
                    }
                    break;
                case DataType.INTRO_DESC:
                    if (this.switchInfo.showIntroDesc) {
                        changedData.introDesc = this.personalData.introDesc ?? '';
                    }
                    break;
            }
        }
        return changedData;
    }
    collectList(): void {
        if (this.switchInfo.showNickName) {
            this.nickNameItem = new ObservedInfoItem(this.personalData.nickName ?? '', (param?: Object) => {
                this.nickNameItem.value = param as string;
                this.personalData.nickName = param as string;
            });
        }
    }
}
