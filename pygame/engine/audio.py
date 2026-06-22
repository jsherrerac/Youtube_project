"""
Audio por eventos: durante el render se loguean colisiones (frame, tipo).
Al terminar, genera una pista sintetizada y la múxea con moviepy v2.
"""

import os
import wave
import numpy as np

SAMPLE_RATE = 44100

# Frecuencias y duraciones por tipo de evento
_FREQ   = {"eat": 880,  "wall": 330, "done": 660}
_LEN_S  = {"eat": 0.04, "wall": 0.09, "done": 0.35}
_VOL    = {"eat": 0.25, "wall": 0.35, "done": 0.6}


class AudioLog:
    def __init__(self):
        self.events: list[tuple[int, str]] = []  # (frame, sound_type)

    def log(self, frame: int, sound_type: str) -> None:
        self.events.append((frame, sound_type))

    def build_and_mux(self, video_path: str, fps: int, total_frames: int) -> None:
        """Genera WAV desde eventos y múxea sobre video_path (sobreescribe el archivo)."""
        if not self.events:
            return
        duration = total_frames / fps
        audio = _synthesize(self.events, fps, duration)
        wav_path = video_path.replace('.mp4', '_audio.wav')
        _save_wav(audio, wav_path)
        out_path = video_path.replace('.mp4', '_muxed.mp4')
        try:
            _mux(video_path, wav_path, out_path)
            os.replace(out_path, video_path)
        except Exception as e:
            print(f"[audio] Mux falló ({e}), video sin audio guardado igual.")
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)


def _synthesize(events, fps: int, duration: float) -> np.ndarray:
    n = int(SAMPLE_RATE * duration)
    audio = np.zeros(n, dtype=np.float32)
    for frame, stype in events:
        t0 = int(frame / fps * SAMPLE_RATE)
        freq  = _FREQ.get(stype, 440)
        secs  = _LEN_S.get(stype, 0.05)
        vol   = _VOL.get(stype, 0.2)
        ns = int(SAMPLE_RATE * secs)
        t  = np.arange(ns) / SAMPLE_RATE
        tone = vol * np.sin(2 * np.pi * freq * t) * np.exp(-t * 20)
        end = min(t0 + ns, n)
        audio[t0:end] += tone[:end - t0]
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio /= peak * 1.05
    return audio


def _save_wav(audio: np.ndarray, path: str) -> None:
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())


def _mux(video_path: str, audio_path: str, out_path: str) -> None:
    from moviepy import VideoFileClip, AudioFileClip
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path).subclipped(0, video.duration)
    result = video.with_audio(audio)
    result.write_videofile(out_path, codec='libx264', audio_codec='aac',
                           logger=None)
    video.close()
    audio.close()
