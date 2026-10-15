#!/usr/bin/env python3
"""Gera os sons provisórios da Paciência, só com a biblioteca padrão.

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


def card_slap(sec=0.07, decay=0.015):
    """Carta batendo na mesa: ruído curto e abafado."""
    return noise(sec, decay)


def main():
    os.makedirs(OUT, exist_ok=True)
    write("mover", tone(880, 0.05, 2, 0.02), gain=0.35)
    write("carta", mix(card_slap(0.04, 0.008), tone(1320, 0.04, 1, 0.015)), gain=0.35)
    write("borda", tone(140, 0.12, 3, 0.05), gain=0.6)
    write("pegar", mix(noise(0.1, rise=True), tone(660, 0.1, 2, 0.05, glide=0.3)), gain=0.5)
    write("soltar", mix(card_slap(), tone(440, 0.08, 2, 0.03)), gain=0.6)
    write("cabe", tone(1175, 0.07, 1, 0.03), gain=0.3)
    write("erro", mix(tone(196, 0.18, 4, 0.1), tone(185, 0.18, 4, 0.1)), gain=0.6)
    write("virar", mix(noise(0.06, 0.01), noise(0.06, 0.01), offsets=[0.0, 0.05]), gain=0.5)
    write("fundacao", mix(card_slap(), tone(784, 0.2, 2, 0.1), tone(1047, 0.2, 2, 0.1),
                          offsets=[0.0, 0.02, 0.08]), gain=0.6)
    write("comprar", mix(noise(0.12, rise=True), card_slap()), gain=0.5)
    write("embaralhar", mix(*[card_slap(0.03, 0.006) for _ in range(14)],
                            offsets=[k * 0.035 for k in range(14)]), gain=0.6)
    write("desfazer", sweep(700, 350, 0.15, 2), gain=0.4)
    write("dica", mix(tone(988, 0.1, 1, 0.05), tone(1319, 0.12, 1, 0.06), offsets=[0.0, 0.09]), gain=0.35)
    write("cascata", mix(*[tone(523 * 2 ** (k / 12.0), 0.15, 2, 0.08) for k in range(0, 24, 2)],
                         offsets=[k * 0.05 for k in range(12)]), gain=0.6)
    write("sequencia", mix(*[tone(f, 0.3, 2, 0.15) for f in (523, 659, 784, 1047, 1319)],
                           offsets=[k * 0.07 for k in range(5)]), gain=0.65)
    write("vitoria", mix(*[tone(f, 0.8, 2, 0.4) for f in (523, 659, 784, 1047, 784, 1047)],
                         offsets=[0.0, 0.12, 0.24, 0.36, 0.6, 0.72]), gain=0.7)
    write("fim", sweep(400, 120, 0.8, 3), gain=0.6)
    write("menu_mover", tone(660, 0.06, 2, 0.03), gain=0.4)
    write("menu_confirmar", mix(tone(660, 0.12, 2, 0.06), tone(990, 0.12, 2, 0.06),
                                offsets=[0.0, 0.05]), gain=0.5)
    print("sons gerados em %s" % os.path.normpath(OUT))


if __name__ == "__main__":
    main()
