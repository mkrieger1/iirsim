#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore, QtGui

import src.iirsim_gui as iirsim_gui

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    main = iirsim_gui.IIRSimMainWindow()
    main.show()
    sys.exit(app.exec_())

