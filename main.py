
import sys
import traceback
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from interfejs.okno_glowne import OknoGlowne

KATALOG_PROJEKTU = Path(__file__).resolve().parent # Katalog glowny projektu

def uruchom_aplikacje():
    aplikacja = QApplication(sys.argv)
    aplikacja.setStyle("Fusion")     # Styl graficzny aplikacji

    czcionka = QFont("Segoe UI", 10)     # Czcionka interfejsu
    aplikacja.setFont(czcionka)

    try:
        okno = OknoGlowne()        # Utworzenie glownego okna
        okno.resize(1200, 800)        # Rozmiar poczatkowy okna
        okno.setMinimumSize(950, 650)         # Minimalny rozmiar okna
        okno.show()         # Wyswietlenie aplikacji

        return aplikacja.exec()         # Uruchomienie petli zdarzen

    except Exception as blad:
        szczegoly = traceback.format_exc()
        print(szczegoly, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(uruchom_aplikacje())
