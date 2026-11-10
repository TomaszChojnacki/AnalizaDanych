
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
    if not katalog.is_dir():
        return []

    obrazy = []

    for plik in sorted(katalog.rglob("*")):
        if not plik.is_file():
            continue

        if plik.suffix.lower() not in ROZSZERZENIA:
            continue

        try:
            with Image.open(plik) as obraz:
                obraz.verify()
            obrazy.append(plik)
        except (OSError, ValueError, SyntaxError):
            print(f"Pominięto uszkodzony obraz: {plik}")

    return obrazy



def odczytaj_klasy(katalog):
    if not katalog.is_dir():
        return {}

    klasy = {}

    for folder in sorted(katalog.iterdir()):
        if folder.is_dir():
            obrazy = pobierz_obrazy(folder)
            if obrazy:
                klasy[folder.name] = obrazy

    return klasy



def sprawdz_przygotowane_dane(katalog):
    """Sprawdza kompletność danych dla YOLO."""
    katalog = Path(katalog)

    train = odczytaj_klasy(katalog / "train")
    val = odczytaj_klasy(katalog / "val")
    test = odczytaj_klasy(katalog / "test")

    if len(train) < 2:
        return False

    if set(train) != set(val):
        return False

    if not test or set(test) != set(train):
        return False

    return all(train[nazwa] and val[nazwa] for nazwa in train)


def kopiuj_obrazy(obrazy, zrodlo_klasy, cel):
    """Kopiuje obrazy, zachowując ich ścieżki względne."""
    cel.mkdir(parents=True, exist_ok=True)

    for obraz in obrazy:
        sciezka_wzgledna = obraz.relative_to(zrodlo_klasy)
        sciezka_docelowa = cel / sciezka_wzgledna

        sciezka_docelowa.parent.mkdir(
            parents=True, exist_ok=True
        )

        shutil.copy2(obraz, sciezka_docelowa)


def przygotuj_dane(nazwa_zbioru, komunikat=None):
    """
    Automatycznie przygotowuje dane do uczenia YOLO.

    Nie modyfikuje oryginalnych obrazów.
    """

    def informuj(tekst):
        if komunikat:
            komunikat(tekst)

    zrodlo = KATALOG_PROJEKTU / "dane" / nazwa_zbioru
    cel = (
        KATALOG_PROJEKTU
        / "dane_przetworzone"
        / nazwa_zbioru
    )

    if not zrodlo.is_dir():
        raise FileNotFoundError(
            f"Nie znaleziono zbioru: {zrodlo}"
        )

    # Ponowne wykorzystanie kompletnych danych
    if sprawdz_przygotowane_dane(cel):
        informuj("Dane są już przygotowane.")
        return cel

    informuj("Przygotowywanie zbioru danych...")

    katalog_train = zrodlo / "train"
    katalog_test = zrodlo / "test"
    katalog_val = zrodlo / "val"

    if katalog_train.is_dir():
        klasy = odczytaj_klasy(katalog_train)
    else:
        # Obsługa układu: zbior/klasa/obraz.jpg
        klasy = odczytaj_klasy(zrodlo)

    if len(klasy) < 2:
        raise ValueError(
            "Nie znaleziono co najmniej dwóch klas "
            "z poprawnymi obrazami."
        )

    oryginalny_test = odczytaj_klasy(katalog_test)
    oryginalna_val = odczytaj_klasy(katalog_val)

    ma_test = bool(oryginalny_test)
    ma_val = (
        bool(oryginalna_val)
        and set(oryginalna_val) == set(klasy)
    )

    if ma_test and set(oryginalny_test) != set(klasy):
        raise ValueError(
            "Klasy w oryginalnym train i test są różne."
        )

    generator = random.Random(42)

    # Najpierw przygotowujemy plan podziału
    plan = {}

    for nazwa, obrazy in klasy.items():
        obrazy = list(obrazy)
        generator.shuffle(obrazy)

        minimum = 1 + (not ma_val) + (not ma_test)

        if len(obrazy) < minimum:
            raise ValueError(
                f"Klasa '{nazwa}' ma za mało obrazów. "
                f"Wymagane minimum: {minimum}."
            )

        if ma_val:
            val = oryginalna_val[nazwa]
        else:
            liczba_val = max(1, round(len(obrazy) * 0.2))
            maks_val = len(obrazy) - 1 - (not ma_test)
            liczba_val = min(liczba_val, maks_val)

            val = obrazy[:liczba_val]
            obrazy = obrazy[liczba_val:]

        if ma_test:
            test = oryginalny_test[nazwa]
        else:
            liczba_test = max(1, round(len(obrazy) * 0.2))
            liczba_test = min(liczba_test, len(obrazy) - 1)

            test = obrazy[:liczba_test]
            obrazy = obrazy[liczba_test:]

        plan[nazwa] = {
            "train": obrazy,
            "val": val,
            "test": test
        }

    # Najpierw budujemy dane w katalogu tymczasowym.
    tymczasowy = (
        cel.parent
        / f".{nazwa_zbioru}_tmp_{uuid4().hex[:8]}"
    )

    tymczasowy.mkdir(parents=True, exist_ok=False)

    try:
        for nazwa, podzbiory in plan.items():
            for podzbior, obrazy in podzbiory.items():
                if podzbior == "test" and ma_test:
                    katalog_zrodlowy = katalog_test / nazwa
                elif podzbior == "val" and ma_val:
                    katalog_zrodlowy = katalog_val / nazwa
                else:
                    katalog_zrodlowy = (
                        katalog_train / nazwa
                        if katalog_train.is_dir()
                        else zrodlo / nazwa
                    )

                katalog_docelowy = (
                    tymczasowy / podzbior / nazwa
                )

                kopiuj_obrazy(
                    obrazy,
                    katalog_zrodlowy,
                    katalog_docelowy
                )

                informuj(
                    f"{podzbior}/{nazwa}: {len(obrazy)} obrazów"
                )

        if not sprawdz_przygotowane_dane(tymczasowy):
            raise RuntimeError(
                "Nie udało się poprawnie przygotować danych."
            )

        # Zachowujemy poprzedni niekompletny katalog
        # zamiast usuwać jego zawartość.
        poprzedni = None

        if cel.exists():
            poprzedni = (
                cel.parent
                / f".{nazwa_zbioru}_poprzednie_{uuid4().hex[:8]}"
            )
            cel.rename(poprzedni)

        try:
            tymczasowy.rename(cel)
        except Exception:
            if poprzedni is not None:
                poprzedni.rename(cel)
            raise

    finally:
        if tymczasowy.exists():
            shutil.rmtree(tymczasowy)

    informuj("Dane zostały przygotowane poprawnie.")
    informuj(f"Katalog: {cel}")

    return cel
