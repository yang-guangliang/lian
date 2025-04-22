import { common, Want } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { BusinessError } from '@kit.BasicServicesKit';
import { deviceInfo } from '@kit.BasicServicesKit';

const TAG: string = '[Page_UIAbilityComponentsInteractive]';
const DOMAIN_NUMBER: number = 0xFF00;

const deviceInfoRecord:Record<string, string> = {
  "manufacture":deviceInfo.manufacture,
  "deviceType":deviceInfo.deviceType,
  "brand":deviceInfo.brand,
  "marketName":deviceInfo.marketName,
  "productSeries":deviceInfo.productSeries
}

@Entry
@Component
struct Page_UIAbilityComponentsInteractive {
  private context = getContext(this) as common.UIAbilityContext;

  @State infoName:string = "brand";
  @State customPopup: boolean = false;
  getDeviceInfo(name:string):string {
    return deviceInfoRecord[name];
  }
  // 第二步：popup构造器定义弹框内容
  @Builder popupBuilder() {
    Column({ space: 2 }) {
      Row().width(64)
        .height(64)
        .backgroundColor(0x409eff)
      Text('Popup')
        .fontSize(10)
        .fontColor(Color.White)
    }
    .justifyContent(FlexAlign.SpaceAround)
    .width(100)
    .height(100)
    .padding(5)
  }
  build() {
    Column() {
      //...
      List({ initialIndex: 0 }) {
        ListItem() {
          Column() {
            Button(`start an Ability`)
              .fontSize(30)
              .fontWeight(FontWeight.Bold)
              .margin(20)
              .onClick(() => {
                // context为Ability对象的成员，在非Ability对象内部调用需要
                // 将Context对象传递过去
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
              })

            Button(`pop up`)
              .onClick(() => {
                this.customPopup = !this.customPopup;
              })
              .backgroundColor(0xf56c6c)
                // 第三步：使用bindPopup接口将弹窗内容绑定给元素
              .bindPopup(this.customPopup, {
                builder: this.popupBuilder,
                placement: Placement.Right,
                maskColor: 0x33000000,
                popupColor: 0xf56c6c,
                enableArrow: true,
                onStateChange: (e) => {
                  if (!e.isVisible) {
                    this.customPopup = false;
                  }
                }
              })
            Text(this.getDeviceInfo(this.infoName))
            //...
          }

        }
        //...
      }
      //...
    }
    //...
  }
}