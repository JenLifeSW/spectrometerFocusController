import random
from datetime import datetime

import caseMaker
from focusController import FocusController
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Signal, Slot, QTimer

TAG = "테스트 모듈 : "
TIME = datetime.now
delay = 1000
caseNum = 1

caseData = caseMaker.load_case(caseNum)
targetPointCnt = caseData["targetPointCnt"]
sign = caseData["sign"]
case = caseData["case"]

print(case)
print(targetPointCnt)


class FocusControllerTest(QObject):
    resumeFocusingSignal = Signal()
    pauseFocusingSignal = Signal()
    restartFocusingSignal = Signal()
    resDeviceConnected = Signal(bool)
    resMoveStage = Signal(float)
    resStopStage = Signal()
    resGetSpectrum = Signal(float)
    exePositionOver = Signal(float, float)

    cnt = 0
    round = 0

    targetPosition = 0.0

    checkDeviceTimer = QTimer()
    connectDeviceTimer = QTimer()
    moveStageTimer = QTimer()
    stopStageTimer = QTimer()

    checkDeviceTimer.setInterval(delay)
    connectDeviceTimer.setInterval(delay)
    moveStageTimer.setInterval(delay)
    stopStageTimer.setInterval(delay / 100)

    def __init__(self):
        print(f"{TIME()} {TAG} init")
        super().__init__()
        self.checkDeviceTimer.timeout.connect(self.checkDevice)
        self.connectDeviceTimer.timeout.connect(self.connectDevice)
        self.moveStageTimer.timeout.connect(self.moveStage)
        self.stopStageTimer.timeout.connect(self.stopStage)

    def initValues(self):
        self.cnt = 0
        self.round = 0

    def resumeFocusing(self):
        print(f"\n{TIME()} {TAG} resumeFocusing 버튼\n")
        self.resumeFocusingSignal.emit()

    def pauseFocusing(self):
        print(f"\n{TIME()} {TAG} pauseFocusing 버튼\n")
        self.pauseFocusingSignal.emit()

    def restartFocusing(self):
        print(f"\n{TIME()} {TAG} restartFocusing 버튼\n")
        self.restartFocusingSignal.emit()

    @Slot()
    def onAlreadyRunningSignal(self):
        print(f"\n{TIME()} {TAG} alreadyRunningSignal 발생\n")

    @Slot()
    def onAlreadyStoppedSignal(self):
        print(f"\n{TIME()} {TAG} alreadyStoppedSignal 발생\n")

    @Slot(list, int)
    def onFocusCompleteSignal(self, roundData, focusPosition):
        print(f"\n{TIME()} {TAG} 포커싱 완료, {roundData}, {focusPosition}")
        print(f"{TIME()} {TAG} 포커싱 완료, focusPositionIdx: {focusPosition}, focusData: {roundData[focusPosition]}\n")

    @Slot()
    def onReqDeviceConnected(self):
        print(f"{TIME()} {TAG} 기기 연결 확인 요청 감지\n")
        # self.checkDeviceTimer.setInterval(delay)
        self.checkDeviceTimer.start()

    @Slot()
    def onReqConnectDevice(self):
        print(f"{TIME()} {TAG} 기기 연결 요청 감지\n")
        # self.connectDeviceTimer.setInterval(delay)
        self.connectDeviceTimer.start()

    @Slot(float)
    def onReqMoveStage(self, position):
        self.targetPosition = position
        if self.cnt >= targetPointCnt[self.round]:
            self.round += 1
            self.cnt = 0

        self.cnt += 1

        print(f"{TIME()} {TAG}라운드{self.round} 스테이지 이동 요청 감지 ({self.cnt}/{targetPointCnt[self.round]})\n")
        self.moveStageTimer.start()

    @Slot()
    def onReqStopStage(self):
        print(f"{TIME()} {TAG} 기기 중지 요청 감지\n")
        self.stopStageTimer.start()

    @Slot()
    def onGetSpectrum(self):
        print(f"{TIME()} {TAG} 스펙트럼 정보 요청 감지")
        self.resGetSpectrum.emit(case[self.round][self.cnt-1])


    @Slot(str)
    def onfocusDisabledErr(self, errMsg):
        print(f"{TIME()} {TAG} 에러 발생 : {errMsg}")


    # 가상 기기
    def checkDevice(self):
        self.checkDeviceTimer.stop()
        rand = random.randint(0, 5)
        if 1:  # rand:
            print(f"{TIME()} {TAG} 기기 연결됨")
            self.resDeviceConnected.emit(True)
        # else:
        #     print(TAG + "기기 연결 안됨")
        #     self.resDeviceConnected.emit(False)

    def connectDevice(self):
        print(f"{TIME()} {TAG} 기기 연결됨")
        self.connectDeviceTimer.stop()
        self.resDeviceConnected.emit()

    def moveStage(self):
        self.moveStageTimer.stop()
        print(f"{TIME()} {TAG} sign: {sign} self.cnt: {self.cnt} len(case[self.round]): {len(case[self.round])}, self.round: {self.round}, len(case): {len(case)}")
        if sign == "positionOver":
            if (self.cnt == len(case[self.round])) and (self.round == len(case) - 1):
                print(f"{TIME()} {TAG} positionOver 예외 발생 position: {self.targetPosition}, intensity: {case[self.round][self.cnt-1]}")
                self.exePositionOver.emit(self.targetPosition, case[self.round][self.cnt-1])
                return

        print(f"{TIME()} {TAG} 스테이지 이동완료 position: {self.targetPosition}, intensity: {case[self.round][self.cnt-1]}")
        self.resMoveStage.emit(self.targetPosition)

    def stopStage(self):
        print(f"{TIME()} {TAG} 기기 정지")
        self.stopStageTimer.stop()
        if self.cnt > 0:
            self.cnt -= 1
        else:
            if self.round > 0:
                self.round -= 1
        self.resStopStage.emit()

# OBSERVER

def resumeFocusingObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resume 신호 발생")
def pauseFocusingObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 pause 신호 발생")
def restartFocusingObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 restart 신호 발생")
def resDeviceConnectedObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resDeviceConnected 시그널 발생")
def resStopStageObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resStopStage 시그널 발생")
def resMoveStageObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resMoveStage 시그널 발생")
def exePositionOverObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 exePositionOver 시그널 발생")

def alreadyRunningSignalObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 alreadyRunningSignal 발생")
def alreadStoppedSignalObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 alreadyStoppedSignal 발생")
def focusCompleteSignalObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 focusCompleteSignal 발생")

def reqDeviceConnectedObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqDeviceConnected 요청 발생")
def reqConnectDeviceObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqConnectDevice 요청 발생")
def reqStopStageObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqStopStage 요청 발생")
def reqMoveStageObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqMoveStage 요청 발생")


focusController = FocusController(testing=True)
test = FocusControllerTest()

# focusController.alreadyRunningSignal.connect(alreadyRunningSignalObserver)
# focusController.alreadyStoppedSignal.connect(alreadStoppedSignalObserver)
# focusController.focusCompleteSignal.connect(focusCompleteSignalObserver)
# focusController.reqDeviceConnected.connect(reqDeviceConnectedObserver)
# focusController.reqConnectDevice.connect(reqConnectDeviceObserver)
# focusController.reqStopStage.connect(reqStopStageObserver)
# focusController.reqMoveStage.connect(reqMoveStageObserver)
# focusController.focusDisabledErr.connect(focusDisabledErrObserver)
#
# test.resumeFocusingSignal.connect(resumeFocusingObserver)
# test.pauseFocusingSignal.connect(pauseFocusingObserver)
# test.restartFocusingSignal.connect(restartFocusingObserver)
# test.resDeviceConnected.connect(resDeviceConnectedObserver)
# test.resStopStage.connect(resStopStageObserver)
# test.resMoveStage.connect(resMoveStageObserver)
# test.exePositionOver.connect(exePositionOverObserver)

focusController.initFocusingSignal.connect(test.initValues)
focusController.alreadyRunningSignal.connect(test.onAlreadyRunningSignal)
focusController.alreadyStoppedSignal.connect(test.onAlreadyStoppedSignal)
focusController.focusCompleteSignal.connect(test.onFocusCompleteSignal)
focusController.reqDeviceConnected.connect(test.onReqDeviceConnected)
focusController.reqConnectDevice.connect(test.onReqConnectDevice)
focusController.reqStopStage.connect(test.onReqStopStage)
focusController.reqMoveStage.connect(test.onReqMoveStage)
focusController.reqGetSpectrum.connect(test.onGetSpectrum)
focusController.focusDisabledErr.connect(test.onfocusDisabledErr)

test.resumeFocusingSignal.connect(focusController.resumeFocusing)
test.pauseFocusingSignal.connect(focusController.pauseFocusing)
test.restartFocusingSignal.connect(focusController.restartFocusing)
test.resDeviceConnected.connect(focusController.onResDeviceConnected)
test.resStopStage.connect(focusController.onResStopStage)
test.resMoveStage.connect(focusController.onResMoveStage)
test.resGetSpectrum.connect(focusController.onResGetSpectrum)

test.exePositionOver.connect(focusController.onExePositionOver)

if __name__ == "__main__":
    app = QApplication([])
    window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)

    btn1 = QPushButton("Resume")
    btn2 = QPushButton("Pause")
    btn3 = QPushButton("ReSstart")
    btn1.clicked.connect(test.resumeFocusing)
    btn2.clicked.connect(test.pauseFocusing)
    btn3.clicked.connect(test.restartFocusing)

    layout.addWidget(btn1)
    layout.addWidget(btn2)
    layout.addWidget(btn3)

    window.setCentralWidget(central_widget)
    window.show()
    app.exec()
