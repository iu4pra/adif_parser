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

        self.quit_button = tk.Button(frame, text="Quit")
        self.quit_button['command'] = master.destroy
        self.quit_button.pack(side=tk.RIGHT)

        self.start_button = tk.Button(frame, text="Generate QSL")
        self.start_button['command'] = self.generate_qsl
        self.start_button.pack(side=tk.RIGHT)

        self.choose_file_button = tk.Button(frame, text="Open file...")
        self.choose_file_button['command'] = self.logfile_chooser
        self.choose_file_button.pack(side=tk.RIGHT)

    def logfile_chooser(self):
        self.logfile = tkfile.askopenfilename(
            filetypes=('ADIF file {adi adif}',))
        print(f"File chosen: {self.logfile}")

    def generate_qsl(self):

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
