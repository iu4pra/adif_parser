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

        # Frame for checkboxes
        self.checkbox_frame = tk.Frame(master)
        self.checkbox_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.out_pdf = 0
        self.out_img = 0
        tk.Checkbutton(self.checkbox_frame, text="PDF", variable=self.out_pdf,
                       onvalue=1, offvalue=0).grid(row=0, column=0)
        tk.Checkbutton(self.checkbox_frame, text="Image",
                       variable=self.out_img, onvalue=1, offvalue=0).grid(row=1, column=0)

        # Frame for main buttons
        self.buttons_frame = tk.Frame(master)
        self.buttons_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # Quit button
        self.quit_button = tk.Button(self.buttons_frame, text="Quit")
        self.quit_button['command'] = master.destroy
        self.quit_button.grid(row=1, column=2)

        # Start generation button
        self.start_button = tk.Button(self.buttons_frame, text="Generate QSL")
        self.start_button['command'] = self.generate_qsl
        self.start_button.grid(row=1, column=1)

        # File chooser button
        self.choose_file_button = tk.Button(
            self.buttons_frame, text="Open file...")
        self.choose_file_button['command'] = self.logfile_chooser
        self.choose_file_button.grid(row=1, column=0)

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
    root.minsize(300, 100)

    app = App(root)
    root.mainloop()

    print("Program terminated")
