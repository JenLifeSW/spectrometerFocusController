import numpy as np
from PySide6.QtCore import QObject, Signal, Slot, QTimer

TAG = "     포커스 모듈 : "


def use_mm(value):
    return value/1000


def use_um(value):
    return value/1000000


# class Command:
#     RESUEME = 1
#     PAUSE = 2
#     RESTART = 3


class Status:
    DISABLED = -1   # 기기 사용 불가
    DEFAULT = 0     # 기본 상태
    IDLE = 1        # 전원 on 상태
    INITIALING = 2  # 초기화 중
    DETECTING = 3   # 검체 감지
    FOCUSING = 4    # 포커싱 진행
    FOCUS_COMPLETING = 5        # 포커스위치로 이동
    PAUSING = 6     # 정지
    RESTARTING = 7  # 재시작 중
    COLLECTING = 8  # Intensities 수집 중
    COLLECTING_REQSPEC = 9      # Intensities 요청
    COLLECTING_MOVING = 10      # 스테이지 이동 중
    COLLECTING_PROCESSING = 11  # 데이터 처리 중

    @classmethod
    def get_name(cls, code):
        status_dict = {
            cls.DISABLED: "DISABLED",
            cls.DEFAULT: "DEFAULT",
            cls.IDLE: "IDLE",
            cls.INITIALING: "INITIALING",
            cls.DETECTING: "DETECTING",
            cls.FOCUSING: "FOCUSING",
            cls.FOCUS_COMPLETING: "FOCUS_COMPLETING",
            cls.PAUSING: "PAUSING",
            cls.RESTARTING: "RESTARTING",
            cls.COLLECTING: "COLLECTING",
            cls.COLLECTING_REQSPEC: "COLLECTING_REQSPEC",
            cls.COLLECTING_MOVING: "COLLECTING_MOVING",
            cls.COLLECTING_PROCESSING: "COLLECTING_PROCESSING",
        }
        return status_dict.get(code, "UNKNOWN")


class IntegrationTime:
    NORMAL = 5000000
    DETECTING = 500000


class StageHeight:
    KIT = use_mm(14.73)
    VOID = use_mm(7.23)


COLLECTING_TIME = 30
COLLECTING_INTEGRATIONS = [100000, 500000, 1000000, 2000000, 5000000]

SPECIMEN_VALUE = 1700
ESTIMATE_SPECIMEN_TIME = 1000

# ---------->
#
# 1. initFocusing(할 때 매개변수 없애기)
# 2. onResDeviceConnected 알고리즘 수정 필요해 보임(어떤 상타일 때 어떤 행동을 하는지?)
# 3. 현재는
# 3. isPaused, isRunning 없앨 수 있나?
# ----------<


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
    initCompleteSignal = Signal()
    initFocusingSignal = Signal()
    statusSignal = Signal(str)
    collectingCompleteSignal = Signal(dict)
    specimenDetectedSignal = Signal(bool)

    alreadyRunningSignal = Signal()
    alreadyStoppedSignal = Signal()
    measuredSignal = Signal(int, int, int)      # (현재 라운드 측정 횟수, 현재 라운드 목표 측정 횟수, 현재 라운드)
    focusCompleteSignal = Signal(np.ndarray)
    focusDisabledErr = Signal(str)

    reqDeviceConnected = Signal()
    reqConnectDevice = Signal()
    reqSetIntegrationTime = Signal(int)
    reqStopStage = Signal()
    reqMoveStage = Signal(float)

    # step = [-use_um(1562), -use_um(625), -use_um(250), -use_um(50), -use_um(10)]
    # targetPointCnt = [6, 6, 6, 11, 11]
    step, targetPointCnt = StepRange().getStepRange(0)

    conReqCnt = 0
    errCnt = 0
    # lastCommand = 0
    status = Status.DEFAULT

    isRunning = False
    isPaused = False
    round = 0               # 현재 라운드
    startPosition = 0.0     # 스테이지 바닥 위치
    targetPosition = 0.0    # 측정을 요청할 위치
    arrivePosition = 0.0    # 스테이지 이동 요청 후 응답 받은 도착 위치
    pointCnt = 0            # 해당 라운드에서 스테이지를 이동한 횟수
    roundData = []          # 해당 라운드에서 이동하면서 수집한 데이터 [("position": "intensity")]

    ''' collecting 변수 '''
    collectingTimeCount = 0
    collectingIntegrationIdx = 0
    collectingDatas = {}
    collectingTemp = []

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

        self.statusTimer = QTimer()
        self.statusTimer.timeout.connect(self.emitStatusSignal)
        self.statusTimer.start(1000)
        # self.initFocusing()

    @Slot()
    def emitStatusSignal(self):
        self.statusSignal.emit(Status.get_name(self.status))

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
            # self.lastCommand = 0
            self.status = Status.INITIALING
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

    def estimateSpecimenInserted(self, intensities):
        if intensities < SPECIMEN_VALUE:
            self.specimenDetectedSignal.emit(False)
        else:
            self.specimenDetectedSignal.emit(True)

    @Slot()
    def resumeFocusing(self):
        print(f"{TAG}4 resumeFocusing")
        command = Status.FOCUSING #Command.RESUEME
        if self.status == command: # self.lastCommand == command:
            if self.isRunning:
                print(f"{TAG}4 resumeFocusing, alreadyRunning")
                self.alreadyRunningSignal.emit()
                return

        # self.lastCommand = command
        self.status = command
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
        command = Status.PAUSING # Command.PAUSE
        if self.status == command: # self.lastCommand == command:
            self.alreadyStoppedSignal.emit()
            return

        # self.lastCommand = command
        self.status = command
        if self.isPaused:
            self.alreadyStoppedSignal.emit()
            return

        self.isPaused = True
        self.reqSetIntegrationTime.emit(IntegrationTime.DETECTING)
        self.status = Status.DETECTING
        # self.reqStopStage.emit()

    @Slot()
    def restartFocusing(self):
        print(f"{TAG}6 restartFocusing")
        # self.lastCommand = Command.RESTART
        self.status = Status.RESTARTING
        if self.isPaused:
            self.isPaused = False
            self.conReqCnt = 0
            self.reqDeviceConnected.emit()
            return

        self.isPaused = True
        self.initFocusing(True)

    # ---------- Collecting ---------- #
    @Slot()
    def moveToKitHeight(self):
        # if self.status == Status.COLLECTING_MOVING:
        #     return

        self.status = Status.COLLECTING_MOVING
        self.reqMoveStage.emit(StageHeight.KIT)

    @Slot()
    def moveToVoidHeight(self):
        # if self.status == Status.COLLECTING_MOVING:
        #     return

        self.status = Status.COLLECTING_MOVING
        self.reqMoveStage.emit(StageHeight.VOID)

    @Slot()
    def collectIntensities(self):
        print(TAG, "collectingIntensities")
        self.collectingTimeCount = 0
        self.collectingIntegrationIdx = 0
        self.status = Status.COLLECTING_PROCESSING
        self.reqSetIntegrationTime.emit(COLLECTING_INTEGRATIONS[self.collectingIntegrationIdx])

    @Slot()
    def onResSetIntegrationTime(self):
        print(TAG, "onResSetIntegrationTime")
        if self.status != Status.COLLECTING_PROCESSING:
            return

        self.status = Status.COLLECTING_REQSPEC
        # self.collectingDatas.append([])

    # ---------- ---------- #
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

        self.status = Status.IDLE
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

        if self.status == Status.INITIALING:
            self.status = Status.IDLE
            self.initCompleteSignal.emit()
            return

        if self.status == Status.COLLECTING_MOVING:
            self.status = Status.COLLECTING
            return

        if self.isPaused or not self.isRunning:
            self.reqSetIntegrationTime.emit(IntegrationTime.DETECTING)
            self.status = Status.DETECTING
        else:   # 여기다 하면 반복 호출됨 수정 필요@@@@@@@@@@@@@@@@@@@@@@@@@@
            if self.status != Status.DETECTING:
                self.reqSetIntegrationTime.emit(IntegrationTime.NORMAL)

        print(f"{TAG}{METHOD}status: {Status.get_name(self.status)} position: {position}")
        self.arrivePosition = position

    @Slot(np.ndarray)
    def onResGetSpectrum(self, intensities):
        METHOD = "9 ResGetSpectrum, "

        if self.status == Status.COLLECTING_REQSPEC:
            self.status = Status.COLLECTING_PROCESSING
            leftIntensities = np.mean(intensities[1][:36])
            self.collectingTemp.append(leftIntensities)
            self.collectingTimeCount += 1

            progress = f"[{self.collectingTimeCount}/{COLLECTING_TIME}] of [{self.collectingIntegrationIdx+1}/{len(COLLECTING_INTEGRATIONS)}]"
            print(f"\r{TAG}{METHOD} ({progress}) mean: {leftIntensities}", end="")

            if self.collectingTimeCount < COLLECTING_TIME:
                self.status = Status.COLLECTING_REQSPEC
                return
            print("")

            self.collectingTimeCount = 0
            dictKey = f"{use_um(COLLECTING_INTEGRATIONS[self.collectingIntegrationIdx])}초"
            self.collectingDatas[dictKey] = self.collectingTemp
            self.collectingTemp = []
            self.collectingIntegrationIdx += 1

            if self.collectingIntegrationIdx < len(COLLECTING_INTEGRATIONS):
                self.reqSetIntegrationTime.emit(COLLECTING_INTEGRATIONS[self.collectingIntegrationIdx])
                return

            self.collectingCompleteSignal.emit(self.collectingDatas)
            self.status = Status.COLLECTING
            return

        # print(f"{TAG}{METHOD}status: {self.status}, isPaused: {self.isPaused}, isRunning: {self.isRunning}")
        if self.status == Status.DETECTING or self.status == Status.IDLE:
            leftIntensities = np.mean(intensities[1][:36])
            self.estimateSpecimenInserted(leftIntensities)
            return

        if self.status == Status.FOCUS_COMPLETING:
            print(f"{TAG}{METHOD}포커싱 완료")
            self.isRunning = False
            self.isCompleted = True
            self.focusCompleteSignal.emit(intensities)
            self.status = Status.IDLE
            return

        if self.isPaused or not self.isRunning:
            self.status = Status.IDLE
            return

        rightIntensities = np.mean(intensities[1][36:])
        self.measuredSignal.emit(self.pointCnt + 1, self.targetPointCnt[self.round], self.round)

        self.tempSumOfIntensities += rightIntensities

        if self.measureCnt < self.measure:
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
            self.status = Status.FOCUS_COMPLETING
            targetPosition = round(self.roundData[maxIdx][0], 3)
            self.reqMoveStage.emit(targetPosition)

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
