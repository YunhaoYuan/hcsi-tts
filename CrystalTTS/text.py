
from ctypes import *

class TextAnalysis(object):
    def __init__(self, dllpath = u'./CrystalTTS/crystal.text.so'):
        self._dllpath = dllpath
        self._libc = cdll.LoadLibrary(self._dllpath)
        self._tts = 0

    def initialize(self, configfile = u'./CrystalTTS/config.xml'):
        _ttsInitialize = self._libc.textInitialize
        _ttsInitialize.restype = c_void_p
        self._tts = _ttsInitialize(c_wchar_p(configfile))
        if self._tts == 0:
            raise Exception('[CrystalTTS]: Text analysis initialization FAILED! Config File: %s' % configfile)
        else:
            print('[CrystalTTS]: Text analysis initialization OK!')

    def terminate(self):
         if self._tts != 0:
             self._libc.textTerminate(c_void_p(self._tts))

    def process(self, text, filename):
        _ttsTextAnalysis = self._libc.textProcess
        _ttsTextAnalysis.restype = c_bool
        flag = _ttsTextAnalysis(c_void_p(self._tts), c_wchar_p(text), c_bool(False), c_wchar_p(filename))
        if flag:
            print('[CrystalTTS]: Text analysis OK! Text=%s' % text)
        else:
            print('[CrystalTTS]: Text analysis FAILED! Text=%s' % text)
        return flag
