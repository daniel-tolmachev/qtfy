#-------------------------------------------------------------------------------
# Name:       pyqtValue2dict.py
# Purpose:    connects spinboxes, linedits and checkable items, like checkboxes
#             to python dictionary so:
#             wherever you change text in edits (QLineEdit etc.),
#             change value in spinboxes or check/uncheck buttons/checkboxes/radiobuttons
#             their state is zmq_send to python dictionary with key looking
#             like "parent_widget.child_widget.widget_name"
#
# Created:      30.07.2016
# Author:       Daniel Tolmachev (Daniel.Tolmachev@mail.ioffe.ru/Daniel.Tolmachev@gmail.com)
#-------------------------------------------------------------------------------

from __future__ import print_function,unicode_literals
import sys
from qtpy import QtCore,QtGui,QtWidgets
__author__ = r"Daniel Tolmachev (Daniel.Tolmachev@mail.ioffe.ru/Daniel.Tolmachev@gmail.com)"

class signal2dict(object):
    def __init__(self,widget,dic,key):
        #super(signal2dict,self).__init__()
        print(widget,key)
        self.widget = widget
        self.dic = dic
        self.key = key
    def slot(self,*args):
        if len(args)==1:
            self.dic[self.key] = args[0]
        elif len(args)>1:
            self.dic[self.key] = args

_widgetlist = []
_widgetnameslist = []

def _makename(Qt_widget,prefix):
    if prefix:
        name = prefix+"."
    else:
        name = ""
    if Qt_widget.objectName():
        name += Qt_widget.objectName()
    else:
        name += "{}".format(Qt_widget.__class__.__name__)
    while name in _widgetnameslist:
        name += name +1
    return name

def _loadvalue(Qt_widget,python_dictionary,key,setter,getter):
    try:
        if key in python_dictionary:
                try:
                    getattr(Qt_widget,setter)(python_dictionary[key])
                except:
                    python_dictionary[key]=getattr(Qt_widget,getter)()
        else:
            python_dictionary[key]=getattr(Qt_widget,getter)()
    except:
        pass

def connect2dict(Qt_widget,python_dictionary,prefix = ""):
    """
    connect signals of Qt_widget and it's child widgets to python_dictionary using aux class
    wherever you change text in edits (QLineEdit etc.),
    change value in spinboxes or check/uncheck buttons/checkboxes/radiobuttons
    their state is zmq_send to python dictionary with key looking
    like "parent_widget.child_widget.widget_name"

    signal supported are: valueChanged - spinboxes
                          stateChanged - checkboxes and other checkable items
                          editingFinished - linedits
    """
    print(Qt_widget,Qt_widget.objectName())
    signal = None
    if hasattr(Qt_widget,"valueChanged"):
        signal,setter,getter = "valueChanged","setValue","value" #spinboxes
    elif hasattr(Qt_widget,"stateChanged"):
        signal,setter,getter = "stateChanged","setChecked","isChecked" #checkboxes and other checkable items
    elif hasattr(Qt_widget,"editingFinished") and hasattr(Qt_widget,"setText"):
        signal,setter,getter = "editingFinished","setText","text" #linedits
    if signal:
        key = _makename(Qt_widget,prefix)
        _loadvalue(Qt_widget,python_dictionary,key,setter,getter)
        cl = signal2dict(Qt_widget,python_dictionary,key)
        getattr(Qt_widget,signal).connect(cl.slot)
        _widgetlist.append(cl)
        _widgetnameslist.append(key)
    elif hasattr(Qt_widget,"children"):
        for child in Qt_widget.children():
            connect2dict(child,python_dictionary,_makename(Qt_widget,prefix))

if __name__ == "__main__":
    from qtpy import QtGui
    app = QtWidgets.QApplication([])
    win = QtWidgets.QMainWindow()
    win.setCentralWidget(QtWidgets.QWidget())
    lo = QtWidgets.QGridLayout()
    win.centralWidget().setLayout(lo)
    sb = QtWidgets.QDoubleSpinBox()
    lo.addWidget(sb)
    lo.addWidget(QtWidgets.QCheckBox("check"))
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
    dic = {}

    connect2dict(win,dic)
    win.show()
    app.exec_()
    print(dic)
