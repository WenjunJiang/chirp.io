Chirp Encoder / Decoder
=======================

Chirp is an interesting platform that allows you to share data using sound. This Python script lets you to convert a message into an audible chirp and vice versa.

The decoding mechanism scans the recorded audio for anything above background noise, then a FFT is performed on each segment to find the maximum frequency present. If the frontdoor pair is located then the rest of the chirp is decoded, and Reed Solomon error correction is performed to fix any transmission errors.

For encoding, a sine wave is generated for each byte in the chirp message, plus the Reed Solomon symbols.

The Reed Solomon library is a pure python implementation written by Tomer Filiba - [reedsolomon](https://github.com/tomerfiliba/reedsolomon)
The latest changes are not available on PyPi so I have copied the latest code to this repo.

This is very simplistic version of Chirp encoding/decoding. For production ready SDK's for many different platforms, head over to the [Chirp Admin Centre](https://admin.chirp.io)


Dependencies
------------

- pyAudio
- numpy

To install pyAudio you will need to install PortAudio bindings, on macOS
this is just `brew install portaudio`.

Usage
-----

Listen for data
```shell
python chirp.py
```

Send a hex string payload
```shell
python chirp.py -x 68656c6c6f
```

Send an array of bytes
```shell
python chirp.py -b 104 101 108 108 111
```

Send an ascii string payload
```shell
python chirp.py -s hello
```

Listen in ultrasonic mode
```shell
python chirp.py -p ultrasonic
```
