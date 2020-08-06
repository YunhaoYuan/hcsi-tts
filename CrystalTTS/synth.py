
from ctypes import *

class WavSynthesis(object):
    def __init__(self, dllpath = u'./CrystalTTS/crystal.synth.so'):
        self._dllpath = dllpath
        self._libc = cdll.LoadLibrary(self._dllpath)
        self._tts = 0

    def initialize(self, configfile = u'./CrystalTTS/config.xml'):
        _ttsInitialize = self._libc.synthInitialize
        _ttsInitialize.restype = c_void_p
        self._tts = _ttsInitialize(c_wchar_p(configfile))
        if self._tts == 0:
            raise Exception('[CrystalTTS]: Synthesizer initialization FAILED! Config File: %s' % configfile)
        else:
            print('[CrystalTTS]: Synthesizer initialization OK!')

    def terminate(self):
         if self._tts != 0:
             self._libc.synthTerminate(c_void_p(self._tts))

    def process(self, ssmlfile, wavfile):
        _ttsSynthesize = self._libc.synthProcess
        _ttsSynthesize.restype = c_bool
        flag = _ttsSynthesize(c_void_p(self._tts), c_wchar_p(ssmlfile), c_wchar_p(wavfile))
        if flag:
            print('[CrystalTTS]: Wav synthesis OK!')
        else:
            print('[CrystalTTS]: Wav synthesis FAILED!')
        return flag
