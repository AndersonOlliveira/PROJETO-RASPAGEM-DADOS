import unicodedata
from typing import Optional


def remover(texto: str) -> str:
    """Return ASCII-only version of texto by removing diacritics.

    If texto is empty or only whitespace, returns empty string.
    """
    if not isinstance(texto, str):
        texto = str(texto or "")

    if not texto.strip():
        return ""

    normalizado = unicodedata.normalize("NFKD", texto)
    return normalizado.encode("ascii", "ignore").decode("utf-8")


class texto:
    """Utility class for simple Unicode/ASCII text operations.

    All abstract/unimplemented behaviors are provided as concrete methods.
    """

    def __init__(self, value: Optional[str] = None):
        self.value = value or ""

    def set(self, value: Optional[str]) -> None:
        self.value = value or ""

    def get(self) -> str:
        return self.value

    def is_empty(self) -> bool:
        return not bool(self.value and self.value.strip())

    def remove_accents(self) -> str:
        """Return value with accents removed.

        Updates nothing; returns processed string.
        """
        return remover(self.value)

    def slug(self, sep: str = "-") -> str:
        """Return a URL/filename friendly slug from value.

        Example: 'Olá Mundo!' -> 'Ola-Mundo'
        """
        s = remover(self.value)
        # keep alnum and spaces, replace others with spaces
        cleaned = []
        for ch in s:
            if ch.isalnum():
                cleaned.append(ch)
            else:
                cleaned.append(" ")
        collapsed = " ".join("".join(cleaned).split())
        return collapsed.replace(" ", sep)

    def lower(self) -> str:
        return (self.value or "").lower()

    def upper(self) -> str:
        return (self.value or "").upper()

    def capitalize(self) -> str:
        return (self.value or "").capitalize()


