# Text Encoder – Braille & Morse

A unified desktop application that converts text to **Braille (Unicode)** and **International Morse Code**, with built-in OCR support via webcam or image file.

---

## Features

| Feature | Detail |
|---|---|
| Text → Braille | Full a–z alphabet + digits 0–9 with numeric prefix `⠼` |
| Text → Morse | Full a–z alphabet + digits 0–9 + word separator `/` |
| Webcam OCR | Capture a frame live, extract text automatically |
| Image OCR | Load `.png` / `.jpg` / `.jpeg`, extract text automatically |
| Tabbed UI | Both encoders in one window — no need to run two scripts |

---

## Architecture (OOP + DRY)

The original codebase consisted of two standalone scripts (`Braille.py`, `Morse.py`) with ~80 lines of verbatim duplication and no class structure. This refactor applies:

### Class Hierarchy

```
OCREngine                    ← stateless utility (was duplicated in both files)
│
BaseConverterFrame (ABC)     ← Template Method pattern
├── BrailleConverterFrame    ← overrides convert(), labels
└── MorseConverterFrame      ← overrides convert(), labels

ConverterApp                 ← root window + tab composition
```

### Design Decisions

**`OCREngine`** — Single Responsibility Principle. All webcam and file OCR logic extracted into one class with `@staticmethod` methods. Previously copy-pasted verbatim across both files (Braille.py L35–72, Morse.py L23–62).

**`BaseConverterFrame` (Template Method)** — The entire UI skeleton, event wiring, and input validation live here once. Subclasses implement only three things: `convert()`, `convert_button_label`, and `output_section_label`. Adding a new encoder (e.g. Binary, Semaphore) requires zero changes to existing code.

**Class-level map constants** — In the original `Braille.py`, the character dictionaries were rebuilt on *every single keystroke* (inside the function body, L8–22). Promoted to class-level `_BRAILLE_MAP`, `_NUMBER_MAP`, and `_MORSE_MAP` so they are constructed exactly once at class definition time.

**`ConverterApp`** — Owns only the window and tab layout. All domain logic is fully delegated — this class has no knowledge of Braille or Morse internals.

---

## Project Structure

```
.
├── converter_app.py     # Single merged application (run this)
├── requirements.txt
└── README.md
```

The original `Braille.py` and `Morse.py` are superseded by `converter_app.py`.

---

## Requirements

- Python 3.10+ (uses `str | None` union syntax)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your system

### Install Tesseract

**Windows:** Download installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).  
**macOS:** `brew install tesseract`  
**Ubuntu/Debian:** `sudo apt install tesseract-ocr`

---

## Installation

```bash
# 1. Clone or download the project
git clone <your-repo-url>
cd <project-folder>

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run the app
python converter_app.py
```

---

## Usage

1. **Type** text directly into the *Input Text* box, then press the convert button.
2. **Webcam**: Click *Capture from Webcam* → press `s` to snap a frame → text is auto-filled.
3. **Image file**: Click *Select Image File* → pick a PNG/JPG → text is auto-filled.
4. Switch between **Braille** and **Morse Code** tabs freely; each tab is independent.

---

## Extending the App

To add a new encoder (e.g. Binary):

```python
class BinaryConverterFrame(BaseConverterFrame):

    @property
    def convert_button_label(self) -> str:
        return "Convert to Binary"

    @property
    def output_section_label(self) -> str:
        return "Binary Output:"

    def convert(self, text: str) -> str:
        return ' '.join(format(ord(ch), '08b') for ch in text)
```

Then register it in `ConverterApp.__init__`:

```python
BinaryConverterFrame(tab_view.add("🔢 Binary"))
```

No other files need to change.

---

## License

MIT
