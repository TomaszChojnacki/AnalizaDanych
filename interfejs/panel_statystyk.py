import json
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QMessageBox
)

from moduly.analiza_statystyczna import analizuj_zbior
from moduly.wizualizacja_statystyk import generuj_wykresy
from moduly.analiza_statystyczna import KATALOG_PROJEKTU


class PracownikAnalizy(QThread):
    sukces = Signal(object)
    blad = Signal(str)

    def __init__(self, nazwa_zbioru, parent=None):
        super().__init__(parent)
        self.nazwa_zbioru = nazwa_zbioru



    def run(self):
        try:
            # Analiza oryginalnych obrazow
            raport = analizuj_zbior(
                self.nazwa_zbioru
            )

            wykresy = generuj_wykresy(raport)
            raport["wykresy"] = wykresy
            raport["porownanie_augmentacji"] = False

            # Szukanie raportow wykonanej augmentacji
            katalog_wynikow = (
                    KATALOG_PROJEKTU
                    / "wyniki"
                    / self.nazwa_zbioru
            )

            raporty = sorted(
                katalog_wynikow.glob(
                    "augmentacja_*/raport.json"
                ),
                key=lambda plik: plik.stat().st_mtime,
                reverse=True
            )

            liczebnosci_train = {
                rekord["klasa"]: rekord["train"]
                for rekord in raport["klasy"]
            }

            # Wybieramy najnowsza zgodna augmentacje
            for plik_raportu in raporty:
                with plik_raportu.open(
                        encoding="utf-8"
                ) as plik:
                    raport_aug = json.load(plik)

                liczebnosci_przed = {
                    rekord["klasa"]: rekord["przed"]
                    for rekord in raport_aug["klasy"]
                }

                if liczebnosci_przed != liczebnosci_train:
                    continue

                sciezka_wykresu = (
                        plik_raportu.parent
                        / "porownanie_przed_po.png"
                )

                if sciezka_wykresu.is_file():
                    raport["wykresy"]["slupkowy"] = str(
                        sciezka_wykresu
                    )
                    raport["porownanie_augmentacji"] = True
                    raport["metoda_augmentacji"] = (
                        raport_aug["metoda"]
                    )
                    break

            self.sukces.emit(raport)

        except Exception as blad:
            self.blad.emit(str(blad))





class PanelStatystyk(QWidget):

    def __init__(self, pobierz_zbior, parent=None):
        super().__init__(parent)

        self.pobierz_zbior = pobierz_zbior
        self.pracownik = None
        self.raport = None

        self.utworz_interfejs()
        self.odswiez_zbior()

    def utworz_interfejs(self):
        glowny = QVBoxLayout(self)
        glowny.setContentsMargins(0, 0, 0, 0)

        przewijanie = QScrollArea()
        przewijanie.setWidgetResizable(True)

        kontener = QWidget()
        uklad = QVBoxLayout(kontener)
        uklad.setContentsMargins(30, 25, 30, 25)
        uklad.setSpacing(18)

        tytul = QLabel("Analiza statystyczna obrazów")
        tytul.setObjectName("naglowekStatystyk")
        uklad.addWidget(tytul)

        self.etykieta_zbioru = QLabel()
        uklad.addWidget(self.etykieta_zbioru)

        self.przycisk_analizy = QPushButton(
            "Rozpocznij analizę statystyczną"
        )
        self.przycisk_analizy.clicked.connect(
            self.rozpocznij_analize
        )
        uklad.addWidget(self.przycisk_analizy)

        self.etykieta_statusu = QLabel(
            "Oczekiwanie na rozpoczęcie analizy."
        )
        self.etykieta_statusu.setWordWrap(True)
        uklad.addWidget(self.etykieta_statusu)

        # PODSUMOWANIE
        wiersz = QHBoxLayout()

        self.wartosc_klas = self.utworz_metryke(
            wiersz, "Liczba klas"
        )
        self.wartosc_obrazow = self.utworz_metryke(
            wiersz, "Liczba obrazów"
        )
        self.wartosc_blednych = self.utworz_metryke(
            wiersz, "Błędne obrazy"
        )

        uklad.addLayout(wiersz)

        # TABELA
        uklad.addWidget(
            QLabel("Liczebność obrazów w klasach")
        )

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels([
            "Klasa",
            "Trening",
            "Test",
            "Razem",
            "Udział (%)"
        ])

        self.tabela.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabela.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabela.setMinimumHeight(170)
        uklad.addWidget(self.tabela)

        # DODATKOWE STATYSTYKI
        self.etykieta_wymiarow = QLabel()
        self.etykieta_wymiarow.setWordWrap(True)
        uklad.addWidget(self.etykieta_wymiarow)

        self.etykieta_formatow = QLabel()
        self.etykieta_formatow.setWordWrap(True)
        uklad.addWidget(self.etykieta_formatow)

        # WYKRESY
        self.tytul_wykresu = QLabel(
            "Liczebność klas przed augmentacją"
        )
        uklad.addWidget(self.tytul_wykresu)

        self.wykres_slupkowy = QLabel(
            "Brak wykresu"
        )
        self.wykres_slupkowy.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.wykres_slupkowy.setMinimumHeight(300)
        uklad.addWidget(self.wykres_slupkowy)

        uklad.addWidget(
            QLabel("Wykres kołowy")
        )

        self.wykres_kolowy = QLabel(
            "Brak wykresu"
        )
        self.wykres_kolowy.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.wykres_kolowy.setMinimumHeight(300)
        uklad.addWidget(self.wykres_kolowy)

        self.etykieta_raportu = QLabel()
        self.etykieta_raportu.setWordWrap(True)
        uklad.addWidget(self.etykieta_raportu)

        uklad.addStretch()

        przewijanie.setWidget(kontener)
        glowny.addWidget(przewijanie)

        self.setStyleSheet("""
            QWidget {
                background: #f3f4f6;
                color: #111827;
            }

            #naglowekStatystyk {
                font-size: 25px;
                font-weight: bold;
            }

            QPushButton {
                background: #2563eb;
                color: white;
                min-height: 43px;
                border: none;
                border-radius: 7px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #1d4ed8;
            }

            QPushButton:disabled {
                background: #9ca3af;
            }

            QTableWidget {
                background: white;
                border: 1px solid #d1d5db;
            }
        """)

    def utworz_metryke(self, uklad, nazwa):
        kontener = QWidget()
        pionowy = QVBoxLayout(kontener)

        tytul = QLabel(nazwa)
        pionowy.addWidget(tytul)

        wartosc = QLabel("—")
        wartosc.setStyleSheet(
            "font-size: 24px;"
            "font-weight: bold;"
            "color: #2563eb;"
        )
        pionowy.addWidget(wartosc)

        uklad.addWidget(kontener)
        return wartosc

    def odswiez_zbior(self):
        nazwa = self.pobierz_zbior()
        self.etykieta_zbioru.setText(
            f"Aktywny zbiór: {nazwa or 'Brak'}"
        )

        if self.raport is not None:
            if self.raport["zbior"] != nazwa:
                self.wyczysc_wyniki()

    def wyczysc_wyniki(self):
        self.raport = None
        self.tabela.setRowCount(0)

        self.wartosc_klas.setText("—")
        self.wartosc_obrazow.setText("—")
        self.wartosc_blednych.setText("—")

        self.etykieta_wymiarow.clear()
        self.etykieta_formatow.clear()
        self.etykieta_raportu.clear()

        self.wykres_slupkowy.clear()
        self.wykres_kolowy.clear()

    def rozpocznij_analize(self):
        if self.pracownik and self.pracownik.isRunning():
            return

        nazwa = self.pobierz_zbior()

        if not nazwa:
            QMessageBox.warning(
                self,
                "Brak zbioru",
                "Wybierz zbiór danych."
            )
            return

        self.wyczysc_wyniki()
        self.etykieta_statusu.setText(
            "Trwa analiza obrazów..."
        )
        self.przycisk_analizy.setEnabled(False)

        self.pracownik = PracownikAnalizy(
            nazwa,
            parent=self
        )

        self.pracownik.sukces.connect(
            self.pokaz_wyniki
        )
        self.pracownik.blad.connect(
            self.pokaz_blad
        )
        self.pracownik.finished.connect(
            lambda: self.przycisk_analizy.setEnabled(True)
        )

        self.pracownik.start()

    def pokaz_wyniki(self, raport):
        self.raport = raport

        self.wartosc_klas.setText(
            str(raport["liczba_klas"])
        )
        self.wartosc_obrazow.setText(
            str(raport["liczba_obrazow"])
        )
        self.wartosc_blednych.setText(
            str(raport["liczba_blednych"])
        )

        klasy = raport["klasy"]
        self.tabela.setRowCount(len(klasy))

        for indeks, rekord in enumerate(klasy):
            wartosci = [
                rekord["klasa"],
                str(rekord["train"]),
                str(rekord["test"]),
                str(rekord["razem"]),
                f"{rekord['procent']:.2f}"
            ]

            for kolumna, wartosc in enumerate(wartosci):
                self.tabela.setItem(
                    indeks,
                    kolumna,
                    QTableWidgetItem(wartosc)
                )

        self.etykieta_wymiarow.setText(
            "Średnia rozdzielczość: "
            f"{raport['srednia_szerokosc']:.0f} × "
            f"{raport['srednia_wysokosc']:.0f} px\n"
            "Zakres szerokości: "
            f"{raport['minimalna_szerokosc']}–"
            f"{raport['maksymalna_szerokosc']} px\n"
            "Zakres wysokości: "
            f"{raport['minimalna_wysokosc']}–"
            f"{raport['maksymalna_wysokosc']} px"
        )

        formaty = ", ".join(
            f"{nazwa}: {liczba}"
            for nazwa, liczba in raport["formaty"].items()
        )
        self.etykieta_formatow.setText(
            "Formaty: " + formaty
        )


        if raport["porownanie_augmentacji"]:
            self.tytul_wykresu.setText(
                "Porównanie przed i po augmentacji "
                "(zbiór treningowy)\n"
                "Metoda: " + raport["metoda_augmentacji"]
            )
        else:
            self.tytul_wykresu.setText(
                "Liczebność klas przed augmentacją"
            )


        self.pokaz_obraz(
            self.wykres_slupkowy,
            raport["wykresy"]["slupkowy"]
        )
        self.pokaz_obraz(
            self.wykres_kolowy,
            raport["wykresy"]["kolowy"]
        )

        self.etykieta_raportu.setText(
            "Raport zapisany w:\n"
            + raport["katalog_wynikow"]
        )

        self.etykieta_statusu.setText(
            "Analiza zakończona pomyślnie."
        )

    def pokaz_obraz(self, etykieta, sciezka):
        obraz = QPixmap(str(Path(sciezka)))

        if obraz.isNull():
            etykieta.setText(
                "Nie udało się wczytać wykresu."
            )
            return

        etykieta.setPixmap(
            obraz.scaled(
                650,
                350,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def pokaz_blad(self, komunikat):
        self.etykieta_statusu.setText(
            "Analiza zakończona błędem."
        )

        QMessageBox.critical(
            self,
            "Błąd analizy",
            komunikat
        )
