#!/usr/bin/python3

# This software under the MIT License
# GUI for QSL generator written in Tkinter

import adif

import qsl_generator
import tkinter as tk
import tkinter.filedialog as tkfile


class App():

    def __init__(self, master: tk.Tk):

        frame = tk.Frame(master)
        frame.grid()

        # Quit button
        self.quit_button = tk.Button(frame, text="Quit")
        self.quit_button['command'] = master.destroy
        self.quit_button.grid(row = 0, column = 2)

        # Start generation button
        self.start_button = tk.Button(frame, text="Generate QSL")
        self.start_button['command'] = self.generate_qsl
        self.start_button.grid(row = 0, column = 1)

        # File chooser button
        self.choose_file_button = tk.Button(frame, text="Open file...")
        self.choose_file_button['command'] = self.logfile_chooser
        self.choose_file_button.grid(row = 0, column = 0)

    def logfile_chooser(self):
        """Open file chooser for log file"""
        self.logfile = tkfile.askopenfilename(
            filetypes=(("ADIF file", "*.adi *.adif"),))
        print(f"File chosen: {self.logfile}")

    def generate_qsl(self):
        """QSL generator callback"""
        if hasattr(self, 'logfile'):
            qsl_generator.generate_qsl_pdf(
                adif.qso_list_from_file(self.logfile))
        else:
            print("ERROR: No logfile chosen!")


if __name__ == '__main__':

    # Run the module

    root = tk.Tk()
    root.wm_title("QSL generator by IU4PRA")
    root.wm_resizable(False, False)
    root.minsize(200, 30)

    app = App(root)
    root.mainloop()

    print("Program terminated")
