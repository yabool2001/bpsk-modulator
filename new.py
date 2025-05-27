# Source: https://ez.analog.com/sw-interface-tools/f/q-a/546389/using-pyadi-iio-how-to-get-rx-data-continuous

import numpy as np
import wave
import matplotlib.pyplot as plt
import scipy.signal as sig
import scipy
import math
import adi
import pyaudio
from multiprocessing import Process, Queue
import os
import time
import random
import datetime

SampleRate = 44100.0 * 12
Targetrate = 44100.0 * 5
Audiorate  = 44100.0

CenterFreq = 84.7e6
TragetRate = 44.1e3
UseAGC     = False
RfAmpGain  = 50

def SdrInit():
    sdr = adi.Pluto()
    sdr.rx_rf_bandwidth = 150000
    sdr.rx_lo = 84700000
    sdr.sample_rate = int(SampleRate)
    sdr.rx_hardwaregain = 50
    sdr.rx_buffer_size = 32768*30
    return sdr

def SdrRxFromPluto(sdr):
    rx = sdr.rx()
    return rx

def write(q):
    global flag_1
    sdr = SdrInit()
    
    while True:
        fmmodulated = SdrRxFromPluto(sdr)
        # put audio data in Queue
        q.put(fmmodulated)

def read(q):
    global flag_1
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)
    while True:
        fmmodulated = q.get()

        downsamp = sig.resample(fmmodulated, int(len(fmmodulated)*Targetrate/SampleRate))
        demod = np.angle(downsamp[1:]*np.conj(downsamp[:-1]))
        a = sig.resample(demod, int(len(demod)*Audiorate/Targetrate))
        a = a/math.pi * 32768.0
        audio = a.astype(np.int16)
        stream.write(audio)

if __name__ == "__main__":
    flag_1 = True
    q = Queue()
    pw = Process(target=write, args=(q,))
    pr = Process(target=read, args=(q,))

    pw.start()
    pr.start()

    pw.join()
    pr.join()
    pr.terminate()