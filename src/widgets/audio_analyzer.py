# audio analyzer - FFT for visualizer

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtMultimedia import QAudioBufferOutput


class AudioAnalyzer(QObject):
    levels_updated = pyqtSignal(list)  # 32 freq bands

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sr = 44100
        self.bands = 32
        self.audio_out = QAudioBufferOutput()
        self.audio_out.audioBufferReceived.connect(self._process)

    def get_audio_buffer_output(self):
        return self.audio_out

    def _process(self, buf):
        try:
            if not buf.isValid():
                return

            fmt = buf.format()
            self.sr = fmt.sampleRate()

            data = np.frombuffer(buf.data(), dtype=np.int16)

            # stereo -> mono
            if fmt.channelCount() == 2:
                data = data.reshape(-1, 2).mean(axis=1).astype(np.int16)

            # normalize
            data = data.astype(np.float32) / 32768.0

            levels = self._analyze(data)
            self.levels_updated.emit(levels)
        except:
            pass

    def _analyze(self, data):
        try:
            win = np.hanning(len(data))
            spec = np.fft.rfft(data * win)
            mag = np.abs(spec)
            mag = np.log1p(mag)

            return self._to_bands(mag)
        except:
            return [0.0] * self.bands

    def _to_bands(self, mag):
        nyq = self.sr / 2
        res = nyq / len(mag)

        edges = np.logspace(np.log10(20), np.log10(nyq), self.bands + 1)

        out = []
        for i in range(self.bands):
            lo = int(edges[i] / res)
            hi = int(edges[i + 1] / res)
            hi = min(hi, len(mag))

            if lo < hi:
                out.append(mag[lo:hi].mean())
            else:
                out.append(0.0)

        mx = max(out) if out else 1.0
        mx = max(mx, 0.1)
        return [min(1.0, max(0.0, v / mx)) for v in out]
