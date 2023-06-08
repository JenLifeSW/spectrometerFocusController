from PySide6.QtSerialPort import *
from PySide6.QtCore import QThread, QIODeviceBase, QTimer, Signal, Slot


class Laser(QThread):
    isConnected = False
    connectedSignal = Signal(bool)
    currentSignal = Signal(float)

    def __init__(self, signalInterval=1000):
        super().__init__()
        try:
            self.laser = LaserAPI()
            self.timer = QTimer()
            self.timer.timeout.connect(self.emitCurrentSignal)
            self.timer.start(signalInterval)
            self.isConnected = True
            self.connectedSignal.emit(True)

        except CanNotConnectLaserException as e:
            print(e)
            self.connectedSignal.emit(False)

    def close(self):
        self.laser.closeCOM()

    @Slot()
    def checkConnected(self):
        self.connectedSignal.emit(self.isConnected)

    @Slot()
    def turnOn(self):
        self.laser.turnOn()

    @Slot()
    def turnOff(self):
        self.laser.turnOff()

    def getCurrent(self):
        return self.laser.getCurrent()

    @Slot()
    def emitCurrentSignal(self):
        current = self.getCurrent()
        self.currentSignal.emit(current)


class LaserAPI(QSerialPort):
    OFF = b'e 0'
    ON_EN = b'e 1'
    ON_DIS = b'e 2'

    READ = b'r r'
    SETTINGS = b'r s'
    INFO = b'r i'
    POWER_MAX = b'r 4'

    POWER_SET = b'c 4'
    START = b'c u 1 1234'
    STATUS = b'Le'

    powerMax = 0.0

    R_Diode_Temp = 0.0
    R_Crystal_Temp = 0.0
    R_Body_Temp = 0.0
    R_LD_Current = '0.0mA'
    R_Crystal_TEC_Load = '0%'
    R_LD_TEC_Load = '0%'
    R_Status = 'OFF'
    R_Fan_Load = '0%'
    R_Input_Voltage = '5V'

    S_Crystal_Temp = 0.0
    S_Diode_Temp = 0.0
    S_LD_Current = '0.0mA'
    S_Feedback_DAC = 0
    S_Power = 0.0
    S_LD_MaxCurrent = 0.0
    S_Autostart_Mode = 'OFF'
    S_Access_Level = 1
    S_Fan_Temp = 0.0

    Firmware = ''
    Serial = ''
    Model = ''
    Operation_Time = ''
    ON_Times = ''

    def __init__(self):
        super().__init__()
        portInfos = QSerialPortInfo.availablePorts()

        for info in portInfos:
            if "Silicon Labs" in info.manufacturer():
                portName = info.portName()
                self.setBaudRate(115200)
                self.setPortName(portName)
                self.openCOM()
                break

        if not self.isOpen():
            raise CanNotConnectLaserException()

    def sendCommand(self, command, logPrint=False, delay=1):
        if self.isOpen():
            self.write(command)
            self.waitForReadyRead(500)
            while self.bytesAvailable() < 5:
                self.waitForReadyRead(500)
            res = str(self.readAll(), encoding="utf-8").strip("\r\n").strip()

            if logPrint:
                print(res, command)

            return res

    def openCOM(self):
        if not self.isOpen():
            self.open(QIODeviceBase.OpenModeFlag.ReadWrite)
            self.flush()

        self.sendCommand(self.ON_DIS)
        self.sendCommand(self.START)
        self.sendCommand(self.STATUS)
        self.getInfo()
        self.setPower(1)

    def closeCOM(self):
        if self.isOpen():
            self.sendCommand(self.OFF)
            self.waitForBytesWritten(500)
            self.close()

    def turnOn(self):
        if self.isOpen():
            self.sendCommand(self.ON_EN)

    def turnOff(self):
        if self.isOpen():
            self.sendCommand(self.ON_DIS)

    def getMaxPower(self):
        if self.isOpen():
            res = self.sendCommand(self.POWER_MAX)

            if not ("<ERR>" in res or "<ACK>" in res):
                self.powerMax = float(res)
        return self.powerMax

    def getRead(self):
        read = []
        if self.isOpen():
            res = self.sendCommand(self.READ)

            if not ("<ERR>" in res or "<ACK>" in res):
                read = res.split(' ')
                if len(read) >= 10:
                    self.R_Diode_Temp = float(read[1])
                    self.R_Crystal_Temp = float(read[2])
                    self.R_Body_Temp = float(read[3])
                    self.R_LD_Current = read[4]
                    self.R_Crystal_TEC_Load = read[5]
                    self.R_LD_TEC_Load = read[6]
                    self.R_Status = read[7]
                    self.R_Fan_Load = read[8]
                    self.R_Input_Voltage = read[9]

        return read

    def getSettings(self):
        settings = []
        if self.isOpen():
            res = self.sendCommand(self.SETTINGS)

            if not ("<ERR>" in res or "<ACK>" in res):
                settings = res.split(" ")
                if len(settings) >= 10:
                    self.S_Crystal_Temp = float(settings[1]) / 100
                    self.S_Diode_Temp = float(settings[2]) / 100
                    self.S_LD_Current = float(settings[3])
                    self.S_Feedback_DAC = float(settings[4])
                    self.S_Power = float(settings[5])
                    self.S_LD_MaxCurrent = float(settings[6])
                    self.S_Autostart_Mode = settings[7]
                    self.S_Access_Level = int(settings[8])
                    self.S_Fan_Temp = float(settings[9]) / 100

        return settings

    def setPower(self, value: float) -> bool:
        if self.isOpen():
            res = self.sendCommand(self.POWER_SET, '{:.2f}'.format(value).encode('utf-8'))

            if "<ACK>" in res:
                return True
        return False

    def getInfo(self):
        info = []
        if self.isOpen():
            res = self.sendCommand(self.INFO)

            if not ("<ERR>" in res or "<ACK>" in res):
                info = res.split("\r\n")

                self.Firmware = info[0]
                self.Serial = info[1].split(':')[1]
                self.Model = info[2].split(':')[1]
                # self.Operation_Time = info[3]
                # self.ON_Times = info[4]
        return info

    def getCurrent(self):
        read = self.getRead()
        if read:
            return read[4]
        else:
            return 0.0


class CanNotConnectLaserException(Exception):
    def __init__(self):
        super().__init__("레이저 모듈에 연결하지 못 했습니다.")