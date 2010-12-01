#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import signal
from PyQt4 import QtCore, QtGui

import src.iirsim_gui as iirsim_gui

if __name__=='__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)
    main = iirsim_gui.IIRSimMainWindow()
    main.show()
    sys.exit(app.exec_())

