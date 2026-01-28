#-------------------------------------------------------------------------------
# Name:       Qt models in python
# Purpose:    creates Qt models which allows to view python collections and object in Qt Views
#             such as ListView, TableView and TreeView without additional work
#
# 
# Author:       Daniel Tolmachev (Daniel.Tolmachev@gmail.com)
#-------------------------------------------------------------------------------
__author__ = r"Danil Tolmachev (Daniel.Tolmachev@gmail.com/Danil.Tolmachev@tu-dortmund.de)"

from qtpy import QtCore
from collections.abc import Collection,Mapping
from collections import OrderedDict
from numbers import Number
from enum import Enum
import types,re,sys
MethodWrapperType = getattr(types,"MethodWrapperType",None)


# DEFAULT_UNEXPANDABLE_TYPES = [int, float, str, bytes, bytearray, type(None),
DEFAULT_UNEXPANDABLE_TYPES = [Number, str, bytes, bytearray, type(None),
             types.BuiltinFunctionType, MethodWrapperType]



class TreeElement(object):
    __slots__ = ["parent","name","value","children","loaded","index","parent_index"]
    def __init__(self,value,parent = None,name = "",index = 0, children = []):
        self.value = value
        self.parent = parent
        self.name = name
        self.children = []
        self.index = 0
        self.loaded = False
        self.parent_index = None

class PythonTreeModelBase(QtCore.QAbstractItemModel):
    class MODE(Enum):
        MAP = 1
        LIST = 2
        ZIPFILE = 5
        HDFFILE = 6
    def __init__(self,obj,col_type = 1,encoding = None, inline_items=3):
        """

        :param obj:
        :param col_type:
        :param encoding:
        :param inline_items:  number of elements to show in string
            if list or array is larger than 'inline_numbers', then only items count will be shown
            if list or array is smaller than 'inline_numbers', then all values will be shown
            reason:
                there are numpy array of size one, it's basically scalar, but it is represented as array of shape (1,)
                if 'inline_items'>=1 this scalar will be shown, so you don't have to open array view or another window
                to view one number
                there are often values that are represented by pair values, e.g. range,
                or by 3 values e.g. coordinates
        """
        self.object = obj
        self.col_name = -1
        self.col_data = 0
        self.col_type = col_type
        self.encoding = encoding
        self.mode = self.MODE.LIST
        self.inline_items = inline_items
        super().__init__()
        self._init_data()

    def _init_data(self):
        self.el0 = TreeElement(self.object)
        self.createChildren(self.el0)

    def index(self, row, col, parent=None, *args, **kwargs):
        if not parent.isValid():
            par_el = self.el0
        else:
            par_el = parent.internalPointer()
        cur_el = par_el.children[row]
        index = self.createIndex(row, col,cur_el)
        cur_el.parent_index = parent
        return index
    def parent(self, index=None):
        if index.isValid():
            el = index.internalPointer()
        else:
            el = self.el0
        return el.parent_index
    def indexForElement(self,el):
        if el is None or el.parent is None:
            index = self.createIndex(-1,-1,self.el0)
        else:
            index = self.indexForElement(el.parent)
        return index
    def rowCount(self, parent=None, *args, **kwargs):
        if parent is None or not parent.isValid():
            el = self.el0
        else:
            el = parent.internalPointer()
            if not el.loaded:
                self.createChildren(el)
        rc = len(el.children)
        return rc
    def formatValue(self, val):
        if val is None:
            ret = "None"
        elif type(val) == type:
            ret = val.__name__
        elif isinstance(val, Number):  # builtin simple types
            ret = str(val)
        elif isinstance(val,str):
            ret = val
        elif isinstance(val, bytes):
            if self.encoding:
                try:
                    ret = val.decode(encoding=self.encoding)
                except UnicodeDecodeError:
                    ret = str(val)
            else:
                ret = str(val)
        elif hasattr(val, "shape") and hasattr(val, "dtype"):  # numpy arrays
            if len(val.shape)==1 and val.shape[0]<=self.inline_items:
                ret = ", ".join([str(el) for el in val]) + " ({})".format(val.dtype)
            else:
                ret = "x".join([str(el) for el in val.shape]) + " {}".format(val.dtype)
        elif hasattr(val, "__len__"):  # containers
            if len(val)<self.inline_items:
                ret = "["+", ".join([str(el) for el in val])+"]"
            elif len(val) == 1:
                ret = "[1 item]"
            elif len(val) == 0:
                ret = "[empty]"
            else:
                ret = "[{} items]".format(len(val))
        else:
            ret = str(val)
        return ret


class PythonCollectionTreeModel(PythonTreeModelBase):
    def __init__(self,obj,col_type = 1,encoding = None):
        super().__init__(obj,col_type=col_type,encoding=encoding)
        if isinstance(self.object,Mapping):
            self.mode = self.MODE.MAP
            self.col_name = 0
            if self.col_name == self.col_type:
                self.col_name += 1
            while self.col_data in (self.col_type, self.col_name):
                self.col_data += 1
        else:
            self.mode = self.MODE.LIST
            self.col_data = 0
    def columnCount(self, parent=None, *args, **kwargs):
        if self.mode == self.MODE.MAP:
            if self.col_type>-1:
                return 3
            else:
                return 2
        else:
            return 1

    def createChildren(self,el):
        obj = el.value
        if isinstance(obj,Mapping):
            for i,(k, val) in enumerate(obj.items()):
                    # child = TreeElement(val, name=repr(k)+":", parent=el, index=i)
                    child = TreeElement(val, name=k, parent=el, index=i)
                    el.children.append(child)
        elif hasattr(obj,"__iter__") and not isinstance(obj,(str,bytes,bytearray,dict)):
            for i,val in enumerate(obj):
                child = TreeElement(val, name="[{}]".format(i), parent=el, index=i)
                el.children.append(child)
        el.loaded = True

    def hasChildren(self, parent=None, *args, **kwargs):
        if parent.isValid():
            el = parent.internalPointer()
        else:
            el = self.el0
        if isinstance(el.value, Collection) and not isinstance(el.value,(str,bytes,bytearray)) \
                and not hasattr(el.value,"shape"):
            return True
        else:
            return False
    def data(self,index, role):
        col = index.column()
        row = index.row()
        if role==QtCore.Qt.DisplayRole:
            if self.mode == self.MODE.MAP:
                if col==self.col_data:
                    val = index.internalPointer().value
                    return self.formatValue(val)
                elif col==self.col_name:
                    return index.internalPointer().name
                elif col==self.col_type:
                    return type(index.internalPointer().value).__name__
                else:
                    return row,col
            # elif self.mode == self.MODE.ARRAY:
            #     return str(self.object[row,col])
            # elif self.mode == self.MODE.DATAFRAME:
            #     return str(self.object.iloc[row,col])
            else:
                val = index.internalPointer().value
                return self.formatValue(val)
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

class PythonArrayTreeModel(PythonTreeModelBase):
    def __init__(self,obj):
        self.dataframe = hasattr(obj,"iloc")
        super().__init__(obj)
    def columnCount(self, parent=None, *args, **kwargs):
        if self.object.ndim<=1:
            return 1
        else:
            return self.object.shape[-1]
    def data(self,index, role):
        col = index.column()
        row = index.row()
        if role in (QtCore.Qt.DisplayRole,QtCore.Qt.ToolTipRole):
            if self.object.ndim>1:
                if self.dataframe:
                    return str(self.object.iloc[row, col])
                else:
                    return str(self.object[row,col])
            else:
                if self.dataframe:
                    return str(self.object.iloc[row])
                else:
                    return str(self.object[row])
    def createChildren(self,el):
        obj = el.value
        if hasattr(obj,"__iter__") and not isinstance(obj,(str,bytes,bytearray,dict)):
            if self.dataframe: #pandas dataframe
                for i in range(len(obj)):
                    child = TreeElement(obj.iloc[i], parent=el, index=i)
                    el.children.append(child)
            else: #numpy array
                for i,val in enumerate(obj):
                    child = TreeElement(val, parent=el, index=i)
                    el.children.append(child)
        el.loaded = True
    def hasChildren(self, parent=None, *args, **kwargs):
        if parent.isValid():
            el = parent.internalPointer()
        else:
            el = self.el0
        if hasattr(el.value,"ndim") and el.value.ndim>1:
            return True
        else:
            return False

class PythonObjectTreeModel(PythonTreeModelBase):
    def __init__(self,obj,hidetypes = (),do_not_expand_types = None,show_double_underscore = True,
                 show_under_score = True, exclude_patterns = []):
        self.hidetypes = hidetypes
        if type(exclude_patterns)==str:
            self.exclude_patterns = [exclude_patterns]
        else:
            self.exclude_patterns = exclude_patterns
        if not show_under_score:
            self.exclude_patterns.append("^_")
        if not show_double_underscore:
            self.exclude_patterns.append("^__")
        self._createExcludePattern()
        super().__init__(obj)
# self.dict_obj = {-1:self.object}
        # self.parents = {}
        self._init_data()
        if do_not_expand_types is None:
            self.do_not_expand_types = tuple(typ for typ in DEFAULT_UNEXPANDABLE_TYPES if typ)
        else:
            self.do_not_expand_types = do_not_expand_types

    def _createExcludePattern(self):
        if self.exclude_patterns:
            self.exclude_pat = re.compile("|".join(self.exclude_patterns))
        else:
            self.exclude_pat = None

    def _init_data(self):
        self.el0 = TreeElement(self.object)
        self.createChildren(self.el0)

    def createChildren(self,el):
        # print("loading",el.value)
        obj = el.value
        if isinstance(obj,dict):
            for i,(k, val) in enumerate(obj.items()):
                if not isinstance(val, self.hidetypes):
                    # child = TreeElement(val, name=repr(k)+":", parent=el, index=i)
                    child = TreeElement(val, name=k, parent=el, index=i)
                    el.children.append(child)
        elif hasattr(obj,"__iter__") and not isinstance(obj,(str,bytes,bytearray,dict)):
            for i,val in enumerate(obj):
                if not isinstance(val, self.hidetypes):
                    child = TreeElement(val, name="[{}]".format(i), parent=el, index=i)
                    el.children.append(child)
        for i,a in enumerate(dir(obj)):
            val = getattr(obj,a)
            if not isinstance(val,self.hidetypes):
                if not self.exclude_pat or not self.exclude_pat.match(a):
                    child = TreeElement(val,name=a,parent=el,index = i)
                    el.children.append(child)
        el.loaded = True
    def index(self, row, col, parent=None, *args, **kwargs):
        # print("index",row,col,"parent",parent.row(),parent.column(),end="")
        if not parent.isValid():
            par_el = self.el0
        else:
            par_el = parent.internalPointer()
        cur_el = par_el.children[row]
        index = self.createIndex(row, col,cur_el)
        cur_el.parent_index = parent
        # print("->",index.row(),cur_el.name)
        return index
    def parent(self, index=None):
        # print("parent", index.row(), index.column(),end="")
        if index.isValid():
            el = index.internalPointer()
        else:
            el = self.el0
        return el.parent_index
    def indexForElement(self,el):
        if el is None or el.parent is None:
            index = self.createIndex(-1,-1,self.el0)
        else:
            index = self.indexForElement(el.parent)
        return index
    def rowCount(self, parent=None, *args, **kwargs):
        row = parent.row()
        col = parent.column()
        if not parent.isValid():
            el = self.el0
        else:
            el = parent.internalPointer()
            if not el.loaded:
                self.createChildren(el)
        rc = len(el.children)
        # print("rowcount",row,col,"->",rc)
        return rc
    def columnCount(self, parent=None, *args, **kwargs):
        return 3
    def hasChildren(self, parent=None, *args, **kwargs):
        # print("has children",parent.row())
        if parent.isValid():
            el = parent.internalPointer()
        else:
            el = self.el0
        # return True
        #TODO
        if isinstance(el.value,self.do_not_expand_types):
            return False
        else:
            return True
    def data(self,index, role):
        col = index.column()
        row = index.row()
        # print("data", row, col)
        if role==QtCore.Qt.DisplayRole:
            # print("data",row,col)
            if col==0:
                return index.internalPointer().name
            elif col==1:
                return type(index.internalPointer().value).__name__
            elif col==2:
                try:
                    val = index.internalPointer().value
                    if val is None:
                        return "None"
                    elif type(val)==type:
                        return val.__name__
                    elif isinstance(val,(Number,str,bytes)): #builting simple types
                        s = str(val)
                        s = re.search(".*",s).group()
                        return s
                    # elif hasattr(val,"shape") and hasattr(val,"dtype") and type(val.shape)==tuple and len(val.shape)>0: #numpy arrays
                    elif isinstance(val,ndarray): #numpy arrays
                        s = "x".join([str(el) for el in val.shape])+" {}".format(val.dtype)
                        return s
                    elif hasattr(val,"__len__"): #containers
                        if len(val)==1:
                            return "1 item"
                        elif len(val)==0:
                            return "empty"
                        else:
                            return "{} items".format(len(val))
                    # else:
                    #     s = str(val)
                    #     # s = re.search(".*", s).group()
                    #     return s
                except:
                    return sys.exc_info()[0]
            else:
                return row,col
        elif role==QtCore.Qt.ToolTipRole:
            if col==2:
                val = index.internalPointer().value
                if isinstance(val,(str,bytes)):
                    return str(val)
        # , parent(), rowCount(), columnCount(), and data().Th
    def toggleTypeVisibility(self,hidetypes):
        self.beginResetModel()
        self.hidetypes = hidetypes
        self._init_data()
        self.endResetModel()
    def toggleExcludePattern(self,exclude_patterns):
        self.beginResetModel()
        self.exclude_patterns = exclude_patterns
        self._createExcludePattern()
        self._init_data()
        self.endResetModel()

from pathlib import Path
import zipfile,datetime
class PythonZipFileTreeModel(PythonTreeModelBase):
    def __init__(self,obj,show_dir_size = True, col_name = 0, col_size = 1, col_date = 2,
                 fmt_size = " 5.3g", fmt_date = "%Y.%m.%D %H:%M:%S"):
        super().__init__(obj)
        self.fmt_size = fmt_size
        self.fmt_date = fmt_date
        self.show_dir_size = show_dir_size
        self.col_name = col_name
        self.col_size = col_size
        self.col_date = col_date
        self._szcache = {}
    def columnCount(self, parent=None, *args, **kwargs):
        return 3
    def data(self,index, role):
        col = index.column()
        row = index.row()
        if role in (QtCore.Qt.DisplayRole,QtCore.Qt.ToolTipRole):
            obj = index.internalPointer()
            if isinstance(obj.value,zipfile.ZipInfo):
                if col==self.col_name:
                    return self.formatValue(obj.name)
                elif col==self.col_size:
                    return self.formatSize(obj.value.file_size)
                elif col==self.col_date:
                    return datetime.datetime(*obj.value.date_time).strftime(self.fmt_date)
                else:
                    return row,col
            elif isinstance(obj.value,dict):
                if col==0:
                    return self.formatValue(obj.name+"/")
                elif col==1 and self.show_dir_size:
                    return self.formatSize(self._calcDirSize(obj.name,obj.value))
        # elif role==QtCore.Qt.ToolTipRole:
        #     if col==self.col_data:
        #         val = index.internalPointer().value
        #         if isinstance(val,(str,bytes)):
        #             return str(val)
    def headerData(self,section,orient,role):
        if orient == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "filename"
            elif section == 1:
                return "size"
            elif section == 2:
                return 'mdate'
    def hasChildren(self, parent=None, *args, **kwargs):
        if parent.isValid():
            el = parent.internalPointer()
        else:
            el = self.el0
        if isinstance(el.value, (zipfile.ZipFile,dict)) or ((isinstance(el.value,zipfile.ZipInfo) and el.value.is_dir())):
            return True
        else:
            return False
    def formatSize(self,sz):
        if sz==0:
            return "0"
        m = 0
        while sz // 1024:
            m+=1
            sz /= 1024
        if m==0:
            return f"{sz}B"
        elif m == 1:
            u = 'KiB'
        elif m == 2:
            u = 'MiB'
        elif m == 3:
            u = 'GiB'
        elif m==4:
            u = 'TiB'
        elif m == 5:
            u = 'PiB'
        elif m == 6:
            u = 'EiB'
        elif m == 7:
            u = 'ZiB'
        elif m == 8:
            u = 'YiB'
        return f"{sz:{self.fmt_size}} {u}"
    def _createSubPathDict(self, parts, dic, zi):
        if parts:
            p,*rest = parts

            if rest:
                if p not in dic:
                    dic[p] = OrderedDict()
                self._createSubPathDict(rest,dic[p],zi)
            else:
                dic[p] = zi
    def _calcDirSize(self,k,dic):
        if k in self._szcache:
            return self._szcache[k]
        else:
            sz = 0
            for k,v in dic.items():
                if isinstance(v,dict):
                    sz+=self._calcDirSize(k,v)
                else:
                    sz+=v.file_size
            self._szcache[k] = sz
            return sz

        
    def createChildren(self,el):
        obj = el.value        
        if isinstance(obj,zipfile.ZipFile):
            paths = OrderedDict()
            for i, zi in enumerate(obj.infolist()):
                fn = Path(zi.filename)
                parts = fn.parts
                while parts and parts[0]=="\\" or parts[0]=="/":
                    parts = parts[1:]
                if len(parts)>1:
                    self._createSubPathDict(parts,paths,zi)
                else:
                    child = TreeElement(zi, name = zi.filename, parent=el, index=i)
                    el.children.append(child)
            for j,(p, dic) in enumerate(paths.items()):
                child = TreeElement(dic, name=p, parent=el, index=j+i)
                el.children.append(child)
        elif isinstance(obj,dict):            
            for i,(k,v) in enumerate(obj.items()):
                    child = TreeElement(v, name=k, parent=el, index=i)
                    el.children.append(child)
        el.loaded = True



