import os
from PyQt4 import QtCore, QtGui

class FactorSlider(QtGui.QWidget):
    def __init__(self, name, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        if scale_bits is None:
            scale_bits = factor_bits-2
        self.scale = 2**scale_bits

        # name label
        nameLabel = QtGui.QLabel(name)
        nameLabel.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.nameLabel = nameLabel

        # slider
        minValue = -2**(factor_bits-1)
        maxValue =  2**(factor_bits-1) - 1
        interval = max(1, 2**(factor_bits-4))

        slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(minValue, maxValue)
        slider.setValue(0)
        slider.setPageStep(interval)
        slider.setTickInterval(interval)
        slider.setTickPosition(slider.TicksBelow)
        slider.setMinimumWidth(50)
        self.slider = slider

        # value label
        self.valueLabel = QtGui.QLabel()
        self.valueLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

        self.connect(self.slider, QtCore.SIGNAL('valueChanged(int)'), \
                     self.updateLabel)

        self.updateLabel()

    def updateLabel(self):
        value = self.slider.value()
        scale = self.scale
        text = '%6i/%i = %6.3f' % (value, scale, float(value)/scale)
        self.valueLabel.setText(text)

class FactorSliderArray(QtGui.QWidget):
    def __init__(self, names, factor_bits, scale_bits=None):
        QtGui.QWidget.__init__(self)

        gridLayout = QtGui.QGridLayout()

        self.factorSliders = [FactorSlider(name, factor_bits) for name in names]
        for (row,factorSlider) in enumerate(self.factorSliders):
            gridLayout.addWidget(factorSlider.nameLabel,  row, 0)
            gridLayout.addWidget(factorSlider.slider,     row, 1)
            gridLayout.addWidget(factorSlider.valueLabel, row, 2)

        # layout
        #self.title.setMinimumWidth(120)
        #self.slider.setMinimumWidth(100)
        #self.label.setMinimumWidth(120)
        self.setLayout(gridLayout)

        # signals

    
class IIRSimCentralWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        # Global Layout
        globalVBox = QtGui.QVBoxLayout()
        globalVBox.addWidget(FactorSliderArray(['a1', 'hans', 'wurst'], 4))
        self.setLayout(globalVBox)

class IIRSimMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        mainTitle = 'IIRSim'
        self.setWindowTitle(mainTitle)

        self.setCentralWidget(IIRSimCentralWidget())



        #mainSize = self.sizeHint()
        #mainSize.setWidth(640)
        #self.resize(mainSize)
        statusBar = QtGui.QStatusBar()
        statusBar.addWidget(QtGui.QLabel(mainTitle))
        self.setStatusBar(statusBar)

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
