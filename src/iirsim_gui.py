import os, numpy
from PyQt4 import QtCore, QtGui, Qwt5

import iirsim_cfg

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

    def getValue(self):
        name = str(self.nameLabel.text())
        value = self.slider.value()
        return [name, value]

class FactorSliderGrid(QtGui.QWidget):
    """A group of FactorSliders aligned in a grid."""
    def __init__(self, names, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        self.factorSliders = [FactorSlider( \
                              name, factor_bits[name], scale_bits[name]) \
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
        return dict([factorSlider.getValue() \
                     for factorSlider in self.factorSliders])

class PlotWindow(Qwt5.QwtPlot):
    def __init__(self, title):
        Qwt5.QwtPlot.__init__(self)
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
        self.setCanvasBackground(QtGui.QColor(QtCore.Qt.white))
        self.setCanvasLineWidth(1)
        self.setTitle(title)
        self.setAutoReplot(True)

        self.curve = Qwt5.QwtPlotCurve()
        self.curve.setRenderHint(Qwt5.QwtPlotItem.RenderAntialiased)
        self.curve.attach(self)

        self.grid = Qwt5.QwtPlotGrid()
        self.grid.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, alpha=32)))
        self.grid.attach(self)

    def plotData(self, x, y):
        self.curve.setData(x, y)


#--------------------------------------------------
# Central Widget
#--------------------------------------------------

class IIRSimCentralWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        # read config, create filter and get names
        cfgfile = 'directForm2.txt'
        self.filt = iirsim_cfg.readconfig(cfgfile)
        names = self.filt.factors().keys()
        factor_bits = self.filt.factor_bits()
        scale_bits = self.filt.scale_bits()

        # Factor Slider Array
        self.slider_grid = FactorSliderGrid(names, factor_bits, scale_bits)
        slider_layout = QtGui.QVBoxLayout()
        slider_layout.addWidget(self.slider_grid)
        slider_groupbox = QtGui.QGroupBox('Factors')
        slider_groupbox.setLayout(slider_layout)

        # Plot Options
        self.impulse_length_edit = QtGui.QLineEdit()
        self.impulse_length_edit.setText('32')
        self.impulse_length_edit.setValidator(QtGui.QIntValidator())
        plot_options_layout = QtGui.QGridLayout()
        plot_options_layout.addWidget(QtGui.QLabel('Length'), 0, 0)
        plot_options_layout.addWidget(self.impulse_length_edit, 0, 1)
        plot_options_groupbox = QtGui.QGroupBox('Plot Options')
        plot_options_groupbox.setLayout(plot_options_layout)

        # Plot Windows
        self.impulse_plot = PlotWindow('Impulse Response')
        self.impulse_plot.setAxisScale(Qwt5.QwtPlot.yLeft, -1, 1)
        self.frequency_plot = PlotWindow('Frequency Response')
        self.frequency_plot.setAxisScale(Qwt5.QwtPlot.yLeft, -96, 30)
        self.frequency_plot.setAxisScale(Qwt5.QwtPlot.xBottom, \
                                         1e-3, 1)
        self.frequency_plot.setAxisScaleEngine(Qwt5.QwtPlot.xBottom, \
                                           Qwt5.QwtLog10ScaleEngine())
        self.frequency_plot.setAxisTitle(Qwt5.QwtPlot.xBottom, \
                                         'f [fs/2]')
        self.frequency_plot.setAxisTitle(Qwt5.QwtPlot.yLeft, \
                                         'dB')


        # Global Layout
        controlVBox = QtGui.QVBoxLayout()
        controlVBox.addWidget(slider_groupbox, 0)
        controlVBox.addWidget(plot_options_groupbox, 0)
        controlVBox.addStretch(1)

        plotVBox = QtGui.QVBoxLayout()
        plotVBox.addWidget(self.impulse_plot)
        plotVBox.addWidget(self.frequency_plot)

        globalHBox = QtGui.QHBoxLayout()
        globalHBox.addLayout(controlVBox, 1)
        globalHBox.addStretch(0)
        globalHBox.addLayout(plotVBox, 2)
        self.setLayout(globalHBox)

        # signals
        self.connect(self.slider_grid, QtCore.SIGNAL('valueChanged()'), \
                     self.updatePlot)
        self.connect(self.impulse_length_edit, \
                     QtCore.SIGNAL('editingFinished()'), \
                     self.updatePlot)

        self.updatePlot()

    def updatePlot(self):
        length = int(self.impulse_length_edit.text())
        self.impulse_plot.setAxisScale(Qwt5.QwtPlot.xBottom, 0, length)
        values = self.slider_grid.getValues()
        for (name, value) in values.iteritems():
            self.filt.set_factor(name, value)
        x = numpy.array(range(length+1))
        f = numpy.arange(0, 1, 2.0/length)
        y = numpy.array(self.filt.impulse_response(length+1, scaled=True))
        Y = 20*numpy.log10(numpy.abs(numpy.fft.fft(y))[0:length/2+1])
        self.impulse_plot.plotData(x, y)
        self.frequency_plot.plotData(f, Y)

#--------------------------------------------------
# Main Window
#--------------------------------------------------

class IIRSimMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        mainTitle = 'IIRSim'
        self.setWindowTitle(mainTitle)

        self.setCentralWidget(IIRSimCentralWidget())

        statusBar = QtGui.QStatusBar()
        statusBar.addWidget(QtGui.QLabel('Ready'))
        self.setStatusBar(statusBar)

