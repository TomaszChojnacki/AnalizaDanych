
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image


KATALOG_PROJEKTU = Path(__file__).resolve().parent.parent

ROZSZERZENIA = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}



def analizuj_zbior(nazwa_zbioru):
    """Analizuje oryginalne obrazy bez modyfikowania plików."""
    katalog = KATALOG_PROJEKTU / "dane" / nazwa_zbioru    # Określenie katalogu wybranego zbioru

    if not katalog.is_dir():     # Sprawdzenie istnienia zbioru
        raise FileNotFoundError(
            f"Nie znaleziono zbioru: {katalog}"
        )

    katalogi = { # Wyszukanie katalogów treningowych i testowych
        nazwa: katalog / nazwa
        for nazwa in ("train", "test")
        if (katalog / nazwa).is_dir()
    }

    if not katalogi: # Sprawdzenie struktury zbioru
        raise ValueError(
            "Zbiór musi zawierać katalog train lub test "
            "z podfolderami klas."
        )

    # Zmienne do przechowywania statystyk
    liczebnosc = {}
    formaty = Counter()
    szerokosci = []
    wysokosci = []
    bledne_pliki = []

    for podzbior, sciezka in katalogi.items(): # Przechodzenie przez zbiory train i test
        for katalog_klasy in sorted(sciezka.iterdir()): # Przechodzenie przez katalogi klas
            if not katalog_klasy.is_dir(): # Pominięcie elementów niebędących katalogami
                continue

            klasa = katalog_klasy.name # Pobranie nazwy klasy

            if klasa not in liczebnosc: # Inicjalizacja liczników dla nowej klasy
                liczebnosc[klasa] = {
                    "train": 0,
                    "test": 0
                }

            for plik in katalog_klasy.rglob("*"): # Przeszukiwanie plików danej klasy
                if not plik.is_file(): # Pominięcie katalogów
                    continue

                if plik.suffix.lower() not in ROZSZERZENIA: # Pominięcie nieobsługiwanych formatów
                    continue

                try:
                    with Image.open(plik) as obraz: # Sprawdzenie poprawności pliku obrazu
                        obraz.verify()

                    with Image.open(plik) as obraz: # Odczyt wymiarów i formatu obrazu
                        obraz.load()
                        szerokosc, wysokosc = obraz.size
                        format_obrazu = obraz.format

                    if szerokosc <= 0 or wysokosc <= 0: # Sprawdzenie poprawności wymiarów
                        raise ValueError(
                            "Nieprawidłowe wymiary."
                        )

                    liczebnosc[klasa][podzbior] += 1 # Zwiększenie licznika obrazów klasy

                    # Zapis wymiarów obrazu
                    szerokosci.append(szerokosc)
                    wysokosci.append(wysokosc)
                    formaty[format_obrazu or "Inny"] += 1 # Zwiększenie licznika danego formatu

                except Exception as blad:
                    bledne_pliki.append({ # Zapis informacji o błędnym pliku
                        "plik": str(plik),
                        "blad": str(blad)
                    })

    liczba_obrazow = sum(  # Obliczenie całkowitej liczby poprawnych obrazów
        sum(podzbiory.values())
        for podzbiory in liczebnosc.values()
    )

    if liczba_obrazow == 0: # Sprawdzenie, czy znaleziono poprawne obrazy
        raise ValueError(
            "Nie znaleziono poprawnych obrazów."
        )

    statystyki_klas = [] # Lista statystyk poszczególnych klas

    # Obliczanie liczebności i udziału każdej klasy
    for nazwa, wartosci in sorted(liczebnosc.items()):

        # Łączna liczba obrazów danej klasy
        razem = wartosci["train"] + wartosci["test"]

        # Dodanie statystyk klasy
        statystyki_klas.append({
            "klasa": nazwa,
            "train": wartosci["train"],
            "test": wartosci["test"],
            "razem": razem,
            "procent": round(
                razem / liczba_obrazow * 100, 2
            )
        })

    # Utworzenie raportu statystycznego
    raport = {
        "zbior": nazwa_zbioru,
        "liczba_klas": len(statystyki_klas),
        "liczba_obrazow": liczba_obrazow,
        "liczba_blednych": len(bledne_pliki),
        "klasy": statystyki_klas,
        "formaty": dict(formaty),

        # Średnie wymiary obrazów
        "srednia_szerokosc": round( sum(szerokosci) / liczba_obrazow, 2),
        "srednia_wysokosc": round(sum(wysokosci) / liczba_obrazow, 2),

        # Minimalne i maksymalne wymiary obrazów
        "minimalna_szerokosc": min(szerokosci),
        "maksymalna_szerokosc": max(szerokosci),
        "minimalna_wysokosc": min(wysokosci),
        "maksymalna_wysokosc": max(wysokosci)
    }

    # Utworzenie unikalnego identyfikatora raportu
    identyfikator = (
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_" + uuid4().hex[:6]
    )

    # Określenie katalogu zapisu wyników
    katalog_wynikow = (
        KATALOG_PROJEKTU
        / "wyniki"
        / nazwa_zbioru
        / f"statystyki_{identyfikator}"
    )

    # Utworzenie katalogu wynikowego
    katalog_wynikow.mkdir(parents=True,exist_ok=False)

    # Zapis raportu w formacie JSON
    with (katalog_wynikow / "raport.json").open(
        "w", encoding="utf-8"
    ) as plik:
        json.dump(raport, plik,indent=4,ensure_ascii=False)

    # Zapis liczebności klas do pliku CSV
    with (katalog_wynikow / "liczebnosc.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as plik:
        zapis = csv.DictWriter(
            plik,
            fieldnames=["klasa", "train", "test","razem", "procent"]
        )

        zapis.writeheader() # Zapis nagłówków kolumn
        zapis.writerows(statystyki_klas) # Zapis statystyk wszystkich klas



    # Zapis listy błędnych obrazów do pliku CSV
    with (katalog_wynikow / "bledne_pliki.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as plik:
        zapis = csv.DictWriter(plik,fieldnames=["plik", "blad"])
        zapis.writeheader() # Zapis nagłówków kolumn
        zapis.writerows(bledne_pliki) # Zapis informacji o błędnych plikach

    raport["katalog_wynikow"] = str(katalog_wynikow) # Dodanie ścieżki raportu do wyników

    return raport # Zwrócenie statystyk do interfejsu

