#-------------------------------------------------------------------------------
# Name:       Qt models in python
# Purpose:    creates Qt model for viewing HDF files in Qt Views
#             such as ListView, TableView and TreeView without additional work
#
# 
# Author:       Daniel Tolmachev (Daniel.Tolmachev@gmail.com)
#-------------------------------------------------------------------------------
__author__ = r"Danil Tolmachev (Daniel.Tolmachev@gmail.com/Danil.Tolmachev@tu-dortmund.de)"

from py2qt_models import PythonTreeModelBase, TreeElement, QtCore
import h5py

class PythonHDFFileTreeModel(PythonTreeModelBase):
    def __init__(self,obj,col_type = 1,encoding = None):
        super().__init__(obj,col_type=col_type,encoding=encoding)
        self.col_name = 0
        if self.col_name == self.col_type:
            self.col_name += 1
        while self.col_data in (self.col_type, self.col_name):
            self.col_data += 1
    def data(self,index, role):
        col = index.column()
        row = index.row()
        if role in (QtCore.Qt.DisplayRole,QtCore.Qt.ToolTipRole):

            if col==self.col_data:
                val = index.internalPointer().value
                if isinstance(val,h5py.Dataset):
                    val = val[()]
                return self.formatValue(val)
            elif col==self.col_name:
                return index.internalPointer().name
            elif col==self.col_type:
                val =  index.internalPointer().value
                if isinstance(val,h5py.Dataset):
                    return f"{type(val).__name__} ({val.dtype})"
                else:
                    return type(val).__name__
            else:
                return row,col
        elif role==QtCore.Qt.ToolTipRole:
            if col==self.col_data:
                val = index.internalPointer().value
                if isinstance(val,(str,bytes)):
                    return str(val)

    def headerData(self,section,orient,role):
        if orient == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == self.col_data:
                return "value"
            elif section == self.col_name:
                return "name"
            elif section == self.col_type:
                return 'type'

    def hasChildren(self, parent=None, *args, **kwargs):
        if parent.isValid():
            el = parent.internalPointer()
        else:
            el = self.el0
        if isinstance(el.value, (h5py.Group,h5py.File)):
            return True
        else:
            return False
    def createChildren(self,el):
        obj = el.value
        if isinstance(obj,(h5py.Group,h5py.File)):
            for i,(k, val) in enumerate(obj.items()):
                child = TreeElement(val, name=k, parent=el, index=i)
                el.children.append(child)
        elif hasattr(obj,"__iter__") and not isinstance(obj,(str,bytes,bytearray,dict)):
            for i,val in enumerate(obj):
                child = TreeElement(val, name="[{}]".format(i), parent=el, index=i)
                el.children.append(child)
        el.loaded = True
    def columnCount(self, parent=None, *args, **kwargs):
        if self.col_type>-1:
            return 3
        else:
            return 2