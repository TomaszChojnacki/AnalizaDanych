import os
from pathlib import Path
import shutil

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QStackedWidget,
    QFrame,
    QScrollArea,
    QMessageBox
)

from interfejs.panel_trenowania import PanelTrenowania
from interfejs.panel_wynikow import PanelWynikow
from interfejs.panel_statystyk import PanelStatystyk
from interfejs.panel_augmentacji import PanelAugmentacji
from importlib.metadata import version


KATALOG_PROJEKTU = Path(__file__).resolve().parent.parent
KATALOG_DANYCH = KATALOG_PROJEKTU / "dane"

ROZSZERZENIA_OBRAZOW = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


class OknoGlowne(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "AnalizaDanych - Tomasz Chojnacki - Maciej Bernatek"
        )
        self.resize(1200, 800)

        self.przyciski_menu = []

        self.utworz_interfejs()
        self.ustaw_style()
        self.odswiez_liste_zbiorow()
        self.pokaz_panel(0)

    def utworz_interfejs(self):
        kontener = QWidget()
        self.setCentralWidget(kontener)

        uklad_glowny = QHBoxLayout(kontener)
        uklad_glowny.setContentsMargins(0, 0, 0, 0)
        uklad_glowny.setSpacing(0)

        # ---------------------------------
        # MENU BOCZNE
        # ---------------------------------
        menu = QFrame()
        menu.setObjectName("menuBoczne")
        menu.setFixedWidth(245)

        uklad_menu = QVBoxLayout(menu)
        uklad_menu.setContentsMargins(16, 25, 16, 20)
        uklad_menu.setSpacing(12)

        tytul = QLabel("AnalizaDanych")
        tytul.setObjectName("tytulAplikacji")
        uklad_menu.addWidget(tytul)

        podtytul = QLabel("Analiza obrazów i YOLO")
        podtytul.setObjectName("podtytulAplikacji")
        uklad_menu.addWidget(podtytul)

        uklad_menu.addSpacing(25)

        nazwy_paneli = [
            "Panel główny",
            "Analiza statystyczna",
            "Augmentacja obrazów",
            "Trenowanie YOLO",
            "Wyniki modeli"
        ]

        for indeks, nazwa in enumerate(nazwy_paneli):
            przycisk = QPushButton(nazwa)
            przycisk.setObjectName("przyciskMenu")
            przycisk.setCheckable(True)
            przycisk.setMinimumHeight(45)
            przycisk.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            przycisk.clicked.connect(
                lambda sprawdzony=False, i=indeks:
                self.pokaz_panel(i)
            )

            uklad_menu.addWidget(przycisk)
            self.przyciski_menu.append(przycisk)

        uklad_menu.addStretch()

        self.etykieta_gpu = QLabel("Sprawdzanie GPU...")
        self.etykieta_gpu.setObjectName("informacjaGPU")
        self.etykieta_gpu.setWordWrap(True)

        uklad_menu.addWidget(self.etykieta_gpu)

        uklad_glowny.addWidget(menu)

        # ---------------------------------
        # OBSZAR ROBOCZY
        # ---------------------------------
        self.stos_paneli = QStackedWidget()

        self.panel_glowny = self.utworz_panel_glowny()
        self.stos_paneli.addWidget(self.panel_glowny)





        # Panel analizy statystycznej
        self.panel_statystyk = PanelStatystyk(
            pobierz_zbior=lambda: (
                self.wybor_zbioru.currentText()
                if self.wybor_zbioru.isEnabled()
                else ""
            )
        )

        self.stos_paneli.addWidget(
            self.panel_statystyk
        )




        # Panel augmentacji

        # Panel augmentacji obrazow
        self.panel_augmentacji = PanelAugmentacji(
            pobierz_zbior=lambda: (
                self.wybor_zbioru.currentText()
                if self.wybor_zbioru.isEnabled()
                else ""
            )
        )

        self.stos_paneli.addWidget(
            self.panel_augmentacji
        )





        # Panel trenowania YOLO
        self.panel_trenowania = PanelTrenowania(
            pobierz_zbior=lambda: (
                self.wybor_zbioru.currentText()
                if self.wybor_zbioru.isEnabled()
                else ""
            )
        )

        self.stos_paneli.addWidget(
            self.panel_trenowania
        )



        # Panel testowania i wizualizacji wynikow
        self.panel_wynikow = PanelWynikow(
            pobierz_zbior=lambda: (
                self.wybor_zbioru.currentText()
                if self.wybor_zbioru.isEnabled()
                else ""
            )
        )

        self.stos_paneli.addWidget(
            self.panel_wynikow
        )



        uklad_glowny.addWidget(self.stos_paneli)

        self.statusBar().showMessage(
            "Aplikacja AnalizaDanych została uruchomiona."
        )

        self.sprawdz_gpu()

    def utworz_panel_glowny(self):
        przewijanie = QScrollArea()
        przewijanie.setWidgetResizable(True)
        przewijanie.setFrameShape(
            QFrame.Shape.NoFrame
        )

        panel = QWidget()
        panel.setObjectName("panelRoboczy")

        uklad = QVBoxLayout(panel)
        uklad.setContentsMargins(35, 30, 35, 30)
        uklad.setSpacing(22)

        naglowek = QLabel("Panel główny")
        naglowek.setObjectName("naglowek")
        uklad.addWidget(naglowek)

        opis = QLabel(
            "Wybierz zbiór danych i rozpocznij analizę obrazów."
        )
        opis.setObjectName("opis")
        uklad.addWidget(opis)

        # WYBÓR ZBIORU
        karta_zbioru = self.utworz_karte()
        uklad_zbioru = QVBoxLayout(karta_zbioru)

        uklad_zbioru.addWidget(
            QLabel("Aktywny zbiór danych")
        )

        self.wybor_zbioru = QComboBox()
        self.wybor_zbioru.setMinimumHeight(38)

        self.wybor_zbioru.currentTextChanged.connect(
            self.odswiez_dane
        )

        uklad_zbioru.addWidget(self.wybor_zbioru)

        self.etykieta_sciezki = QLabel("")
        self.etykieta_sciezki.setObjectName("opis")
        self.etykieta_sciezki.setWordWrap(True)
        uklad_zbioru.addWidget(self.etykieta_sciezki)

        uklad.addWidget(karta_zbioru)

        # STATYSTYKI
        uklad_statystyk = QHBoxLayout()
        uklad_statystyk.setSpacing(15)

        karta_klas = self.utworz_karte_statystyki(
            "Liczba klas", "—"
        )
        karta_obrazow = self.utworz_karte_statystyki(
            "Liczba obrazów", "—"
        )
        karta_gpu = self.utworz_karte_statystyki(
            "Akceleracja", "—"
        )

        self.wartosc_klas = karta_klas[1]
        self.wartosc_obrazow = karta_obrazow[1]
        self.wartosc_gpu = karta_gpu[1]

        for karta, _ in [
            karta_klas, karta_obrazow, karta_gpu
        ]:
            uklad_statystyk.addWidget(karta)

        uklad.addLayout(uklad_statystyk)

        # SZYBKI DOSTĘP
        karta_operacji = self.utworz_karte()

        uklad_operacji = QVBoxLayout(karta_operacji)
        uklad_operacji.setContentsMargins(20, 20, 20, 20)
        uklad_operacji.setSpacing(12)

        # Naglowek
        etykieta = QLabel("Szybki dostęp")
        etykieta.setObjectName("tytulSekcji")
        uklad_operacji.addWidget(etykieta)

        # Opis
        opis = QLabel(
            "Zarządzanie zbiorami danych wykorzystywanymi w projekcie."
        )
        opis.setObjectName("opis")
        uklad_operacji.addWidget(opis)

        # Przycisk otwierania katalogu dane
        przycisk_katalog = QPushButton("Otwórz katalog danych")
        przycisk_katalog.setObjectName("przyciskAkcji")
        przycisk_katalog.setMinimumHeight(45)
        przycisk_katalog.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        przycisk_katalog.clicked.connect(
            self.otworz_katalog_danych
        )

        uklad_operacji.addWidget(przycisk_katalog)

        # Przycisk odswiezania listy zbiorow
        przycisk_odswiez = QPushButton("Odśwież listę zbiorów")
        przycisk_odswiez.setObjectName("przyciskOdswiez")
        przycisk_odswiez.setMinimumHeight(45)
        przycisk_odswiez.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        przycisk_odswiez.clicked.connect(
            self.odswiez_liste_zbiorow
        )

        uklad_operacji.addWidget(przycisk_odswiez)

        # ---------------------------------
        # CZYSZCZENIE WYGENEROWANYCH DANYCH
        # ---------------------------------

        uklad_operacji.addSpacing(15)

        etykieta_czyszczenia = QLabel(
            "Czyszczenie wygenerowanych plików"
        )
        etykieta_czyszczenia.setObjectName("tytulSekcji")
        uklad_operacji.addWidget(etykieta_czyszczenia)

        opis_czyszczenia = QLabel(
            "Usuwanie wyników dla aktualnie wybranego "
            "zbioru danych. Oryginalne zdjęcia "
            "pozostaną nienaruszone."
        )
        opis_czyszczenia.setObjectName("opis")
        opis_czyszczenia.setWordWrap(True)
        uklad_operacji.addWidget(opis_czyszczenia)

        # Usuwanie augmentacji
        self.przycisk_usun_augmentacje = QPushButton(
            "Usuń dane przetworzone i augmentację"
        )
        self.przycisk_usun_augmentacje.setObjectName(
            "przyciskUsunAugmentacje"
        )
        self.przycisk_usun_augmentacje.setMinimumHeight(45)

        self.przycisk_usun_augmentacje.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.przycisk_usun_augmentacje.clicked.connect(
            self.usun_dane_augmentacji
        )

        uklad_operacji.addWidget(
            self.przycisk_usun_augmentacje
        )

        # Usuwanie zapisanych modeli
        self.przycisk_usun_modele = QPushButton(
            "Usuń zapisane modele YOLO"
        )
        self.przycisk_usun_modele.setObjectName(
            "przyciskUsunModele"
        )
        self.przycisk_usun_modele.setMinimumHeight(45)

        self.przycisk_usun_modele.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.przycisk_usun_modele.clicked.connect(
            self.usun_zapisane_modele
        )

        uklad_operacji.addWidget(
            self.przycisk_usun_modele
        )

        # Dodanie sekcji do panelu glownego
        uklad.addWidget(karta_operacji)
        uklad.addStretch()

        # szybki dostęp end ---------

        przewijanie.setWidget(panel)
        return przewijanie

    def otworz_katalog_danych(self):
        """Otwiera katalog dane w Eksploratorze Windows."""
        import os

        KATALOG_DANYCH.mkdir(
            parents=True,
            exist_ok=True
        )

        os.startfile(str(KATALOG_DANYCH))

        self.statusBar().showMessage(
            "Otwarto katalog danych."
        )

    def odswiez_liste_zbiorow(self):
        """Odswieza liste dostepnych zbiorow danych."""

        KATALOG_DANYCH.mkdir(
            parents=True,
            exist_ok=True
        )

        poprzedni_zbior = self.wybor_zbioru.currentText()

        zbiory = sorted(
            katalog.name
            for katalog in KATALOG_DANYCH.iterdir()
            if katalog.is_dir()
        )

        self.wybor_zbioru.blockSignals(True)
        self.wybor_zbioru.clear()

        if zbiory:
            self.wybor_zbioru.addItems(zbiory)
            self.wybor_zbioru.setEnabled(True)

            if poprzedni_zbior in zbiory:
                self.wybor_zbioru.setCurrentText(
                    poprzedni_zbior
                )
        else:
            self.wybor_zbioru.addItem("Brak zbiorów")
            self.wybor_zbioru.setEnabled(False)

        self.wybor_zbioru.blockSignals(False)

        if zbiory:
            self.odswiez_dane()
        else:
            self.wartosc_klas.setText("0")
            self.wartosc_obrazow.setText("0")
            self.etykieta_sciezki.setText(
                "Brak dostępnych zbiorów danych."
            )

        self.statusBar().showMessage(
            "Lista zbiorów została odświeżona."
        )

    def czy_trwaja_obliczenia(self):
        """
        Sprawdza, czy aplikacja wykonuje aktualnie
        operacje w osobnych watkach.
        """

        nazwy_paneli = (
            "panel_statystyk",
            "panel_augmentacji",
            "panel_trenowania",
            "panel_wynikow"
        )

        for nazwa in nazwy_paneli:
            panel = getattr(self, nazwa, None)

            if panel is None:
                continue

            pracownik = getattr(panel, "pracownik", None)

            if (
                    pracownik is not None
                    and pracownik.isRunning()
            ):
                return True

        return False

    def pobierz_aktywny_zbior(self):
        """
        Zwraca nazwe aktualnego zbioru.
        Sprawdza, czy nazwa odpowiada rzeczywistemu
        katalogowi bezposrednio w folderze dane.
        """

        if not self.wybor_zbioru.isEnabled():
            return None

        nazwa = self.wybor_zbioru.currentText()

        katalog = KATALOG_DANYCH / nazwa

        if (
                not nazwa
                or not katalog.is_dir()
                or katalog.is_symlink()
                or katalog.resolve().parent
                != KATALOG_DANYCH.resolve()
        ):
            return None

        return nazwa

    def przygotuj_czyszczenie(self, rodzaj):
        """
        Przygotowuje liste katalogow do usuniecia.

        Usuwane sa wylacznie okreslone katalogi
        wygenerowane przez program.
        """

        if self.czy_trwaja_obliczenia():
            QMessageBox.warning(
                self,
                "Trwające obliczenia",
                "Nie można usuwać plików podczas "
                "analizy, augmentacji, trenowania "
                "lub testowania modelu."
            )
            return None

        nazwa = self.pobierz_aktywny_zbior()

        if nazwa is None:
            QMessageBox.warning(
                self,
                "Brak zbioru",
                "Wybierz poprawny zbiór danych."
            )
            return None

        katalog_wynikow = (
                KATALOG_PROJEKTU / "wyniki" / nazwa
        )

        katalog_przetworzony = (
                KATALOG_PROJEKTU
                / "dane_przetworzone"
                / nazwa
        )

        katalogi_do_usuniecia = []

        if rodzaj == "augmentacja":
            # Usuwamy caly katalog danych przetworzonych
            # wybranego zbioru, lacznie z train/val/test
            # i wszystkimi wariantami augmentacji.

            if (
                    katalog_przetworzony.is_dir()
                    and not katalog_przetworzony.is_symlink()
            ):
                katalogi_do_usuniecia.append(
                    katalog_przetworzony
                )

            przedrostek = "augmentacja_"


        elif rodzaj == "modele":
            przedrostek = "trening_"

        else:
            raise ValueError(
                "Nieznany rodzaj czyszczenia."
            )

        if katalog_wynikow.is_dir():
            for katalog in katalog_wynikow.iterdir():
                if (
                        katalog.is_dir()
                        and not katalog.is_symlink()
                        and katalog.name.startswith(przedrostek)
                ):
                    katalogi_do_usuniecia.append(katalog)

        return nazwa, katalogi_do_usuniecia

    def potwierdz_i_usun(self, rodzaj):
        """
        Wyswietla potwierdzenie i usuwa
        wybrane katalogi wygenerowane przez program.
        """

        przygotowane = self.przygotuj_czyszczenie(rodzaj)

        if przygotowane is None:
            return

        nazwa, katalogi = przygotowane

        if not katalogi:
            QMessageBox.information(
                self,
                "Brak plików",
                "Nie znaleziono plików do usunięcia "
                f"dla zbioru {nazwa}."
            )
            return

        if rodzaj == "augmentacja":
            opis = (
                "Zostaną usunięte WSZYSTKIE dane przetworzone "
                "wybranego zbioru, w tym katalogi train, val, test, "
                "obrazy augmentowane i raporty augmentacji.\n\n"
                "Oryginalne zdjęcia pozostaną nienaruszone."
            )
            tytul = "Usuwanie danych przetworzonych"
        else:
            opis = (
                "Zostaną usunięte katalogi treningowe "
                "wraz z modelami best.pt i last.pt "
                "oraz wynikami uczenia."
            )
            tytul = "Usuwanie modeli YOLO"

        lista_katalogow = "\n".join(
            f"• {katalog.relative_to(KATALOG_PROJEKTU)}"
            for katalog in katalogi
        )

        odpowiedz = QMessageBox.question(
            self,
            tytul,
            f"Wybrany zbiór: {nazwa}\n\n"
            f"{opis}\n\n"
            f"Katalogi do usunięcia:\n"
            f"{lista_katalogow}\n\n"
            "Tej operacji nie można cofnąć.\n\n"
            "Czy na pewno chcesz kontynuować?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if odpowiedz != QMessageBox.StandardButton.Yes:
            return

        # Ograniczenie operacji do katalogow projektu

        # Katalogi nadrzedne, w ktorych mozna usuwac
        # tylko odpowiednio wybrane dane.

        katalog_wynikow = (
                KATALOG_PROJEKTU / "wyniki" / nazwa
        ).resolve()

        katalog_przetworzonych = (
                KATALOG_PROJEKTU / "dane_przetworzone"
        ).resolve()

        dozwolone_katalogi = [
            katalog_wynikow,
            katalog_przetworzonych
        ]

        liczba_usunietych = 0
        bledy = []

        for katalog in katalogi:
            try:
                if katalog.is_symlink():
                    continue

                sciezka = katalog.resolve()

                if rodzaj == "augmentacja":
                    poprawna_sciezka = (
                        # Raporty augmentacji
                            (
                                    sciezka.parent == dozwolone_katalogi[0]
                                    and sciezka.name.startswith("augmentacja_")
                            )
                            or
                            # Caly katalog przetworzonych danych wybranego zbioru
                            (
                                    sciezka.parent == dozwolone_katalogi[1]
                                    and sciezka.name == nazwa
                            )
                    )
                else:
                    poprawna_sciezka = (
                        # Tylko katalogi zapisanych treningow
                            sciezka.parent == dozwolone_katalogi[0]
                            and sciezka.name.startswith("trening_")
                    )

                if not poprawna_sciezka:
                    continue

                if sciezka.exists() and sciezka.is_dir():
                    shutil.rmtree(sciezka)
                    liczba_usunietych += 1

            except OSError as blad:
                bledy.append(
                    f"{katalog.name}: {blad}"
                )

        if bledy:
            QMessageBox.warning(
                self,
                "Czyszczenie niepełne",
                "Nie udało się usunąć wszystkich katalogów:\n\n"
                + "\n".join(bledy)
            )
        else:
            QMessageBox.information(
                self,
                "Czyszczenie zakończone",
                f"Usunięto {liczba_usunietych} katalogów "
                f"dla zbioru {nazwa}."
            )

        self.statusBar().showMessage(
            f"Czyszczenie: usunięto {liczba_usunietych} katalogów."
        )

    def usun_dane_augmentacji(self):
        """Usuwa wygenerowane warianty augmentacji."""
        self.potwierdz_i_usun("augmentacja")

    def usun_zapisane_modele(self):
        """Usuwa zapisane eksperymenty treningowe."""
        self.potwierdz_i_usun("modele")


    def utworz_karte(self):
        karta = QFrame()
        karta.setObjectName("karta")
        return karta

    def utworz_karte_statystyki(self, nazwa, wartosc):
        karta = self.utworz_karte()

        uklad = QVBoxLayout(karta)
        uklad.setContentsMargins(20, 20, 20, 20)

        etykieta = QLabel(nazwa)
        etykieta.setObjectName("opis")
        uklad.addWidget(etykieta)

        etykieta_wartosci = QLabel(wartosc)
        etykieta_wartosci.setObjectName("wartosc")
        uklad.addWidget(etykieta_wartosci)

        return karta, etykieta_wartosci

    def utworz_panel_informacyjny(self, nazwa, opis):
        panel = QWidget()
        panel.setObjectName("panelRoboczy")

        uklad = QVBoxLayout(panel)
        uklad.setContentsMargins(35, 30, 35, 30)

        naglowek = QLabel(nazwa)
        naglowek.setObjectName("naglowek")
        uklad.addWidget(naglowek)

        etykieta_opisu = QLabel(opis)
        etykieta_opisu.setObjectName("opis")
        etykieta_opisu.setWordWrap(True)
        uklad.addWidget(etykieta_opisu)

        uklad.addStretch()

        return panel

    def pokaz_panel(self, indeks):
        self.stos_paneli.setCurrentIndex(indeks)

        for i, przycisk in enumerate(self.przyciski_menu):
            przycisk.setChecked(i == indeks)

        if indeks == 1:
            self.panel_statystyk.odswiez_zbior()

        elif indeks == 2:
            self.panel_augmentacji.odswiez_zbior()

        elif indeks == 3:
            self.panel_trenowania.odswiez_zbior()

        elif indeks == 4:
            self.panel_wynikow.odswiez_zbior()





    def odswiez_dane(self, *_):
        nazwa_zbioru = self.wybor_zbioru.currentText()
        sciezka = KATALOG_DANYCH / nazwa_zbioru

        self.etykieta_sciezki.setText(
            f"Lokalizacja: {sciezka}"
        )

        if not sciezka.exists():
            self.wartosc_klas.setText("0")
            self.wartosc_obrazow.setText("0")
            self.statusBar().showMessage(
                "Nie znaleziono katalogu danych."
            )
            return

        liczebnosc = {}

        # Rozpoznawanie katalogów klas w train i test
        for podzbior in ["train", "test"]:
            katalog_podzbioru = sciezka / podzbior

            if not katalog_podzbioru.exists():
                continue

            for katalog_klasy in katalog_podzbioru.iterdir():
                if not katalog_klasy.is_dir():
                    continue

                liczebnosc.setdefault(
                    katalog_klasy.name, 0
                )

                liczebnosc[katalog_klasy.name] += sum(
                    1
                    for plik in katalog_klasy.rglob("*")
                    if plik.is_file()
                    and plik.suffix.lower()
                    in ROZSZERZENIA_OBRAZOW
                )

        self.wartosc_klas.setText(
            str(len(liczebnosc))
        )
        self.wartosc_obrazow.setText(
            str(sum(liczebnosc.values()))
        )

        self.statusBar().showMessage(
            f"Aktywny zbiór: {nazwa_zbioru}"
        )

    def sprawdz_gpu(self):
        try:
            import torch

            if torch.cuda.is_available():
                nazwa_gpu = torch.cuda.get_device_name(0)
                self.etykieta_gpu.setText(
                    f"GPU: {nazwa_gpu}\nCUDA: aktywna"
                )
                self.wartosc_gpu.setText("CUDA")
            else:
                self.etykieta_gpu.setText(
                    "GPU: niedostępne\nTryb CPU"
                )
                self.wartosc_gpu.setText("CPU")

        except ImportError:
            self.etykieta_gpu.setText(
                "PyTorch nie jest zainstalowany"
            )
            self.wartosc_gpu.setText("Brak")



    def closeEvent(self, zdarzenie):
        pracownicy = []

        for nazwa_panelu in (
                "panel_augmentacji",
                "panel_statystyk",
                "panel_trenowania",
                "panel_wynikow"
        ):
            panel = getattr(self, nazwa_panelu, None)

            if panel is not None:
                pracownik = getattr(
                    panel, "pracownik", None
                )

                if (
                        pracownik is not None
                        and pracownik.isRunning()
                ):
                    pracownicy.append(pracownik)

        if pracownicy:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Trwające obliczenia",
                "Trwa trenowanie lub testowanie modelu.\n"
                "Zakończ obliczenia przed zamknięciem aplikacji."
            )
            zdarzenie.ignore()
            return

        zdarzenie.accept()




    def ustaw_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f3f4f6;
            }

            #menuBoczne {
                background-color: #111827;
            }

            #tytulAplikacji {
                color: #ffffff;
                font-size: 23px;
                font-weight: bold;
            }

            #podtytulAplikacji {
                color: #9ca3af;
                font-size: 12px;
            }

            #przyciskMenu {
                background-color: transparent;
                color: #d1d5db;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 15px;
                font-size: 13px;
            }

            #przyciskMenu:hover {
                background-color: #374151;
            }

            #przyciskMenu:checked {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
            }

            #informacjaGPU {
                color: #93c5fd;
                font-size: 11px;
            }

            #panelRoboczy {
                background-color: #f3f4f6;
            }

            #naglowek {
                color: #111827;
                font-size: 26px;
                font-weight: bold;
            }

            #opis {
                color: #6b7280;
                font-size: 13px;
            }

            #karta {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }

            #wartosc {
                color: #111827;
                font-size: 28px;
                font-weight: bold;
            }

            #tytulSekcji {
                color: #111827;
                font-size: 17px;
                font-weight: bold;
            }

            #przyciskAkcji {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 13px;
                font-weight: bold;
            }

            #przyciskAkcji:hover {
                background-color: #1d4ed8;
            }

            QComboBox {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 7px;
                color: #111827;
            }
            #przyciskOdswiez {
            background-color: #e5e7eb;
            color: #111827;
            border: 1px solid #d1d5db;
            border-radius: 7px;
            font-size: 13px;
            font-weight: bold;
            }
            
            #przyciskOdswiez:hover {
            background-color: #d1d5db;
            }
            
            #przyciskUsunAugmentacje {
                background-color: #fff7ed;
                color: #9a3412;
                border: 1px solid #fed7aa;
                border-radius: 7px;
                font-size: 13px;
                font-weight: bold;
            }
            
            #przyciskUsunAugmentacje:hover {
                background-color: #ffedd5;
            }
            
            #przyciskUsunModele {
                background-color: #fef2f2;
                color: #991b1b;
                border: 1px solid #fecaca;
                border-radius: 7px;
                font-size: 13px;
                font-weight: bold;
            }
            
            #przyciskUsunModele:hover {
                background-color: #fee2e2;
            }

        """)
