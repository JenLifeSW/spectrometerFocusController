from PySide6.QtCore import QObject, Signal, Slot

TAG = "     포커스 모듈 : "


class Command:
    RESUEME = 1
    PAUSE = 2
    RESTART = 3


class FocusController(QObject):
    testing = False
    initFocusingSignal = Signal()

    alreadyRunningSignal = Signal()
    alreadyStoppedSignal = Signal()
    roundDataSignal = Signal(int, dict)
    focusCompleteSignal = Signal(list, int)

    reqDeviceConnected= Signal()
    reqConnectDevice = Signal()
    reqStopDevice = Signal()
    reqMoveDevice = Signal(float)

    focusDisabledErr = Signal(str)

    step = [1562.5, 1562.5, 625, 250, 50, 10]
    targetPointCnt = [4, 5, 5, 5, 10, 10]
    conReqCnt = 0
    errCnt = 0
    lastCommand = 0

    isRunning = False
    isPaused = False
    round = 1               # 현재 라운드
    startPosition = 0.0     # 스테이지 바닥 위치
    targetPosition = 0.0     # 해당 라운드에서 측정을 시작할 위치
    pointCnt = 0            # 해당 라운드에서 스테이지를 이동한 횟수
    roundData = []          # 해당 라운드에서 이동하면서 수집한 데이터 [("position": "intensity")]

    def __init__(self, startPosition=0.0, testing=False):
        super().__init__()
        print(f"{TAG}1 init")
        self.startPosition = startPosition
        self.testing=testing

        # self.initFocusing()

    def initFocusing(self):
        print(f"{TAG}2 initFocusing")
        self.isRunning = False
        self.isPaused = False
        self.round = 1

        self.targetPosition = self.startPosition
        self.pointCnt = 0
        self.roundData = []
        if self.testing:
            self.initFocusingSignal.emit()

    def initRound(self, targetPosition):
        print(f"{TAG}3 initRound, targetPosition: {targetPosition}")
        self.targetPosition = targetPosition
        self.pointCnt = 0
        self.roundData = []

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
            print(f"{TAG}4 resumeFocusing, paused -> resume")

        print(f"{TAG}4 resumeFocusing, reqDeviceConnected 요청")
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
        self.reqStopDevice.emit()

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
        self.reqStopDevice.emit()

    @Slot(bool)
    def onResDeviceConnected(self, isConnected):
        print(f"{TAG}7 onResDeviceConnected, isConnected: {isConnected}")
        if not isConnected:
            print(f"{TAG}7 onResDeviceConnected, not Connected 연결확인횟수: {self.conReqCnt+1}")
            if self.conReqCnt < 2:
                self.conReqCnt += 1
                self.reqConnectDevice.emit()
            return

        print(f"{TAG}7 onResDeviceConnected, isPaused: {self.isPaused}")
        if self.isPaused:
            self.isPaused = False
        else:
            self.initFocusing()

        self.isRunning = True
        print(f"{TAG}7 onResDeviceConnected, reqMoveDevice 요청")
        self.reqMoveDevice.emit(self.targetPosition)

    @Slot(float, float)
    def onResMoveDevice(self, position, intensity):
        METHOD = "9 onResDeviceMoved "
        print(f"{TAG}{METHOD}position: {position} intensity: {intensity}")
        if self.isPaused or not self.isRunning:
            print(f"{TAG}{METHOD}isPaused: {self.isPaused} isRunning: {self.isRunning}")
            return

        self.roundData.append((position, intensity))
        if self.pointCnt < self.targetPointCnt[self.round] - 1:
            self.pointCnt += 1
            self.targetPosition = position + self.step[self.round]
            print(f"{TAG}{METHOD}next targetPosition: {self.targetPosition}")

            self.reqMoveDevice.emit(self.targetPosition)
            return

        intensities = [data[1] for data in self.roundData]
        maxIdx = intensities.index(max(intensities))

        print(f"{TAG}{METHOD}라운드: {self.round}, data: {self.roundData}, maxIds: {maxIdx}")
        if self.round < 5:

            if not (maxIdx == 0 or maxIdx == self.targetPointCnt[self.round] - 1):
                targetPosition = self.roundData[maxIdx][0] - self.step[self.round]
                self.round += 1
                self.initRound(targetPosition)
                print(f"{TAG}{METHOD}round complete. reqMoveDevice to {self.targetPosition}")
                self.reqMoveDevice.emit(self.targetPosition)
                return

            if self.round == 1:
                if maxIdx != 0:
                    targetPosition = position - 2 * self.step[0]
                    self.initRound(targetPosition)
                    self.reqMoveDevice.emit(self.targetPosition)
                    return

                self.exceptionHandling()
                return

        else:
            print(f"{TAG}{METHOD}포커싱 완료")
            self.isRunning = False
            self.focusCompleteSignal.emit(self.roundData, maxIdx)

    def exceptionHandling(self):
        METHOD = "10 exceptionHandling "
        if self.errCnt < 1:
            print(f"{TAG}{METHOD}데이터 비정상 재측정")
            self.initFocusing()
            self.errCnt += 1
            self.reqMoveDevice.emit(self.targetPosition)
        else:
            print(f"{TAG}{METHOD}재측정 횟수 초과")
            self.focusDisabledErr.emit("데이터 비정상")

    @Slot()
    def onResStopDevice(self):
        print(f"{TAG}8 onResStopDevices")
        if self.lastCommand == Command.RESTART:
            self.initFocusing()
            self.isRunning = True
            self.reqMoveDevice.emit(self.targetPosition)
