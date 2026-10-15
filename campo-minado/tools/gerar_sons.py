#!/usr/bin/env python3
"""Gera os sons provisórios do Campo Minado, só com a biblioteca padrão.

Para trocar um som, ponha um arquivo com o mesmo nome em sounds/ (WAV ou OGG)
e apague o provisório.

    python3 tools/gerar_sons.py
"""
import math
import os
import random
import struct
import wave

RATE = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")
rng = random.Random(7)


def n(sec):
    return int(RATE * sec)


def tone(freq, sec, harmonics=1, decay=0.15, glide=0.0):
    out = []
    phase = 0.0
    for k in range(n(sec)):
        t = k / RATE
        f = freq * (1 + glide * t / sec)
        phase += 2 * math.pi * f / RATE
        v = sum(math.sin(phase * h) / h for h in range(1, harmonics + 1))
        out.append(v * math.exp(-t / decay))
    return out


def noise(sec, decay=0.1, rise=False):
    out = []
    last = 0.0
    for k in range(n(sec)):
        t = k / RATE
        last = 0.7 * last + 0.3 * rng.uniform(-1, 1)   # ruído mais grave
        env = (t / sec) if rise else math.exp(-t / decay)
        out.append(last * env)
    return out


def sweep(f0, f1, sec, harmonics=3):
    out, phase = [], 0.0
    for k in range(n(sec)):
        t = k / RATE
        f = f0 * (f1 / f0) ** (t / sec)
        phase += 2 * math.pi * f / RATE
        env = min(1.0, t / 0.02) * (1 - t / sec)
        out.append(env * sum(math.sin(phase * h) / h for h in range(1, harmonics + 1)))
    return out


def mix(*parts, offsets=None):
    offsets = offsets or [0.0] * len(parts)
    length = max(n(o) + len(p) for p, o in zip(parts, offsets))
    out = [0.0] * length
    for p, o in zip(parts, offsets):
        start = n(o)
        for k, v in enumerate(p):
            out[start + k] += v
    return out


def write(name, samples, gain=0.8):
    peak = max(1e-9, max(abs(v) for v in samples))
    fade = min(len(samples), n(0.01))
    data = bytearray()
    for k, v in enumerate(samples):
        if k >= len(samples) - fade:
            v *= (len(samples) - k) / float(fade)
        data += struct.pack("<h", int(max(-1, min(1, v / peak * gain)) * 32767))
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(data))


def main():
    os.makedirs(OUT, exist_ok=True)
    write("fechada", noise(0.07, 0.015), gain=0.35)
    write("marcada", mix(tone(1568, 0.25, 3, 0.12), tone(2093, 0.25, 2, 0.1)), gain=0.4)
    write("num_0", noise(0.12, 0.05), gain=0.18)
    # de 1 a 8, uma escala subindo; quanto mais minas, mais harmônicos (mais áspero)
    for k, f in enumerate((392, 440, 494, 523, 587, 659, 740, 784), start=1):
        write("num_%d" % k, tone(f, 0.12, harmonics=k, decay=0.06), gain=0.45)
    write("borda", tone(110, 0.12, 3, 0.05), gain=0.6)
    write("erro", mix(tone(196, 0.18, 4, 0.1), tone(185, 0.18, 4, 0.1)), gain=0.6)
    write("cavar", mix(noise(0.1, 0.03), tone(220, 0.08, 2, 0.03)), gain=0.6)
    write("abrir_muitas", mix(*[noise(0.06, 0.015) for _ in range(8)],
                              offsets=[k * 0.03 for k in range(8)]), gain=0.6)
    write("marcar", mix(noise(0.03, 0.005), tone(1568, 0.12, 2, 0.05), offsets=[0.0, 0.02]), gain=0.5)
    write("desmarcar", sweep(1200, 600, 0.12, 2), gain=0.4)
    write("explosao", mix(noise(1.4, 0.45), sweep(160, 35, 1.4, 4)), gain=0.9)
    write("inicio", mix(*[tone(f, 0.5, 2, 0.25) for f in (330, 440, 554)],
                        offsets=[0.0, 0.1, 0.2]), gain=0.6)
    write("vitoria", mix(*[tone(f, 0.8, 2, 0.4) for f in (523, 659, 784, 1047, 784, 1047)],
                         offsets=[0.0, 0.12, 0.24, 0.36, 0.6, 0.72]), gain=0.7)
    write("menu_mover", tone(660, 0.06, 2, 0.03), gain=0.4)
    write("menu_confirmar", mix(tone(660, 0.12, 2, 0.06), tone(990, 0.12, 2, 0.06),
                                offsets=[0.0, 0.05]), gain=0.5)
    print("sons gerados em %s" % os.path.normpath(OUT))


if __name__ == "__main__":
    main()
