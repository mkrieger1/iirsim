#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import signal
from PyQt4 import QtCore, QtGui

import iirsim.gui

if __name__=='__main__':
    # Allow killing the app by pressing Ctrl-C (see also:
    # http://stackoverflow.com/q/4938723/4621513).
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)
    main = iirsim.gui.IIRSimMainWindow(sys.argv)
    main.show()
    sys.exit(app.exec_())

