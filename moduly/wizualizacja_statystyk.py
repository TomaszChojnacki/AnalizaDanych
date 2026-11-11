
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np



def generuj_wykresy(raport):
    """Generuje wykresy statystyczne zbioru."""

    katalog = Path(raport["katalog_wynikow"])     # Określenie katalogu zapisu wykresów
    katalog.mkdir(parents=True, exist_ok=True)

    klasy = [                           # Pobranie nazw klas z raportu
        rekord["klasa"]
        for rekord in raport["klasy"]
    ]

    liczebnosci = [                      # Pobranie liczby obrazów w każdej klasie
        rekord["razem"]
        for rekord in raport["klasy"]
    ]

    # WYKRES SŁUPKOWY -----------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5)) # Utworzenie wykresu o wymiarach 9 x 5 cali

    slupki = ax.bar(     # Utworzenie słupków dla poszczególnych klas
        klasy,
        liczebnosci,
        color="#2563eb"  # Kolor niebieski
    )

    ax.bar_label(slupki, padding=4)     # Wyświetlenie wartości nad słupkami

    # Ustawienie tytułu i opisów osi
    ax.set_title("Liczebność klas przed augmentacją")
    ax.set_xlabel("Klasa")
    ax.set_ylabel("Liczba obrazów")
    ax.set_ylim(0, max(liczebnosci) * 1.15)         # Ustawienie zakresu osi Y z dodatkowym miejscem
    fig.tight_layout()                                      # Automatyczne dopasowanie układu wykresu
    sciezka_slupkowy = (katalog / "wykres_slupkowy.png")    # Określenie ścieżki zapisu wykresu
    fig.savefig(sciezka_slupkowy, dpi=160)                  # Zapis wykresu w formacie PNG
    plt.close(fig)                                          # Zamknięcie wykresu i zwolnienie pamięci

    # WYKRES KOŁOWY------------------------------------------------------------------------------------------


    fig, ax = plt.subplots(figsize=(7, 6))              # Utworzenie wykresu o wymiarach 7 × 6 cali

    # Utworzenie wykresu udziału procentowego klas
    ax.pie(
        liczebnosci,
        labels=klasy,       # Nazwy klas
        autopct="%1.1f%%",  # Procenty z jednym miejscem po przecinku
        startangle=90       # Początkowy kąt wykresu
    )

    ax.set_title("Udział klas przed augmentacją")       # Ustawienie tytułu wykresu
    fig.tight_layout()                                  # Dopasowanie układu wykresu
    sciezka_kolowy = (katalog / "wykres_kolowy.png")    # Określenie ścieżki zapisu wykresu kołowego
    fig.savefig(sciezka_kolowy, dpi=160)                # Zapis wykresu w formacie PNG
    plt.close(fig)                                      # Zamknięcie wykresu

    # Zwrócenie ścieżek do wygenerowanych wykresów
    return {
        "slupkowy": str(sciezka_slupkowy),
        "kolowy": str(sciezka_kolowy)
    }




def generuj_wykres_porownawczy(raport):
    """
    Dla każdej klasy pokazuje dwa słupki:
    przed augmentacją i po augmentacji.
    """
    katalog = Path(raport["katalog_raportu"])     # Określenie katalogu zapisu wykresu
    katalog.mkdir(parents=True, exist_ok=True)

    klasy = [                                   # Pobranie nazw klas z raportu
        rekord["klasa"]
        for rekord in raport["klasy"]
    ]

    przed = [                                   # Pobranie liczby obrazów przed augmentacją
        rekord["przed"]
        for rekord in raport["klasy"]
    ]

    po = [                                       # Pobranie liczby obrazów po augmentacji
        rekord["po"]
        for rekord in raport["klasy"]
    ]

    pozycje = np.arange(len(klasy))                 # Wyznaczenie pozycji słupków i ich szerokości
    szerokosc = 0.36

    fig, ax = plt.subplots(figsize=(max(9, len(klasy) * 1.6), 5.5))    # Utworzenie wykresu dopasowanego do liczby klas

    # Utworzenie słupków przed augmentacją
    slupki_przed = ax.bar(
        pozycje - szerokosc / 2,
        przed,
        szerokosc,
        label="Przed augmentacją",
        color="#2563eb"
    )

    # Utworzenie słupków po augmentacji
    slupki_po = ax.bar(
        pozycje + szerokosc / 2,
        po,
        szerokosc,
        label="Po augmentacji",
        color="#f59e0b"
    )


    ax.bar_label(slupki_przed, padding=3, fontsize=9)    # Wyświetlenie wartości nad słupkami przed augmentacją
    ax.bar_label(slupki_po, padding=3, fontsize=9)      # Wyświetlenie wartości nad słupkami po augmentacji

    # Ustawienie tytułu i opisów osi
    ax.set_title("Liczebność klas przed i po augmentacji")
    ax.set_xlabel("Klasa")
    ax.set_ylabel("Liczba obrazów")

    # Ustawienie pozycji i nazw klas na osi X
    ax.set_xticks(pozycje)
    ax.set_xticklabels(klasy)
    ax.set_ylim(0, max(po) * 1.15)     # Ustawienie zakresu osi Y
    ax.legend()                              # Dodanie legendy
    ax.grid(axis="y", alpha=0.2)                # Dodanie poziomych linii pomocniczych
    ax.set_axisbelow(True)                  # Umieszczenie siatki za słupkami
    fig.tight_layout()                      # Automatyczne dopasowanie układu wykresu
    sciezka = (katalog / "porownanie_przed_po.png") # Określenie ścieżki zapisu wykresu

    fig.savefig(sciezka,dpi=170,bbox_inches="tight")     # Zapis wykresu do pliku PNG
    plt.close(fig)     # Zamknięcie wykresu i zwolnienie pamięci

    return str(sciezka)    # Zwrócenie ścieżki do wygenerowanego wykresu
