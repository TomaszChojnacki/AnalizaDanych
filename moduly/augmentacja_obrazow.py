
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

ROZSZERZENIA = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

METODY = {
    "Obrót",
    "Skalowanie",
    "Przesunięcie",
    "Zmiana kolorów",
    "Szum gaussowski",
    "Wszystkie metody"
}



def sprawdz_ustawienia(ustawienia):
    """Kontroluje parametry augmentacji."""

    if not (
        0.5 <= ustawienia["skala_min"]
        <= ustawienia["skala_max"] <= 2.0
    ):
        raise ValueError(
            "Skala minimalna musi być mniejsza lub równa "
            "maksymalnej. Dozwolony zakres: 0.5–2.0."
        )

    zakresy = {
        "kat_obrotu": (0, 90),
        "przesuniecie": (0, 40),
        "jasnosc": (0, 60),
        "kontrast": (0, 60),
        "nasycenie": (0, 60),
        "szum": (0, 60)
    }

    for nazwa, (minimum, maksimum) in zakresy.items():
        wartosc = ustawienia[nazwa]

        if not minimum <= wartosc <= maksimum:
            raise ValueError(
                f"Nieprawidłowa wartość: {nazwa}."
            )


def zmodyfikuj_obraz(
    obraz,
    metoda,
    generator,
    ustawienia=None
):
    """
    Wykonuje wybraną augmentację obrazu
    z parametrami ustawionymi przez użytkownika.
    """

    if ustawienia is None:
        ustawienia = {
            "kat_obrotu": 15,
            "skala_min": 0.85,
            "skala_max": 1.15,
            "przesuniecie": 10,
            "jasnosc": 20,
            "kontrast": 20,
            "nasycenie": 30,
            "szum": 12
        }

    sprawdz_ustawienia(ustawienia)

    obraz = obraz.convert("RGB")
    szerokosc, wysokosc = obraz.size

    # KOMBINACJA METOD
    if metoda == "Wszystkie metody":
        metody = [
            "Obrót",
            "Skalowanie",
            "Przesunięcie",
            "Zmiana kolorów",
            "Szum gaussowski"
        ]

        generator.shuffle(metody)
        liczba_metod = generator.randint(2, 4)

        for wybrana in metody[:liczba_metod]:
            obraz = zmodyfikuj_obraz(
                obraz,
                wybrana,
                generator,
                ustawienia
            )

        return obraz

    # OBRÓT ----------------------------------------------------------------
    if metoda == "Obrót":
        kat = generator.uniform(
            -ustawienia["kat_obrotu"],
            ustawienia["kat_obrotu"]
        )

        return obraz.rotate(
            kat,
            resample=Image.Resampling.BICUBIC, #służy do zmiany częstotliwości próbkowania szeregów czasowych
            fillcolor=(128, 128, 128) #do ustawiania koloru wypełnienia rysowanych kształtów
        )

    # SKALOWANIE ----------------------------------------------------------------
    if metoda == "Skalowanie":
        # Losowanie współczynnika skalowania
        skala = generator.uniform(
            ustawienia["skala_min"],
            ustawienia["skala_max"]
        )
        odwrotnosc = 1.0 / skala   # Obliczenie odwrotności skali

        przesuniecie_x = (         # Wyśrodkowanie obrazu w poziomie
                szerokosc * (1 - odwrotnosc) / 2
        )

        przesuniecie_y = (         # Wyśrodkowanie obrazu w pionie
                wysokosc * (1 - odwrotnosc) / 2
        )

        # Skalowanie z zachowaniem wymiarów obrazu
        return obraz.transform(obraz.size,Image.Transform.AFFINE,
            (
                odwrotnosc, 0, przesuniecie_x,
                0, odwrotnosc, przesuniecie_y
            ),
            resample=Image.Resampling.BICUBIC,  # Interpolacja pikseli do zmiany częstotliwości próbkowania szeregów czasowych
            fillcolor=(128, 128, 128)  # Szare wypełnienie
        )

    # PRZESUNIĘCIE ----------------------------------------------------------------
    if metoda == "Przesunięcie":
        udzial = ustawienia["przesuniecie"] / 100 # Zamiana procentów na wartość dziesiętną

        max_dx = int(szerokosc * udzial) # Obliczenie maksymalnego przesunięcia w pikselach
        max_dy = int(wysokosc * udzial)
        dx = generator.randint(-max_dx, max_dx)  # Losowanie przesunięcia w poziomie i pionie
        dy = generator.randint(-max_dy, max_dy)

        # Przesunięcie obrazu z zachowaniem jego wymiarów
        return obraz.transform(obraz.size,Image.Transform.AFFINE,(1, 0, -dx, 0, 1, -dy),  # Macierz przesunięcia
            resample=Image.Resampling.BICUBIC,  # Interpolacja pikseli do zmiany częstotliwości próbkowania szeregów czasowych
            fillcolor=(128, 128, 128)  # Szare wypełnienie
        )

    # ZMIANA KOLORÓW ----------------------------------------------------------------
    if metoda == "Zmiana kolorów":
        jasnosc = ustawienia["jasnosc"] / 100 # Zamiana procentów na wartości dziesiętne
        kontrast = ustawienia["kontrast"] / 100
        nasycenie = ustawienia["nasycenie"] / 100

        #Losowa Zmiana bo ustawiamy maksymalny zakres zmiany, a nie konkretną wartość, która ma zostać zastosowana dla:
        # jasności
        obraz = ImageEnhance.Brightness(obraz
        ).enhance(
            generator.uniform(
                1 - jasnosc,
                1 + jasnosc
            )
        )

        # kontrastu
        obraz = ImageEnhance.Contrast(
            obraz
        ).enhance(
            generator.uniform(
                1 - kontrast,
                1 + kontrast
            )
        )

        # nasycenia kolorów
        obraz = ImageEnhance.Color(
            obraz
        ).enhance(
            generator.uniform(
                1 - nasycenie,
                1 + nasycenie
            )
        )

        return obraz

    # SZUM GAUSSOWSKI ----------------------------------------------------------------
    if metoda == "Szum gaussowski":
        tablica = np.asarray( # Zamiana obrazu na tablicę NumPy
            obraz,
            dtype=np.float32
        )

        ziarno = generator.randrange(2**32) # Losowanie ziarna dla generatora NumPy
        generator_numpy = np.random.default_rng(ziarno) # Utworzenie generatora liczb losowych

        szum = generator_numpy.normal(
            loc=0, # określa wartość oczekiwaną (średnią szumu ) tego rozkładu, czyli położenie jego szczytu na osi X
            scale=ustawienia["szum"], # Określa on, jak szeroki i spłaszczony jest wykres dzwonowy czyli siła szumu
            size=tablica.shape # określa kształt i liczbę wylosowanych wyników czyli rozmiar tablicy szumu
        )

        wynik = np.clip( # Dodanie szumu i ograniczenie wartości pikseli do 0-255
            tablica + szum, 0, 255
        ).astype(np.uint8)

        return Image.fromarray(wynik)  # Zamiana tablicy z powrotem na obraz

    raise ValueError(
        f"Nieznana metoda augmentacji: {metoda}"
    )



def pobierz_obrazy(katalog):
    return sorted(
        plik for plik in katalog.rglob("*")
        if plik.is_file()
        and plik.suffix.lower() in ROZSZERZENIA
    )



def przygotuj_przyklady(
    obrazy_klas,
    katalog_raportu,
    metoda,
    ustawienia,
    ziarno=42
):
    """
    Przygotowuje tabelę porównawczą augmentacji.
    Dla każdej klasy wybiera jeden obraz i tworzy
    jego wersje po wybranych transformacjach.
    """
    wszystkie_metody = [     # Lista dostępnych metod augmentacji
        "Obrót",
        "Skalowanie",
        "Przesunięcie",
        "Zmiana kolorów",
        "Szum gaussowski",
        "Wszystkie metody"
    ]

    if metoda == "Wszystkie metody":     # Wybór metod wyświetlanych w tabeli
        metody_podgladu = wszystkie_metody
    else:
        metody_podgladu = [metoda]


    katalog_przykladow = ( # Utworzenie katalogu na przykładowe obrazy
        katalog_raportu / "przyklady"
    )
    katalog_przykladow.mkdir(
        parents=True, exist_ok=True
    )

    wynik = [] # Lista wyników dla wszystkich klas

    # Przetwarzanie kolejnych klas obrazów
    for numer_klasy, (nazwa_klasy, obrazy) in enumerate(
        sorted(obrazy_klas.items())
    ):
        if not obrazy: # Pominięcie klasy bez obrazów
            continue

        generator_wyboru = random.Random( # Utworzenie powtarzalnego generatora losowego
            ziarno + numer_klasy
        )

        wybrany_obraz = generator_wyboru.choice( # Losowanie jednego obrazu z danej klasy
            obrazy
        )

        katalog_klasy = ( # Utworzenie katalogu dla danej klasy
            katalog_przykladow / nazwa_klasy
        )
        katalog_klasy.mkdir(
            parents=True, exist_ok=True
        )

        with Image.open(wybrany_obraz) as plik: # Wczytanie obrazu i konwersja do RGB
            oryginal = plik.convert("RGB")

        sciezka_oryginalu = ( # Zapis oryginalnego obrazu
            katalog_klasy / "oryginal.jpg"
        )
        oryginal.save(
            sciezka_oryginalu,
            quality=95
        )

        przyklady = { # Dodanie oryginału do pierwszej kolumny tabeli
            "Oryginał": str(sciezka_oryginalu)
        }

        for numer_metody, nazwa_metody in enumerate( # Generowanie obrazów dla kolejnych metod
            metody_podgladu
        ):
            # Generator losowy dla konkretnej transformacji
            generator = random.Random(
                ziarno + 1000 + numer_klasy * 100 + numer_metody
            )

            zmieniony = zmodyfikuj_obraz( # Augmentacja kopii tego samego obrazu
                oryginal.copy(),
                nazwa_metody,
                generator,
                ustawienia
            )

            nazwa_pliku = ( # Utworzenie nazwy pliku augmentowanego
                f"metoda_{numer_metody + 1}.jpg"
            )

            sciezka_zmienionego = ( # Określenie ścieżki zapisu obrazu
                katalog_klasy / nazwa_pliku
            )

            zmieniony.save( # Zapis zmodyfikowanego obrazu
                sciezka_zmienionego,
                quality=95
            )

            przyklady[nazwa_metody] = str( # Dodanie obrazu do odpowiedniej kolumny
                sciezka_zmienionego
            )

        wynik.append({ # Dodanie wyników danej klasy do tabeli
            "klasa": nazwa_klasy,
            "plik_zrodlowy": str(wybrany_obraz),
            "obrazy": przyklady
        })

    return { # Zwrócenie nagłówków kolumn i danych tabeli
        "metody": ["Oryginał"] + metody_podgladu,
        "wiersze": wynik
    }



def wykonaj_augmentacje(
    nazwa_zbioru,
    metoda="Wszystkie metody",
    liczba_kopii=2,
    komunikat=None,
    postep=None,
    ustawienia=None,
    ziarno=42
):
    """
    Tworzy osobny wariant danych do treningu YOLO.
    Augmentuje tylko train, zachowując val i test.
    """
    if ustawienia is None:
        ustawienia = {
            "kat_obrotu": 15,
            "skala_min": 0.85,
            "skala_max": 1.15,
            "przesuniecie": 10,
            "jasnosc": 20,
            "kontrast": 20,
            "nasycenie": 30,
            "szum": 12
        }

    sprawdz_ustawienia(ustawienia)    # Sprawdzenie poprawności ustawień

    if metoda not in METODY: # Sprawdzenie wybranej metody
        raise ValueError("Nieprawidłowa metoda augmentacji.")

    if not 1 <= liczba_kopii <= 10: # Sprawdzenie liczby generowanych kopii
        raise ValueError(
            "Liczba kopii musi wynosić od 1 do 10."
        )

    def informuj(tekst): # Przekazywanie komunikatów do interfejsu
        if komunikat:
            komunikat(tekst)

    zrodlo = przygotuj_dane( # Automatyczne przygotowanie train/val/test
        nazwa_zbioru,
        komunikat=informuj
    )

    katalog_train = zrodlo / "train"

    klasy = sorted( # Pobranie katalogów poszczególnych klas
        folder for folder in katalog_train.iterdir()
        if folder.is_dir()
    )

    obrazy_klas = { # Przypisanie obrazów do ich klas
        folder.name: pobierz_obrazy(folder)
        for folder in klasy
    }

    obrazy_klas = { # Pominięcie klas bez obrazów
        nazwa: obrazy
        for nazwa, obrazy in obrazy_klas.items()
        if obrazy
    }

    if len(obrazy_klas) < 2: # Sprawdzenie minimalnej liczby klas
        raise ValueError(
            "Zbiór musi mieć co najmniej dwie klasy."
        )

    liczba_zrodel = sum( # Obliczenie liczby obrazów źródłowych
        len(obrazy) for obrazy in obrazy_klas.values()
    )

    identyfikator = ( # Utworzenie unikalnego identyfikatora augmentacji
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_" + uuid4().hex[:6]
    )

    nazwa_wariantu = f"augmentacja_{identyfikator}"

    katalog_wariantu = ( # Katalog na obrazy po augmentacji
        KATALOG_PROJEKTU
        / "dane_przetworzone"
        / nazwa_zbioru
        / "warianty"
        / nazwa_wariantu
    )

    katalog_raportu = ( # Katalog na raport i przykładowe obrazy
        KATALOG_PROJEKTU
        / "wyniki"
        / nazwa_zbioru
        / nazwa_wariantu
    )

    katalog_wariantu.mkdir(parents=True) # Utworzenie katalogów wynikowych
    katalog_raportu.mkdir(parents=True)

    generator = random.Random(ziarno) # Generator losowy i zmienne pomocnicze
    przetworzono = 0
    statystyki = []
    przyklad = None

    try:
        for nazwa_klasy, obrazy in obrazy_klas.items(): # Przetwarzanie kolejnych klas
            zrodlo_klasy = katalog_train / nazwa_klasy

            cel_klasy = (katalog_wariantu / "train" / nazwa_klasy)

            for plik in obrazy: # Przetwarzanie każdego obrazu w klasie

                sciezka_wzgledna = plik.relative_to(zrodlo_klasy) # Zachowanie względnej ścieżki obrazu
                cel_oryginalu = (cel_klasy / sciezka_wzgledna) # Wyznaczenie miejsca zapisu oryginału
                cel_oryginalu.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(plik, cel_oryginalu) # Skopiowanie oryginalnego obrazu

                with Image.open(plik) as oryginal:
                    oryginal = oryginal.convert("RGB") # Wczytanie obrazu i konwersja do RGB

                    for numer in range(1, liczba_kopii + 1): # Generowanie wybranej liczby kopii

                        # Wykonanie augmentacji obrazu
                        nowy = zmodyfikuj_obraz(
                            oryginal,
                            metoda,
                            generator,
                            ustawienia
                        )

                        # Utworzenie identyfikatora pliku
                        identyfikator_pliku = (
                            hashlib.sha256(
                                str(sciezka_wzgledna).encode("utf-8")
                            ).hexdigest()[:12]
                        )

                        # Nadanie nazwy nowemu obrazowi
                        nazwa_pliku = (
                            f"aug_{numer}_"
                            f"{identyfikator_pliku}.jpg"
                        )

                        # Ścieżka zapisu obrazu po augmentacji
                        cel_nowego = (
                            cel_klasy
                            / "_augmentowane"
                            / nazwa_pliku
                        )

                        cel_nowego.parent.mkdir(parents=True, exist_ok=True)

                        # Zapis obrazu w formacie JPEG
                        nowy.save(
                            cel_nowego,
                            format="JPEG",
                            quality=92
                        )

                        # Zapamiętanie pierwszego przykładu
                        if przyklad is None:
                            przyklad = {
                                "oryginal": str(plik),
                                "augmentowany": str(cel_nowego)
                            }

                przetworzono += 1 # Zwiększenie liczby przetworzonych obrazów

                if postep: # Aktualizacja paska postępu
                    postep(
                        int(przetworzono / liczba_zrodel * 100)
                    )

            przed = len(obrazy) # Liczba obrazów danej klasy przed augmentacją

            # Zapis liczebności klasy przed i po augmentacji
            statystyki.append({
                "klasa": nazwa_klasy,
                "przed": przed,
                "po": przed * (liczba_kopii + 1)
            })

            # Wyświetlenie liczebności w dzienniku
            informuj(
                f"{nazwa_klasy}: "
                f"{przed} -> "
                f"{przed * (liczba_kopii + 1)} obrazów"
            )

        # Kopiowanie walidacji i testu bez augmentacji
        for podzbior in ("val", "test"):
            shutil.copytree(
                zrodlo / podzbior,
                katalog_wariantu / podzbior
            )

        # o tabeli porównawczej
        informuj("Generowanie tabeli przykładów augmentacji")

        # Generowanie przykładów dla każdej klasy
        przyklady_augmentacji = przygotuj_przyklady(
            obrazy_klas=obrazy_klas,
            katalog_raportu=katalog_raportu,
            metoda=metoda,
            ustawienia=ustawienia,
            ziarno=ziarno
        )

        # Przygotowanie raportu augmentacji
        raport = {
            "zbior": nazwa_zbioru,
            "metoda": metoda,
            "liczba_kopii": liczba_kopii,
            "ustawienia": ustawienia.copy(),
            "klasy": statystyki,
            "liczba_przed": sum(
                rekord["przed"] for rekord in statystyki
            ),
            "liczba_po": sum(
                rekord["po"] for rekord in statystyki
            ),
            "przyklad": przyklad,
            "przyklady_augmentacji": przyklady_augmentacji,
            "katalog_danych": str(katalog_wariantu),
            "katalog_raportu": str(katalog_raportu),
            "ziarno": ziarno,
        }

        # Zapis raportu w formacie JSON
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
        # Usuwamy tylko nieukończony wariant, nigdy dane oryginalne ani bazowe.
        shutil.rmtree(katalog_wariantu, ignore_errors=True)
        shutil.rmtree(katalog_raportu, ignore_errors=True)
        raise
