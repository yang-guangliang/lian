async function hc(){
  let samplePointReadRequest: SamplePointReadRequest = {
    samplePointDataType: healthStore.samplePointHelper.bodyTemperature.DATA_TYPE,
    startTime: 1698633801000,
    endTime: 1698633801000,
    fields: {
      bodyTemperature: 39
    }
  }

  const sequenceReadRequest: ExerciseSequenceReadRequest<healthStore.exerciseSequenceHelper.running.DetailFields> = {
    startTime: 1698633801000,
    endTime: 1698633801000,
    exerciseType: healthStore.exerciseSequenceHelper.running.EXERCISE_TYPE,
    count: 1,
    sortOrder: 1,
    readOptions: {
      withPartialDetails: ['exerciseHeartRate', 'altitude']
    }
  };

  let healthSequenceReadRequest: HealthSequenceReadRequest = {
    healthSequenceDataType: healthStore.healthSequenceHelper.sleepRecord.DATA_TYPE,
    startTime: 1695740400000,
    endTime: 1695769200000,
    readOptions: {
      withDetails: true
    }
  }
  let a = samplePointReadRequest
  let b = sequenceReadRequest
  let c = healthSequenceReadRequest
    let samplePoints = await healthStore.readData(a);

    const healthSequences = await healthStore.readData(b);

    const runningSequences = await healthStore.readData<healthStore.exerciseSequenceHelper.running.Model>(c);

}