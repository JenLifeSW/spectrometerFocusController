from datetime import datetime

import numpy as np

from deviceAPIs import Laser, Spectrometer, Stage

from focusController import FocusController
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PySide6.QtCore import QObject, Signal, Slot

TAG = "실제 기기 테스트 : "
TIME = datetime.now


def use_mm(value):
    return value/1000


def use_um(value):
    return value/1000000


stageSettings = {
    "bottom": use_mm(3),
    "top": use_mm(17),
    "maxVelocity": use_mm(1),
    "acceleration": use_mm(1)
}


class FocusControllerTest(QObject):
    targetPosition = 0.0
    isPaused = False

    laserConnected = False
    specConnected = False
    stageConnected = False
    # stageSetted = False

    laser = Laser()
    spec = Spectrometer()
    stage = Stage(1)

    logMessage = Signal(str)

    ''' 모듈 통신 '''
    reqMoveStage = Signal(int, float)
    reqStopStage = Signal()

    ''' 포커스 컨트롤러 통신 '''
    initFocusingSignal = Signal()
    resumeFocusingSignal = Signal()
    pauseFocusingSignal = Signal()
    restartFocusingSignal = Signal()
    resDeviceConnected = Signal(bool)
    resMoveStage = Signal(float)
    resStopStage = Signal()
    resGetSpectrum = Signal(float)
    exePositionOver = Signal(float, float)

    def __init__(self):
        super().__init__()

    def initWithLog(self):
        self.log_print(f"{TIME()} {TAG} init")

        self.laser.turnOn()
        self.stage.setLimit(0, stageSettings["bottom"], stageSettings["top"])
        self.stage.setUpVelocity(
            0,
            stageSettings["maxVelocity"],
            stageSettings["acceleration"]
        )
        self.initConnect()
        self.initFocusing()

    def initConnect(self):

        self.stage.nomalLogSignal.connect(self.onNomalLogSignal)

        # 테스트모듈 -> 기기 요청
        self.reqMoveStage.connect(self.stage.move)
        self.reqStopStage.connect(self.stage.stopMove)

        # 기기 -> 테스트모듈 일반시그널
        self.stage.stageMovedSignal.connect(self.onResMoveStage)
        self.stage.stoppedSignal.connect(self.onResStopStage)
        self.stage.errCannotDetect.connect(self.onErrCannotDetect)
        self.stage.errPositionLimit.connect(self.onErrPositionLimit)

        # 기기 -> 테스트모듈 응답
        self.laser.connectedSignal.connect(self.onLaserConnected)
        self.spec.connectedSignal.connect(self.onSpectrometerConnected)
        self.stage.connectedSignal.connect(self.onStageConnected)
        self.laser.checkConnected()
        self.spec.checkConnected()
        self.stage.checkConnected()

    def close(self):
        self.laser.close()
        self.spec.close()
        self.stage.close()

    def log_print(self, message):
        self.logMessage.emit(message)

    @Slot(str)
    def onNomalLogSignal(self, msg):
        self.log_print(msg)

    ''' 모듈 '''
    def initFocusing(self):
        self.log_print(f"\n{TIME()} {TAG} initFocusing 버튼")
        #self.stage.stages[0].home()
        #self.reqMoveStage.emit(0, limit[0] * -1)
        #self.reqMoveStage.emit(0, stageSettings["top"])
        self.initFocusingSignal.emit()

    @Slot(bool)
    def onLaserConnected(self, isConnected):
        if isConnected:
            self.log_print(f"{TIME()} {TAG} 레이저 연결됨")
            self.laserConnected = True
        else:
            self.log_print(f"{TIME()} {TAG} 레이저 연결 실패")
            self.laserConnected = False

    @Slot(bool)
    def onSpectrometerConnected(self, isConnected):
        if isConnected:
            self.log_print(f"{TIME()} {TAG} 스펙트로미터 연결됨")
            self.specConnected = True
        else:
            self.log_print(f"{TIME()} {TAG} 스펙트로미터 연결 실패")
            self.specConnected = False

    @Slot(list)
    def onStageConnected(self, stageConnected):
        if stageConnected[0]:
            self.log_print(f"{TIME()} {TAG} 스테이지 연결됨")
            self.stageConnected = True
        else:
            self.log_print(f"{TIME()} {TAG} 스테이지 연결 실패")
            self.stageConnected = False

    @Slot(str)
    def onErrCannotDetect(self, msg):
        self.log_print(f"{TIME()} {TAG} {msg}")

    @Slot(str)
    def onErrPositionLimit(self, msg):
        self.log_print(f"{TIME()} {TAG} {msg}")

    ''' 포커싱 '''
    # 베이직 시그널
    def resumeFocusing(self):
        self.log_print(f"\n{TIME()} {TAG} resumeFocusing 버튼")
        self.resumeFocusingSignal.emit()

    def pauseFocusing(self):
        self.log_print(f"\n{TIME()} {TAG} pauseFocusing 버튼")
        self.pauseFocusingSignal.emit()

    def restartFocusing(self):
        self.log_print(f"\n{TIME()} {TAG} restartFocusing 버튼")
        self.restartFocusingSignal.emit()
    # 베이직 시그널 응답
    @Slot()
    def onAlreadyRunningSignal(self):
        self.log_print(f"\n{TIME()} {TAG} alreadyRunningSignal 발생\n")

    @Slot()
    def onAlreadyStoppedSignal(self):
        self.log_print(f"\n{TIME()} {TAG} alreadyStoppedSignal 발생\n")

    @Slot(list, int)
    def onFocusCompleteSignal(self, roundData, focusPosition):
        self.log_print(f"\n{TIME()} {TAG} 포커싱 완료, {roundData}, {focusPosition}")
        self.log_print(f"{TIME()} {TAG} 포커싱 완료, focusPositionIdx: {focusPosition}, focusData: {roundData[focusPosition]}\n")

    # 기기 응답에 따라 포커싱알고리즘에 응답
    @Slot()
    def onReqDeviceConnected(self):
        self.log_print(f"{TIME()} {TAG} 기기 연결 확인 요청 감지 laser: {self.laserConnected}, spec: {self.specConnected}, stage: {self.stageConnected}\n")
        if (self.laserConnected and self.specConnected and self.stageConnected):
            self.resDeviceConnected.emit(True)
        else:
            self.resDeviceConnected.emit(False)

    @Slot()
    def onReqConnectDevice(self):
        self.log_print(f"{TIME()} {TAG} 기기 연결 요청 감지\n")
        ''' 
        Todo: 연결안된 기기 파악하여 연결
        '''

    @Slot(float)
    def onReqMoveStage(self, position):
        self.log_print(f"{TIME()} {TAG} 스테이지 이동 요청 감지: {position}\n")
        self.targetPosition = position
        self.reqMoveStage.emit(0, position)

    def onReqStopStage(self):
        self.log_print(f"{TIME()} {TAG} 기기 중지 요청 감지\n")

    def onReqGetSpectrum(self):
        self.log_print(f"{TIME()} {TAG} 스펙트럼 정보 요청 감지\n")
        intensities = self.spec.getSpectrum()
        #average = sum(intensities) / len(intensities)
        average = np.mean(intensities)
        self.resGetSpectrum.emit(average)

    # 포커싱알고리즘 응답에 따라 기기에 응답
    @Slot(int, float)
    def onResMoveStage(self, idx, position):
        self.log_print(f"{TIME()} {TAG} 스테이지 #{idx} 이동 완료\n")
        self.resMoveStage.emit(position)
        #self.reqRamanShift.emit(633.0)

    @Slot(int, float)
    def onResStopStage(self, idx, position):
        self.log_print(f"{TIME()} {TAG} 스테이지 #{idx} 정지")
        self.resStopStage.emit()

    @Slot(str)
    def onfocusDisabledErr(self, errMsg):
        self.log_print(f"{TIME()} {TAG} 에러 발생 : {errMsg}")


class LogWindow(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def append_log(self, message):
        print(message)
        self.append(message)


class Window(QMainWindow):
    print("Window 객체 생성")
    focusController = FocusController(testing=True)
    focusController.setStartPosition(stageSettings["top"])
    test = FocusControllerTest()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.initDevice()
        self.initUI()

    def initDevice(self):

        self.focusController.alreadyRunningSignal.connect(self.test.onAlreadyRunningSignal)
        self.focusController.alreadyStoppedSignal.connect(self.test.onAlreadyStoppedSignal)
        self.focusController.focusCompleteSignal.connect(self.test.onFocusCompleteSignal)
        self.focusController.reqDeviceConnected.connect(self.test.onReqDeviceConnected)
        self.focusController.reqConnectDevice.connect(self.test.onReqConnectDevice)
        self.focusController.reqMoveStage.connect(self.test.onReqMoveStage)
        self.focusController.reqStopStage.connect(self.test.onReqStopStage)
        self.focusController.reqGetSpectrum.connect(self.test.onReqGetSpectrum)
        self.focusController.focusDisabledErr.connect(self.test.onfocusDisabledErr)

        self.test.initFocusingSignal.connect(self.focusController.initFocusing)
        self.test.resumeFocusingSignal.connect(self.focusController.resumeFocusing)
        self.test.pauseFocusingSignal.connect(self.focusController.pauseFocusing)
        self.test.restartFocusingSignal.connect(self.focusController.restartFocusing)
        self.test.resDeviceConnected.connect(self.focusController.onResDeviceConnected)
        self.test.resMoveStage.connect(self.focusController.onResMoveStage)
        self.test.resStopStage.connect(self.focusController.onResStopStage)
        self.test.resGetSpectrum.connect(self.focusController.onResGetSpectrum)
        self.test.exePositionOver.connect(self.focusController.onExePositionOver)

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        logWindow = LogWindow()
        btnInit = QPushButton("initFocusing")
        btn1 = QPushButton("Resume")
        btn2 = QPushButton("Pause")
        btn3 = QPushButton("ReStart")

        btnInit.clicked.connect(self.test.initFocusing)
        btn1.clicked.connect(self.test.resumeFocusing)
        btn2.clicked.connect(self.test.pauseFocusing)
        btn3.clicked.connect(self.test.restartFocusing)
        self.test.logMessage.connect(logWindow.append_log)
        self.test.initWithLog()

        layout.addWidget(btnInit)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(btn3)
        layout.addWidget(logWindow)
        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        self.test.close()


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
