import io
import threading
import wave
import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._frames: list[np.ndarray] = []
        self._recording = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            self._frames = []
            self._recording = True

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> bytes:
        self._stream.stop()
        self._stream.close()
        with self._lock:
            self._recording = False
            frames = list(self._frames)

        audio = np.concatenate(frames, axis=0) if frames else np.zeros((0, self.channels), dtype="float32")
        return self._to_wav_bytes(audio)

    def _callback(self, indata, frames, time, status):
        with self._lock:
            if self._recording:
                self._frames.append(indata.copy())

    def _to_wav_bytes(self, audio: np.ndarray) -> bytes:
        pcm = (audio * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()
