import random
from datetime import datetime

from focusController import FocusController
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Signal, Slot, QTimer

TAG = "테스트 모듈 : "
TIME = datetime.now
delay = 1000

case = []
case.append([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5])
case.append([1.0, 1.5, 2.0, 1.6, 1.0])
case.append([1.5, 1.75, 2.0, 1.75, 1.5])
case.append([1.75, 1.8, 2.0, 1.8, 1.75])
case.append([1.8, 1.85, 1.9, 1.95, 2.0, 1.97, 1.95, 1.9, 1.85, 1.8])
case.append([1.95, 1.96, 1.97, 1.98, 1.99, 2.0, 1.99, 1.98, 1.97, 1.96])


class FocusControllerTest(QObject):
    resumeFocusingSignal = Signal()
    pauseFocusingSignal = Signal()
    restartFocusingSignal = Signal()
    resDeviceConnected = Signal(bool)
    resMoveDevice = Signal(float, float)
    resStopDevice = Signal()

    cnt = 0
    round = 1
    targetPointCnt = [4, 5, 5, 5, 10, 10]

    targetPosition = 0.0

    checkDeviceTimer = QTimer()
    connectDeviceTimer = QTimer()
    moveDeviceTimer = QTimer()
    stopDeviceTimer = QTimer()

    checkDeviceTimer.setInterval(delay)
    connectDeviceTimer.setInterval(delay)
    moveDeviceTimer.setInterval(delay)
    stopDeviceTimer.setInterval(delay / 100)

    def __init__(self):
        print(f"{TIME()} {TAG} init")
        super().__init__()
        self.checkDeviceTimer.timeout.connect(self.checkDevice)
        self.connectDeviceTimer.timeout.connect(self.connectDevice)
        self.moveDeviceTimer.timeout.connect(self.moveDevice)
        self.stopDeviceTimer.timeout.connect(self.stopDevice)

    def initValues(self):
        self.cnt = 0
        self.round = 1

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

    # @Slot(int, list)
    # def onRoundDataSignal(self, round, roundData):
    #     print("roundDataSignal 발생")
    #     print(f"round: ${round}")
    #     for idx, data in roundData:
    #         print(f"${idx}: ${data}")

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
    def onReqMoveDevice(self, position):
        self.targetPosition = position
        if self.cnt >= self.targetPointCnt[self.round]:
            self.round += 1
            self.cnt = 0

        self.cnt += 1

        #current_time = datetime.now()
        print(f"{TIME()} {TAG}라운드{self.round} 스테이지 이동 요청 감지 ({self.cnt}/{self.targetPointCnt[self.round]})\n")
        # self.moveDeviceTimer.setInterval(delay)
        self.moveDeviceTimer.start()
        # self.resDeviceMoved.emit(position, case[self.round][self.cnt-1])

    @Slot()
    def onReqStopDevice(self):
        print(f"{TIME()} {TAG} 기기 중지 요청 감지\n")
        # self.stopDeviceTimer.setInterval(delay)
        self.stopDeviceTimer.start()

    @Slot(str)
    def onDevicePositionErr(self, errMsg):
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

    def moveDevice(self):
        self.moveDeviceTimer.stop()
        print(f"{TIME()} {TAG} 스테이지 이동완료 position: {self.targetPosition}, intensity: {case[self.round][self.cnt-1]}")
        self.resMoveDevice.emit(self.targetPosition, case[self.round][self.cnt-1])

    def stopDevice(self):
        print(f"{TIME()} {TAG} 기기 정지")
        self.stopDeviceTimer.stop()
        if self.cnt > 0:
            self.cnt -= 1
        else:
            if self.round > 0:
                self.round -= 1
        self.resStopDevice.emit()

# OBSERVER

def resumeFocusingObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resume 신호 발생")
def pauseFocusingObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 pause 신호 발생")
def restartFocusingObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 restart 신호 발생")
def resDeviceConnectedObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resDeviceConnected 시그널 발생")
def resStopDeviceObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resStopDevice 시그널 발생")
def resMoveDeviceObserver():
    print(f"                    {TIME()}[OBSERVER] 테스트 모듈 resMoveDevice 시그널 발생")

def alreadyRunningSignalObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 alreadyRunningSignal 발생")
def alreadStoppedSignalObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 alreadStoppedSignal 발생")
def roundDataSignalObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 roundDataSignal 발생")
def focusCompleteSignalObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 focusCompleteSignal 발생")

def reqDeviceConnectedObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqDeviceConnected 요청 발생")
def reqConnectDeviceObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqConnectDevice 요청 발생")
def reqStopDeviceObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqStopDevice 요청 발생")
def reqMoveDeviceObserver():
    print(f"                    {TIME()}[OBSERVER] 포커스 모듈 reqMoveDevice 요청 발생")


focusController = FocusController(testing=True)
test = FocusControllerTest()

# focusController.alreadyRunningSignal.connect(alreadyRunningSignalObserver)
# focusController.alreadyStoppedSignal.connect(alreadStoppedSignalObserver)
# focusController.focusCompleteSignal.connect(focusCompleteSignalObserver)
# focusController.reqDeviceConnected.connect(reqDeviceConnectedObserver)
# focusController.reqConnectDevice.connect(reqConnectDeviceObserver)
# focusController.reqStopDevice.connect(reqStopDeviceObserver)
# focusController.reqMoveDevice.connect(reqMoveDeviceObserver)
# focusController.errDevicePosition.connect(reqMoveDeviceObserver)
#
# test.resumeFocusingSignal.connect(resumeFocusingObserver)
# test.pauseFocusingSignal.connect(pauseFocusingObserver)
# test.restartFocusingSignal.connect(restartFocusingObserver)
# test.resDeviceConnected.connect(resDeviceConnectedObserver)
# test.resStopDevice.connect(resStopDeviceObserver)
# test.resMoveDevice.connect(resMoveDeviceObserver)

focusController.initFocusingSignal.connect(test.initValues)
focusController.alreadyRunningSignal.connect(test.onAlreadyRunningSignal)
focusController.alreadyStoppedSignal.connect(test.onAlreadyStoppedSignal)
# focusController.roundDataSignal.connect(test.onRoundDataSignal)
focusController.focusCompleteSignal.connect(test.onFocusCompleteSignal)
focusController.reqDeviceConnected.connect(test.onReqDeviceConnected)
focusController.reqConnectDevice.connect(test.onReqConnectDevice)
focusController.reqStopDevice.connect(test.onReqStopDevice)
focusController.reqMoveDevice.connect(test.onReqMoveDevice)
focusController.errDevicePosition.connect(test.onDevicePositionErr)

test.resumeFocusingSignal.connect(focusController.resumeFocusing)
test.pauseFocusingSignal.connect(focusController.pauseFocusing)
test.restartFocusingSignal.connect(focusController.restartFocusing)
test.resDeviceConnected.connect(focusController.onResDeviceConnected)
test.resStopDevice.connect(focusController.onResStopDevice)
test.resMoveDevice.connect(focusController.onResMoveDevice)


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
