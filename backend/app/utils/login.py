"""Login (telefon yoki ism) ni solishtirish uchun normallashtirish.

"95 810 06 00", "+998 95 810-06-00", "958100600" — hammasi bitta login hisoblanadi.
Telefon bo'lmagan login (masalan, ism) katta-kichik harfga qaramay solishtiriladi.
"""
import re

_PHONE_CHARS = re.compile(r"^[\d\s+()\-]+$")


def normalize_login(value: str | None) -> str:
    v = (value or "").strip()
    if _PHONE_CHARS.match(v):
        digits = re.sub(r"\D", "", v)
        if len(digits) >= 9:
            return digits[-9:]
        return digits
    return re.sub(r"\s+", " ", v).lower()
