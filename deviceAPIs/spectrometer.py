import numpy as np
import seatease.spectrometers as st
import seabreeze.spectrometers as sb
from PySide6.QtCore import QThread, QTimer, Signal, Slot


class Spectrometer(QThread):
    isConnected = False

    limitTop = None
    limitBottom = None

    connectedSignal = Signal(bool)
    integrationTimeSettedSignal = Signal()
    resGetSpectrum = Signal(np.ndarray)
    ramanSignal = Signal(list)

    def __init__(self, isVirtual=False, signalInterval=1000):
        super().__init__()
        try:
            self.spec = st.Spectrometer.from_first_available() if isVirtual else sb.Spectrometer.from_first_available()
            self.timer = QTimer()
            self.timer.timeout.connect(self.getSpectrum)
            self.timer.start(signalInterval)
            self.setIntegrationTime(100000)
            self.isConnected = True
            self.isProcessing = False
            self.connectedSignal.emit(True)

        except Exception as e:
            print("스펙트로미터 장치에 연결할 수 없습니다.", e)
            self.connectedSignal.emit(False)

    def run(self):
        self.getSpectrumAsync()

    def close(self):
        self.spec.close()

    def setIntegrationTime(self, value):
        self.spec.integration_time_micros(value)
        self.integrationTimeSettedSignal.emit()
        self.timer.stop()
        self.timer.setInterval(value / 1000)
        self.timer.start()

    @Slot()
    def getSpectrum(self):
        self.start()

    def getSpectrumAsync(self):
        self.isProcessing = True
        info = self.spec.spectrum()
        self.isProcessing = False
        self.resGetSpectrum.emit(info)

    def stopGetSpectrum(self):
        self.timer.stop()

    @Slot()
    def checkConnected(self):
        self.connectedSignal.emit(self.isConnected)

    @Slot(float)
    def getRamanShift(self, laserWavelength):
        ramanShift = (1 / laserWavelength - 1 / self.getSpectrum()[0]) * (10 ** 7)
        self.ramanSignal.emit(ramanShift)
        return ramanShift
