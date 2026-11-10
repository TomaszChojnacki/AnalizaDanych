
import csv
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch

from PIL import Image
from PySide6.QtCore import QThread, Signal

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix
)

from ultralytics import YOLO


KATALOG_PROJEKTU = Path(__file__).resolve().parent.parent

ROZSZERZENIA = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


def zbierz_obrazy_testowe(katalog_test):
    """
    Odczytuje obrazy testowe i ich rzeczywiste klasy.
    """
    if not katalog_test.is_dir():
        raise FileNotFoundError(
            f"Brak katalogu testowego:\n{katalog_test}"
        )

    obrazy = []

    for katalog_klasy in sorted(katalog_test.iterdir()):
        if not katalog_klasy.is_dir():
            continue

        nazwa_klasy = katalog_klasy.name

        for plik in sorted(katalog_klasy.rglob("*")):
            if not plik.is_file():
                continue

            if plik.suffix.lower() not in ROZSZERZENIA:
                continue

            # Kontrola poprawnosci obrazu
            try:
                with Image.open(plik) as obraz:
                    obraz.verify()
            except (OSError, ValueError, SyntaxError) as blad:
                raise ValueError(
                    f"Niepoprawny obraz testowy:\n{plik}\n{blad}"
                ) from blad

            obrazy.append((plik, nazwa_klasy))

    if not obrazy:
        raise ValueError(
            "Zbiór testowy nie zawiera obrazów."
        )

    return obrazy


def zapisz_macierz(macierz, klasy, sciezka):
    """Zapisuje macierz pomylek jako obraz PNG."""
    rozmiar = max(6, len(klasy) * 1.2)

    fig, ax = plt.subplots(
        figsize=(rozmiar, rozmiar)
    )

    obraz = ax.imshow(
        macierz,
        cmap="Blues"
    )

    fig.colorbar(obraz, ax=ax)

    ax.set_xticks(range(len(klasy)))
    ax.set_yticks(range(len(klasy)))

    ax.set_xticklabels(klasy, rotation=35, ha="right")
    ax.set_yticklabels(klasy)

    ax.set_xlabel("Klasa przewidziana")
    ax.set_ylabel("Klasa rzeczywista")
    ax.set_title("Macierz pomyłek - YOLO")

    prog = macierz.max() / 2 if macierz.size else 0

    for i in range(len(klasy)):
        for j in range(len(klasy)):
            wartosc = int(macierz[i, j])

            ax.text(
                j, i, str(wartosc),
                ha="center",
                va="center",
                color="white" if wartosc > prog else "black"
            )

    fig.tight_layout()
    fig.savefig(sciezka, dpi=160)
    plt.close(fig)


class PracownikTestowania(QThread):
    """
    Wykonuje testowanie modelu YOLO poza watkiem GUI.
    """

    postep = Signal(int)
    komunikat = Signal(str)
    sukces = Signal(object)
    blad = Signal(str)

    def __init__(
        self,
        nazwa_zbioru,
        sciezka_modelu,
        parent=None
    ):
        super().__init__(parent)

        self.nazwa_zbioru = nazwa_zbioru
        self.sciezka_modelu = Path(sciezka_modelu)

    def run(self):
        try:
            self.wykonaj_test()

        except Exception as wyjatek:
            self.blad.emit(str(wyjatek))

    def wykonaj_test(self):
        if not self.sciezka_modelu.is_file():
            raise FileNotFoundError(
                "Nie znaleziono wybranego modelu."
            )

        # Dane przygotowane przez poprzedni modul
        katalog_test = (
            KATALOG_PROJEKTU
            / "dane_przetworzone"
            / self.nazwa_zbioru
            / "test"
        )

        self.komunikat.emit(
            "Sprawdzanie zbioru testowego..."
        )

        obrazy = zbierz_obrazy_testowe(katalog_test)

        self.komunikat.emit(
            f"Liczba obrazów testowych: {len(obrazy)}"
        )

        self.komunikat.emit(
            "Wczytywanie wytrenowanego modelu..."
        )

        model = YOLO(str(self.sciezka_modelu))

        if model.task != "classify":
            raise ValueError(
                "Wybrany model nie jest klasyfikatorem YOLO."
            )

        # Ustalanie nazw klas na podstawie modelu
        klasy = [
            str(model.names[indeks])
            for indeks in sorted(model.names)
        ]

        klasy_testowe = {
            nazwa for _, nazwa in obrazy
        }

        if set(klasy) != klasy_testowe:
            raise ValueError(
                "Klasy modelu nie odpowiadają klasom "
                "zbioru testowego.\n"
                f"Model: {klasy}\n"
                f"Test: {sorted(klasy_testowe)}"
            )

        if len(set(klasy)) != len(klasy):
            raise ValueError(
                "Model zawiera powtarzające się nazwy klas."
            )

        urzadzenie = (
            0 if torch.cuda.is_available() else "cpu"
        )

        self.komunikat.emit(
            "Urządzenie: "
            + ("GPU CUDA" if urzadzenie == 0 else "CPU")
        )

        rzeczywiste = []
        przewidziane = []
        rekordy = []

        # Przewidywanie w malych partiach
        wielkosc_partii = 8
        liczba_obrazow = len(obrazy)

        for poczatek in range(
            0, liczba_obrazow, wielkosc_partii
        ):
            partia = obrazy[
                poczatek:poczatek + wielkosc_partii
            ]

            sciezki = [
                str(plik)
                for plik, _ in partia
            ]

            wyniki = model.predict(
                source=sciezki,
                device=urzadzenie,
                batch=wielkosc_partii,
                verbose=False
            )

            if len(wyniki) != len(partia):
                raise RuntimeError(
                    "Liczba wyników nie odpowiada "
                    "liczbie obrazów."
                )

            for (plik, klasa_prawdziwa), wynik in zip(
                partia, wyniki
            ):
                if wynik.probs is None:
                    raise RuntimeError(
                        f"Brak wyniku klasyfikacji: {plik}"
                    )

                indeks = int(wynik.probs.top1)
                klasa_modelu = str(wynik.names[indeks])
                pewnosc = float(
                    wynik.probs.top1conf.item()
                )

                rzeczywiste.append(klasa_prawdziwa)
                przewidziane.append(klasa_modelu)

                rekordy.append({
                    "obraz": str(plik),
                    "klasa_rzeczywista": klasa_prawdziwa,
                    "klasa_przewidziana": klasa_modelu,
                    "pewnosc": round(pewnosc, 6),
                    "poprawna": int(
                        klasa_prawdziwa == klasa_modelu
                    )
                })

            wykonano = poczatek + len(partia)

            procent = int(
                wykonano / liczba_obrazow * 100
            )

            self.postep.emit(procent)
            self.komunikat.emit(
                f"Sprawdzono {wykonano}/{liczba_obrazow} obrazów"
            )

        # METRYKI KLASYFIKACJI
        accuracy = accuracy_score(
            rzeczywiste, przewidziane
        )

        precision, recall, f1, support = (
            precision_recall_fscore_support(
                rzeczywiste,
                przewidziane,
                labels=klasy,
                zero_division=0
            )
        )

        precision_macro = float(
            np.mean(precision)
        )
        recall_macro = float(
            np.mean(recall)
        )
        f1_macro = float(
            np.mean(f1)
        )

        macierz = confusion_matrix(
            rzeczywiste,
            przewidziane,
            labels=klasy
        )

        metryki_klas = []

        for i, nazwa in enumerate(klasy):
            metryki_klas.append({
                "klasa": nazwa,
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "liczba_obrazow": int(support[i])
            })

        # KATALOG RAPORTU
        identyfikator = (
            datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_" + uuid4().hex[:6]
        )

        katalog_raportu = (
            KATALOG_PROJEKTU
            / "wyniki"
            / self.nazwa_zbioru
            / f"test_{identyfikator}"
        )

        katalog_raportu.mkdir(
            parents=True, exist_ok=False
        )

        # Macierz pomylek
        sciezka_macierzy = (
            katalog_raportu / "macierz_pomylek.png"
        )

        zapisz_macierz(
            macierz, klasy, sciezka_macierzy
        )

        # Szczegolowe predykcje
        sciezka_csv = (
            katalog_raportu / "predykcje.csv"
        )

        with sciezka_csv.open(
            "w", newline="", encoding="utf-8-sig"
        ) as plik:
            zapis = csv.DictWriter(
                plik,
                fieldnames=[
                    "obraz",
                    "klasa_rzeczywista",
                    "klasa_przewidziana",
                    "pewnosc",
                    "poprawna"
                ]
            )

            zapis.writeheader()
            zapis.writerows(rekordy)

        raport = {
            "zbior": self.nazwa_zbioru,
            "model": str(self.sciezka_modelu.resolve()),
            "liczba_obrazow": liczba_obrazow,
            "accuracy": float(accuracy),
            "precision": precision_macro,
            "recall": recall_macro,
            "f1": f1_macro,
            "sposob_uśredniania": "macro",
            "klasy": klasy,
            "metryki_klas": metryki_klas,
            "macierz_pomylek": macierz.tolist(),
            "sciezka_macierzy": str(sciezka_macierzy),
            "katalog_raportu": str(katalog_raportu)
        }

        # Raport JSON
        with (
            katalog_raportu / "raport.json"
        ).open("w", encoding="utf-8") as plik:
            json.dump(
                raport,
                plik,
                ensure_ascii=False,
                indent=4
            )

        self.postep.emit(100)

        self.komunikat.emit(
            "Testowanie zakończone pomyślnie."
        )

        self.komunikat.emit(
            f"Accuracy: {accuracy:.2%}"
        )

        self.komunikat.emit(
            f"F1 macro: {f1_macro:.2%}"
        )

        self.sukces.emit(raport)
