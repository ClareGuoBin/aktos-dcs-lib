# -*- coding: utf-8 -*-

# Copyright (c) 2009-2011 Christopher S. Case and David H. Bronke
# Licensed under the MIT license; see the LICENSE file for details.

"""Qt compatibility wrapper

Detects either PySide or PyQt.

"""
import sys
import logging
from aktos_dcs import sleep


__all__ = [
        'QtCore', 'QtGui', 'QtNetwork', 'QtWebKit', 'QtUiTools', 'Signal',
        'Slot', 'loadUI'
        ]

QtCore = None
QtGui = None
QtNetwork = None
QtWebKit = None
QtUiTools = None
Signal = None
Slot = None
loadUI = None

greenlet_exec = None

binding = ""


# Internal: UI loader instance for PySide
_uiLoader = None


logger = logging.getLogger("Qt")


def initialize(prefer=None, args=[]):
    if prefer is not None:
        prefer = prefer.lower()

    remainingArgs = list()
    for arg in args:
        if arg in ["--use-pyqt", "--use-pyqt4"]:
            prefer = "pyqt"
        elif arg == "--use-pyside":
            prefer = "pyside"
        else:
            remainingArgs.append(arg)

    if prefer is None:
        prefer = 'pyside'

    if prefer in ["pyqt", "pyqt4"]:
        if not importPyQt():
            if prefer is not None:
                logger.warn("PyQt4 requested, but not installed.")

            if not importPySide():
                logger.error("Couldn't import PySide or PyQt4! You must have "
                        + "one or the other to run this app.")
                sys.exit(1)
    else:
        if not importPySide():
            if prefer is not None:
                logger.warn("PySide requested, but not installed.")

            if not importPyQt():
                logger.error("Couldn't import PySide or PyQt4! You must have "
                        + "one or the other to run this app.")
                sys.exit(1)

    global greenlet_exec

    def greenlet_exec(app):
        timer = QtCore.QTimer()
        import gevent

        def gevent_loop():
            gevent.sleep(0.01)
            timer.start(0)
        timer.timeout.connect(gevent_loop)
        timer.start(0)
        app.exec_()



    if len(remainingArgs) > 0:
        return remainingArgs


def importPySide():
    try:
        from PySide import QtCore, QtGui, QtNetwork, QtWebKit, QtUiTools
        from PySide.QtCore import Signal, Slot, Property

        class UiLoader(QtUiTools.QUiLoader):
            def __init__(self):
                super(UiLoader, self).__init__()
                self._rootWidget = None

            def createWidget(self, className, parent=None, name=''):
                widget = super(UiLoader, self).createWidget(
                        className, parent, name)

                if name:
                    if self._rootWidget is None:
                        self._rootWidget = widget
                    elif not hasattr(self._rootWidget, name):
                        setattr(self._rootWidget, name, widget)
                    else:
                        logger.error("Name collision! Ignoring second "
                                "occurrance of %r.", name)

                    if parent is not None:
                        setattr(parent, name, widget)
                    else:
                        # Sadly, we can't reparent it to self, since QUiLoader
                        # isn't a QWidget.
                        logger.error("No parent specified! This will probably "
                                "crash due to C++ object deletion.")

                return widget

            def load(self, fileOrName, parentWidget=None):
                if self._rootWidget is not None:
                    raise Exception("UiLoader is already started loading UI!")

                widget = super(UiLoader, self).load(fileOrName, parentWidget)

                if widget != self._rootWidget:
                    logger.error("Returned widget isn't the root widget... "
                            "LOLWUT?")

                self._rootWidget = None
                return widget

        def loadUI(uiFilename, parent=None):
            global _uiLoader
            if _uiLoader is None:
                _uiLoader = UiLoader()

            uiFile = QtCore.QFile(uiFilename, parent)
            if not uiFile.open(QtCore.QIODevice.ReadOnly):
                logger.error("Couldn't open file %r!", uiFilename)
                return None

            try:
                return _uiLoader.load(uiFile, parent)

            except:
                logger.exception("Exception loading UI from %r!", uiFilename)

            finally:
                uiFile.close()
                uiFile.deleteLater()

            return None

        logger.info("Successfully initialized PySide.")

        globals().update(
                QtCore=QtCore,
                QtGui=QtGui,
                QtNetwork=QtNetwork,
                QtWebKit=QtWebKit,
                QtUiTools=QtUiTools,
                Signal=Signal,
                Slot=Slot,
                Property=Property,
                loadUI=loadUI,
                binding="PySide",
                )

        return True

    except ImportError:
        return False


def importPyQt():
    try:
        import sip
        sip.setapi('QString', 2)
        sip.setapi('QVariant', 2)

        from PyQt4 import QtCore, QtGui, QtNetwork, QtWebKit, uic
        from PyQt4.QtCore import pyqtSignal as Signal, pyqtSlot as Slot, \
                pyqtProperty as Property
        QtUiTools = object()

        def loadUI(uiFilename, parent=None):
            newWidget = uic.loadUi(uiFilename)
            newWidget.setParent(parent)
            return newWidget

        logger.info("Successfully initialized PyQt4.")

        globals().update(
                QtCore=QtCore,
                QtGui=QtGui,
                QtNetwork=QtNetwork,
                QtWebKit=QtWebKit,
                QtUiTools=QtUiTools,
                Signal=Signal,
                Slot=Slot,
                Property=Property,
                loadUI=loadUI,
                binding="PyQt4",
                )

        return True

    except ImportError:
        return False


def isPySide():
    if binding == "PySide":
        return True

    return False


def isPyQt4():
    if binding == "PyQt4":
        return True

    return False


