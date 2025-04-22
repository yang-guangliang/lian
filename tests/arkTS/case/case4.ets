let wantInfo: Want = {
    deviceId: '', // deviceId为空表示本设备
    bundleName: 'com.example.abilitytest',
    moduleName: '', // moduleName非必选
    abilityName: 'FuncAbility',
    parameters: {
    // 自定义信息
    info: '来自EntryAbility Page_UIAbilityComponentsInteractive页面'
    },
};
hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onWindowStageCreate');
// hilog.info(0x0000, 'testTag', '%{public}s', deviceInfo.deviceType)
// context为调用方UIAbility的UIAbilityContext
this.context.startAbilityForResult(wantInfo).then(() => {
    hilog.info(DOMAIN_NUMBER, TAG, 'startAbility success.');
}).catch((error: BusinessError) => {
    hilog.error(DOMAIN_NUMBER, TAG, 'startAbility failed.');
});