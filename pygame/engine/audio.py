"""
Audio por eventos: durante el render se loguean colisiones (frame, tipo).
Al terminar, genera una pista sintetizada y la múxea con moviepy v2.

Tipos de evento soportados:
  "eat"          -> bloop ascendente
  "note:{freq}"  -> nota de melodía a la frecuencia dada (Hz)
"""

import os
import wave
import numpy as np

SAMPLE_RATE = 44100

# Nombres de nota -> semitonos desde A4 (dentro de la misma octava)
_NOTE_ST = {'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2, 'A': 0, 'B': 2}


def note_to_freq(name: str) -> float:
    """
    Convierte nombre de nota ('E4', 'F#4', 'Bb4') a Hz.
    Referencia: A4 = 440 Hz, temperamento igual: freq = 440 * 2^(semis/12).
    """
    i = 0
    st = _NOTE_ST[name[i]]; i += 1
    while i < len(name) and name[i] in ('#', 'b'):
        st += 1 if name[i] == '#' else -1
        i += 1
    octave = int(name[i:])
    semis_from_a4 = st + (octave - 4) * 12
    return 440.0 * (2 ** (semis_from_a4 / 12))


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
    rng = np.random.default_rng(7)

    for frame, stype in events:
        t0 = int(frame / fps * SAMPLE_RATE)
        if stype == "eat":
            tone = _make_eat(rng)
        elif stype.startswith("note:"):
            freq = float(stype[5:])
            tone = _make_note_tone(freq)
        else:
            continue
        end = min(t0 + len(tone), n)
        audio[t0:end] += tone[:end - t0]

    peak = np.max(np.abs(audio))
    if peak > 0:
        audio /= peak * 1.05
    return audio


def _make_eat(rng) -> np.ndarray:
    """Bloop ascendente — igual lógica que engine/sounds.py."""
    dur = 0.11
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freq = 500 + 900 * (t / dur) ** 0.6
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * np.pi
    tone = 0.48 * np.sin(phase) * np.exp(-t * 22)
    tone += 0.12 * np.sin(phase * 2) * np.exp(-t * 35)
    return tone.astype(np.float32)


def _make_note_tone(freq: float, dur: float = 0.18) -> np.ndarray:
    """Nota de melodía: sinusoide limpia con ataque y decay suaves."""
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    tone = 0.5 * np.sin(2 * np.pi * freq * t)
    # Segunda armónica suave para calidez
    tone += 0.15 * np.sin(2 * np.pi * freq * 2 * t)
    n_att = int(SAMPLE_RATE * 0.012)
    n_rel = int(SAMPLE_RATE * 0.05)
    env = np.ones(len(t))
    env[:n_att] = np.linspace(0, 1, n_att)
    env[-n_rel:] = np.linspace(1, 0, n_rel)
    return (tone * env).astype(np.float32)


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
