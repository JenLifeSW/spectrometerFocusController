from PySide6.QtCore import QObject, Signal, Slot


class Command:
    RESUEME = 1
    PAUSE = 2
    RESTART = 3


class FocusController(QObject):
    alreadyRunningSignal = Signal()
    alreadyStoppedSignal = Signal()
    roundDataSignal = Signal(int, dict)
    focusCompleteSignal = Signal(dict, int)

    reqDeviceConnected= Signal()
    reqConnectDevice = Signal()
    reqStopDevice = Signal()
    reqMoveStage = Signal(float)

    errStagePosition = Signal(str)
    errFocusingFailed = Signal(str)

    step = [1562.5, 1562.5, 625, 250, 50, 10]
    targetPointCnt = [4, 5, 5, 5, 10, 10]
    conReqCnt = 0
    lastCommand = 0

    isRunning = False
    isPaused = False
    round = 0               # 현재 라운드
    targetPosition = 0.0     # 해당 라운드에서 측정을 시작할 위치
    pointCnt = 0            # 해당 라운드에서 스테이지를 이동한 횟수
    roundData = []          # 해당 라운드에서 이동하면서 수집한 데이터 [("position": "intensity")]

    def __init__(self):
        super().__init__()
        self.initFocuing()

    def initFocuing(self):
        self.isRunning = False
        self.isPaused = False
        self.round = 0

        self.targetPosition = 0.0
        self.pointCnt = 0
        self.roundData = []

    def initRound(self, targetPosition):
        self.targetPosition = targetPosition
        self.pointCnt = 0
        self.roundData = []

    @Slot
    def resumeFocusing(self):
        command = Command.RESUEME
        if self.lastCommand == command:
            self.alreadyRunningSignal.emit()
            return

        self.lastCommand = command
        self.conReqCnt = 0

        if self.isRunning:
            self.alreadyRunningSignal.emit()
            return

        self.reqDeviceConnected.emit()


    @Slot
    def pauseFocusing(self):
        command = Command.PAUSE
        if self.lastCommand == command:
            self.alreadyStoppedSignal.emit()
            return

        self.lastCommand = command
        if self.isPaused:
            self.alreadyStoppedSignal.emit()
            return

        self.reqStopDevice.emit()

    @Slot
    def restartFocusing(self):
        command = Command.RESTART
        if self.isPaused:
            self.isPaused = False
            self.conReqCnt = 0
            self.reqDeviceConnected.emit()
            return
        self.reqStopDevice.emit()

    @Slot(bool)
    def onResDeviceConnected(self, isConnected):
        if not isConnected:
            if self.conReqCnt < 2:
                self.conReqCnt += 1
                self.reqConnectDevice.emit()
            return

        if self.isPaused:
            self.isPaused = False
        else:
            self.initFocuing()

        self.isRunning = True
        self.reqMoveStage.emit(self.targetPosition)

    @Slot
    def onResStopDevices(self):
        self.isPaused = True
        if self.lastCommand == Command.RESTART:
            self.isPaused = False
            self.initFocuing()
            self.reqMoveStage.emit(self.targetPosition)

    @Slot(float, float)
    def onResStageMoved(self, position, intensity):
        self.roundData.append(position, intensity)
        if self.pointCnt < self.targetPointCnt[self.round]:
            self.pointCnt += 1
            self.targetPosition = position + self.step[self.round]
            self.reqMoveStage.emit(self.targetPosition)
            return

        if self.round < 4:
            maxIdx = 0
            maxIntensity = self.roundData[0][1]
            for idx, _, intensity in enumerate(self.roundData):
                if intensity > maxIntensity:
                    maxIntensity = intensity
                    maxIdx = idx

            if maxIdx == 0:     # 첫번째 점이 가장 높을 경우
                self.errStagePosition.emit("작업을 진행할 수 없습니다.")
                return

            elif maxIdx == self.targetPointCnt[self.round] - 1:     # 마지막 점이 가장 높을 경우
                if self.round == 0:     # 라운드 0이면 다음 구간을 측정함
                    targetPosition = position - 2 * self.step[0]
                    self.initRound(targetPosition)
                else:                   # 라운드 0 이후면 데이터가 잘못됐으므로 다시 시작
                    self.errFocusingFailed.emit("포커싱을 다시 시작합니다")
                    self.initFocuing()

                # self.roundDataSignal.emit(self.round, self.roundData)
            else:
                targetPosition = position - self.step[self.round]
                self.round += 1
                self.initRound(targetPosition)

            self.reqMoveStage.emit(self.targetPosition)
