# Bozze issue per iu4pra/adif_parser

Ordine consigliato: 1 → 2 → 3 → 4 → 5 → 6. Le label sono suggerimenti.

---

## 1. Replace wkhtmltopdf/wkhtmltoimage with Playwright (Chromium)
**Labels:** `enhancement`, `architecture`

wkhtmltox is a system-level dependency that must be installed by hand, and the upstream wkhtmltopdf project is archived. This makes installation harder and blocks the standalone executable (#5).

**Decision:** use Playwright (Chromium) to render the Jinja2 templates to PDF and JPEG. Jinja2 stays as the template engine. Rationale: templates must be easy to edit by non-technical users and by LLMs, and Chromium renders standard HTML/CSS exactly like a browser, so a template can be previewed by simply opening it in Chrome or Edge.

- [ ] Add `playwright` to `requirements.txt`
- [ ] Abstract rendering behind a small interface in `qsl_generator.py` (`render_pdf`, `render_image`) so a second backend (e.g. WeasyPrint, PDF only) can be added later
- [ ] Launch the browser once per run and reuse it for every card (not once per QSO)
- [ ] Browser selection: on Windows use the installed Edge (`channel="msedge"`), otherwise installed Chrome/Chromium, otherwise Playwright's own Chromium (`playwright install chromium`); clear error message if none is found (see #2)
- [ ] Fixed card size (e.g. 14x9 cm) via `@page` for PDF and viewport for JPEG
- [ ] Resolve relative paths of images and fonts against the template folder (base URL)
- [ ] Enable Jinja2 autoescape so names containing `&` or `<` do not break the page
- [ ] Check the existing templates render the same as before
- [ ] Remove `wkhtml.py`; close or rework #47 and #49 (custom wkhtmltox args), possibly replaced by custom Playwright/Chromium options
- [ ] Update README (Prerequisites section)

**Template editing support (same issue or follow-up):**
- [ ] Commented example template with all available variables
- [ ] README section documenting variables (`qso.*`, `qsos`) and a ready-to-use prompt for asking an LLM to write a template
- [ ] Preview command with fake data that opens the result in the browser

**Note:** do this before the standalone build (#5). Chromium size affects the executable; evaluate using the system browser to keep it small.

---

## 2. Show a clear message in the GUI when the rendering tool is missing
**Labels:** `enhancement`, `GUI`, `good first issue`

Today a missing renderer produces a technical error. The GUI should check at startup and explain what to do.

- [ ] At startup, detect whether the renderer is available (wkhtmltox now, the new backend after #1)
- [ ] If missing, show a dialog with the reason, the download link and the steps to verify the install
- [ ] Disable the "Generate QSL" button until the check passes, with a "Check again" button
- [ ] Same check and readable message in the CLI (non-zero exit code)

---

## 3. Run generation in a background thread with a progress bar
**Labels:** `enhancement`, `GUI`

With large logs the Tkinter window freezes during generation.

- [ ] Run generation in a worker thread (`threading` or `concurrent.futures`)
- [ ] Progress bar (`ttk.Progressbar`) updated per processed QSO, with a "n / total" label
- [ ] "Cancel" button that stops after the current card
- [ ] Buttons disabled while running; UI updated only from the main thread (`after` / queue)
- [ ] On completion: summary message and an "Open output folder" button
- [ ] Output folder selectable from the GUI

---

## 4. Option: multiple QSOs on the same QSL card
**Labels:** `enhancement`

Let the user choose whether to print one card per QSO or one card per station, listing all QSOs with that station.

- [ ] Option in CLI (e.g. `--group-by-call`) and a checkbox in the GUI; default stays one card per QSO
- [ ] Group QSOs by `CALL` (decide whether band/mode variants of the same call are merged; callsign suffixes like `/P` treated as different stations unless stated otherwise)
- [ ] Template receives both `qso` (first QSO) and `qsos` (list) so existing templates keep working
- [ ] Default template shows a table of QSOs (date, UTC, band, mode, RST) when `qsos` has more than one entry
- [ ] Decide a maximum rows per card and what happens past it (second page or smaller font)
- [ ] Unit tests and sample log: `samples/multi_qso_same_station.adi` (7 QSOs, 3 stations: 4 + 2 + 1)
- [ ] Document the `qsos` variable in the README

---

## 5. Standalone executable and GitHub Releases
**Labels:** `enhancement`, `packaging`, `CI`

Users who are not developers should not need Python, pip or system tools.

- [ ] Build the GUI with PyInstaller for Windows and Linux (Windows first)
- [ ] Bundle `templates/` and a sample log; make paths work both from source and from the frozen app
- [ ] Bundle the renderer, or document that it is included (depends on #1)
- [ ] GitHub Actions workflow (there is already `.github/workflows`): on tag `v*`, build and attach the artifacts to a Release
- [ ] Version number shown in the GUI title or "About"
- [ ] README: "Download" section with a link to the latest release

**Depends on:** #1

---

## 6. Sample logs folder
**Labels:** `documentation`, `good first issue`

The sample `.adi` files are scattered in the repo root. Gather them in `samples/`.

- [ ] Create `samples/` with `minimal_1qso.adi`, `multi_qso_same_station.adi`, `mixed_bands_modes.adi`, `malformed.adi` and its `README.md` (provided)
- [ ] Move `sample_2qso.adi`, `sample_log.adi`, `iu4pra_sample_log.adi`, `test_log.adi` into `samples/` (`git mv`)
- [ ] Update the paths used by `test_adif.py`, `test_qso.py`, `unit_test.py` and the README examples
- [ ] Mention the folder in the README "Project Structure" section
