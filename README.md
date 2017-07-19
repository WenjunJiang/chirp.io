Chirp.io
========

Chirp is an interesting new platform that allows you to share data using sound. This Python script allows you to convert a message into an audible chirp and vice versa.

The decoding mechanism scans the recorded audio for any substantial amplitude levels, then a FFT is performed on each segment to find the maximum frequency present. If the frontdoor pair is located then the rest of the chirp is decoded. The received code is shipped off to the Chirp API to run error correction. Once this is complete the url will be opened in your default browser.

For encoding, a sine wave is generated for each character in the chirp message.


Dependencies
------------

- pyAudio
- numpy
- requests

Usage
-----

```
python chirp.py [-h] [-l] [-i] [-u <url>] [-c <code>] [-f <file>]

optional arguments:
  -h, --help                  show this help message and exit
  -l, --listen	              listen out for chirps
  -u <url>, --url <url>       chirp a url
  -c <code>, --code <code>    chirp a code
```
