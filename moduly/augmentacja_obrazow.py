
import hashlib
import json
import random
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image, ImageEnhance

from moduly.przygotowanie_danych import przygotuj_dane


KATALOG_PROJEKTU = Path(__file__).resolve().parent.parent

ROZSZERZENIA = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}

METODY = {
    "Obrót",
    "Skalowanie",
    "Przesunięcie",
    "Zmiana kolorów",
    "Szum gaussowski",
    "Wszystkie metody"
}


def zmodyfikuj_obraz(obraz, metoda, generator):
    """
    Zwraca nowy obraz po wybranej transformacji.
    Nie modyfikuje oryginalnego pliku.
    """
    obraz = obraz.convert("RGB")
    szerokosc, wysokosc = obraz.size

    if metoda == "Wszystkie metody":
        metody = [
            "Obrót",
            "Skalowanie",
            "Przesunięcie",
            "Zmiana kolorów",
            "Szum gaussowski"
        ]

        generator.shuffle(metody)

        # Losowa kombinacja od 2 do 4 transformacji
        liczba = generator.randint(2, 4)

        for wybrana in metody[:liczba]:
            obraz = zmodyfikuj_obraz(
                obraz, wybrana, generator
            )

        return obraz

    if metoda == "Obrót":
        kat = generator.uniform(-15, 15)

        return obraz.rotate(
            kat,
            resample=Image.Resampling.BICUBIC,
            fillcolor=(128, 128, 128)
        )

    if metoda == "Skalowanie":
        skala = generator.uniform(0.85, 1.15)

        odwrotnosc = 1.0 / skala
        przesuniecie_x = (
            szerokosc * (1 - odwrotnosc) / 2
        )
        przesuniecie_y = (
            wysokosc * (1 - odwrotnosc) / 2
        )

        return obraz.transform(
            obraz.size,
            Image.Transform.AFFINE,
            (
                odwrotnosc, 0, przesuniecie_x,
                0, odwrotnosc, przesuniecie_y
            ),
            resample=Image.Resampling.BICUBIC,
            fillcolor=(128, 128, 128)
        )

    if metoda == "Przesunięcie":
        dx = generator.randint(
            -int(szerokosc * 0.1),
            int(szerokosc * 0.1)
        )
        dy = generator.randint(
            -int(wysokosc * 0.1),
            int(wysokosc * 0.1)
        )

        return obraz.transform(
            obraz.size,
            Image.Transform.AFFINE,
            (1, 0, -dx, 0, 1, -dy),
            resample=Image.Resampling.BICUBIC,
            fillcolor=(128, 128, 128)
        )

    if metoda == "Zmiana kolorów":
        obraz = ImageEnhance.Brightness(
            obraz
        ).enhance(generator.uniform(0.8, 1.2))

        obraz = ImageEnhance.Contrast(
            obraz
        ).enhance(generator.uniform(0.8, 1.2))

        return ImageEnhance.Color(
            obraz
        ).enhance(generator.uniform(0.7, 1.3))

    if metoda == "Szum gaussowski":
        tablica = np.asarray(
            obraz, dtype=np.float32
        )

        ziarno = generator.randrange(2**32)
        generator_numpy = np.random.default_rng(ziarno)

        szum = generator_numpy.normal(
            loc=0,
            scale=12,
            size=tablica.shape
        )

        wynik = np.clip(
            tablica + szum, 0, 255
        ).astype(np.uint8)

        return Image.fromarray(wynik)

    raise ValueError(
        f"Nieznana metoda augmentacji: {metoda}"
    )


def pobierz_obrazy(katalog):
    return sorted(
        plik for plik in katalog.rglob("*")
        if plik.is_file()
        and plik.suffix.lower() in ROZSZERZENIA
    )


def przygotuj_przyklady(obrazy_klas, katalog_raportu, metoda):
    """
    Przygotowuje tabelę porównawczą augmentacji.

    Dla każdej klasy losuje jeden obraz i stosuje
    do niego wszystkie wybrane transformacje.
    """

    wszystkie_metody = [
        "Obrót",
        "Skalowanie",
        "Przesunięcie",
        "Zmiana kolorów",
        "Szum gaussowski",
        "Wszystkie metody"
    ]

    if metoda == "Wszystkie metody":
        metody_podgladu = wszystkie_metody
    else:
        metody_podgladu = [metoda]

    katalog_przykladow = (
        katalog_raportu / "przyklady"
    )
    katalog_przykladow.mkdir(
        parents=True, exist_ok=True
    )

    wynik = []

    for numer_klasy, (nazwa_klasy, obrazy) in enumerate(
        sorted(obrazy_klas.items())
    ):
        if not obrazy:
            continue

        # Jeden losowy obraz z danej klasy
        generator_wyboru = random.Random(
            42 + numer_klasy
        )

        wybrany_obraz = generator_wyboru.choice(
            obrazy
        )

        katalog_klasy = (
            katalog_przykladow / nazwa_klasy
        )
        katalog_klasy.mkdir(
            parents=True, exist_ok=True
        )

        with Image.open(wybrany_obraz) as plik:
            oryginal = plik.convert("RGB")

        # Pierwsza kolumna - oryginal
        sciezka_oryginalu = (
            katalog_klasy / "oryginal.jpg"
        )
        oryginal.save(
            sciezka_oryginalu,
            quality=95
        )

        przyklady = {
            "Oryginał": str(sciezka_oryginalu)
        }

        # Kolejne kolumny - transformacje tego samego obrazu
        for numer_metody, nazwa_metody in enumerate(
            metody_podgladu
        ):
            generator = random.Random(
                1000 + numer_klasy * 100 + numer_metody
            )

            zmieniony = zmodyfikuj_obraz(
                oryginal.copy(),
                nazwa_metody,
                generator
            )

            nazwa_pliku = (
                f"metoda_{numer_metody + 1}.jpg"
            )

            sciezka_zmienionego = (
                katalog_klasy / nazwa_pliku
            )

            zmieniony.save(
                sciezka_zmienionego,
                quality=95
            )

            przyklady[nazwa_metody] = str(
                sciezka_zmienionego
            )

        wynik.append({
            "klasa": nazwa_klasy,
            "plik_zrodlowy": str(wybrany_obraz),
            "obrazy": przyklady
        })

    return {
        "metody": ["Oryginał"] + metody_podgladu,
        "wiersze": wynik
    }


def wykonaj_augmentacje(
    nazwa_zbioru,
    metoda="Wszystkie metody",
    liczba_kopii=2,
    komunikat=None,
    postep=None
):
    """
    Tworzy osobny wariant danych do treningu YOLO.

    - Zachowuje oryginalne dane.
    - Augmentuje tylko train.
    - Zachowuje val i test bez transformacji.
    - Tworzy raport porównawczy.
    """

    if metoda not in METODY:
        raise ValueError("Nieprawidłowa metoda augmentacji.")

    if not 1 <= liczba_kopii <= 10:
        raise ValueError(
            "Liczba kopii musi wynosić od 1 do 10."
        )

    def informuj(tekst):
        if komunikat:
            komunikat(tekst)

    # Automatyczne przygotowanie train/val/test
    zrodlo = przygotuj_dane(
        nazwa_zbioru,
        komunikat=informuj
    )

    katalog_train = zrodlo / "train"

    klasy = sorted(
        folder for folder in katalog_train.iterdir()
        if folder.is_dir()
    )

    obrazy_klas = {
        folder.name: pobierz_obrazy(folder)
        for folder in klasy
    }

    obrazy_klas = {
        nazwa: obrazy
        for nazwa, obrazy in obrazy_klas.items()
        if obrazy
    }

    if len(obrazy_klas) < 2:
        raise ValueError(
            "Zbiór musi mieć co najmniej dwie klasy."
        )

    liczba_zrodel = sum(
        len(obrazy) for obrazy in obrazy_klas.values()
    )

    identyfikator = (
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_" + uuid4().hex[:6]
    )

    nazwa_wariantu = f"augmentacja_{identyfikator}"

    # Każdy wariant ma osobny katalog
    katalog_wariantu = (
        KATALOG_PROJEKTU
        / "dane_przetworzone"
        / nazwa_zbioru
        / "warianty"
        / nazwa_wariantu
    )

    katalog_raportu = (
        KATALOG_PROJEKTU
        / "wyniki"
        / nazwa_zbioru
        / nazwa_wariantu
    )

    katalog_wariantu.mkdir(parents=True)
    katalog_raportu.mkdir(parents=True)

    generator = random.Random(42)
    przetworzono = 0
    statystyki = []
    przyklad = None

    try:
        for nazwa_klasy, obrazy in obrazy_klas.items():
            zrodlo_klasy = katalog_train / nazwa_klasy
            cel_klasy = (
                katalog_wariantu / "train" / nazwa_klasy
            )

            for plik in obrazy:
                sciezka_wzgledna = plik.relative_to(
                    zrodlo_klasy
                )

                cel_oryginalu = (
                    cel_klasy / sciezka_wzgledna
                )
                cel_oryginalu.parent.mkdir(
                    parents=True, exist_ok=True
                )

                shutil.copy2(plik, cel_oryginalu)

                with Image.open(plik) as oryginal:
                    oryginal = oryginal.convert("RGB")
                    for numer in range(1, liczba_kopii + 1):
                        nowy = zmodyfikuj_obraz(
                            oryginal, metoda, generator
                        )

                        identyfikator_pliku = (
                            hashlib.sha256(
                                str(sciezka_wzgledna).encode(
                                    "utf-8"
                                )
                            ).hexdigest()[:12]
                        )

                        nazwa_pliku = (
                            f"aug_{numer}_"
                            f"{identyfikator_pliku}.jpg"
                        )

                        cel_nowego = (
                            cel_klasy
                            / "_augmentowane"
                            / nazwa_pliku
                        )
                        cel_nowego.parent.mkdir(
                            parents=True, exist_ok=True
                        )

                        nowy.save(
                            cel_nowego,
                            format="JPEG",
                            quality=92
                        )

                        if przyklad is None:
                            przyklad = {
                                "oryginal": str(plik),
                                "augmentowany": str(cel_nowego)
                            }

                przetworzono += 1

                if postep:
                    postep(
                        int(przetworzono / liczba_zrodel * 100)
                    )

            przed = len(obrazy)

            statystyki.append({
                "klasa": nazwa_klasy,
                "przed": przed,
                "po": przed * (liczba_kopii + 1)
            })

            informuj(
                f"{nazwa_klasy}: "
                f"{przed} → "
                f"{przed * (liczba_kopii + 1)} obrazów"
            )

        # Walidacja i test pozostają bez augmentacji
        for podzbior in ("val", "test"):
            shutil.copytree(
                zrodlo / podzbior,
                katalog_wariantu / podzbior
            )



        # Przygotowanie porownania obrazow dla kazdej klasy
        informuj("Generowanie tabeli przykładów augmentacji...")

        przyklady_augmentacji = przygotuj_przyklady(
            obrazy_klas=obrazy_klas,
            katalog_raportu=katalog_raportu,
            metoda=metoda
        )


        raport = {
            "zbior": nazwa_zbioru,
            "metoda": metoda,
            "liczba_kopii": liczba_kopii,
            "klasy": statystyki,
            "liczba_przed": sum(rekord["przed"] for rekord in statystyki),
            "liczba_po": sum(rekord["po"] for rekord in statystyki),
            "przyklad": przyklad,
            "przyklady_augmentacji": przyklady_augmentacji,
            "katalog_danych": str(katalog_wariantu),
            "katalog_raportu": str(katalog_raportu)
        }



        with (
            katalog_raportu / "raport.json"
        ).open("w", encoding="utf-8") as plik:
            json.dump(
                raport,
                plik,
                ensure_ascii=False,
                indent=4
            )

        informuj("Augmentacja zakończona pomyślnie.")
        return raport

    except Exception:
        # Usuwamy tylko nieukończony wariant,
        # nigdy dane oryginalne ani bazowe.
        shutil.rmtree(
            katalog_wariantu, ignore_errors=True
        )
        shutil.rmtree(
            katalog_raportu, ignore_errors=True
        )
        raise
