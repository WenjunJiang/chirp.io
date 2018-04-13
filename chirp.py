#!/usr/bin/env python
"""
Chirp Encoder/Decoder
"""
import sys
import time
import wave
import codecs
import pyaudio
import argparse
import reedsolo
import threading
import numpy as np

MIN_AMPLITUDE = 100
SAMPLE_RATE = 44100.0  # Hz
MESSAGE_LENGTH = 0.08  # secs


class Audio(object):
    """
    Audio Processing
    """
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    RATE = int(SAMPLE_RATE)
    CHUNK = int(SAMPLE_RATE * MESSAGE_LENGTH)

    def __init__(self, callback):
        self.stream = None
        self.audio = pyaudio.PyAudio()
        self.callback = callback

    def __del__(self):
        self.audio.terminate()

    def close(self):
        if self.stream:
            self.stream.stop_stream()

    def record(self):
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.callback
        )

    def play(self, frames):
        """ Write data to system audio buffer """
        stream = self.audio.open(format=pyaudio.paInt16,
                                 channels=1,
                                 rate=self.RATE,
                                 output=True)
        stream.write(frames, len(frames))
        stream.stop_stream()
        stream.close()

    def save(self, filename, frames):
        """ Save to wav file """
        f = wave.open(filename, 'wb')
        f.setparams((self.CHANNELS, 2, self.RATE, 0, 'NONE', 'not compressed'))
        f.writeframes(frames.tostring())
        f.close()


class Signal(object):
    """
    Digital Signal Processing
    """
    def __init__(self, fs):
        self.fs = float(fs)  # sampling frequency

    def fft(self, y):
        """ Perform FFT on y with sampling rate"""
        n = len(y)  # length of the signal
        k = np.arange(n)
        T = n / self.fs
        freq = k / T  # two sides frequency range
        freq = freq[range(int(n / 2))]  # one side frequency range

        Y = np.fft.fft(y) / n  # fft computing and normalisation
        Y = Y[range(int(n / 2))]

        return (freq, abs(Y))

    def max_freq(self, data):
        """ Perform FFT on data and return maximum frequency """
        x, y = self.fft(data)
        index = y.argmax()
        return x[index]

    def sine_wave(self, freq, duration):
        """ Generate a sine wave array at given frequency for duration in seconds """
        return np.sin(2 * np.pi * np.arange(self.fs * duration) * freq / self.fs)


class Chirp(object):
    """
    Chirp Encoding/Decoding
    """
    CHIRP_VOLUME = 2 ** 16 / 4  # quarter of max amplitude
    STANDARD_PROTOCOL = {
        'frontdoor': [16, 48], 'frontdoor_length': 0.12,
        'message_length': 0.08, 'max_length': 32
    }

    def __init__(self):
        self.payload = []
        self.window = []
        self.last_heard = None
        self.decoding = False
        self.protocol = self.STANDARD_PROTOCOL
        self.map = self.get_standard_map()
        self.dsp = Signal(SAMPLE_RATE)

    def get_map(self, base_freq, interval, size):
        """ Construct map of frequencies """
        return [n for n in range(
            base_freq,
            base_freq + (interval * size),
            interval)]

    def get_standard_map(self):
        """ Construct map of frequencies for standard protocol """
        return self.get_map(1500, 45, 2 ** 8)

    def get_char(self, data):
        """ Find maximum frequency in fft data then find the closest
            frequency in chirp map and return the value """
        freq = self.dsp.max_freq(data)
        f = min(self.map, key=lambda v: abs(v - freq))
        return self.map.index(f)

    def callback(self, data, frames, info, status):
        """ Callback from pyaudio once a bytes worth
            of data is loaded into the buffer """
        DecodeThread(self.process, data).start()
        return (None, pyaudio.paContinue)

    def process(self, data):
        """ Send data off to a processing thread
            Once the frontdoor pair is located, decode the payload """
        audio = np.fromstring(data, dtype=np.int16)
        freq = self.dsp.max_freq(audio)
        f = min(self.map, key=lambda v: abs(v - freq))

        v = self.map.index(f)
        if self.decoding:
            self.payload.append(v)
            self.decode()

        if self.last_heard == self.protocol['frontdoor'][0] and v == self.protocol['frontdoor'][1]:
            print('Receiving...')
            self.decoding = True

        self.last_heard = v

    def decode(self):
        """ Decode audio data """
        if self.payload and self.payload[0] == self.protocol['frontdoor'][-1]:
            self.payload = self.payload[1:]
        if self.payload:
            length = self.payload[0] + self.get_rs_length(self.payload[0]) + 1
            if len(self.payload) == length:
                print('Received')
                message_length = self.payload.pop(0)
                print(self.rs_decode(self.payload, message_length))
                self.payload = []
                self.decoding = False

    def encode(self, payload):
        """ Generate audio data from a payload """
        samples = np.array([], dtype=np.int16)
        frontdoor = self.protocol['frontdoor']
        frontdoor.append(len(payload))
        payload = self.rs_encode(payload)

        for s in frontdoor:
            freq = self.map[s]
            char = self.dsp.sine_wave(freq, self.protocol['frontdoor_length'])
            samples = np.concatenate([samples, char])

        for s in payload:
            freq = self.map[s]
            char = self.dsp.sine_wave(freq, self.protocol['message_length'])
            samples = np.concatenate([samples, char])

        samples = (samples * self.CHIRP_VOLUME).astype(np.int16)
        return samples

    def hex_encode(self, payload):
        """ Convert payload to hex string """
        return codecs.encode(bytearray(payload), 'hex-codec')

    def hex_decode(self, hex):
        """ Convert hex string to payload """
        return codecs.decode(hex, 'hex-codec')

    def get_rs_length(self, length):
        """ Get reed solomon length """
        rs_length_range = 32 - 8
        message_length_normalised = float(length - 1) / float(self.protocol['max_length'] - 1)
        return 8 + int(message_length_normalised * rs_length_range)

    def rs_encode(self, payload):
        """ Reed Solomon Error Correction Encoding """
        rsl = self.get_rs_length(len(payload))
        padded = [0] * (255 - rsl)
        for i in range(0, len(payload)):
            padded[i] = payload[i]
        rs = reedsolo.RSCodec(nsym=rsl, fcr=1)
        encoded = payload[:]
        encoded.extend(list(rs.encode(padded))[-rsl:])
        return encoded

    def rs_decode(self, payload, length):
        """ Reed Solomon Error Correction Decoding """
        padded = [0] * 255
        for i in range(0, length):
            padded[i] = payload[i]
        parity = payload[length:]
        for i in range(0, len(parity)):
            padded[255 - len(parity) + i] = parity[i]
        try:
            rs = reedsolo.RSCodec(nsym=len(parity), fcr=1)
            return list(rs.decode(padded))[:length]
        except reedsolo.ReedSolomonError:
            print('Decode failed')


class DecodeThread(threading.Thread):
    """ Thread to run digital signal processing functions """
    def __init__(self, fn, *args):
        self.fn = fn
        self.args = args
        self.thread = threading.Thread.__init__(self)

    def run(self):
        self.fn(*self.args)

    def stop(self):
        self.thread.set()

    def stopped(self):
        return self.thread.isSet()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chirp Encoder/Decoder')
    parser.add_argument('-x', '--hex', help='Send a hex string payload to the speakers')
    parser.add_argument('-b', '--bytes', nargs='+', type=int, help='Send an array of bytes to the speakers')
    parser.add_argument('-s', '--string', help='Send an ascii string payload to the speakers')
    parser.add_argument('-w', '--wavfile', help='Filename to write wav file')
    args = parser.parse_args()

    chirp = Chirp()
    audio = Audio(chirp.callback)
    samples = None

    if args.bytes:
        samples = chirp.encode(args.bytes)
        print('Chirping payload: %s' % chirp.hex_encode(args.bytes).decode())
        audio.play(samples)
    elif args.hex:
        payload = [ord(ch) for ch in chirp.hex_decode(args.hex)]
        samples = chirp.encode(payload)
        print('Chirping payload: %s' % args.hex)
        audio.play(samples)
    elif args.string:
        payload = [ord(ch) for ch in args.string]
        samples = chirp.encode(payload)
        print('Chirping payload: %s' % args.string)
        audio.play(samples)
    else:
        try:
            print('Recording...')
            audio.record()
            time.sleep(300)

        except KeyboardInterrupt:
            pass

    if samples is not None and args.wavfile:
        audio.save(args.wavfile, samples)

    print('Exiting..')
    audio.close()
    sys.exit(0)
