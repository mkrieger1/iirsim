import os, numpy
from PyQt4 import QtCore, QtGui, Qwt5

import iirsim_cfg

#--------------------------------------------------
# Filter coefficient sliders
#--------------------------------------------------

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
    def __init__(self, name, factor_bits, scale_bits=None, factor=None):
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
        if factor is not None:
            self.slider.setValue(factor)
        else:
            self.slider.setValue(0)
        #self._updateSpinBox()
        self._updateLabel()
        #self._signalValueChanged()

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

    def _getMinLabelWidth(self):
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
    def __init__(self, factor_dict, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        self.factorSliders = dict(zip(factor_dict.keys(), \
            [FactorSlider(name, factor_bits[name], scale_bits[name], factor) \
                          for (name, factor) in factor_dict.iteritems()]))

        gridLayout = QtGui.QGridLayout()
        for (row, factorSlider) in enumerate(self.factorSliders.itervalues()):
            gridLayout.addWidget(factorSlider.nameLabel,  row, 0)
            gridLayout.addWidget(factorSlider.slider,     row, 1)
            gridLayout.addWidget(factorSlider.valueLabel, row, 2)
            gridLayout.addWidget(factorSlider.spinBox,    row, 3)
            self.connect(factorSlider, QtCore.SIGNAL('valueChanged()'), \
                         self._signalValueChanged)
        minLabelWidth = max([slider._getMinLabelWidth() \
                             for slider in self.factorSliders.itervalues()])
        gridLayout.setColumnMinimumWidth(1, 50)
        gridLayout.setColumnMinimumWidth(2, minLabelWidth)
        self.setLayout(gridLayout)

    def _signalValueChanged(self):
        self.emit(QtCore.SIGNAL('valueChanged()'))

    def getValues(self):
        return dict([self.factorSliders[name].getValue() \
                     for name in self.factorSliders.iterkeys()])

#--------------------------------------------------
# Plot options
#--------------------------------------------------

class intValidator(QtGui.QIntValidator):
    def __init__(self, int_min, int_max, parent):
        QtGui.QIntValidator.__init__(self)
        self.setRange(int_min, int_max)
        self.parent = parent

    def fixup(self, string):
        i = int(string)
        if i < self.bottom():
            i = self.bottom()
        elif i > self.top():
            i = self.top()
        self.parent.setText(str(i))
        self.parent.emit(QtCore.SIGNAL('editingFinished()'))

class intEdit(QtGui.QLineEdit):
    def __init__(self, int_min, int_max):
        QtGui.QLineEdit.__init__(self)
        self.validator = intValidator(int_min, int_max, self)
        self.setValidator(self.validator)
        self.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

#--------------------------------------------------
# Plot area
#--------------------------------------------------

class Plot(Qwt5.QwtPlot):
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
        factor_dict = self.filt.factors()
        factor_bits = self.filt.factor_bits()
        scale_bits = self.filt.scale_bits()

        # Factor Slider Array
        self.slider_grid = FactorSliderGrid( \
            factor_dict, factor_bits, scale_bits)
        slider_layout = QtGui.QVBoxLayout()
        slider_layout.addWidget(self.slider_grid)
        slider_groupbox = QtGui.QGroupBox('Filter coefficients')
        slider_groupbox.setLayout(slider_layout)

        # Plot Options
        self.num_samples_edit = intEdit(8, 8192)
        self.num_samples_edit.setText('32')
        self.sample_rate_edit = QtGui.QLineEdit()
        self.sample_rate_edit.setText('50000')
        self.sample_rate_edit.setValidator(QtGui.QDoubleValidator(None))
        self.sample_rate_edit.setAlignment( \
            QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        plot_options_layout = QtGui.QGridLayout()
        plot_options_layout.addWidget(QtGui.QLabel('Samples'),     0, 0)
        plot_options_layout.addWidget(self.num_samples_edit,       0, 1)
        plot_options_layout.addWidget(QtGui.QLabel('Sample rate'), 1, 0)
        plot_options_layout.addWidget(QtGui.QLabel('Hz'),          1, 2)
        plot_options_layout.addWidget(self.sample_rate_edit,       1, 1)
        plot_options_groupbox = QtGui.QGroupBox('Plot Options')
        plot_options_groupbox.setLayout(plot_options_layout)

        # Plot Windows
        xaxis = Qwt5.QwtPlot.xBottom
        yaxis = Qwt5.QwtPlot.yLeft
        self.impulse_plot = Plot('Impulse Response')
        self.impulse_plot.setAxisScale(yaxis, -1, 1)
        self.impulse_plot.setAxisTitle(yaxis, 'Amplitude')
        self.frequency_plot = Plot('Frequency Response')
        self.frequency_plot.setAxisScale(yaxis, -30, 30)
        self.frequency_plot.setAxisScaleEngine(xaxis, \
                                Qwt5.QwtLog10ScaleEngine())
        self.frequency_plot.setAxisTitle(xaxis, 'Frequency / Hz')
        self.frequency_plot.setAxisTitle(yaxis, 'Gain / dB')


        # Global Layout
        controlVBox = QtGui.QVBoxLayout()
        controlVBox.addWidget(slider_groupbox, 0)
        controlVBox.addWidget(plot_options_groupbox, 0)
        controlVBox.addStretch(1)

        plotVBox = QtGui.QVBoxLayout()
        plotVBox.addWidget(self.impulse_plot, 1)
        plotVBox.addWidget(self.frequency_plot, 1)

        globalHBox = QtGui.QHBoxLayout()
        globalHBox.addLayout(controlVBox, 1)
        globalHBox.addStretch(0)
        globalHBox.addLayout(plotVBox, 2)
        self.setLayout(globalHBox)

        # signals
        self.connect(self.slider_grid, QtCore.SIGNAL('valueChanged()'), \
                     self.updatePlot)
        self.connect(self.num_samples_edit, \
                     QtCore.SIGNAL('editingFinished()'), \
                     self.updatePlot)
        self.connect(self.sample_rate_edit, \
                     QtCore.SIGNAL('editingFinished()'), \
                     self.updatePlot)

        self.updatePlot()

    def updatePlot(self):
        length = int(self.num_samples_edit.text())
        fs = float(self.sample_rate_edit.text())
        axis = Qwt5.QwtPlot.xBottom
        duration = length/fs
        prefix = ''
        if 10*duration < 1:
            duration = 1000*duration
            prefix = 'm'
        if 10*duration < 1:
            duration = 1000*duration
            prefix = 'u'
        if 10*duration < 1:
            duration = 1000*duration
            prefix = 'n'
        self.impulse_plot.setAxisScale(axis, 0, duration)
        self.impulse_plot.setAxisTitle(axis,'Time / %ss' % prefix)
        self.frequency_plot.setAxisScale(axis, fs/1000, fs)

        coefficients = self.slider_grid.getValues()
        for (name, value) in coefficients.iteritems():
            self.filt.set_factor(name, value)

        t = numpy.linspace(0, duration, length)
        y = numpy.array(self.filt.impulse_response(length, scaled=True))
        self.impulse_plot.plotData(t, y)

        fftlen = (length+1)/2
        f = numpy.linspace(0, fs, fftlen)
        Y = 20*numpy.log10(numpy.abs(numpy.fft.fft(y)[:fftlen]))
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

