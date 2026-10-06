#!/usr/bin/python3

# This software under the MIT License
# Unit test for ADIF parser GUI

import gui
import tkinter as tk
import unittest


class AppTest(unittest.TestCase):

    def test_init_widgets(self):
        app = gui.App(tk.Tk())
        self.assertIsNotNone(app.input_frame)
        self.assertIsNotNone(app.out_img)
        self.assertIsNotNone(app.out_pdf)


if __name__ == "__main__":
    unittest.main()
