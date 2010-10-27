import os
from PyQt4 import QtCore, QtGui

class QSlider_autoticks(QtGui.QSlider):
    """A slider with self adjusting tick marks."""
    def __init__(self, orientation, tick_min_distance):
        QtGui.QSlider.__init__(self, orientation)
        self.setTickPosition(self.TicksBelow)
        self.tick_min_distance = tick_min_distance

    def resizeEvent(self, event):
        width = self.width()
        value_range = self.maximum() - self.minimum()
        interval = 1
        while (interval*width/value_range < self.tick_min_distance):
            interval = 2*interval
        self.setTickInterval(interval)

class FactorSlider(QtGui.QWidget):
    """A slider with name and value label and a spin box."""
    def __init__(self, name, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        if scale_bits is None:
            scale_bits = factor_bits-2
        self.scale = 2**scale_bits
        self.factor_bits = factor_bits

        # name label
        self.nameLabel = QtGui.QLabel(name)
        self.nameLabel.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)

        # slider
        self.slider = QSlider_autoticks(QtCore.Qt.Horizontal, 10)
        self.slider.setRange(-2**(factor_bits-1), 2**(factor_bits-1)-1)
        self.slider.setPageStep(max(1, 2**(factor_bits-3)))
        self.slider.setValue(0)

        # value label
        self.valueLabel = QtGui.QLabel()
        self.valueLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

        # spinbox
        self.spinBox = QtGui.QDoubleSpinBox()
        self.spinBox.setMinimum(float(self.slider.minimum())/self.scale)
        self.spinBox.setMaximum(float(self.slider.maximum())/self.scale)
        self.spinBox.setSingleStep(1.0/self.scale)
        self.spinBox.setDecimals(6)
        self.spinBox.setKeyboardTracking(False)

        # signals
        self.connect(self.spinBox, QtCore.SIGNAL('valueChanged(double)'), \
                     self._updateSlider)
        self.connect(self.spinBox, QtCore.SIGNAL('editingFinished()'), \
                     self._updateSpinBox)
        self.connect(self.slider, QtCore.SIGNAL('valueChanged(int)'), \
                     self._updateLabel)
        self.connect(self.slider, QtCore.SIGNAL('valueChanged(int)'), \
                     self._updateSpinBox)
        self.connect(self.slider, QtCore.SIGNAL('valueChanged(int)'), \
                     self._signalValueChanged)

        # set initial value
        self._updateLabel()
        self._signalValueChanged()

    def _valueLabelText(self, value=None, scale=None):
        if value is None:
            value = self.slider.value()
        if scale is None:
            scale = self.scale
        return '%i/%i =' % (value, scale)

    def _updateLabel(self):
        text = self._valueLabelText()
        self.valueLabel.setText(text)

    def _updateSlider(self):
        self.slider.setValue(round(self.spinBox.value()*self.scale))

    def _updateSpinBox(self):
        self.spinBox.setValue(float(self.slider.value())/self.scale)

    def _signalValueChanged(self):
        self.emit(QtCore.SIGNAL('valueChanged()'))

    def getMinLabelWidth(self):
        label = QtGui.QLabel()
        value = -2**(self.factor_bits-1)
        text = self._valueLabelText(value)
        label.setText(text)
        return label.minimumSizeHint().width()

class FactorSliderGrid(QtGui.QWidget):
    """A group of FactorSliders aligned in a grid."""
    def __init__(self, names, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        self.factorSliders = [FactorSlider(name, factor_bits, scale_bits) \
                              for name in names]

        gridLayout = QtGui.QGridLayout()
        for (row, factorSlider) in enumerate(self.factorSliders):
            gridLayout.addWidget(factorSlider.nameLabel,  row, 0)
            gridLayout.addWidget(factorSlider.slider,     row, 1)
            gridLayout.addWidget(factorSlider.valueLabel, row, 2)
            gridLayout.addWidget(factorSlider.spinBox,    row, 3)
            self.connect(factorSlider, QtCore.SIGNAL('valueChanged()'), \
                         self._signalValueChanged)
        minLabelWidth = max([slider.getMinLabelWidth() \
                             for slider in self.factorSliders])
        gridLayout.setColumnMinimumWidth(1, 50)
        gridLayout.setColumnMinimumWidth(2, minLabelWidth)
        self.setLayout(gridLayout)

    def _signalValueChanged(self):
        self.emit(QtCore.SIGNAL('valueChanged()'))

    def getValues(self):
        return [factorSlider.slider.value() \
                for factorSlider in self.factorSliders]


#--------------------------------------------------
# Top Level ab hier
#--------------------------------------------------

class IIRSimCentralWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        # Factor Slider Array
        names = ['b0', 'b1', 'b2', 'a1', 'a2']
        factor_bits = 12
        self.slider_grid = FactorSliderGrid(names, factor_bits)

        # Global Layout
        globalVBox = QtGui.QVBoxLayout()
        globalVBox.addWidget(self.slider_grid)
        globalVBox.addStretch()
        self.setLayout(globalVBox)

        # signals
        self.connect(self.slider_grid, QtCore.SIGNAL('valueChanged()'), \
                     self.printNewValues)

    def printNewValues(self):
        print self.slider_grid.getValues()

class IIRSimMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        mainTitle = 'IIRSim'
        self.setWindowTitle(mainTitle)

        self.setCentralWidget(IIRSimCentralWidget())

        statusBar = QtGui.QStatusBar()
        statusBar.addWidget(QtGui.QLabel('Ready'))
        self.setStatusBar(statusBar)

