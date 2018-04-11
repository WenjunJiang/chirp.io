"""
Chirp Encoder/Decoder Test Suite
"""
import chirp
import unittest


class TestChirp(unittest.TestCase):

    def setUp(self):
        self.chirp = chirp.Chirp(protocol='standard')

    def test_get_standard_map(self):
        m = self.chirp.get_standard_map()
        self.assertEqual(len(m), 256)

    def test_get_ultrasonic_map(self):
        m = self.chirp.get_ultrasonic_map()
        self.assertEqual(len(m), 32)

    def test_get_rs_length(self):
        l = self.chirp.get_rs_length(5)
        self.assertEqual(l, 9)

    def test_hex_encode(self):
        h = self.chirp.hex_encode(b'hello')
        self.assertEqual(h, b'68656c6c6f')

    def test_hex_decode(self):
        p = self.chirp.hex_decode(b'68656c6c6f')
        self.assertEqual(p, b'hello')

    def test_rs_encode(self):
        p = [ord(ch) for ch in 'hello']
        rs = self.chirp.rs_encode(p)
        p.extend([140, 31, 146, 96, 78, 78, 112, 211, 173])
        self.assertEqual(rs, p)

    def test_rs_decode(self):
        p = [ord(ch) for ch in 'hello']
        p.extend([140, 31, 146, 96, 78, 78, 112, 211, 173])
        rs = self.chirp.rs_decode(p, 5)
        self.assertEqual(rs, [ord(ch) for ch in 'hello'])


if __name__ == '__main__':
    unittest.main()
