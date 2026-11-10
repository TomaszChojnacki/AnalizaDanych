
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image


KATALOG_PROJEKTU = Path(__file__).resolve().parent.parent

ROZSZERZENIA = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


def analizuj_zbior(nazwa_zbioru):
    """Analizuje oryginalne obrazy bez modyfikowania plikow."""

    katalog = KATALOG_PROJEKTU / "dane" / nazwa_zbioru

    if not katalog.is_dir():
        raise FileNotFoundError(
            f"Nie znaleziono zbioru: {katalog}"
        )

    katalogi = {
        nazwa: katalog / nazwa
        for nazwa in ("train", "test")
        if (katalog / nazwa).is_dir()
    }

    if not katalogi:
        raise ValueError(
            "Zbiór musi zawierać katalog train lub test "
            "z podfolderami klas."
        )

    liczebnosc = {}
    formaty = Counter()
    szerokosci = []
    wysokosci = []
    bledne_pliki = []

    for podzbior, sciezka in katalogi.items():
        for katalog_klasy in sorted(sciezka.iterdir()):
            if not katalog_klasy.is_dir():
                continue

            klasa = katalog_klasy.name

            if klasa not in liczebnosc:
                liczebnosc[klasa] = {
                    "train": 0,
                    "test": 0
                }

            for plik in katalog_klasy.rglob("*"):
                if not plik.is_file():
                    continue

                if plik.suffix.lower() not in ROZSZERZENIA:
                    continue

                try:
                    with Image.open(plik) as obraz:
                        obraz.verify()

                    with Image.open(plik) as obraz:
                        obraz.load()
                        szerokosc, wysokosc = obraz.size
                        format_obrazu = obraz.format

                    if szerokosc <= 0 or wysokosc <= 0:
                        raise ValueError(
                            "Nieprawidłowe wymiary."
                        )

                    liczebnosc[klasa][podzbior] += 1
                    szerokosci.append(szerokosc)
                    wysokosci.append(wysokosc)
                    formaty[format_obrazu or "Inny"] += 1

                except Exception as blad:
                    bledne_pliki.append({
                        "plik": str(plik),
                        "blad": str(blad)
                    })

    liczba_obrazow = sum(
        sum(podzbiory.values())
        for podzbiory in liczebnosc.values()
    )

    if liczba_obrazow == 0:
        raise ValueError(
            "Nie znaleziono poprawnych obrazów."
        )

    statystyki_klas = []

    for nazwa, wartosci in sorted(liczebnosc.items()):
        razem = wartosci["train"] + wartosci["test"]

        statystyki_klas.append({
            "klasa": nazwa,
            "train": wartosci["train"],
            "test": wartosci["test"],
            "razem": razem,
            "procent": round(
                razem / liczba_obrazow * 100, 2
            )
        })

    raport = {
        "zbior": nazwa_zbioru,
        "liczba_klas": len(statystyki_klas),
        "liczba_obrazow": liczba_obrazow,
        "liczba_blednych": len(bledne_pliki),
        "klasy": statystyki_klas,
        "formaty": dict(formaty),
        "srednia_szerokosc": round(
            sum(szerokosci) / liczba_obrazow, 2
        ),
        "srednia_wysokosc": round(
            sum(wysokosci) / liczba_obrazow, 2
        ),
        "minimalna_szerokosc": min(szerokosci),
        "maksymalna_szerokosc": max(szerokosci),
        "minimalna_wysokosc": min(wysokosci),
        "maksymalna_wysokosc": max(wysokosci)
    }

    identyfikator = (
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_" + uuid4().hex[:6]
    )

    katalog_wynikow = (
        KATALOG_PROJEKTU
        / "wyniki"
        / nazwa_zbioru
        / f"statystyki_{identyfikator}"
    )

    katalog_wynikow.mkdir(
        parents=True,
        exist_ok=False
    )

    with (katalog_wynikow / "raport.json").open(
        "w", encoding="utf-8"
    ) as plik:
        json.dump(
            raport, plik,
            indent=4,
            ensure_ascii=False
        )

    with (katalog_wynikow / "liczebnosc.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as plik:
        zapis = csv.DictWriter(
            plik,
            fieldnames=[
                "klasa", "train", "test",
                "razem", "procent"
            ]
        )
        zapis.writeheader()
        zapis.writerows(statystyki_klas)

    with (katalog_wynikow / "bledne_pliki.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as plik:
        zapis = csv.DictWriter(
            plik,
            fieldnames=["plik", "blad"]
        )
        zapis.writeheader()
        zapis.writerows(bledne_pliki)

    raport["katalog_wynikow"] = str(katalog_wynikow)

    return raport
