
import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont

from interfejs.okno_glowne import OknoGlowne


# Katalog glowny projektu
KATALOG_PROJEKTU = Path(__file__).resolve().parent


def uruchom_aplikacje():
    aplikacja = QApplication(sys.argv)

    # Styl graficzny aplikacji
    aplikacja.setStyle("Fusion")

    # Czcionka interfejsu
    czcionka = QFont("Segoe UI", 10)
    aplikacja.setFont(czcionka)

    try:
        # Utworzenie glownego okna
        okno = OknoGlowne()

        # Rozmiar poczatkowy okna
        okno.resize(1200, 800)

        # Minimalny rozmiar okna
        okno.setMinimumSize(950, 650)

        # Wyswietlenie aplikacji
        okno.show()

        # Uruchomienie petli zdarzen
        return aplikacja.exec()

    except Exception as blad:
        szczegoly = traceback.format_exc()
        print(szczegoly, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(uruchom_aplikacje())
