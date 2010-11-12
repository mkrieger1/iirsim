import os, numpy
from PyQt4 import QtCore, QtGui, Qwt5

import iirsim_cfg


#--------------------------------------------------
# Useful widgets
#--------------------------------------------------

class floatValidator(QtGui.QDoubleValidator):
    def __init__(self, float_min, float_max, parent):
        QtGui.QDoubleValidator.__init__(self, parent)
        self.setRange(float_min, float_max)
        self.parent = parent

    def fixup(self, string):
        d = float(string)
        if d < self.bottom():
            d = self.bottom()
        elif d > self.top():
            d = self.top()
        self.parent.setText(str(d))
        self.parent.emit(QtCore.SIGNAL('editingFinished()'))

class floatEdit(QtGui.QLineEdit):
    def __init__(self, float_min, float_max):
        QtGui.QLineEdit.__init__(self)
        self.validator = floatValidator(float_min, float_max, self)
        self.setValidator(self.validator)
        self.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

class intValidator(QtGui.QIntValidator):
    def __init__(self, int_min, int_max, parent):
        QtGui.QIntValidator.__init__(self, parent)
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
# Filter settings
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
        self._updateLabel()

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
    def __init__(self, factor_dict, factor_bits, scale_bits):
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

class FilterSettings(QtGui.QWidget):
    def __init__(self, iirfilter):
        QtGui.QWidget.__init__(self)
        factors     = iirfilter.factors()
        bits        = iirfilter.bits()
        factor_bits = iirfilter.factor_bits()
        scale_bits  = iirfilter.scale_bits()

        self.bits_edit = intEdit(2, 32)
        self.num_samples_edit.setText(str(bits))

        self.slider_grid = FactorSliderGrid(factors, factor_bits, \
                                            scale_bits)

        self.connect(self.slider_grid, QtCore.SIGNAL('valueChanged()'), \
                     self._signalValueChanged)
        self.connect(self.bits_edit, QtCore.SIGNAL('editingFinished()'), \
                     self._signalValueChanged)

    def _signalValueChanged(self):
        self.emit(QtCore.SIGNAL('valueChanged()'))

    def get_settings(self):
        bits = int(self.bits_edit.text())
        factors = self.slider_grid.getValues()
        return dict([['bits',    bits], \
                     ['factors', factors]])

#--------------------------------------------------
# Plot options
#--------------------------------------------------

class plotOptions(QtGui.QWidget):
    def __init__(self, samples=128, rate=44100, show_time=False):
        QtGui.QWidget.__init__(self)
        self.num_samples_edit = intEdit(8, 8192)
        self.num_samples_edit.setText(str(samples))
        self.time_checkbox = QtGui.QCheckBox('Show time instead of samples')
        self.time_checkbox.setChecked(show_time)
        self.sample_rate_edit = floatEdit(1, 1e12)
        self.sample_rate_edit.setText(str(rate))
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel('Samples'),     0, 0)
        grid.addWidget(self.num_samples_edit,       0, 1)
        grid.addWidget(QtGui.QLabel('Sample rate'), 1, 0)
        grid.addWidget(QtGui.QLabel('Hz'),          1, 2)
        grid.addWidget(self.sample_rate_edit,       1, 1)
        grid.addWidget(self.time_checkbox,          2, 0, 1, 2)
        self.setLayout(grid)

        self.connect(self.num_samples_edit, \
                     QtCore.SIGNAL('editingFinished()'), \
                     self._signalEditingFinished)
            
        self.connect(self.sample_rate_edit, \
                     QtCore.SIGNAL('editingFinished()'), \
                     self._signalEditingFinished)

        self.connect(self.time_checkbox, \
                     QtCore.SIGNAL('stateChanged(int)'), \
                     self._signalEditingFinished)

    def _signalEditingFinished(self):
        self.emit(QtCore.SIGNAL('editingFinished()'))

    def get_options(self):
        num_samples = int(self.num_samples_edit.text())
        sample_rate = float(self.sample_rate_edit.text())
        time_checked = self.time_checkbox.isChecked()
        return dict([ \
            ['num_samples', num_samples], \
            ['sample_rate', sample_rate], \
            ['time_checked', time_checked] ])


#--------------------------------------------------
# Plot Area
#--------------------------------------------------

class Plot(Qwt5.QwtPlot):
    def __init__(self, title):
        Qwt5.QwtPlot.__init__(self)
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
        self.setCanvasBackground(QtGui.QColor(QtCore.Qt.white))
        self.setCanvasLineWidth(1)
        self.setTitle(title)

        self.curve = Qwt5.QwtPlotCurve()
        self.curve.setRenderHint(Qwt5.QwtPlotItem.RenderAntialiased)
        self.curve.attach(self)

        self.grid = Qwt5.QwtPlotGrid()
        self.grid.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, alpha=32)))
        self.grid.attach(self)

    def plotData(self, x, y):
        self.curve.setData(x, y)

class FilterResponsePlot(QtGui.QWidget):
    def __init__(self, iirfilter):
        QtGui.QWidget.__init__(self)
        self.filt = iirfilter
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

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.impulse_plot, 1)
        vbox.addWidget(self.frequency_plot, 1)
        self.setLayout(vbox)

    def updatePlot(self, options):
        length = options['num_samples']
        fs = options['sample_rate']
        time = options['time_checked']
        duration = (length-1)/fs
        axis = Qwt5.QwtPlot.xBottom
        if time:
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
        else:
            self.impulse_plot.setAxisScale(axis, 0, length-1)
            self.impulse_plot.setAxisTitle(axis,'Samples')

        t = numpy.arange(length)
        if time:
            t = t*duration/(length-1)
        y = numpy.array(self.filt.impulse_response(length, scaled=True))
        self.impulse_plot.plotData(t, y)

        fftlen = (length+1)/2
        f = numpy.linspace(0, fs/2, fftlen)
        Y = 20*numpy.log10(numpy.abs(numpy.fft.fft(y)[:fftlen]))

        min_gain = 20*numpy.log10(2**(-self.filt.bits()))
        for i in range(fftlen):
            if Y[i] == -numpy.Inf:
                Y[i] = min_gain
        self.frequency_plot.setAxisScale(axis, fs/2000, fs/2)
        self.frequency_plot.plotData(f, Y)

        self.impulse_plot.replot()
        self.frequency_plot.replot()


#--------------------------------------------------
# Central Widget
#--------------------------------------------------

class IIRSimCentralWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        # read config, create filter and get names
        cfgfile = '../filters/directForm2.txt'
        self.filt = iirsim_cfg.readconfig(cfgfile)
        factor_dict = self.filt.factors()
        factor_bits = self.filt.factor_bits()
        scale_bits = self.filt.scale_bits()

        # Factor Slider Array
        self.slider_grid = FactorSliderGrid( \
            factor_dict, factor_bits, scale_bits)
        slider_groupbox = QtGui.QGroupBox('Filter coefficients')
        slider_groupbox.setLayout(self.slider_grid.layout())

        # Plot Options
        self.plot_options = plotOptions()
        plot_options_groupbox = QtGui.QGroupBox('Plot Options')
        plot_options_groupbox.setLayout(self.plot_options.layout())

        # Plot Area
        self.plot_area = FilterResponsePlot(self.filt)

        # Global Layout
        controlVBox = QtGui.QVBoxLayout()
        controlVBox.addWidget(slider_groupbox, 0)
        controlVBox.addWidget(plot_options_groupbox, 0)
        controlVBox.addStretch(1)

        globalHBox = QtGui.QHBoxLayout()
        globalHBox.addLayout(controlVBox, 1)
        globalHBox.addStretch(0)
        globalHBox.addWidget(self.plot_area, 2)
        self.setLayout(globalHBox)

        # signals
        self.connect(self.slider_grid, QtCore.SIGNAL('valueChanged()'), \
                     self._updatePlot)
        self.connect(self.plot_options, QtCore.SIGNAL('editingFinished()'), \
                     self._updatePlot)

        self._updatePlot()

    def _updatePlot(self):
        coefficients = self.slider_grid.getValues()
        for (name, value) in coefficients.iteritems():
            self.filt.set_factor(name, value)
        options = self.plot_options.get_options()
        self.plot_area.updatePlot(options)


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

