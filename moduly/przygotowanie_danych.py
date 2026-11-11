
import random
import shutil
from pathlib import Path
from uuid import uuid4

from PIL import Image


KATALOG_PROJEKTU = Path(__file__).resolve().parent.parent

ROZSZERZENIA = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}



def pobierz_obrazy(katalog):
    """Zwraca listę poprawnych obrazów z katalogu."""

    if not katalog.is_dir():                        # Sprawdzenie istnienia katalogu
        return []

    obrazy = []                                     # Lista poprawnych obrazów

    for plik in sorted(katalog.rglob("*")):         # Przeszukiwanie katalogu i podkatalogów
        if not plik.is_file():                      # Pominięcie elementów niebędących plikami
            continue

        if plik.suffix.lower() not in ROZSZERZENIA: # Sprawdzenie obsługiwanego formatu obrazu
            continue

        try:
            with Image.open(plik) as obraz:         # Sprawdzenie poprawności pliku graficznego
                obraz.verify()

            obrazy.append(plik)                     # Dodanie poprawnego obrazu do listy

        except (OSError, ValueError, SyntaxError): # Pominięcie uszkodzonego obrazu
            print(f"Pominięto uszkodzony obraz: {plik}")

    return obrazy     # Zwrócenie listy poprawnych obrazów





def odczytaj_klasy(katalog):

    if not katalog.is_dir():                 # Sprawdzenie istnienia katalogu
        return {}

    klasy = {}                               # Słownik przechowujący klasy i ich obrazy

    for folder in sorted(katalog.iterdir()): # Przechodzenie przez foldery poszczególnych klas
        if folder.is_dir():                 # Sprawdzenie, czy element jest katalogiem
            obrazy = pobierz_obrazy(folder) # Pobranie poprawnych obrazów danej klasy

            if obrazy:                      # Dodanie klasy, jeśli zawiera poprawne obrazy
                klasy[folder.name] = obrazy

    return klasy                            # Zwrócenie słownika klas i przypisanych obrazów





def sprawdz_przygotowane_dane(katalog):
    """Sprawdza kompletność danych dla YOLO."""
    katalog = Path(katalog)                 # Zamiana ścieżki na obiekt Path

    train = odczytaj_klasy(katalog / "train") # Pobranie klas ze zbiorów train, val i test
    val = odczytaj_klasy(katalog / "val")
    test = odczytaj_klasy(katalog / "test")

    if len(train) < 2:                          # Sprawdzenie minimalnej liczby klas treningowych
        return False

    if set(train) != set(val):                   # Sprawdzenie zgodności klas treningowych i walidacyjnych
        return False

    if not test or set(test) != set(train):     # Sprawdzenie obecności testu i zgodności klas
        return False

    return all(train[nazwa] and val[nazwa] for nazwa in train) # Sprawdzenie, czy każda klasa train i val zawiera obrazy




def kopiuj_obrazy(obrazy, zrodlo_klasy, cel):
    """Kopiuje obrazy, zachowując ich ścieżki względne."""
    cel.mkdir(parents=True, exist_ok=True)          # Utworzenie katalogu docelowego

    for obraz in obrazy:     # Przechodzenie przez wszystkie obrazy
        sciezka_wzgledna = obraz.relative_to(zrodlo_klasy)         # Pobranie ścieżki względem katalogu źródłowego
        sciezka_docelowa = cel / sciezka_wzgledna                   # Utworzenie ścieżki docelowej obrazu
        sciezka_docelowa.parent.mkdir(parents=True, exist_ok=True)    # Utworzenie wymaganych podkatalogów
        shutil.copy2(obraz, sciezka_docelowa)                       # Skopiowanie obrazu z zachowaniem metadanych




def przygotuj_dane(nazwa_zbioru, komunikat=None):
    """
    Automatycznie przygotowuje dane do uczenia YOLO.
    Nie modyfikuje oryginalnych obrazów.
    """

    def informuj(tekst):                # Funkcja przekazująca komunikaty do interfejsu
        if komunikat:
            komunikat(tekst)

    zrodlo = KATALOG_PROJEKTU / "dane" / nazwa_zbioru # Określenie katalogu oryginalnych danych

    cel = (                         # Określenie katalogu danych przetworzonych
        KATALOG_PROJEKTU
        / "dane_przetworzone"
        / nazwa_zbioru
    )

    if not zrodlo.is_dir():                     # Sprawdzenie istnienia zbioru źródłowego
        raise FileNotFoundError(
            f"Nie znaleziono zbioru: {zrodlo}"
        )

    if sprawdz_przygotowane_dane(cel):          # Ponowne wykorzystanie przygotowanych danych
        informuj("Dane są już przygotowane.")
        return cel

    informuj("Przygotowywanie zbioru danych...")

    katalog_train = zrodlo / "train"                # Ścieżki do oryginalnych podzbiorów
    katalog_test = zrodlo / "test"
    katalog_val = zrodlo / "val"

    if katalog_train.is_dir():                      # Odczyt klas z katalogu treningowego
        klasy = odczytaj_klasy(katalog_train)
    else:
        klasy = odczytaj_klasy(zrodlo)              # Obsługa układu: zbior/klasa/obraz.jpg

    if len(klasy) < 2:                              # Sprawdzenie minimalnej liczby klas
        raise ValueError(
            "Nie znaleziono co najmniej dwóch klas "
            "z poprawnymi obrazami."
        )

    oryginalny_test = odczytaj_klasy(katalog_test)     # Odczyt istniejących zbiorów testowego i walidacyjnego
    oryginalna_val = odczytaj_klasy(katalog_val)

    ma_test = bool(oryginalny_test)              # Sprawdzenie dostępności zbiorów test i val
    ma_val = (
        bool(oryginalna_val)
        and set(oryginalna_val) == set(klasy)
    )

    if ma_test and set(oryginalny_test) != set(klasy):     # Sprawdzenie zgodności klas treningowych i testowych
        raise ValueError(
            "Klasy w oryginalnym train i test są różne."
        )

    generator = random.Random(42)           # Utworzenie generatora losowego z ustalonym ziarnem
    plan = {}                           # Słownik przechowujący plan podziału danych

    for nazwa, obrazy in klasy.items():         # Przetwarzanie każdej klasy osobno
        obrazy = list(obrazy)               # Kopiowanie i losowe mieszanie listy obrazów
        generator.shuffle(obrazy)

        minimum = 1 + (not ma_val) + (not ma_test) # Minimalna liczba obrazów potrzebna do podziału

        if len(obrazy) < minimum:           # Sprawdzenie liczebności klasy
            raise ValueError(
                f"Klasa '{nazwa}' ma za mało obrazów. "
                f"Wymagane minimum: {minimum}."
            )

        if ma_val:                          # Wykorzystanie istniejącego zbioru walidacyjnego
            val = oryginalna_val[nazwa]

        else:
            liczba_val = max(                   # Wyznaczenie 20% obrazów do walidacji
                1,
                round(len(obrazy) * 0.2)
            )

            maks_val = len(obrazy) - 1 - (not ma_test) # Pozostawienie obrazów dla pozostałych podzbiorów
            liczba_val = min(liczba_val, maks_val)
            val = obrazy[:liczba_val]             # Podział na walidację i pozostałe obrazy
            obrazy = obrazy[liczba_val:]

        if ma_test:                             # Wykorzystanie istniejącego zbioru testowego
            test = oryginalny_test[nazwa]

        else:
            liczba_test = max(                  # Wyznaczenie 20% pozostałych obrazów do testowania
                1,
                round(len(obrazy) * 0.2)
            )

            liczba_test = min(              # Pozostawienie co najmniej jednego obrazu do treningu
                liczba_test,
                len(obrazy) - 1
            )

            test = obrazy[:liczba_test]             # Podział na test i trening
            obrazy = obrazy[liczba_test:]

        plan[nazwa] = {                         # Zapis planu podziału dla danej klasy
            "train": obrazy,
            "val": val,
            "test": test
        }

    tymczasowy = (                           # Utworzenie unikalnej ścieżki katalogu tymczasowego
        cel.parent
        / f".{nazwa_zbioru}_tmp_{uuid4().hex[:8]}"
    )


    tymczasowy.mkdir(parents=True,exist_ok=False)     # Utworzenie katalogu tymczasowego

    try:
        for nazwa, podzbiory in plan.items():         # Przechodzenie przez klasy i podzbiory
            for podzbior, obrazy in podzbiory.items():

                if podzbior == "test" and ma_test:                 # Wybór katalogu źródłowego dla testu
                    katalog_zrodlowy = katalog_test / nazwa

                elif podzbior == "val" and ma_val:                 # Wybór katalogu źródłowego dla walidacji
                    katalog_zrodlowy = katalog_val / nazwa

                else:
                    katalog_zrodlowy = ( # Pobranie obrazów z katalogu treningowego
                        katalog_train / nazwa
                        if katalog_train.is_dir()
                        else zrodlo / nazwa
                    )

                katalog_docelowy = (tymczasowy / podzbior / nazwa)    # Określenie katalogu docelowego
                kopiuj_obrazy(obrazy,katalog_zrodlowy,katalog_docelowy) # Kopiowanie obrazów do odpowiedniego podzbioru
                informuj(f"{podzbior}/{nazwa}: {len(obrazy)} obrazów") # Wyświetlenie liczby skopiowanych obrazów


        if not sprawdz_przygotowane_dane(tymczasowy):         # Sprawdzenie poprawności przygotowanych danych
            raise RuntimeError("Nie udało się poprawnie przygotować danych.")

        poprzedni = None         # Zmienna przechowująca ścieżkę poprzednich danych

        if cel.exists():         # Zachowanie poprzedniego niekompletnego katalogu
            poprzedni = (cel.parent/ f".{nazwa_zbioru}_poprzednie_{uuid4().hex[:8]}")

            cel.rename(poprzedni)           # Zmiana nazwy poprzedniego katalogu

        try:
            tymczasowy.rename(cel)             # Przeniesienie przygotowanych danych do katalogu docelowego

        except Exception:
            if poprzedni is not None: # Przywrócenie poprzednich danych w razie błędu
                poprzedni.rename(cel)
            raise

    finally:
        if tymczasowy.exists():             # Usunięcie pozostałości katalogu tymczasowego
            shutil.rmtree(tymczasowy)

    informuj("Dane zostały przygotowane poprawnie.")     # Informacja o poprawnym przygotowaniu danych
    informuj(f"Katalog: {cel}")

    return cel     # Zwrócenie ścieżki do przygotowanego zbioru

