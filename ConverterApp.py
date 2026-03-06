import customtkinter as ctk
import cv2
import pytesseract
from tkinter import filedialog, messagebox
from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════
# OCREngine  –  single responsibility: image → text
# DRY fix: was duplicated verbatim in both files (Braille L35-72,
#           Morse L23-62). Now lives in exactly one place.
# ══════════════════════════════════════════════════════════════════
class OCREngine:
    """
    Stateless utility class that wraps all OCR operations.
    Using @staticmethod keeps the interface clean while still
    allowing future subclassing (e.g. cloud-OCR backend).
    """

    @staticmethod
    def capture_from_webcam() -> str | None:
        """Open webcam, let user capture a frame, return OCR text."""
        cap = cv2.VideoCapture(0)
        messagebox.showinfo("Info", "Press 's' to capture or 'q' to quit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                messagebox.showerror("Error", "Failed to capture image.")
                break
            cv2.imshow("Webcam", frame)
            key = cv2.waitKey(1)
            if key == ord('s'):
                cv2.imwrite("captured_image.png", frame)
                cap.release()
                cv2.destroyAllWindows()
                try:
                    return pytesseract.image_to_string("captured_image.png")
                except Exception as e:
                    messagebox.showerror("Error", f"OCR failed: {e}")
                    return None
            elif key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return None
        cap.release()
        cv2.destroyAllWindows()
        return None

    @staticmethod
    def extract_from_image_file() -> str | None:
        """Prompt user for an image file, return OCR text."""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        if not file_path:
            return None
        try:
            img = cv2.imread(file_path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            messagebox.showerror("Error", f"OCR failed: {e}")
            return None


# ══════════════════════════════════════════════════════════════════
# BaseConverterFrame  –  Template Method pattern
# Owns the shared UI skeleton and event wiring.
# Subclasses provide ONLY the three abstract members below.
# ══════════════════════════════════════════════════════════════════
class BaseConverterFrame(ABC):
    """
    Abstract base for every encoder panel.

    Invariant behaviour (defined here):
        • Build input / output / action UI sections
        • Wire OCR buttons to OCREngine
        • Guard empty input before converting

    Variable behaviour (defined in subclasses):
        • convert()              – the encoding algorithm
        • convert_button_label   – button caption
        • output_section_label   – output box header
    """

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._ocr = OCREngine()
        self._build_ui(parent)

    # ── Abstract interface ─────────────────────────────────────────
    @abstractmethod
    def convert(self, text: str) -> str:
        """Encode *text* and return the result string."""
        ...

    @property
    @abstractmethod
    def convert_button_label(self) -> str:
        """Caption for the primary conversion button."""
        ...

    @property
    @abstractmethod
    def output_section_label(self) -> str:
        """Header text above the output box."""
        ...

    # ── Shared UI builder (Template Method) ───────────────────────
    def _build_ui(self, parent: ctk.CTkFrame) -> None:
        # -- Input section --
        input_frame = ctk.CTkFrame(parent, corner_radius=10)
        input_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(input_frame, text="Input Text:", font=("Arial", 14)).pack(
            anchor="w", pady=5
        )
        self._text_input = ctk.CTkTextbox(input_frame, height=100)
        self._text_input.pack(fill="x", pady=5)

        ctk.CTkButton(
            input_frame, text=self.convert_button_label, command=self._on_convert
        ).pack(pady=5)

        # -- Output section --
        output_frame = ctk.CTkFrame(parent, corner_radius=10)
        output_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(output_frame, text=self.output_section_label, font=("Arial", 14)).pack(
            anchor="w", pady=5
        )
        self._output_text = ctk.CTkTextbox(output_frame, height=100)
        self._output_text.pack(fill="x", pady=5)

        # -- Action buttons --
        options_frame = ctk.CTkFrame(parent, corner_radius=10)
        options_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(
            options_frame, text="Capture from Webcam", command=self._on_webcam
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            options_frame, text="Select Image File", command=self._on_image_file
        ).pack(side="left", padx=10, pady=10)

    # ── Shared event handlers ──────────────────────────────────────
    def _on_convert(self) -> None:
        text = self._text_input.get("1.0", ctk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Input text is empty!")
            return
        result = self.convert(text)
        self._output_text.delete("1.0", ctk.END)
        self._output_text.insert(ctk.END, result)

    def _on_webcam(self) -> None:
        text = self._ocr.capture_from_webcam()
        if text:
            self._text_input.delete("1.0", ctk.END)
            self._text_input.insert(ctk.END, text)

    def _on_image_file(self) -> None:
        text = self._ocr.extract_from_image_file()
        if text:
            self._text_input.delete("1.0", ctk.END)
            self._text_input.insert(ctk.END, text)


# ══════════════════════════════════════════════════════════════════
# BrailleConverterFrame  –  concrete encoder
# ══════════════════════════════════════════════════════════════════
class BrailleConverterFrame(BaseConverterFrame):
    """
    Encodes Latin text to Unicode Braille.
    Maps are class-level constants (not rebuilt on every call –
    fixes the per-call dict construction in original Braille.py L8-22).
    """

    _BRAILLE_MAP: dict[str, str] = {
        'a': '\u2801', 'b': '\u2803', 'c': '\u2809', 'd': '\u2819', 'e': '\u2811',
        'f': '\u280B', 'g': '\u281B', 'h': '\u2813', 'i': '\u280A', 'j': '\u281A',
        'k': '\u2805', 'l': '\u2807', 'm': '\u280D', 'n': '\u281D', 'o': '\u2815',
        'p': '\u280F', 'q': '\u281F', 'r': '\u2817', 's': '\u280E', 't': '\u281E',
        'u': '\u2825', 'v': '\u2827', 'w': '\u283A', 'x': '\u282D', 'y': '\u283D',
        'z': '\u2835', ' ': ' ',
    }
    _NUMBER_PREFIX: str = '\u283C'
    _NUMBER_MAP: dict[str, str] = {
        '1': '\u2801', '2': '\u2803', '3': '\u2809', '4': '\u2819', '5': '\u2811',
        '6': '\u280B', '7': '\u281B', '8': '\u2813', '9': '\u280A', '0': '\u281A',
    }

    @property
    def convert_button_label(self) -> str:
        return "Convert to Braille"

    @property
    def output_section_label(self) -> str:
        return "Braille Output:"

    def convert(self, text: str) -> str:
        parts: list[str] = []
        for ch in text.lower():
            if ch.isdigit():
                parts.append(self._NUMBER_PREFIX + self._NUMBER_MAP[ch])
            else:
                parts.append(self._BRAILLE_MAP.get(ch, '?'))
        return ''.join(parts)


# ══════════════════════════════════════════════════════════════════
# MorseConverterFrame  –  concrete encoder
# ══════════════════════════════════════════════════════════════════
class MorseConverterFrame(BaseConverterFrame):
    """Encodes Latin text + digits to International Morse Code."""

    _MORSE_MAP: dict[str, str] = {
        'a': '.-',   'b': '-...',  'c': '-.-.',  'd': '-..',   'e': '.',
        'f': '..-.',  'g': '--.',   'h': '....',  'i': '..',    'j': '.---',
        'k': '-.-',   'l': '.-..',  'm': '--',    'n': '-.',    'o': '---',
        'p': '.--.',  'q': '--.-',  'r': '.-.',   's': '...',   't': '-',
        'u': '..-',   'v': '...-',  'w': '.--',   'x': '-..-',  'y': '-.--',
        'z': '--..',  '1': '.----', '2': '..---', '3': '...--', '4': '....-',
        '5': '.....', '6': '-....', '7': '--...', '8': '---..',  '9': '----.',
        '0': '-----', ' ': '/',
    }

    @property
    def convert_button_label(self) -> str:
        return "Convert to Morse"

    @property
    def output_section_label(self) -> str:
        return "Morse Output:"

    def convert(self, text: str) -> str:
        return ' '.join(self._MORSE_MAP.get(ch.lower(), '?') for ch in text)


# ══════════════════════════════════════════════════════════════════
# ConverterApp  –  application root
# Composes both panels into a tabbed window.
# ══════════════════════════════════════════════════════════════════
class ConverterApp:
    """
    Top-level application class.
    Owns the CTk root window and tab layout; delegates all domain
    logic entirely to the converter frame classes.
    """

    def __init__(self) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._root = ctk.CTk()
        self._root.title("Text Encoder – Braille & Morse")
        self._root.geometry("700x560")

        tab_view = ctk.CTkTabview(self._root)
        tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        BrailleConverterFrame(tab_view.add("🔡 Braille"))
        MorseConverterFrame(tab_view.add("📡 Morse Code"))

    def run(self) -> None:
        self._root.mainloop()


# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    ConverterApp().run()
