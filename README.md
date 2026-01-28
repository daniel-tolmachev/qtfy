# Qtfy python object. 
## make any paython object qt aware

### QtWrapper
makes any python object to run in background thread and emit Qt signals

### py2qt_models.py
contains a collection of model which can be used with Qt Views using model/view approach such as QListView, QTableView and QTreeView
you can easily view any python object or collection in QTreeView

### py2qt_models_hdf.py
add a model for HDF files

### connect2dict     
connects signals of Qt_widget and it's child widgets to python_dictionary using aux class so wherever you change text in edits (QLineEdit etc.), change value in spinboxes or check/uncheck buttons/checkboxes/radiobuttons their state is sent to python dictionary 

_this is a spin off from my laboratory apps https://bitbucket.org/DanielTolmachev/lab_python_apps_
