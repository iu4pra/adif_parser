# ADIF Parser and QSL Generator

A Python tool to parse ADIF (Amateur Data Interchange Format) log files and generate personalized QSL cards using HTML/Jinja2 templates. The tool can output multi-page PDFs or individual image files for each contact.

## Features
* **ADIF Parsing:** Robust parsing of standard `.adi` log files.
* **Custom Templates:** Design QSL cards using standard HTML and CSS.
* **Dual Output:** Generate printable PDFs or digital JPEG images.
* **Cross-Platform:** Works on Windows, Linux, and macOS.
* **GUI & CLI:** Includes a simple Tkinter GUI for ease of use and a CLI for scripting.

## Prerequisites

Before running the Python scripts, you must install the **wkhtmltox** suite (wkhtmltopdf / wkhtmltoimage). These are system-level tools used to render the HTML templates into final files.

1.  **Download:** Go to [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)
2.  **Install:** Download the installer appropriate for your operating system and run it.
3.  **Verify:** Open your terminal/command prompt and type `wkhtmltopdf --version` to ensure it is installed and in your system PATH.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/iu4pra/adif_parser.git](https://github.com/iu4pra/adif_parser.git)
    cd adif_parser
    ```

2.  **Install Python Dependencies:**
    It is recommended to use a virtual environment.
    `pip install -r requirements.txt`

## How to Run

### Option 1: Graphical Interface (Recommended)
The easiest way to use the tool is via the built-in GUI.

python gui.py

1. Click **"Open file..."** to select your `.adi` log file.
2. (Optional) Click **"Choose template..."** to select a custom HTML template.
3. Select your output format (**PDF Output** or **Image Output**).
4. Click **"Generate QSL"**.

### Option 2: Command Line Interface

You can also run the generator directly from the terminal, which is useful for batch processing.

```bash
python qsl_generator.py <input_file.adi> [options]

```

**Examples:**

```bash
# Generate a PDF (default)
python qsl_generator.py my_log.adi

# Generate images using a custom template
python qsl_generator.py my_log.adi --image --template templates/my_custom_card.html --output-dir ./qsl_cards

```

## Project Structure

* `adif.py`: **The Parser.** Handles reading the .adi files and validating tags.
* `qso.py`: **The Data Model.** Defines the `QSO` class representing a single contact.
* `qsl_generator.py`: **The Logic.** Handles the Jinja2 templating and PDF/Image generation.
* `gui.py`: **The Interface.** A Tkinter-based GUI for easy interaction.
* `templates/`: Folder containing HTML QSL templates.

## License

This software is released under the MIT License.

73 de IU4PRA
