"""Capture helpers that must not require optional pitch deps."""

from __future__ import annotations

import unittest

from audio.capture import list_input_devices


class CaptureHelpersTest(unittest.TestCase):
    def test_list_input_devices(self) -> None:
        devices = list_input_devices()
        self.assertIsInstance(devices, list)
        for item in devices:
            self.assertIsInstance(item[0], int)
            self.assertIsInstance(item[1], str)


if __name__ == "__main__":
    unittest.main()
