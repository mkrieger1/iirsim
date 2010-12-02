import os, numpy
from PyQt4 import QtCore, QtGui, Qwt5

import iirsim_cfg


#--------------------------------------------------
# Useful widgets
#--------------------------------------------------

# float line edit
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

# int  line edit
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

# file selection/load/save
class LineEditDnD(QtGui.QLineEdit):
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.scheme() == 'file':
                event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        filename = str(event.mimeData().urls()[0].toLocalFile())
        self.setText(os.path.realpath(filename))

class FileSelect(QtGui.QWidget):
    def __init__(self, what, loadtext, savetext):
        QtGui.QWidget.__init__(self)
        self.filename_edit = LineEditDnD()
        self.filename_edit.setToolTip('Enter path to %s' % what)
        self.loadtext = loadtext
        self.savetext = savetext

        self.loadbutton = QtGui.QPushButton('Load...')
        self.savebutton = QtGui.QPushButton('Save...')
        self.loadbutton.setToolTip(self.loadtext)
        self.savebutton.setToolTip(self.savetext)
        self.last_path = os.path.abspath(os.path.expanduser('~'))

        self.connect(self.loadbutton, QtCore.SIGNAL('clicked()'), \
            self._select_load_file)
        self.connect(self.savebutton, QtCore.SIGNAL('clicked()'), \
            self._select_save_file)
        self.connect(self.filename_edit, \
            QtCore.SIGNAL('editingFinished()'), self._signalEditingFinished)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.loadbutton)
        hbox.addWidget(self.savebutton)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.filename_edit)
        vbox.addLayout(hbox)
        vbox.setMargin(0)
        self.setLayout(vbox)

    def text(self):
        return self.filename_edit.text()
 
    def _select_load_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, \
            caption = self.loadtext, \
            #filter = 'Text files (*.txt);;All Files (*.*)', \
            directory = self.last_path)
        if filename: # False if dialog is cancelled
            self.last_path = os.path.dirname(str(filename))
            self.filename_edit.setText(filename)
            self._signalEditingFinished()
 
    def _select_save_file(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, \
            caption = self.savetext, \
            #filter = 'Text files (*.txt);;All Files (*.*)', \
            directory = self.last_path)
        if filename: # False if dialog is cancelled
            self.last_path = os.path.dirname(str(filename))
            print 'saving to %s' % filename #TODO

    def _signalEditingFinished(self):
        self.emit(QtCore.SIGNAL('editingFinished()'))

#--------------------------------------------------
# Input data settings
#--------------------------------------------------

class InputSettings(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.dropdown = QtGui.QComboBox()
        self.dropdown.addItems(['Unit pulse', 'Custom pulse'])

        self.file_select = FileSelect('input data file', \
            'Load pulse from file', 'Save filtered pulse to file')

        self.input_norm = QtGui.QCheckBox('Input is normalized')
        self.input_norm.setChecked(True)
        self.file_select.layout().itemAt(1).layout().insertWidget( \
            0, self.input_norm)

        self.connect(self.dropdown, QtCore.SIGNAL('currentIndexChanged(int)'), \
                     self._signalChanged)
        self.connect(self.file_select, QtCore.SIGNAL('editingFinished()'), \
                     self._signalChanged)
        self.connect(self.input_norm, QtCore.SIGNAL('stateChanged(int)'), \
                     self._signalChanged)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.dropdown)
        vbox.addWidget(self.file_select)
        self.setLayout(vbox)

        self._signalChanged()

    def get_settings(self):
        if self.dropdown.currentIndex() == 1:
            pulse_type = 'custom'
        else:
            pulse_type = 'unit'
        pulse_file = os.path.abspath(os.path.expanduser( \
            str(self.file_select.text())) )
        norm = self.input_norm.isChecked()
        return dict([ \
            ['pulse_type', pulse_type], \
            ['pulse_file', pulse_file], \
            ['input_norm', norm]])

    def _signalChanged(self):
        pulse_type = self.get_settings()['pulse_type']
        if pulse_type == 'unit':
            self.file_select.setEnabled(False)
            self.input_norm.setEnabled(False)
            self.emit(QtCore.SIGNAL('valueChanged()'))
        else:
            self.file_select.setEnabled(True)
            self.input_norm.setEnabled(True)
            if self.file_select.text():
                self.emit(QtCore.SIGNAL('valueChanged()'))
            

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
    def __init__(self, name, factor_bits, norm_bits=None, factor=None):
        QtGui.QWidget.__init__(self)

        if norm_bits is None:
            norm_bits = factor_bits-2
        self.norm = 2**norm_bits
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
        self.spinBox.setAlignment(QtCore.Qt.AlignRight)
        self.spinBox.setMinimum(float(self.slider.minimum())/self.norm)
        self.spinBox.setMaximum(float(self.slider.maximum())/self.norm)
        self.spinBox.setSingleStep(1.0/self.norm)
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

    def _valueLabelText(self, value=None, norm=None):
        if value is None:
            value = self.slider.value()
        if norm is None:
            norm = self.norm
        return '%i/%i =' % (value, norm)

    def _updateLabel(self):
        text = self._valueLabelText()
        self.valueLabel.setText(text)

    def _updateSlider(self):
        self.slider.setValue(round(self.spinBox.value()*self.norm))

    def _updateSpinBox(self):
        self.spinBox.setValue(float(self.slider.value())/self.norm)

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
    def __init__(self, factor_dict, factor_bits, norm_bits):
        QtGui.QWidget.__init__(self)

        self.factorSliders = dict(zip(factor_dict.keys(), \
            [FactorSlider(name, factor_bits[name], norm_bits[name], factor) \
                          for (name, factor) in factor_dict.iteritems()]))

        gridLayout = QtGui.QGridLayout()
        for (row, factorSlider) in enumerate(self.factorSliders.itervalues()):
            gridLayout.addWidget(factorSlider.nameLabel,  row, 0)
            gridLayout.addWidget(factorSlider.slider,     row, 1)
            gridLayout.addWidget(factorSlider.valueLabel, row, 2)
            gridLayout.addWidget(factorSlider.spinBox,    row, 3)
            self.connect(factorSlider, QtCore.SIGNAL('valueChanged()'), \
                         self._signalValueChanged)

        if factor_dict:
            minLabelWidth = max([slider._getMinLabelWidth() \
                                 for slider in self.factorSliders.itervalues()])
            gridLayout.setColumnMinimumWidth(1, 50)
            gridLayout.setColumnMinimumWidth(2, minLabelWidth)

        gridLayout.setMargin(0)
        self.setLayout(gridLayout)

    def _signalValueChanged(self):
        self.emit(QtCore.SIGNAL('valueChanged()'))

    def getValues(self):
        return dict([self.factorSliders[name].getValue() \
                     for name in self.factorSliders.iterkeys()])

class FilterSettings(QtGui.QWidget):
    def __init__(self, filename):
        QtGui.QWidget.__init__(self)

        self.last_filename = os.path.abspath(os.path.expanduser(filename))

        self.filter_select = FileSelect('filter definition file', \
            'Load filter from file', 'Save filter to file')
        self.filter_select.filename_edit.setText(filename)
        self.bits_edit = QtGui.QSpinBox()
        self.bits_edit.setAlignment(QtCore.Qt.AlignRight)
        self.bits_edit.setRange(2, 32)
        self.bits_edit_label = QtGui.QLabel('Bits')
        self.sliders = FactorSliderGrid({}, {}, None)

        self.connect(self.filter_select, QtCore.SIGNAL('editingFinished()'), \
                     self._signalFilterChanged)
        self.connect(self.bits_edit, QtCore.SIGNAL('valueChanged(int)'), \
                     self._signalValueChanged)
        self.connect(self.sliders, QtCore.SIGNAL('valueChanged()'), \
                     self._signalValueChanged)

        self.filter_select.layout().itemAt(1).layout().insertWidget( \
            0, self.bits_edit)
        self.filter_select.layout().itemAt(1).layout().insertWidget( \
            0, self.bits_edit_label)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.filter_select)
        self.vbox.addWidget(self.sliders)
        self.setLayout(self.vbox)

    def _signalValueChanged(self):
        self._updateFilter()
        self.emit(QtCore.SIGNAL('valueChanged()'))

    def _signalFilterChanged(self):
        filename = os.path.abspath(os.path.expanduser( \
            str(self.filter_select.text())) )
        if not filename == self.last_filename:
            self.last_filename = filename
            self.emit(QtCore.SIGNAL('filterChanged()'))

    def load_filter(self):
        try:
            self.filt = iirsim_cfg.read_config(self.last_filename)
        except (IOError, RuntimeError, ValueError) as (msg, ):
            self.bits_edit.setEnabled(False)
            self.bits_edit_label.setEnabled(False)
            self.sliders.setEnabled(False)
            raise

        factors     = self.filt.factors()
        bits        = self.filt.bits()
        factor_bits = self.filt.factor_bits()
        norm_bits   = self.filt.norm_bits()

        self.bits_edit.setValue(bits)
        self.bits_edit.setEnabled(True)
        self.bits_edit_label.setEnabled(True)

        # destroy old and create new sliders (TODO better solution?)
        self.sliders.setParent(None)
        self.sliders.deleteLater()
        self.sliders = FactorSliderGrid(factors, factor_bits, norm_bits)
        self.connect(self.sliders, QtCore.SIGNAL('valueChanged()'), \
                     self._signalValueChanged)
        self.vbox.addWidget(self.sliders)

    def _updateFilter(self):
        bits = self.bits_edit.value()
        factors = self.sliders.getValues()
        for (name, value) in factors.iteritems():
            self.filt.set_factor(name, value)
        self.filt.set_bits(bits)

    def get_filter(self):
        return self.filt

#--------------------------------------------------
# Plot options
#--------------------------------------------------

class logAxes(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.logx_pulse = QtGui.QCheckBox('horizontal')
        self.logy_pulse = QtGui.QCheckBox('vertical')
        self.logx_spectrum = QtGui.QCheckBox('horizontal')
        self.logy_spectrum = QtGui.QCheckBox('vertical')

        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel('Logarithmic pulse plot'), 0, 0)
        grid.addWidget(QtGui.QLabel('Logarithmic spectrum plot'), 1, 0)
        grid.addWidget(self.logx_pulse, 0, 1)
        grid.addWidget(self.logy_pulse, 0, 2)
        grid.addWidget(self.logx_spectrum, 1, 1)
        grid.addWidget(self.logy_spectrum, 1, 2)
        grid.setMargin(0)
        self.setLayout(grid)

        self.connect(self.logx_pulse, QtCore.SIGNAL('stateChanged(int)'), \
                     self._signalStateChanged)
        self.connect(self.logy_pulse, QtCore.SIGNAL('stateChanged(int)'), \
                     self._signalStateChanged)
        self.connect(self.logx_spectrum, QtCore.SIGNAL('stateChanged(int)'), \
                     self._signalStateChanged)
        self.connect(self.logy_spectrum, QtCore.SIGNAL('stateChanged(int)'), \
                     self._signalStateChanged)

    def isChecked(self):
        return [box.isChecked() for box in [self.logx_pulse, \
                                            self.logy_pulse, \
                                            self.logx_spectrum, \
                                            self.logy_spectrum]]

    def setChecked(self, state):
        for (i, box) in enumerate([self.logx_pulse, self.logy_pulse, \
                                   self.logx_spectrum, self.logy_spectrum]):
            box.setChecked(state[i])

    def _signalStateChanged(self):
        self.emit(QtCore.SIGNAL('stateChanged()'))


class plotOptions(QtGui.QWidget):
    def __init__(self, samples=128, rate=44100, show_time=False):
        QtGui.QWidget.__init__(self)
        self.num_samples_edit = intEdit(8, 8192)
        self.num_samples_edit.setText(str(samples))
        self.sample_rate_edit = floatEdit(1, 1e12)
        self.sample_rate_edit.setText(str(rate))
        self.time_checkbox = QtGui.QCheckBox('Show time instead of samples')
        self.time_checkbox.setChecked(show_time)
        self.spectrum_norm = QtGui.QCheckBox('Normalize frequency spectrum')
        self.spectrum_norm.setChecked(True)

        self.logaxes = logAxes()
        self.logaxes.setChecked([False, False, True, True])

        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel('Samples'),     0, 0)
        grid.addWidget(self.num_samples_edit,       0, 1)
        grid.addWidget(QtGui.QLabel('Sample rate'), 1, 0)
        grid.addWidget(QtGui.QLabel('Hz'),          1, 2)
        grid.addWidget(self.sample_rate_edit,       1, 1)
        grid.addWidget(self.time_checkbox,          2, 0, 1, 2)
        grid.addWidget(self.spectrum_norm,          3, 0, 1, 2)
        grid.addWidget(self.logaxes,                4, 0, 2, 2)
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
        self.connect(self.spectrum_norm, \
                     QtCore.SIGNAL('stateChanged(int)'), \
                     self._signalEditingFinished)
        self.connect(self.logaxes, \
                     QtCore.SIGNAL('stateChanged()'), \
                     self._signalEditingFinished)

    def _signalEditingFinished(self):
        self.emit(QtCore.SIGNAL('editingFinished()'))

    def get_options(self):
        num_samples = int(self.num_samples_edit.text())
        sample_rate = float(self.sample_rate_edit.text())
        time_checked = self.time_checkbox.isChecked()
        spectrum_norm = self.spectrum_norm.isChecked()
        [logx_pulse, logy_pulse, logx_spectrum, logy_spectrum] = \
            self.logaxes.isChecked()
        return dict([ \
            ['num_samples', num_samples], \
            ['sample_rate', sample_rate], \
            ['time_checked', time_checked], \
            ['spectrum_norm', spectrum_norm], \
            ['logx_pulse', logx_pulse], \
            ['logy_pulse', logy_pulse], \
            ['logx_spectrum', logx_spectrum], \
            ['logy_spectrum', logy_spectrum] ])


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
        #self.setTitle(title)

        self.grid = Qwt5.QwtPlotGrid()
        self.grid.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, alpha=32)))
        self.grid.attach(self)

        self.curves = []

    def setLogScale(self, axis):
        self.setAxisScaleEngine(axis, Qwt5.QwtLog10ScaleEngine())

    def setLinScale(self, axis):
        self.setAxisScaleEngine(axis, Qwt5.QwtLinearScaleEngine())

    def plot(self, data, colors=None):
        # detach old curves from plot
        for curve in self.curves:
            curve.detach()
        # shrink or grow list of curves
        if len(data) < len(self.curves):
            self.curves = self.curves[:len(data)]
        elif len(data) > len(self.curves):
            for i in range(len(data)-len(self.curves)):
                curve = Qwt5.QwtPlotCurve()
                curve.setRenderHint(Qwt5.QwtPlotItem.RenderAntialiased)
                self.curves.append(curve)
        # re-attach curves with new data in reversed order so that the first
        # item in the data list is on top
        for (i, [x, y]) in enumerate(data):
            self.curves[i].setData(x, y)
            if colors is not None:
                self.curves[i].setPen(QtGui.QPen(colors[i]))
        for curve in reversed(self.curves):
            curve.attach(self)

class FilterResponsePlot(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        xaxis = Qwt5.QwtPlot.xBottom
        yaxis = Qwt5.QwtPlot.yLeft
        self.impulse_plot = Plot('Impulse response')
        self.frequency_plot = Plot('Frequency response')
        self.frequency_plot.setAxisTitle(xaxis, 'Frequency / Hz')

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.impulse_plot, 1)
        vbox.addWidget(self.frequency_plot, 1)
        self.setLayout(vbox)

    def replot(self, data, filt, options):
        use_unit_pulse = (data is None)

        length        = options['num_samples']
        fs            = options['sample_rate']
        time          = options['time_checked']
        spectrum_norm = options['spectrum_norm']
        input_norm    = options['input_norm']
        logx_pulse    = options['logx_pulse']
        logy_pulse    = options['logy_pulse']
        logx_spectrum = options['logx_spectrum']
        logy_spectrum = options['logy_spectrum']

        duration = (length-1)/fs
        fftlen = (length+1)/2
        t = numpy.arange(length)
        f = numpy.linspace(1, fftlen, fftlen)*fs/2/fftlen
        xaxis = Qwt5.QwtPlot.xBottom
        yaxis = Qwt5.QwtPlot.yLeft

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
            t = t*duration/(length-1)
            self.impulse_plot.setAxisTitle(xaxis, 'Time / %ss' % prefix)
        else:
            self.impulse_plot.setAxisTitle(xaxis, 'Samples')

        if use_unit_pulse:
            x = numpy.array(filt.unit_pulse(length, norm=True))
        else:
            x = data
            while len(x) < length:
                x.append(0.0)
            x = numpy.array(x)
            if not input_norm:
                B = 1 << filt.bits()-1
                x /= B

        [y_id, y] = [numpy.array( \
                     filt.response(x, length, True, ideal)) \
                     for ideal in [True, False]]

        X = numpy.abs(numpy.fft.fft(x)[1:fftlen])
        [Y_id, Y] = \
            [numpy.abs(numpy.fft.fft(data)[1:fftlen]) for data in [y_id, y]]
        if spectrum_norm:
            Y_id = Y_id/X
            Y    = Y   /X

        impulse_plot_data = [[t, y], [t, y_id]]
        frequency_plot_data = [[f, Y], [f, Y_id]]
        if not use_unit_pulse:
            impulse_plot_data.append([t, x])
        if not spectrum_norm:
            frequency_plot_data.append([f, X])

        if logx_pulse:
            self.impulse_plot.setLogScale(xaxis)
            self.impulse_plot.setAxisScale(xaxis, t[1], t[length-1])
        else:
            self.impulse_plot.setLinScale(xaxis)
            self.impulse_plot.setAxisScale(xaxis, 0, t[length-1])

        if logx_spectrum:
            self.frequency_plot.setLogScale(xaxis)
            self.frequency_plot.setAxisScale(xaxis, fs/200, fs/2)
        else:
            self.frequency_plot.setLinScale(xaxis)
            self.frequency_plot.setAxisScale(xaxis, 0, fs/2)

        if logy_pulse:
            minval = 1.0 / 2**(filt.bits()-1)
            self.impulse_plot.setAxisScale(yaxis, 20*numpy.log10(minval), 0)
            self.impulse_plot.setAxisTitle(yaxis, 'Signal amplitude / dBFS')
            for (i, data) in enumerate(impulse_plot_data):
                d = data[1]
                for j in range(len(d)):
                    if d[j] <= 0:
                        d[j] = minval
                impulse_plot_data[i][1] = 20*numpy.log10(d)
        else:
            self.impulse_plot.setAxisScale(yaxis, -1, 1)
            self.impulse_plot.setAxisTitle(yaxis, 'Signal amplitude')

        if logy_spectrum:
            self.frequency_plot.setAxisScale(yaxis, -30, 30)
            self.frequency_plot.setAxisTitle(yaxis, 'Magnitude / dB')
            for (i, data) in enumerate(frequency_plot_data):
                d = data[1]
                frequency_plot_data[i][1] = 20*numpy.log10(d)
        else:
            self.frequency_plot.setAxisScale(yaxis, 0, 30)
            self.frequency_plot.setAxisTitle(yaxis, 'Magnitude') # TODO title

        colors = [QtCore.Qt.black, QtCore.Qt.gray, QtCore.Qt.blue]
        self.impulse_plot.plot(impulse_plot_data, colors)
        self.frequency_plot.plot(frequency_plot_data, colors)

        self.impulse_plot.replot()
        self.frequency_plot.replot()


#--------------------------------------------------
# Central Widget
#--------------------------------------------------

class IIRSimCentralWidget(QtGui.QWidget):
    def __init__(self, status_bar=None):
        QtGui.QWidget.__init__(self)

        # status bar, if provided
        if status_bar is not None:
            self.status_bar = status_bar

        # Input Data Settings
        self.input_settings = InputSettings()
        self.input_settings_groupbox = QtGui.QGroupBox('Input data')
        self.input_settings_groupbox.setLayout(self.input_settings.layout())
        self.input_data = None
        self.input_norm = self.input_settings.get_settings()['input_norm']

        # Factor Slider Array
        self.filter_settings = FilterSettings( \
            '/home/michael/Studium/diplom/code/iirsim/filters/directForm2.txt')
        self.filter_settings_groupbox = QtGui.QGroupBox('Filter settings')
        self.filter_settings_groupbox.setLayout(self.filter_settings.layout())

        # Plot Options
        self.plot_options = plotOptions()
        self.plot_options_groupbox = QtGui.QGroupBox('Plot options')
        self.plot_options_groupbox.setLayout(self.plot_options.layout())

        # Plot Area
        self.plot_area = FilterResponsePlot()

        # Global Layout
        controlVBox = QtGui.QVBoxLayout()
        controlVBox.addWidget(self.input_settings_groupbox, 0)
        controlVBox.addWidget(self.filter_settings_groupbox, 0)
        controlVBox.addWidget(self.plot_options_groupbox, 0)
        controlVBox.addStretch(1)

        globalHBox = QtGui.QHBoxLayout()
        globalHBox.addLayout(controlVBox, 1)
        globalHBox.addStretch(0)
        globalHBox.addWidget(self.plot_area, 2)
        self.setLayout(globalHBox)

        # connect signals
        self.connect(self.filter_settings, QtCore.SIGNAL('filterChanged()'), \
                     self._updateFilter)
        self.connect(self.input_settings, QtCore.SIGNAL('valueChanged()'), \
                     self._updateInput)
        self.connect(self.filter_settings, QtCore.SIGNAL('valueChanged()'), \
                     self._updatePlot)
        self.connect(self.plot_options, QtCore.SIGNAL('editingFinished()'), \
                     self._updatePlot)

        # read input data and plot once
        self._updateFilter()

    # slots
    def _updateFilter(self):
        filter_valid = True

        try:
            self.filter_settings.load_filter()
        except (IOError, RuntimeError, ValueError) as (msg, ):
            filter_valid = False
            self.input_settings_groupbox.setEnabled(False)
            self.plot_options_groupbox.setEnabled(False)
            self.status_bar.showMessage('Error: %s' % msg)

        if filter_valid:
            self.input_settings_groupbox.setEnabled(True)
            self.plot_options_groupbox.setEnabled(True)
            self.status_bar.clearMessage()
            self._updateInput()

    def _updateInput(self):
        input_settings = self.input_settings.get_settings()
        pulse_type = input_settings['pulse_type']
        pulse_file = input_settings['pulse_file']
        input_norm = input_settings['input_norm']

        data = None
        input_valid = True

        if pulse_type == 'custom':
            try:
                data = iirsim_cfg.read_data(pulse_file)
            except IOError as (msg, ):
                input_valid = False
                self.filter_settings_groupbox.setEnabled(False)
                self.plot_options_groupbox.setEnabled(False)
                self.status_bar.showMessage('Error: %s' % msg)

        if input_valid:
            self.input_data = data
            self.input_norm = input_norm
            self.filter_settings_groupbox.setEnabled(True)
            self.plot_options_groupbox.setEnabled(True)
            self.status_bar.clearMessage()
            self._updatePlot()

    def _updatePlot(self):
        data = self.input_data
        filt = self.filter_settings.get_filter()
        options = self.plot_options.get_options()
        options['input_norm'] = self.input_norm
        try:
            self.status_bar.clearMessage()
            self.plot_area.replot(data, filt, options)
        except ValueError as (msg, ):
            self.status_bar.showMessage('Error: %s' % msg)
        


#--------------------------------------------------
# Main Window
#--------------------------------------------------

class IIRSimMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        mainTitle = 'IIRSim'
        self.setWindowTitle(mainTitle)
        self.resize(960, 540)

        statusBar = QtGui.QStatusBar()
        statusBar.addWidget(QtGui.QLabel('Ready'))
        self.setStatusBar(statusBar)

        self.setCentralWidget(IIRSimCentralWidget(statusBar))

