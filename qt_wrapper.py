
""" This file allow to quickly wrap any python object into Qt QObject, thus allowing
 to use Qt Signals and Thread

 example:
    let's assume you have voltmeter that can measure voltage and you want to display measured value on screen
    
    without threads:
    
        vm = Voltmeter("com1")
        l = QtWidgets.QLabel()
        
        while True:
            v = vm.getVoltage()
            l.setText(str(v))
            time.sleep(.1)
            
        this code will query voltage every second and display it on screen
        if voltmeter is not responding, program will freeze
    
    with threads
    
        vm = QtWrapper(Voltmeter("com1"))      #this will create separate thread  
        l = QtWidgets.QLabel()
        vm.getVoltage.connect(lambda v:l.setText(str(v)))
        
        while True:
            v = vm.getVoltage()  #actual command will be exceuted in separate thread
            
            
        this code will do same, but communication with voltmeter will ocuur in separate thread
        vm.getVoltage() will send signal from main thread to wrapper object running in another thread, 
        then Voltmeter.getVoltage() will be invoked in separate thread
        then returned value will be sent back using another signal to main thread
        and then value will be displayed in a label.
    
"""
__author__ = r"Daniel Tolmachev (Daniel.Tolmachev@gmail.com/Danil.Tolmachev@tu-dortmund.de)"


import sys, traceback, logging
from qtpy import QtCore

log = logging.getLogger(__name__)
class QtWrapper(QtCore.QObject):
    """
    
    """
    # public signals
    sigFunctionReturned = QtCore.Signal(str, object)
    sigExceptionRaised = QtCore.Signal(str, object)
    wrp_threads_static = []
    # public methods
    def __init__(self, obj, *, thread=None, moveToNewThread=True, printExcInfo=True,
                 printReturns=False, verbose=False, skipPrivateMethods=True):
        self.wrp_printExcInfo = printExcInfo
        self.wrp_printReturns = printReturns
        self.wrp_skipPrvateMethods = skipPrivateMethods
        self.object = None
        self.wrp_object2create = None
        if verbose:
            log.setLevel(logging.DEBUG)
        super(QtWrapper, self).__init__()
        if isinstance(thread, QtCore.QThread):
            self.wrp_threads_static.append(thread)
            self.moveToThread(thread)
        elif moveToNewThread:
            thread = QtCore.QThread()
            self.wrp_threads_static.append(thread)
            thread.start()
            self.moveToThread(thread)
        self.setObject(obj)
        self.wrp_sigCallRequested.connect(self.wrp_call__wrapped_func_, QtCore.Qt.QueuedConnection)
        self.sigFunctionReturned.connect(self.dispatchSignals)

    def setObject(self, obj):
        """
        This functions set object that will be Qtfied:
        if obj is a typename, we instantiate new object of this type
        directly inside wrapper, that can be useful in some cases if Qtfy object works
        in another thread, in that case wrapped object will be instantiated 
        in that thread 
        :param obj: Object or ClassType or tuple(ClassType,init_args...)        
        """
        # if obj is a typename, we instantiate new object of this type
        # directly inside wrapper, that can be useful if Qtfy object works
        #  in another thread, in that case wrapped object will be instantiated
        # in that thread
        self.wrp_sigObjectSetRequested.connect(self.wrp_createObject)
        if type(obj) == type:  # obj is a type name
            self.wrp_findAttributes(obj)
            self.wrp_object2create = obj
            self.wrp_sigObjectSetRequested.emit()
            # self.object = obj()
        elif isinstance(obj, tuple):  # obj is a type name with arguments for initialization
            self.wrp_findAttributes(obj[0])
            self.wrp_object2create = obj
            self.wrp_sigObjectSetRequested.emit()

            # self.object = obj[0](*obj[1:])
        else:
            self.wrp_findAttributes(type(obj))
            self.object = obj
            self.object_exists = True

    def dispatchSignals(self, func_name, returned_values):
        """
        this method can be reimplemented,
        so you can properly dispatch output of function call:
        for ex. you can format values, so you can show them on label
        :param func_name: name of function, that has returned
        :param returned_values: values returned by function
        """
        if self.wrp_printReturns:
            print(func_name, "returned", returned_values)

    # private members
    wrp_sigCallRequested = QtCore.Signal(object, str, tuple, dict)
    wrp_sigObjectSetRequested = QtCore.Signal()

    class _Method(QtCore.QObject):
        sigReturned = QtCore.Signal(object)

        def __init__(self, parent, function_name):
            super().__init__()
            self.parent = parent
            self.function_name = function_name

        def __call__(self, *args, **kwargs):
            self.parent.wrp_sigCallRequested.emit(self, self.function_name, args, kwargs)

        def connect(self, slot):
            """
            shortcut to sigReturned.connect
            this will connect sigReturned with given slot
            """
            self.sigReturned.connect(slot)

        def disconnect(self, slot):
            """
            shortcut to sigReturned.disconnect
            this will disconnect sigReturned from given slot
            """
            self.sigReturned.disconnect(slot)

    def wrp_findAttributes(self, obj):
        # find all objects's method
        attrs = {}
        for k in dir(obj):
            if k not in attrs and (not self.wrp_skipPrvateMethods or k[0] != "_"):
                v = getattr(obj, k, None)
                if callable(v):
                    attrs[k] = v
        self_attr = dir(self)
        for k, v in attrs.items():
            f = self._Method(self, k)
            if k in self_attr:
                k += "_"
            setattr(self, k, f)

    def wrp_createObject(self):
        log.debug("creating object %s in a thread",self.wrp_object2create)
        if type(self.wrp_object2create) == type:  # obj is a type name
            self.object = self.wrp_object2create()
        elif isinstance(self.wrp_object2create, tuple):  # obj is a type name with arguments for initialization
            self.object = self.wrp_object2create[0](*self.wrp_object2create[1:])
        self.wrp_object2create = None

    def wrp_call__wrapped_func_(self, sender, func_name, args, kwargs):
        try:
            log.debug("calling %s%s %s", func_name, args, kwargs)
            f = getattr(self.object, func_name)
            log.debug("%s %s %s %s",self.object, type(self.object), f, type(f))
            ret = f(*args, **kwargs)
            log.debug("function '%s' returned %s",func_name,ret)
            # if isinstance(ret,tuple):
            #     ret = (func_name,)+ret
            # else:
            #     ret = (func_name,ret)
            sender.sigReturned.emit(ret)
            self.sigFunctionReturned.emit(func_name, ret)
        except:
            exc = sys.exc_info()
            self.sigExceptionRaised.emit(func_name, exc)
            log.exception("exception in %s",func_name)
            if self.wrp_printExcInfo:
                traceback.print_exception(*exc)

    def __getattr__(self, item):
        if not self.object: #if object is scheduled for creating, but user requests an attribute
            # it will be created immidiately in caller's thread
            log.warning("creating object in caller's thread")
            self.wrp_createObject()
        return getattr(self.object,item)

#    def stop(self):
#        self._thrd.exit()


if __name__ == "__main__":
    MULTITHREADED = True
    import socket, random
    import install_exception_hook
    from qtpy import QtWidgets
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication([])
    port = random.randint(1025, 65535)
    soc1 = QtWrapper((socket.socket, socket.AF_INET, socket.SOCK_STREAM),
                     moveToNewThread=MULTITHREADED, printReturns=False)
    soc1.bind(("127.0.0.1", port))
    print("socket type is ", soc1.type)
    soc1.listen(5)
    soc1.accept()
    soc2 = QtWrapper((socket.socket, socket.AF_INET, socket.SOCK_STREAM),
                     moveToNewThread=MULTITHREADED, printReturns=False)
    soc2.bind(("127.0.0.1", random.randint(1025, 65535)))
    soc2.listen(5)
    soc2.accept()
    # *******************************************************************
    # if you create soc with moveToNewThread=False, program will never end
    # since socket.accept will wait for connection indefinitely
    # *******************************************************************
    soc3 = QtWrapper((socket.socket, socket.AF_INET, socket.SOCK_STREAM))
    soc3.connect(("127.0.0.1", port))  # connect to soc1, soc2 will wait forever
    t = QtCore.QTimer()  # quit after 1 second
    t.timeout.connect(app.quit)
    t.start(1000)
    print("socket type is ", soc1.type)
    app.exec()  # start event loop (so thread can be started also)
