import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import hilog from "@ohos:hilog";
import type window from "@ohos:window";
import healthStore from "@bundle:com.huawei.hmos.health.kit/HealthStore/ets/Index";
import deviceInfo from "@ohos:deviceInfo";
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onCreate');
    }
    onDestroy(): void {
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onDestroy');
    }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        // Main window is created, set main page for this ability
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onWindowStageCreate');
        windowStage.loadContent('pages/Index', (err) => {
            if (err.code) {
                hilog.error(0x0000, 'testTag', 'Failed to load the content. Cause: %{public}s', JSON.stringify(err) ?? '');
                return;
            }
            hilog.info(0x0000, 'testTag', 'Succeeded in loading the content.');
        });
        this.send_healthseq();
    }
    onWindowStageDestroy(): void {
        // Main window is destroyed, release UI related resources
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onWindowStageDestroy');
    }
    onForeground(): void {
        // Ability has brought to foreground
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onForeground');
    }
    onBackground(): void {
        // Ability has back to background
        hilog.info(0x0000, 'testTag', '%{public}s', 'Ability onBackground');
    }
    async send_healthseq(): Promise<void> {
        let healthSequenceReadRequest: healthStore.HealthSequenceReadRequest = {
            healthSequenceDataType: healthStore.healthSequenceHelper.sleepRecord.DATA_TYPE,
            startTime: 1695740400000,
            endTime: 1695769200000,
            readOptions: {
                withDetails: true
            }
        };
        // 查询跑步记录
        let sequenceReadRequest: healthStore.ExerciseSequenceReadRequest<healthStore.exerciseSequenceHelper.running.DetailFields> = {
            startTime: 1698040800000,
            endTime: 1698042600000,
            exerciseType: healthStore.exerciseSequenceHelper.running.EXERCISE_TYPE,
            count: 1,
            sortOrder: 1,
            readOptions: {
                withPartialDetails: ['exerciseHeartRate', 'altitude']
            }
        };
        try {
            healthStore.init(getContext(this));
            const healthSequences = await healthStore.readData(healthSequenceReadRequest);
            const runningsequences = await healthStore.readData(sequenceReadRequest);
            hilog.info(0x0000, 'testTag', 'Succeeded in reading data.');
            hilog.info(0x0000, 'testTag', '%{public}s', deviceInfo.brand);
            healthSequences.forEach((healthSequence) => {
                hilog.info(0x0000, 'testTag', `the start time is ${healthSequence.startTime}.`);
                hilog.info(0x0000, 'testTag', `the end time is ${healthSequence.endTime}.`);
                Object.keys(healthSequence.summaries).forEach((key) => {
                    hilog.info(0x0000, 'testTag', `the summaries of ${key} is ${healthSequence.summaries[key]}.`);
                });
            });
        }
        catch (err) {
            hilog.error(0x0000, 'testTag', `Failed to read data. Code: ${err.code}, message: ${err.message}`);
        }
    }
}
