#!/usr/bin/python3

# This software under the MIT License
# GUI for QSL generator written in Tkinter

import adif
import qsl_generator

import logging
import os.path
import tkinter as tk
import tkinter.filedialog as tkfile
import tkinter.scrolledtext as tkscroll


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # Source: https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget

    def __init__(self, text: tkscroll.ScrolledText):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        """Actually log the specified logging record, required by superclass"""
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

    def clear(self):
        """Clear the textbox"""
        self.text.configure(state='normal')
        self.text.delete(1.0, tk.END)
        self.text.configure(state='disabled')


class App():
    """Main application class"""

    def __init__(self, master: tk.Tk):
        """Create and initialize widgets"""

        # Main frame
        frame = tk.Frame(master)
        frame.grid(padx=5, pady=5)

        # Frame for checkboxes
        self.input_frame = tk.Frame(master)
        self.input_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        # Checkbox for PDF output
        self.out_pdf = tk.IntVar()
        self.out_pdf.set(1)
        c_pdf = tk.Checkbutton(self.input_frame, text="PDF Output",
                               variable=self.out_pdf, onvalue=1, offvalue=0)
        c_pdf.grid(row=0, column=1, sticky='w')

        # Checkbox for image output
        self.out_img = tk.IntVar()
        c_img = tk.Checkbutton(self.input_frame, text="Image Output",
                               variable=self.out_img, onvalue=1, offvalue=0)
        c_img.grid(row=1, column=1, sticky='w')

        # File chooser button
        self.choose_file_button = tk.Button(
            self.input_frame, text="Open file...")
        self.choose_file_button['command'] = self.logfile_chooser
        self.choose_file_button.grid(row=0, column=0)

        # File validation button
        self.validate_file_button = tk.Button(
            self.input_frame, state=tk.DISABLED, text="Validate log")
        self.validate_file_button['command'] = self.validate_logfile
        self.validate_file_button.grid(row=1, column=0)

        # Frame for main buttons
        self.buttons_frame = tk.Frame(master)
        self.buttons_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # Clear log button
        self.clear_log_button = tk.Button(self.buttons_frame, text="Clear Log")
        self.clear_log_button.grid(row=1, column=0, padx=5, pady=5)

        # Start generation button
        self.start_button = tk.Button(self.buttons_frame, text="Generate QSL")
        self.start_button['command'] = self.generate_qsl
        self.start_button.grid(row=1, column=1, padx=5, pady=5)

        # Quit button
        self.quit_button = tk.Button(self.buttons_frame, text="Quit")
        self.quit_button['command'] = master.destroy
        self.quit_button.grid(row=1, column=2, padx=5, pady=5)

        # Logging text box
        self.logbox = tkscroll.ScrolledText(
            master, state=tk.DISABLED, width=50, height=10)
        self.logbox.grid(row=2, column=0, columnspan=3)

        # Logger configuration
        self.logger = logging.getLogger('app')
        log_handler = TextHandler(self.logbox)
        log_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'))
        self.logger.addHandler(log_handler)
        self.logger.setLevel(logging.INFO)

        # Bind clear log command
        self.clear_log_button['command'] = log_handler.clear

    def logfile_chooser(self):
        """Open file chooser for log file"""
        self.logfile = tkfile.askopenfilename(
            filetypes=(("ADIF file", "*.adi *.adif"),))
        if self.logfile:
            self.logger.info(f"File chosen: {os.path.basename(self.logfile)}")
            self.validate_file_button.config(state=tk.NORMAL)
        else:
            self.logger.info("No logfile chosen")
            self.validate_file_button.config(state=tk.DISABLED)

    def validate_logfile(self):
        """Callback for log file validation"""
        if hasattr(self, 'logfile') and os.path.isfile(self.logfile):
            try:
                _result = True  # Validation result
                adif.parse_adif_file(self.logfile)
            except Exception as e:
                self.logger.error(e)
                _result = False
            finally:
                if _result == True:
                    self.logger.info("Validation passed")
                else:
                    self.logger.error("Validation failed")
        else:
            self.logger.error("No logfile chosen!")

    def generate_qsl(self):
        """QSL generator callback"""
        if hasattr(self, 'logfile') and os.path.isfile(self.logfile):
            qso_list = adif.qso_list_from_file(self.logfile)
            if self.out_pdf.get() == 1:
                self.logger.info("Proceeding to output as PDF")
                qsl_generator.generate_qsl_pdf(qso_list)
            else:
                self.logger.info("No PDF output")
            if self.out_img.get() == 1:
                self.logger.info("Proceeding to output as image")
                qsl_generator.generate_qsl_image(qso_list)
            else:
                self.logger.info("No image output")
        else:
            self.logger.error("No logfile chosen!")


if __name__ == '__main__':

    # Run the module
    root = tk.Tk()
    root.wm_title("QSL generator by IU4PRA")
    root.wm_resizable(False, False)
    root.minsize(300, 100)

    # Run the app
    app = App(root)
    root.mainloop()

    print("Program terminated")
