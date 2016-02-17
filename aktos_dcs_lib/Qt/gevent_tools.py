__author__ = 'ceremcem'

from PySide import QtCore

def greenlet_exec(app):
    timer = QtCore.QTimer()
    import gevent

    def gevent_loop():
        gevent.sleep(0.01)
        timer.start(0)
    timer.timeout.connect(gevent_loop)
    timer.start(0)
    app.exec_()
