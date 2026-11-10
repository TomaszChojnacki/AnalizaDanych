
from pathlib import Path
from datetime import datetime
from uuid import uuid4

import torch
from PySide6.QtCore import QThread, Signal
from ultralytics import YOLO
from moduly.przygotowanie_danych import przygotuj_dane


KATALOG_PROJEKTU = Path(__file__).resolve().parent.parent
KATALOG_WYNIKOW = KATALOG_PROJEKTU / "wyniki"

ROZSZERZENIA_OBRAZOW = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


def sprawdz_zbior(sciezka):
    """
    Sprawdza, czy zbior jest gotowy do klasyfikacji YOLO.
    """
    sciezka = Path(sciezka)

    if not sciezka.is_dir():
        raise ValueError(
            f"Nie znaleziono katalogu danych:\n{sciezka}"
        )

    klasy_treningowe = None

    for podzbior in ("train", "val"):
        katalog = sciezka / podzbior

        if not katalog.is_dir():
            raise ValueError(
                f"Brakuje katalogu '{podzbior}'.\n"
                "Przygotuj dane train/val/test przed treningiem."
            )

        klasy = {
            folder.name
            for folder in katalog.iterdir()
            if folder.is_dir()
        }

        if len(klasy) < 2:
            raise ValueError(
                f"W katalogu {podzbior} wymagane są "
                "co najmniej dwie klasy."
            )

        if klasy_treningowe is None:
            klasy_treningowe = klasy
        elif klasy != klasy_treningowe:
            raise ValueError(
                "Klasy w train i val są różne."
            )

        for nazwa in klasy:
            folder_klasy = katalog / nazwa

            obrazy = [
                plik
                for plik in folder_klasy.rglob("*")
                if plik.is_file()
                and plik.suffix.lower()
                in ROZSZERZENIA_OBRAZOW
            ]

            if not obrazy:
                raise ValueError(
                    f"Brak obrazów: {podzbior}/{nazwa}"
                )

    return sorted(klasy_treningowe)


class PracownikTrenowania(QThread):
    """
    Uruchamia trenowanie YOLO w osobnym watku,
    aby interfejs graficzny nie przestawal odpowiadac.
    """

    postep = Signal(int)
    komunikat = Signal(str)
    sukces = Signal(str)
    blad = Signal(str)

    def __init__(
            self,
            nazwa_zbioru,
            sciezka_danych,
            epoki=30,
            rozmiar=224,
            partia=8,
            nazwa_modelu="yolo26n-cls.pt",
            parent=None
    ):
        super().__init__(parent)

        self.nazwa_zbioru = nazwa_zbioru
        self.sciezka_danych = Path(sciezka_danych)
        self.epoki = epoki
        self.rozmiar = rozmiar
        self.partia = partia
        self.nazwa_modelu = nazwa_modelu

    def run(self):
        try:
            # 1. Automatyczne przygotowanie danych
            self.komunikat.emit(
                "Sprawdzanie i przygotowywanie danych..."
            )

            sciezka = przygotuj_dane(
                self.nazwa_zbioru,
                komunikat=self.komunikat.emit
            )

            # 2. Kontrola gotowego zbioru
            klasy = sprawdz_zbior(sciezka)

            self.komunikat.emit(
                "Wykryte klasy: " + ", ".join(klasy)
            )

            # 3. Kontrola GPU
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA jest niedostępna. "
                    "Nie można rozpocząć trenowania na GPU."
                )

            self.komunikat.emit(
                "GPU: " + torch.cuda.get_device_name(0)
            )

            # 4. Wybór modelu
            dozwolone_modele = {
                "yolo26n-cls.pt",
                "yolo26s-cls.pt",
                "yolo26m-cls.pt"
            }

            if self.nazwa_modelu not in dozwolone_modele:
                raise ValueError(
                    "Wybrano nieobsługiwany model."
                )

            lokalny_model = (
                    KATALOG_PROJEKTU / self.nazwa_modelu
            )

            if lokalny_model.is_file():
                model = YOLO(str(lokalny_model))
            else:
                self.komunikat.emit(
                    "Pobieranie modelu: " + self.nazwa_modelu
                )
                model = YOLO(self.nazwa_modelu)

            if model.task != "classify":
                raise ValueError(
                    "Wybrany model nie obsługuje klasyfikacji."
                )

            # 5. Katalog wyników
            identyfikator = (
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                    + "_" + uuid4().hex[:6]
            )

            nazwa_treningu = f"trening_{identyfikator}"

            katalog_wynikow = (
                    KATALOG_WYNIKOW / self.nazwa_zbioru
            )

            katalog_wynikow.mkdir(
                parents=True,
                exist_ok=True
            )

            # 6. Aktualizacja paska postępu
            def aktualizuj_postep(trener):
                numer_epoki = min(
                    trener.epoch + 1,
                    self.epoki
                )

                procent = int(
                    numer_epoki / self.epoki * 100
                )

                self.postep.emit(procent)
                self.komunikat.emit(
                    f"Zakończono epokę "
                    f"{numer_epoki}/{self.epoki}"
                )

            model.add_callback(
                "on_fit_epoch_end",
                aktualizuj_postep
            )

            # 7. Trenowanie
            self.komunikat.emit(
                "Rozpoczynanie trenowania YOLO..."
            )

            model.train(
                data=str(sciezka.resolve()),
                epochs=self.epoki,
                imgsz=self.rozmiar,
                batch=self.partia,
                device=0,
                workers=0,
                seed=42,
                save=True,
                project=str(katalog_wynikow.resolve()),
                name=nazwa_treningu,
                exist_ok=False
            )

            # 8. Odszukanie najlepszego modelu
            najlepszy_model = (
                    katalog_wynikow
                    / nazwa_treningu
                    / "weights"
                    / "best.pt"
            )

            if not najlepszy_model.is_file():
                raise FileNotFoundError(
                    "Nie znaleziono zapisanego modelu best.pt."
                )

            self.postep.emit(100)

            self.komunikat.emit(
                "Trenowanie zakończone pomyślnie."
            )

            self.komunikat.emit(
                f"Model zapisany: {najlepszy_model}"
            )

            self.sukces.emit(str(najlepszy_model))

        except Exception as blad:
            self.blad.emit(str(blad))


def wczytaj_model(sciezka):
    """
    Wczytuje zapisany klasyfikator YOLO.
    Nie uruchamia ponownego treningu.
    """
    sciezka = Path(sciezka)

    if not sciezka.is_file():
        raise FileNotFoundError(
            f"Nie znaleziono modelu: {sciezka}"
        )

    model = YOLO(str(sciezka))

    if model.task != "classify":
        raise ValueError(
            "Plik nie zawiera modelu klasyfikacyjnego."
        )

    return model
