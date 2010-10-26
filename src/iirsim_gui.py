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
    """A slider with name and value label."""
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
        self.slider.setValue(0)
        self.slider.setPageStep(max(1, 2**(factor_bits-3)))

        # value label
        self.valueLabel = QtGui.QLabel()
        self.valueLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

        self.connect(self.slider, QtCore.SIGNAL('valueChanged(int)'), \
                     self.updateLabel)
        self.updateLabel()

    def updateLabel(self):
        value = self.slider.value()
        scale = self.scale
        text = '%i/%i = %6.3f' % (value, scale, float(value)/scale)
        self.valueLabel.setText(text)

    def getMinLabelWidth(self):
        label = QtGui.QLabel()
        value = -2**(self.factor_bits-1)
        scale = self.scale
        text = '%i/%i = %6.3f' % (value, scale, float(value)/scale)
        label.setText(text)
        return label.minimumSizeHint().width()

class FactorSliderGrid(QtGui.QWidget):
    def __init__(self, names, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        self.factorSliders = [FactorSlider(name, factor_bits, scale_bits) for name in names]

        gridLayout = QtGui.QGridLayout()
        for (row, factorSlider) in enumerate(self.factorSliders):
            gridLayout.addWidget(factorSlider.nameLabel,  row, 0)
            gridLayout.addWidget(factorSlider.slider,     row, 1)
            gridLayout.addWidget(factorSlider.valueLabel, row, 2)
        minLabelWidth = max([slider.getMinLabelWidth() \
                             for slider in self.factorSliders])
        gridLayout.setColumnMinimumWidth(1, 50)
        gridLayout.setColumnMinimumWidth(2, minLabelWidth)
        self.setLayout(gridLayout)
    
class IIRSimCentralWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        # Factor Slider Array
        names = ['b0', 'b1', 'b2', 'a1', 'a2']
        factor_bits = 5
        slider_grid = FactorSliderGrid(names, factor_bits)

        # Global Layout
        globalVBox = QtGui.QVBoxLayout()
        globalVBox.addWidget(slider_grid)
        self.setLayout(globalVBox)

class IIRSimMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        mainTitle = 'IIRSim'
        self.setWindowTitle(mainTitle)

        self.setCentralWidget(IIRSimCentralWidget())

        statusBar = QtGui.QStatusBar()
        statusBar.addWidget(QtGui.QLabel('Ready'))
        self.setStatusBar(statusBar)

