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


# --- Helper Classes ---
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

        # --- UI Layout ---
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
        self.logfile = None

        # File validation button
        self.validate_file_button = tk.Button(
            self.input_frame, state=tk.DISABLED, text="Validate log")
        self.validate_file_button['command'] = self.validate_logfile
        self.validate_file_button.grid(row=1, column=0)

        # Template chooser button
        self.choose_template_button = tk.Button(
            self.input_frame, text="Choose template...")
        self.choose_template_button['command'] = self.template_chooser
        self.choose_template_button.grid(row=0, column=2)
        # Template default file initialization
        self.template_file = None

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

    # --- Event Handlers ---

    def template_chooser(self):
        """
        Opens a file dialog to select an HTML template.
        If the user cancels, it defaults to TEMPLATE_DEFAULT_FILE.
        """
        self.template_file = tkfile.askopenfilename(
            filetypes=(("QSL template", "*.html *.htm"),)) or self.template_file
        if self.template_file:
            self.template_file = os.path.basename(self.template_file)
            self.logger.info(
                f"Template chosen: {self.template_file}")
        else:
            self.template_file = os.path.basename(
                qsl_generator.TEMPLATE_DEFAULT_FILE)
            self.logger.info("No template chosen, default %s selected" %
                             self.template_file)

    def logfile_chooser(self):
        """
        Opens a file dialog to select the ADIF log file.
        
        Action:
            - Opens system file picker for .adi/.adif files.
            - Stores the path in self.logfile.
            - Enables the 'Validate log' button if a valid file is picked.
        """
        self.logfile = tkfile.askopenfilename(
            filetypes=(("ADIF file", "*.adi *.adif"),)) or self.logfile
        if self.logfile:
            self.logger.info(
                f"Log file chosen: {os.path.basename(self.logfile)}")
            self.validate_file_button.config(state=tk.NORMAL)
        else:
            self.logger.info("No log file chosen")
            self.validate_file_button.config(state=tk.DISABLED)

    def validate_logfile(self):
        """
        Runs the ADIF parser on the selected file to check for errors.
        
        Action:
            - Calls adif.parse_adif_file().
            - Logs 'Validation passed' if successful.
            - Logs specific error messages if the parser fails.
        """
        if hasattr(self, 'logfile') and os.path.isfile(self.logfile):
            try:
                _result = True  # Validation result
                adif.parse_adif_file(self.logfile)
            except Exception as e:
                _result = False
                self.logger.error(e)
            finally:
                if _result == True:
                    self.logger.info("Validation passed!")
                else:
                    self.logger.error("Validation failed!")
        else:
            self.logger.error("No logfile chosen!")

    def generate_qsl(self):
        """
        Main execution function triggered by the 'Generate QSL' button.
        
        Action:
            1. Reads the ADIF file and converts it to a list of QSO objects.
            2. Checks the state of PDF and Image checkboxes.
            3. Calls the appropriate functions in qsl_generator (generate_qsl_pdf or generate_qsl_image).
        """
        if hasattr(self, 'logfile') and os.path.isfile(self.logfile):
            qso_list = adif.qso_list_from_file(self.logfile)
            # Check if PDF output checkbox is ticked
            if self.out_pdf.get() == 1:
                self.logger.info("Proceeding to output as PDF")
                qsl_generator.generate_qsl_pdf(
                    qso_list, _template=self.template_file or qsl_generator.TEMPLATE_DEFAULT_FILE)
            else:
                self.logger.info("No PDF output")
            # Check if image output checkbox is ticked
            if self.out_img.get() == 1:
                self.logger.info("Proceeding to output as image")
                qsl_generator.generate_qsl_image(
                    qso_list, _template=self.template_file or qsl_generator.TEMPLATE_DEFAULT_FILE)
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