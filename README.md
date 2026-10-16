# ADIF Parser and QSL Generator

A Python tool to parse ADIF (Amateur Data Interchange Format) log files and generate personalized QSL cards using HTML/Jinja2 templates. The tool can output multi-page PDFs or individual image files.

## Features
* **ADIF Parsing:** Robust parsing of standard `.adi` log files.
* **Custom Templates:** Design QSL cards using standard HTML and CSS.
* **Dual Output:** Generate printable PDFs or digital JPEG images.
* **Cross-Platform:** Works on Windows and Linux
* **GUI & CLI:** Includes a simple Tkinter GUI for ease of use and a CLI for scripting.
* **Grouped Cards:** Contacts with the same sending and receiving callsigns share a card, up to three QSOs per card by default.
* **Chronological Contacts:** QSOs are sorted by their UTC start date and time before grouping and rendering.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/iu4pra/adif_parser.git
    cd adif_parser
    ```

2.  **Install Python Dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m pip install -r requirements.txt
    ```

3.  **Install the rendering browser:**
    ```bash
    python -m playwright install chromium
    ```
    Playwright uses Chromium to render the HTML as PDF or images; installing the
    Python package alone does not install the browser. On Linux, if Chromium
    reports missing system libraries, use
    `python -m playwright install --with-deps chromium`.

Run the commands below from the repository root, so the relative `templates/`,
`samples/`, `tmp/`, and `out/` paths resolve correctly.

## How to Run

### Option 1: Graphical Interface (Recommended)
The easiest way to use the tool is via the built-in GUI.

```bash
python gui.py
```

1. Click **"Open file..."** to select your `.adi` log file.
2. (Optional) Click **"Validate log"** to check the ADIF fields. This checks parsing,
   not whether every contact has all fields needed for generation.
3. (Optional) Put a custom HTML template in `templates/`, then click
   **"Choose template..."** to select it. The GUI keeps the filename only, so
   templates must be available in that folder.
4. Select **"PDF Output"**, **"Image Output"**, or both; keep at least one selected.
5. Click **"Generate QSL"**. Default outputs are `out/qsl.pdf` and/or
   `out/qsl_0001.jpg`, `out/qsl_0002.jpg`, and so on.

### Option 2: Command Line Interface

You can also run the generator directly from the terminal, which is useful for batch processing.

```bash
python qsl_generator.py <input_file.adi> [output_file] [options]
```

**Examples:**

```bash
# Generate a PDF (default)
python qsl_generator.py my_log.adi

# Generate images using a custom template
python qsl_generator.py my_log.adi --image --template my_custom_card.html --output-dir ./qsl_cards

# Generate both PDF and images, using "contacts" as the output base name
python qsl_generator.py my_log.adi contacts.pdf --pdf --image --output-dir ./qsl_cards

# Try the supplied multi-contact log
python qsl_generator.py samples/multi_qso_same_station.adi
```

`--template` is relative to `templates/`: use `my_custom_card.html`, not
`templates/my_custom_card.html`. The optional `output_file` is the base name
(default `qsl.pdf`); use `--output-dir` for the destination folder. For example,
the third command writes `qsl_cards/contacts.pdf` and numbered
`qsl_cards/contacts_0001.jpg` images. Existing outputs with the same names can be
overwritten, and `tmp/` is recreated and removed during generation.

| Option | Behavior |
| --- | --- |
| `--pdf` | Generate one PDF containing the cards; also the default if neither output flag is given. |
| `--image` | Generate numbered images; add `--pdf` to generate both formats. |
| `--template NAME` | Load `NAME` from `templates/`; default `template.html`. |
| `--output-dir PATH` | Output directory; default `./out/`. |
| `--image-format FORMAT` | Image filename extension; default `jpg` (for example, `png`). |
| `--width CM`, `--height CM` | Card dimensions in centimeters; defaults 14 by 9. Width must be greater than 0 and at most 700; height greater than 0 and at most 180. |
| `--max-qso N` | Maximum contacts per card; default 3. Use 1 to disable multi-contact cards. Must be a positive integer. |
| `--only-valid` | Discard contacts missing essential fields during parsing. It does not validate calendar dates or time values. |
| `--dry-run` | Log the planned rendering without writing output files. Chromium is still launched, so its installation is required. |
| `--quiet`, `--verbose` | Suppress normal logging or enable debug logging; cannot be combined. |

Use `python qsl_generator.py --help` for the command-line reference.

## Grouping, sorting, and valid contacts

The generator sorts the input list in place by `QSO_DATE` and `TIME_ON`, using
`QSO.timestamp_on()`. Dates use `YYYYMMDD`, and times use `HHMM` or `HHMMSS` in UTC;
four-digit times are padded with zero seconds. Dates and times must be parseable.

Contacts are then grouped by both `STATION_CALLSIGN` (sender) and `CALL`
(recipient), with at most **three QSOs per card by default**. Different bands and modes for
the same callsign pair stay in the same group; `CALL/P` remains distinct from
`CALL`. Within each group, contacts appear chronologically. The order of separate
station groups is not guaranteed.

Grouping is automatic in both GUI and CLI. The CLI supports `--max-qso N` to
change the maximum contacts per card; `--max-qso 1` produces one contact per card
and uses the single-contact QSL format. There is no `--group-by-call` option or
grouping checkbox. Extra contacts start another card. A one-contact chunk uses
the single-contact template context described below, including the last chunk
of a larger group.

`QSO.is_valid()` checks for `STATION_CALLSIGN`, `CALL`, `QSO_DATE`, `TIME_ON`,
`MODE`, and at least one of `FREQ` or `BAND`. It checks presence, not full ADIF
value validity. Sorting happens before the grouping helper filters invalid
contacts, so a record missing essential fields can stop generation; use
`--only-valid` in the CLI to discard such records first. Malformed dates or times
still need correcting in the input log.

## Writing HTML/Jinja2 templates

Use `templates/template.html` as the reference template. Its comments describe
the full context and filters. `templates/template_multi.html` is a separate
multi-contact example that expects `qsos`; it does not handle single-contact
chunks. Use the default reference template when the log can produce both kinds.

The template structure is simple HTML/CSS with Jinja2 placeholders, so you can
customize the layout, colors, text, and fields or supply your own HTML template.
Keep both single- and multi-contact branches when your log may produce either
kind of card, and adjust the card dimensions as described below.

### Template context

The context contains the ADIF fields of the current card, with **lowercase field
names** and **string values**, not `QSO` objects. The generator supplies exactly
one of these variables:

| Variable | When supplied | Example |
| --- | --- | --- |
| `qso` | The card has exactly one contact. | `{{ qso.call }}` |
| `qsos` | The card has multiple contacts (up to `--max-qso`; default 3). A list of dictionaries, one per contact. | `{% for contact in qsos %}{{ contact.call }}{% endfor %}` |

`qso` is not supplied alongside `qsos`. Inside a loop, the template can name its
local variable `qso`, as the default template does. For a template that handles
both contexts, normalize them to a list:

```jinja2
{% set contacts = [qso] if qso is defined else qsos %}
<p>Confirming QSO with {{ contacts[0].call }}</p>
{% for contact in contacts %}
<p>
  {{ contact.qso_date | format_date }}
  {{ contact.time_on | format_time }} UTC,
  {{ contact.mode }}
  {% if contact.band is defined %}on {{ contact.band }}{% endif %}
</p>
{% endfor %}
```

There is no fixed list of optional template fields: any non-empty field retained
in the parsed QSO is available under its lowercase ADIF name. Fields from the
ADIF header, such as `ADIF_VER`, are not part of the contact context. Common
fields include:

| Field | Meaning |
| --- | --- |
| `station_callsign`, `call` | Sending and receiving callsigns. |
| `qso_date`, `time_on` | Contact start date and UTC time. |
| `qso_date_off`, `time_off` | Optional contact end date and UTC time. |
| `band`, `freq` | Band and frequency (MHz); either can be absent. |
| `mode`, `submode` | Mode and optional submode. |
| `rst_sent`, `rst_rcvd` | Optional sent and received signal reports. |
| `name`, `qth`, `gridsquare`, `country` | Optional recipient details. |
| `operator`, `my_name`, `my_gridsquare`, `my_rig` | Optional operator/station details. |
| `comment`, `qslmsg` | Optional comment and QSL message. |

Missing fields are not filled in. Guard them with `{% if contact.name is defined %}`
or use `{{ contact.name | default('') }}`. For a field named like a dictionary
method, use bracket access, for example `{{ contact['items'] }}`. HTML templates
autoescape field values.

### Date and time filters

| Filter | Input and result |
| --- | --- |
| `format_date` | `20260912` becomes `12/09/2026` by default. |
| `format_date(fmt="%Y/%m/%d")` | The same date becomes `2026/09/12`; accepts Python `strftime` formats. |
| `format_time` | `183000` or `1830` becomes `18:30`. |
| `format_time(include_seconds=True)` | `183000` becomes `18:30:00`; seconds are included only when present. |
| `format_time(True, separator="-")` | `183000` becomes `18-30-00`. |

An invalid date is logged and returned unchanged by `format_date`. `format_time`
inserts separators; it does not validate time ranges or convert timezones.

Keep the template's CSS dimensions in sync with `--width` and `--height`. PDFs
use the requested physical size, while screenshots use Playwright's fixed
96-DPI conversion. The default template hides overflow, so oversized custom
content may be clipped.

## Development and verification

Install the development dependencies and run the tests from the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

The suite covers ADIF parsing, QSO validation/timestamps, grouping, template
context, date/time filters, CLI behavior, and the Playwright wrapper.
`conftest.py` automatically mocks Playwright for the tests, so unit tests do not
need a Chromium download and do not verify actual browser layout or rendered
PDF/image files. For coverage, install the same dependencies and run:

```bash
python -m pytest --cov=. --cov-report=term-missing
```

For a real rendering check, install Chromium as above and run the single- and
multi-contact samples into separate output folders:

```bash
python qsl_generator.py samples/minimal_1qso.adi --pdf --image --output-dir ./out/single
python qsl_generator.py samples/multi_qso_same_station.adi --pdf --image --output-dir ./out/multi
```

The multi-contact sample has seven contacts and produces four cards (3 + 1,
2, and 1 contacts for its three recipients). Open the PDF/images to check both
single- and multi-contact layouts. Do not rely on a fixed order between recipients.

Use the files in `samples/` for reproducible checks. Random stress-log generation
is still tracked in [#77](https://github.com/iu4pra/adif_parser/issues/77);
`QSO.generate_random()` is planned but not currently available.

## Project Structure

* `adif.py`: **The Parser.** Handles reading the .adi files and validating tags.
* `qso.py`: **The Data Model.** Defines the `QSO` class representing a single contact.
* `qsl_generator.py`: **The Logic.** Handles the Jinja2 templating and PDF/Image generation using Playwright.
* `gui.py`: **The Interface.** A Tkinter-based GUI for easy interaction.
* `playwright_wrapper.py`: **The Renderer.** Reuses a Chromium browser to render cards.
* `templates/`: Folder containing HTML QSL templates.
* `samples/`: ADIF fixtures, including repeated contacts for grouped-card checks.
* `test_*.py`, `conftest.py`: Unit tests and shared Playwright mocks.

## License

This software is released under the MIT License.

73 de IU4PRA
