from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QDoubleSpinBox, QLabel, QSpinBox, QPushButton

topWidth = 120


class Setting(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.InputStep = [InputStep()]
        self.layout = QVBoxLayout(self)

        lbIntergrationTime = QLabel("intergration time")
        lbMeasureTime = QLabel("스펙트럼 측정 횟수")
        lbRepeatTime = QLabel("반복 횟수")

        lbIntergrationTime.setAlignment(Qt.AlignCenter)
        lbMeasureTime.setAlignment(Qt.AlignCenter)
        lbRepeatTime.setAlignment(Qt.AlignCenter)

        lbIntergrationTime.setMinimumWidth(topWidth)
        lbMeasureTime.setMinimumWidth(topWidth)
        lbRepeatTime.setMinimumWidth(topWidth)

        lytTop = QHBoxLayout()

        lytTop.addWidget(lbIntergrationTime)
        lytTop.addWidget(lbMeasureTime)
        lytTop.addWidget(lbRepeatTime)
        lytTop.addStretch()

        self.layout.addLayout(lytTop)
        # for _ in range(5):
        #     self.addStep()

    def initStep(self, steps):
        print(f"initStep: {steps}")
        for step in steps:
            self.addStep()
            self.InputStep[-1].setStep(*step)

    def addStep(self):
        self.InputStep.append(InputStep())
        idx = len(self.InputStep) - 1
        self.layout.addLayout(self.InputStep[idx])
        self.InputStep[idx].btnAdd.clicked.connect(self.addStep)

    def connectBtn(self):
        for idx, stepInfo in enumerate(self.InputStep):
            stepInfo.btnAdd.clicked.connect(self.addStep)

    def getInputStep(self):
        steps = []
        for step in self.InputStep:
            steps.append([step.getIntergrationTime(), step.getMeasureTime(), step.getRepeatTime()])
            print(f"step: {step}")
        return steps



class InputStep(QHBoxLayout):
    def __init__(self, parent=None, intergrationTime=0.1, measureNumber=1, repeatTime=50):
        super().__init__(parent)

        self.sboxIntergrationTime = QDoubleSpinBox()
        self.sboxIntergrationTime.setRange(0.007, 100)
        self.sboxIntergrationTime.setValue(intergrationTime)
        self.sboxIntergrationTime.setMinimumWidth(topWidth)
        self.sboxIntergrationTime.valueChanged.connect(self.setEstimatedTime)

        self.sboxSetMeasure = QSpinBox()
        self.sboxSetMeasure.setRange(1, 10000)
        self.sboxSetMeasure.setValue(measureNumber)
        self.sboxSetMeasure.setMinimumWidth(topWidth)
        self.sboxSetMeasure.valueChanged.connect(self.setEstimatedTime)

        self.sboxRepeatTime = QSpinBox()
        self.sboxRepeatTime.setRange(1, 1000)
        self.sboxRepeatTime.setValue(repeatTime)
        self.sboxRepeatTime.setMinimumWidth(topWidth)
        self.sboxRepeatTime.valueChanged.connect(self.setEstimatedTime)

        self.lbEstimatedTime = QLabel("예상 작업시간: 분")

        self.btnAdd = QPushButton("+")

        self.addWidget(self.sboxIntergrationTime)
        self.addWidget(self.sboxSetMeasure)
        self.addWidget(self.sboxRepeatTime)
        self.addWidget(self.lbEstimatedTime)
        self.addWidget(self.btnAdd)
        self.setEstimatedTime()

    def setStep(self, intergrationTime=0.1, measureNumber=1, repeatTime=50):
        self.sboxIntergrationTime.setValue(intergrationTime)
        self.sboxSetMeasure.setValue(measureNumber)
        self.sboxRepeatTime.setValue(repeatTime)

    def getIntergrationTime(self):
        return self.sboxIntergrationTime.value() * 1000000

    def getMeasureTime(self):
        return self.sboxSetMeasure.value()

    def getRepeatTime(self):
        return self.sboxRepeatTime.value()

    def setEstimatedTime(self):
        estimate = self.getIntergrationTime() * self.getMeasureTime() * self.getRepeatTime() / 1000000 * 50 / 60
        self.lbEstimatedTime.setText(f"예상 작업시간: {round(estimate, 2)}분")
