#-------------------------------------------------------------------------------
# Name:     spinbox_advanced.py
# Purpose:  upgrades QDoubleSpinBox from Qt framework so user can:
#                 input numbers in exponential form
#                 accepts both dot and comma as decimal separator
#                 automatically adjusts step size
#
#           upgradeSpinBox(doubleSpinBox,defaultPrecision = 3)
#                 upgrade doubleSpinBox by redirecting its validate and textFromValue
#                 methods to methods of instance of special DoubleSpinBoxHelper class
#
#                 doubleSpinBox - QDoubleSpinBox widget (QSpinBox should also work)
#                 defaultPrecision - precision used for value formatting {:{precision}g}
#
#           upgradeAllDoubleSpinBoxes(widgetWithSpinBoxes,defaultPrecision = 3)
#                 calls upgradeSpinBox(...) on each DoubleSpinBox found on a widget
#                 widgetWithSpinBoxes - Qt widget, containing doubleSpinBoxes
#
# Created:      30.07.2016
# Author:       Daniel Tolmachev (Daniel.Tolmachev@mail.ioffe.ru/Daniel.Tolmachev@gmail.com)
#-------------------------------------------------------------------------------

from __future__ import print_function,unicode_literals
import sys,traceback
from math import log10
from qtpy import QtCore,QtWidgets,QtGui
__author__ = r"Daniel Tolmachev (Daniel.Tolmachev@mail.ioffe.ru/Daniel.Tolmachev@gmail.com)"



doubleSpinBoxHelperList = []



class DoubleSpinBoxHelper(QtCore.QObject):
    def __init__(self,doubleSpinBox,precision = 3):
        super(DoubleSpinBoxHelper,self).__init__()
        self.precision = precision
        self.spinBox = doubleSpinBox
        self.step_init = doubleSpinBox.singleStep()
        self.upgradeSpinBox(doubleSpinBox)
        #print(doubleSpinBox)
        self.palette_bas = doubleSpinBox.palette()
        # self.font_basic = doubleSpinBox.font()
        # self.font_wrong = QtGui.QFont(doubleSpinBox.font())
        # self.font_wrong.set
        self.palette_inc = QtGui.QPalette(doubleSpinBox.palette())
        self.palette_inc.setColor(QtGui.QPalette.Text,QtCore.Qt.red)
    def upgradeSpinBox(self,doubleSpinBox):
        doubleSpinBox.validate = self.validate
        doubleSpinBox.textFromValue = self.format_float
        doubleSpinBox.valueFromText = self.atof_comma_safe
    def validate(self,text,pos):
        try:
            self.atof_comma_safe(text)
            self.setColorBasic()
            return (2,text,pos)
        except:
            self.setColorIncorrect()
            return (1,text,pos)
    def setColorIncorrect(self):
        self.spinBox.setPalette(self.palette_inc)
    def setColorBasic(self):
        self.spinBox.setPalette(self.palette_bas)
    def format_float(self,f):
        try:
            if f and f!=self.spinBox.maximum() and f!=self.spinBox.minimum():
                mag = log10(abs(f))
                st = self.spinBox.singleStep()
                stlog = log10(st)
                if mag>=stlog+self.precision: #increase step
                    stlog = mag-self.precision+1
                    self.spinBox.setSingleStep(10**stlog)
                # elif st>abs(f-self.spinBox.minimum()): #reduce step
                #     while st>abs(f-self.spinBox.minimum()):
                #         st/=10
                #         self.spinBox.setSingleStep(st)
                elif st>abs(f-self.spinBox.minimum()) and st>self.step_init: #reset step to initial
                    self.spinBox.setSingleStep(self.step_init)
        except:
            traceback.print_exc()
        return "{:.{}g}".format(f,self.precision)
    def atof_comma_safe(self, text):
        try:
            f = float(text)
            return f
        except ValueError:
            pass
        if "," in text:
            if "." in text:
                    s2 =  text.replace(",", "")
                    f = float(s2)
            else:
                    s2 = text.replace(",", ".")
                    f = float(s2)
            return f
        raise ValueError


def upgradeSpinBox(doubleSpinBox,defaultPrecision = 3):
    """
    upgrade doubleSpinBox by redirecting its validate and textFromValue
    methods to methods of instance of special DoubleSpinBoxHelper class

    doubleSpinBox - QDoubleSpinBox widget (QSpinBox should also work)
    defaultPrecision - precision used for value formatting {:{precision}g}
    """
    doubleSpinBoxHelperList.append(DoubleSpinBoxHelper(doubleSpinBox,defaultPrecision))

def upgradeAllDoubleSpinBoxes(widgetWithSpinBoxes,defaultPrecision = 3):
    """
    calls upgradeSpinBox(...) on each DoubleSpinBox found on a widget
    widgetWithSpinBoxes - Qt widget, containing doubleSpinBoxes
    """
    if hasattr(widgetWithSpinBoxes,"children"):
        for child in widgetWithSpinBoxes.children():
            if type(child) == QtWidgets.QDoubleSpinBox:
                upgradeSpinBox(child,defaultPrecision)
        print("sbhelper:",doubleSpinBoxHelperList)
    else:
        sys.stderr.write("upgradeAllDoubleSpinBoxes: not a Qt widget (has no children() method)")


if __name__ == "__main__":
    import quickQtApp
    from qtpy import QtGui
    import install_exception_hook
    app,opt,win,cons = quickQtApp.mkAppWin()
    sb = QtWidgets.QDoubleSpinBox()
    f = sb.font()
    #f = QtGui.QFont()
    p = sb.palette()
    p.setColor(QtGui.QPalette.WindowText,QtCore.Qt.red)
    #p = QtGui.QPalette()
    #print(p.color(QtCore.Qt.TextColorRole))
    sb.setMaximum(sys.float_info.max)
    sb.setMinimum(-sys.float_info.max)
    sb.setAccelerated(True)

    print(sb.value(),sb.decimals(),sb.singleStep())
    #upgradeSpinBox(sb)
    win.setCentralWidget(sb)
    upgradeAllDoubleSpinBoxes(win)
    win.show()
    app.exec_()