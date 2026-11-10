
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def generuj_wykresy(raport):
    """Generuje wykresy statystyczne zbioru."""

    katalog = Path(raport["katalog_wynikow"])
    katalog.mkdir(parents=True, exist_ok=True)

    klasy = [
        rekord["klasa"]
        for rekord in raport["klasy"]
    ]

    liczebnosci = [
        rekord["razem"]
        for rekord in raport["klasy"]
    ]

    # WYKRES SLUPKOWY
    fig, ax = plt.subplots(figsize=(9, 5))

    slupki = ax.bar(
        klasy,
        liczebnosci,
        color="#2563eb"
    )

    ax.bar_label(slupki, padding=4)
    ax.set_title(
        "Liczebność klas przed augmentacją"
    )
    ax.set_xlabel("Klasa")
    ax.set_ylabel("Liczba obrazów")
    ax.set_ylim(0, max(liczebnosci) * 1.15)

    fig.tight_layout()

    sciezka_slupkowy = (
        katalog / "wykres_slupkowy.png"
    )

    fig.savefig(sciezka_slupkowy, dpi=160)
    plt.close(fig)

    # WYKRES KOLOWY
    fig, ax = plt.subplots(figsize=(7, 6))

    ax.pie(
        liczebnosci,
        labels=klasy,
        autopct="%1.1f%%",
        startangle=90
    )

    ax.set_title(
        "Udział klas przed augmentacją"
    )

    fig.tight_layout()

    sciezka_kolowy = (
        katalog / "wykres_kolowy.png"
    )

    fig.savefig(sciezka_kolowy, dpi=160)
    plt.close(fig)

    return {
        "slupkowy": str(sciezka_slupkowy),
        "kolowy": str(sciezka_kolowy)
    }



def generuj_wykres_porownawczy(raport):
    """
    Dla każdej klasy pokazuje dwa słupki:
    przed augmentacją i po augmentacji.
    """

    import numpy as np

    katalog = Path(raport["katalog_raportu"])
    katalog.mkdir(parents=True, exist_ok=True)

    klasy = [
        rekord["klasa"]
        for rekord in raport["klasy"]
    ]

    przed = [
        rekord["przed"]
        for rekord in raport["klasy"]
    ]

    po = [
        rekord["po"]
        for rekord in raport["klasy"]
    ]

    pozycje = np.arange(len(klasy))
    szerokosc = 0.36

    fig, ax = plt.subplots(
        figsize=(max(9, len(klasy) * 1.6), 5.5)
    )

    slupki_przed = ax.bar(
        pozycje - szerokosc / 2,
        przed,
        szerokosc,
        label="Przed augmentacją",
        color="#2563eb"
    )

    slupki_po = ax.bar(
        pozycje + szerokosc / 2,
        po,
        szerokosc,
        label="Po augmentacji",
        color="#f59e0b"
    )

    ax.bar_label(
        slupki_przed, padding=3, fontsize=9
    )

    ax.bar_label(
        slupki_po, padding=3, fontsize=9
    )

    ax.set_title(
        "Liczebność klas przed i po augmentacji"
    )
    ax.set_xlabel("Klasa")
    ax.set_ylabel("Liczba obrazów")

    ax.set_xticks(pozycje)
    ax.set_xticklabels(klasy)

    ax.set_ylim(0, max(po) * 1.15)
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)

    fig.tight_layout()

    sciezka = (
        katalog / "porownanie_przed_po.png"
    )

    fig.savefig(
        sciezka,
        dpi=170,
        bbox_inches="tight"
    )

    plt.close(fig)

    return str(sciezka)
