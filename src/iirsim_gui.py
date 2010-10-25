import os
from PyQt4 import QtCore, QtGui

class FactorSlider(QtGui.QWidget):
    def __init__(self, title, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        self.factor_bits = factor_bits
        self.scale_bits = factor_bits-2 if scale_bits is None else scale_bits

        # slider
        minValue = -2**(factor_bits-1)
        maxValue =  2**(factor_bits-1) - 1
        interval = max(1, 2**(factor_bits-4))

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(minValue, maxValue)
        self.slider.setValue(0)
        self.slider.setPageStep(interval)
        self.slider.setTickInterval(interval)
        self.slider.setTickPosition(self.slider.TicksBelow)

        # label
        self.label = QtGui.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.updateLabel()

        # title
        self.title = QtGui.QLabel()
        self.title.setText(title)

        # layout
        self.title.setMinimumWidth(120)
        self.slider.setMinimumWidth(100)
        self.label.setMinimumWidth(120)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.title)
        hbox.addWidget(self.slider)
        hbox.addWidget(self.label)
        self.setLayout(hbox)

        # signals
        self.connect(self.slider, QtCore.SIGNAL('valueChanged(int)'),
            self.updateLabel)

    def updateLabel(self):
        value = self.slider.value()
        scale = 2**self.scale_bits
        text = '%i/%i = %6.3f' % (value, scale, float(value)/scale)
        self.label.setText(text)

    
class iirSimMainWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.mainTitle = 'IIRSim'
        self.setWindowTitle(self.mainTitle)

        # Global Layout
        globalVBox = QtGui.QVBoxLayout()
        globalVBox.addWidget(FactorSlider('a1', 4))
        globalVBox.addWidget(FactorSlider('hans', 6))
        globalVBox.addWidget(FactorSlider('abrakadabra', 9))
        self.setLayout(globalVBox)

        mainSize = self.sizeHint()
        mainSize.setWidth(640)
        self.resize(mainSize)

## modified LineEdit which accepts dropped files and puts the file path
#class LineEditFileDrop(QtGui.QLineEdit):
#    def dragEnterEvent(self, event):
#        if event.mimeData().hasUrls():
#            url = event.mimeData().urls()[0]
#            if url.scheme() == 'file':
#                event.accept()
#        else:
#            event.ignore()
#
#    def dropEvent(self, event):
#        filename = str(event.mimeData().urls()[0].toLocalFile())
#        self.setText(os.path.realpath(filename))
#
## main window
#class wavDiffMainWindow(QtGui.QWidget):
#    def __init__(self, parent=None):
#        QtGui.QWidget.__init__(self, parent)
#
#        self.mainTitle = 'WavDiff'
#        self.setWindowTitle(self.mainTitle)
#        self.setWindowIcon(QtGui.QIcon('icon/wavdiff.ico'))
#        self.lastFileSelectedPath = os.path.expanduser('~/Desktop')
#
#        # Close Button
#        self.closeButton = QtGui.QPushButton('Close', self)
#        self.connect(self.closeButton, QtCore.SIGNAL('clicked()'),
#            QtGui.qApp, QtCore.SLOT('quit()'))
#        closeButtonHBox = QtGui.QHBoxLayout()  
#        closeButtonHBox.addStretch(0)
#        closeButtonHBox.addWidget(self.closeButton)
#
#        # Source File 1
#        self.source1Label = QtGui.QLabel('Source 1')
#        self.source1Edit = LineEditFileDrop()
#        self.source1OpenButton = QtGui.QPushButton('Open...', self)
#        self.connect(self.source1OpenButton, QtCore.SIGNAL('clicked()'),
#            self.getSource1FileName)
#        self.connect(self.source1Edit, QtCore.SIGNAL('textChanged(QString)'),
#            self.testStartButtonDisable)
#
#        # Source File 2
#        self.source2Label = QtGui.QLabel('Source 2')
#        self.source2Edit = LineEditFileDrop()
#        self.source2OpenButton = QtGui.QPushButton('Open...', self)
#        self.connect(self.source2OpenButton, QtCore.SIGNAL('clicked()'),
#            self.getSource2FileName)
#        self.connect(self.source2Edit, QtCore.SIGNAL('textChanged(QString)'),
#            self.testStartButtonDisable)
#
#        # Source Info Text
#        sourceInfoLabel = QtGui.QLabel('Destination = Source 1 - Source 2')
#
#        # Save as
#        self.progressBar = QtGui.QProgressBar(self)
#        self.saveButton = QtGui.QPushButton('Save as...', self)
#        self.saveButton.setDisabled(True)
#        self.connect(self.saveButton, QtCore.SIGNAL('clicked()'),
#            self.doWavDiff)
#        saveHBox = QtGui.QHBoxLayout()
#        saveHBox.addWidget(self.saveButton)
#        saveHBox.addStretch(1)
#        saveVBox = QtGui.QVBoxLayout()
#        saveVBox.addWidget(self.progressBar)
#        saveVBox.addLayout(saveHBox)
#
#        # Global Layout
#        sourceGrid = QtGui.QGridLayout()
#        sourceGrid.addWidget(self.source1Label, 0, 0)
#        sourceGrid.addWidget(self.source1Edit, 0, 1)
#        sourceGrid.addWidget(self.source1OpenButton, 0, 2)
#        sourceGrid.addWidget(self.source2Label, 1, 0)
#        sourceGrid.addWidget(self.source2Edit, 1, 1)
#        sourceGrid.addWidget(self.source2OpenButton, 1, 2)
#        sourceGrid.addWidget(sourceInfoLabel, 2, 0, 1, 2)
#        sourceGroupBox = QtGui.QGroupBox('Select source files')
#        sourceGroupBox.setLayout(sourceGrid)
#
#        globalVBox = QtGui.QVBoxLayout()
#        globalVBox.addWidget(sourceGroupBox)
#        globalVBox.addSpacing(20)
#        globalVBox.addLayout(saveVBox)
#        globalVBox.addLayout(closeButtonHBox)
#        self.setLayout(globalVBox)
#
#        mainSize = self.sizeHint()
#        mainSize.setWidth(640)
#        self.resize(mainSize)
#        self.setFixedHeight(mainSize.height())
#
#    def getSource1FileName(self):
#        self.getSourceFileName(self.source1Edit)
#    def getSource2FileName(self):
#        self.getSourceFileName(self.source2Edit)
#    def getSourceFileName(self, lineEdit):
#        filename = str(QtGui.QFileDialog.getOpenFileName(self, \
#            filter = 'WAV Files (*.wav);;All Files (*.*)',
#            directory = self.lastFileSelectedPath)) # QString -> str
#        if len(filename):
#            self.lastFileSelectedPath = os.path.dirname(filename)
#            lineEdit.setText(os.path.realpath(filename))
#    def testStartButtonDisable(self):
#        source1 = self.source1Edit.text()
#        source2 = self.source2Edit.text()
#        disabled = not(os.path.isfile(source1) and
#                       os.path.isfile(source2))
#        self.saveButton.setDisabled(disabled)
#
#    def doWavDiff(self):
#        # select destination file
#        source1 = str(self.source1Edit.text())
#        source2 = str(self.source2Edit.text())
#        destination_suggest = source1.replace('.wav', '_diff.wav')
#        destination = str(QtGui.QFileDialog.getSaveFileName(self, \
#            filter = 'WAV Files (*.wav);;All Files (*.*)',
#            directory = destination_suggest)) # QString -> str
#        if len(destination):
#            self.lastFileSelectedPath = os.path.dirname(destination)
#            # disable all buttons and lineEdits
#            self.source1Edit.setDisabled(True)
#            self.source2Edit.setDisabled(True)
#            self.source1OpenButton.setDisabled(True)
#            self.source2OpenButton.setDisabled(True)
#            self.saveButton.setDisabled(True)
#            self.closeButton.setDisabled(True)
#            # perform wavDiff
#            try:
#                for percentage_done in wavdiff(source1, source2, destination):
#                    self.progressBar.setValue(percentage_done)
#                self.progressBar.reset()
#            except ValueError as (msg, ):
#                QtGui.QMessageBox.critical(self, self.mainTitle, msg)
#            finally:
#                # reactivate buttons and lineEdits
#                self.source1Edit.setDisabled(False)
#                self.source2Edit.setDisabled(False)
#                self.source1OpenButton.setDisabled(False)
#                self.source2OpenButton.setDisabled(False)
#                self.saveButton.setDisabled(False)
#                self.closeButton.setDisabled(False)
#
