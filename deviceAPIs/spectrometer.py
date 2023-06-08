import seatease.spectrometers as st
import seabreeze.spectrometers as sb
from PySide6.QtCore import QThread, QTimer, Signal, Slot


class Spectrometer(QThread):
    isConnected = False

    limitTop = None
    limitBottom = None

    connectedSignal = Signal(bool)
    infoSignal = Signal(list)
    ramanSignal = Signal(list)

    def __init__(self, isVirtual=False, signalInterval=1000):
        super().__init__()
        try:
            self.spec = st.Spectrometer.from_first_available() if isVirtual else sb.Spectrometer.from_first_available()
            self.setIntegrationTime(100000)
            self.timer = QTimer()
            self.timer.timeout.connect(self.emitInfoSignal)
            self.timer.start(signalInterval)
            self.isConnected = True
            self.connectedSignal.emit(True)

        except Exception as e:
            print("스펙트로미터 장치에 연결할 수 없습니다.", e)
            self.connectedSignal.emit(False)

    def close(self):
        self.spec.close()

    def setIntegrationTime(self, value):
        self.spec.integration_time_micros(value)

    def getSpectrum(self):
        return self.spec.spectrum()

    @Slot()
    def checkConnected(self):
        self.connectedSignal.emit(self.isConnected)

    @Slot()
    def emitInfoSignal(self):
        info = self.getSpectrum()
        self.infoSignal.emit(info)

    @Slot(float)
    def getRamanShift(self, laserWavelength):
        ramanShift = (1 / laserWavelength - 1 / self.getSpectrum()[0]) * (10 ** 7)
        self.ramanSignal.emit(ramanShift)
        return ramanShift
