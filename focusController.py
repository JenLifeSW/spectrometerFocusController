from PySide6.QtCore import QObject, Signal, Slot, QTimer

TAG = "     포커스 모듈 : "


def use_mm(value):
    return value/1000


def use_um(value):
    return value/1000000


class Command:
    RESUEME = 1
    PAUSE = 2
    RESTART = 3


class StepRange:
    step = [-use_um(1562), -use_um(625), -use_um(250), -use_um(50), -use_um(10)]
    targetPointCnt = [6, 6, 6, 11, 11]

    def getStepRange(self, num):
        return self.step[num:], self.targetPointCnt[num:]

# 시그널 만들기 (pointCnt, 현재 라운드 목표 카운트, 현재라운드)
class FocusController(QObject):
    testing = False
    isCompleted = False

    normalLogSignal = Signal(str)
    initFocusingSignal = Signal()

    alreadyRunningSignal = Signal()
    alreadyStoppedSignal = Signal()
    measuredSignal = Signal(int, int, int)      # (현재 라운드 측정 횟수, 현재 라운드 목표 측정 횟수, 현재 라운드)
    focusCompleteSignal = Signal(list, int)
    focusDisabledErr = Signal(str)

    reqDeviceConnected = Signal()
    reqConnectDevice = Signal()
    reqStopStage = Signal()
    reqMoveStage = Signal(float)
    reqGetSpectrum = Signal()

    # step = [-use_um(1562), -use_um(625), -use_um(250), -use_um(50), -use_um(10)]
    # targetPointCnt = [6, 6, 6, 11, 11]
    step, targetPointCnt = StepRange().getStepRange(0)

    conReqCnt = 0
    errCnt = 0
    lastCommand = 0

    isRunning = False
    isPaused = False
    round = 0               # 현재 라운드
    startPosition = 0.0     # 스테이지 바닥 위치
    targetPosition = 0.0    # 측정을 요청할 위치
    arrivePosition = 0.0    # 스테이지 이동 요청 후 응답 받은 도착 위치
    pointCnt = 0            # 해당 라운드에서 스테이지를 이동한 횟수
    roundData = []          # 해당 라운드에서 이동하면서 수집한 데이터 [("position": "intensity")]

    ''' 스펙트럼 오차 보완용 재측정 '''
    measure = 1         # 목표 재측정 횟수
    measureCnt = 0      # 누적 횟수
    measureInterval = 1    # 재측정 간격 (ms)
    tempSumOfIntensities = 0.0    # 스펙트럼 평균

    def __init__(self, startPosition=startPosition, testing=False):
        super().__init__()
        print(f"{TAG}1 init")
        self.startPosition = startPosition
        self.testing = testing

        # self.initFocusing()

    def setStartPosition(self, startPosition):
        self.startPosition = startPosition

    def setMeasure(self, mesure):
        self.measure = mesure

    def getRoundSteps(self):    # 라운드별 측정횟수
        return self.targetPointCnt

    def initFocusing(self, restart=False):
        print(f"{TAG}2 initFocusing")

        if restart:
            self.isRunning = True
        else:
            self.lastCommand = 0
            self.isRunning = False

        self.isPaused = False
        self.round = 0

        self.initRound(self.startPosition)
        self.reqMoveStage.emit(self.targetPosition)

        if self.testing:
            self.initFocusingSignal.emit()

    def initRound(self, targetPosition):
        print(f"{TAG}3 initRound, targetPosition: {targetPosition}")
        self.targetPosition = targetPosition
        self.pointCnt = 0
        self.roundData = []
        self.initMeasureCnt()

    def initMeasureCnt(self):
        self.measureCnt = 1
        self.tempSumOfIntensities = 0.0


    @Slot()
    def resumeFocusing(self):
        print(f"{TAG}4 resumeFocusing")
        command = Command.RESUEME
        if self.lastCommand == command:
            if self.isRunning:
                print(f"{TAG}4 resumeFocusing, alreadyRunning")
                self.alreadyRunningSignal.emit()
                return

        self.lastCommand = command
        self.conReqCnt = 0

        if self.isRunning:
            if not self.isPaused:
                print(f"{TAG}4 resumeFocusing, not Running, not Paused")
                self.alreadyRunningSignal.emit()
                return
            print(f"{TAG}4 resumeFocusing, paused -> resume")

        print(f"{TAG}4 resumeFocusing, reqDeviceConnected 요청")

        if self.isCompleted:
            self.isCompleted = False
            self.restartFocusing()
        else:
            self.reqDeviceConnected.emit()

    @Slot()
    def pauseFocusing(self):
        print(f"{TAG}5 pauseFocusing")
        command = Command.PAUSE
        if self.lastCommand == command:
            self.alreadyStoppedSignal.emit()
            return

        self.lastCommand = command
        if self.isPaused:
            self.alreadyStoppedSignal.emit()
            return

        self.isPaused = True
        # self.reqStopStage.emit()

    @Slot()
    def restartFocusing(self):
        print(f"{TAG}6 restartFocusing")
        self.lastCommand = Command.RESTART
        if self.isPaused:
            self.isPaused = False
            self.conReqCnt = 0
            self.reqDeviceConnected.emit()
            return

        self.isPaused = True
        self.initFocusing(True)

    def exceptionHandling(self):
        METHOD = "7 exceptionHandling "
        self.normalLogSignal.emit("데이터 비정상")
        self.initFocusing(True)
        # if self.errCnt < 1:
        #     print(f"{TAG}{METHOD}데이터 비정상 재측정")
        #     self.initFocusing()
        #     self.errCnt += 1
        #     self.reqMoveStage.emit(self.targetPosition)
        # else:
        #     print(f"{TAG}{METHOD}재측정 횟수 초과")
        #     self.focusDisabledErr.emit("데이터 비정상")

    @Slot(bool)
    def onResDeviceConnected(self, isConnected):
        METHOD = "8 onResDeviceConnected "
        print(f"{TAG}{METHOD}isConnected: {isConnected}")
        if not isConnected:
            print(f"{TAG}{METHOD}not Connected 연결확인횟수: {self.conReqCnt+1}")
            if self.conReqCnt < 2:
                self.conReqCnt += 1
                self.reqConnectDevice.emit()
            return

        print(f"{TAG}{METHOD}isPaused: {self.isPaused}")
        if self.isPaused:
            self.isPaused = False
        else:
            self.initFocusing()

        self.isRunning = True
        print(f"{TAG}{METHOD} reqMoveDevice 요청")
        self.reqMoveStage.emit(self.targetPosition)

    @Slot(float)
    def onResMoveStage(self, position):
        METHOD = "9 onResMoveStage "
        print(f"{TAG}{METHOD}isPaused: {self.isPaused} isRunning: {self.isRunning}")
        if self.isPaused or not self.isRunning:
            return
        print(f"{TAG}{METHOD}position: {position}")
        self.arrivePosition = position

        self.reqGetSpectrum.emit()

    @Slot(float)
    def onResGetSpectrum(self, intensities):
        METHOD = "9 ResGetSpectrum "
        print(f"{TAG}{METHOD}isPaused: {self.isPaused} isRunning: {self.isRunning}")
        self.measuredSignal.emit(self.pointCnt + 1, self.targetPointCnt[self.round], self.round)

        if self.isPaused or not self.isRunning:
            return

        self.tempSumOfIntensities += intensities

        if self.measureCnt < self.measure:
            QTimer.singleShot(self.measureInterval, self.reqGetSpectrum.emit)
            self.measureCnt += 1
            return

        position = self.arrivePosition
        self.roundData.append((position, self.tempSumOfIntensities / self.measure))

        if self.pointCnt < self.targetPointCnt[self.round] - 1:
            self.pointCnt += 1
            self.initMeasureCnt()
            self.targetPosition = position + self.step[self.round]
            print(f"{TAG}{METHOD}next targetPosition: {self.targetPosition}")

            self.reqMoveStage.emit(self.targetPosition)
            return

        intensitiesList = [data[1] for data in self.roundData]
        maxIdx = intensitiesList.index(max(intensitiesList))

        #self.normalLogSignal.emit(f"{TAG}{METHOD}라운드: {self.round} maxIdx: {maxIdx} max value: {round(intensitiesList[maxIdx], 3)}")
        #if self.round == len(self.targetPointCnt) - 1:
        for i, d in enumerate(self.roundData):
            log = f"{TAG}{METHOD}라운드: {self.round}, position: {round(d[0] * 1000, 3)}, intensities: {round(d[1], 3)}"
            if i == maxIdx: log += "\tmax"
            self.normalLogSignal.emit(log)

        if self.round < len(self.targetPointCnt) - 1:

            if not (maxIdx == 0 or maxIdx == self.targetPointCnt[self.round] - 1):
                targetPosition = self.roundData[maxIdx][0] - self.step[self.round]
                self.round += 1
                self.initRound(targetPosition)
                self.normalLogSignal.emit(f"{TAG}{METHOD}round complete. 다음 라운드 측정 진행. reqMoveStage to {self.targetPosition}")
                self.reqMoveStage.emit(self.targetPosition)
                return

            if self.round == 0:
                if maxIdx == 0:
                    self.round += 1
                    self.initRound(self.startPosition)
                    self.normalLogSignal.emit(f"{TAG}{METHOD}First is Max. 다음 라운드 측정 진행. reqMoveStage to {self.targetPosition}")
                    self.reqMoveStage.emit(self.targetPosition)
                    return

                else:
                    self.normalLogSignal.emit(f"{TAG}{METHOD}End is Max. 현재 라운드 측정 유지. reqMoveStage to {self.targetPosition}")
                    targetPosition = position - 2 * self.step[0]
                    self.initRound(targetPosition)
                    self.reqMoveStage.emit(self.targetPosition)
                    return

            self.exceptionHandling()
            return

        else:
            print(f"{TAG}{METHOD}포커싱 완료")
            self.isRunning = False
            self.isCompleted = True
            self.focusCompleteSignal.emit(self.roundData, maxIdx)

    @Slot(float, float)
    def onExePositionOver(self, position, intensity):
        METHOD = "10 onExePositionOver"
        print(f"{TAG}{METHOD}라운드 : {self.round}, 캡쳐 위치: {self.pointCnt}")
        if self.round > 0:
            self.exceptionHandling()
            return
        if self.pointCnt <= 2:
            self.exceptionHandling()
            return

        self.roundData.append((position, intensity))

        intensities = [data[1] for data in self.roundData]
        maxIdx = intensities.index(max(intensities))
        sortedData = sorted(self.roundData, key=lambda x: x[1])
        diff = sortedData[0][0] - sortedData[1][0]

        print(f"{TAG}{METHOD}data: {self.roundData}, maxIds: {maxIdx}, diff: {diff}")

        if (maxIdx == 0) or (maxIdx == self.pointCnt-1):
            self.exceptionHandling()
            return

        targetRound = 0
        for idx, s in enumerate(self.step[self.round:]):
            if s < diff:
                targetRound = idx - 1
                break

        print(f"{TAG}{METHOD}targetRound: {targetRound}")
        if targetRound < 1:
            self.exceptionHandling()
            return
        self.round = targetRound
        targetPosition = sortedData[0][0] - self.step[self.round]
        self.initRound(targetPosition)
        print(f"{TAG}{METHOD}next targetPosition: {self.targetPosition}")

        self.reqMoveStage.emit(self.targetPosition)

    @Slot()
    def onResStopStage(self):
        print(f"{TAG}11 onResStopStage")
