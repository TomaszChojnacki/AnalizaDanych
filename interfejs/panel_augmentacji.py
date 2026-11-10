
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox,
    QSpinBox, QProgressBar, QTextEdit,
    QScrollArea, QMessageBox, QTableWidget, QHeaderView,QAbstractItemView
)

from moduly.augmentacja_obrazow import (
    wykonaj_augmentacje
)
from moduly.wizualizacja_statystyk import (
    generuj_wykres_porownawczy
)


class PracownikAugmentacji(QThread):
    postep = Signal(int)
    komunikat = Signal(str)
    sukces = Signal(object)
    blad = Signal(str)

    def __init__(
        self, zbior, metoda, liczba_kopii, parent=None
    ):
        super().__init__(parent)
        self.zbior = zbior
        self.metoda = metoda
        self.liczba_kopii = liczba_kopii

    def run(self):
        try:
            raport = wykonaj_augmentacje(
                nazwa_zbioru=self.zbior,
                metoda=self.metoda,
                liczba_kopii=self.liczba_kopii,
                komunikat=self.komunikat.emit,
                postep=self.postep.emit
            )

            raport["wykres"] = (
                generuj_wykres_porownawczy(raport)
            )

            self.sukces.emit(raport)

        except Exception as blad:
            self.blad.emit(str(blad))


class PanelAugmentacji(QWidget):

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
        uklad.setSpacing(16)

        tytul = QLabel("Augmentacja obrazów")
        tytul.setStyleSheet(
            "font-size: 25px; font-weight: bold;"
        )
        uklad.addWidget(tytul)

        self.etykieta_zbioru = QLabel()
        uklad.addWidget(self.etykieta_zbioru)

        uklad.addWidget(QLabel("Metoda augmentacji:"))

        self.wybor_metody = QComboBox()
        self.wybor_metody.addItems([
            "Obrót",
            "Skalowanie",
            "Przesunięcie",
            "Zmiana kolorów",
            "Szum gaussowski",
            "Wszystkie metody"
        ])
        self.wybor_metody.setCurrentText(
            "Wszystkie metody"
        )
        uklad.addWidget(self.wybor_metody)

        wiersz = QHBoxLayout()
        wiersz.addWidget(
            QLabel("Nowe obrazy na jeden oryginał:")
        )

        self.liczba_kopii = QSpinBox()
        self.liczba_kopii.setRange(1, 10)
        self.liczba_kopii.setValue(2)
        wiersz.addWidget(self.liczba_kopii)

        uklad.addLayout(wiersz)

        self.przycisk_start = QPushButton(
            "Rozpocznij augmentację"
        )
        self.przycisk_start.setMinimumHeight(43)
        self.przycisk_start.clicked.connect(
            self.rozpocznij_augmentacje
        )
        uklad.addWidget(self.przycisk_start)

        self.pasek = QProgressBar()
        self.pasek.setRange(0, 100)
        self.pasek.setValue(0)
        uklad.addWidget(self.pasek)

        self.etykieta_liczebnosci = QLabel(
            "Nie wykonano jeszcze augmentacji."
        )
        uklad.addWidget(self.etykieta_liczebnosci)

        # ---------------------------------
        # TABELA POROWNANIA AUGMENTACJI
        # ---------------------------------

        tytul_tabeli = QLabel(
            "Porównanie metod augmentacji dla każdej klasy"
        )
        tytul_tabeli.setStyleSheet(
            "font-size: 17px; font-weight: bold;"
        )
        uklad.addWidget(tytul_tabeli)

        opis_tabeli = QLabel(
            "Każdy wiersz przedstawia jedno losowe zdjęcie "
            "z danej klasy oraz jego wersje po augmentacji."
        )
        opis_tabeli.setWordWrap(True)
        uklad.addWidget(opis_tabeli)

        self.tabela_augmentacji = QTableWidget()

        self.tabela_augmentacji.setMinimumHeight(540)
        self.tabela_augmentacji.setAlternatingRowColors(True)

        self.tabela_augmentacji.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.tabela_augmentacji.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )

        self.tabela_augmentacji.setWordWrap(True)

        self.tabela_augmentacji.verticalHeader().setVisible(False)

        self.tabela_augmentacji.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.tabela_augmentacji.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8fafc;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                gridline-color: #e5e7eb;
            }

            QHeaderView::section {
                background-color: #e5e7eb;
                color: #111827;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #d1d5db;
            }
        """)

        uklad.addWidget(self.tabela_augmentacji)





        # Wykres porównawczy
        uklad.addWidget(
            QLabel("Liczebność przed i po augmentacji")
        )

        self.etykieta_wykresu = QLabel()
        self.etykieta_wykresu.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.etykieta_wykresu.setMinimumHeight(350)
        uklad.addWidget(self.etykieta_wykresu)

        self.etykieta_katalogu = QLabel()
        self.etykieta_katalogu.setWordWrap(True)
        uklad.addWidget(self.etykieta_katalogu)

        uklad.addWidget(QLabel("Dziennik augmentacji"))

        self.dziennik = QTextEdit()
        self.dziennik.setReadOnly(True)
        self.dziennik.setMinimumHeight(130)
        uklad.addWidget(self.dziennik)

        uklad.addStretch()

        przewijanie.setWidget(kontener)
        glowny.addWidget(przewijanie)

        self.setStyleSheet("""
            QWidget {
                background-color: #f3f4f6;
                color: #111827;
            }

            QComboBox, QSpinBox, QTextEdit {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px;
            }

            QPushButton {
                background: #2563eb;
                color: white;
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
        """)

    def odswiez_zbior(self):
        nazwa = self.pobierz_zbior()
        self.etykieta_zbioru.setText(
            f"Aktywny zbiór: {nazwa or 'Brak'}"
        )

    def rozpocznij_augmentacje(self):
        if self.pracownik and self.pracownik.isRunning():
            return

        nazwa = self.pobierz_zbior()

        if not nazwa:
            QMessageBox.warning(
                self, "Brak zbioru",
                "Najpierw wybierz zbiór danych."
            )
            return

        self.pasek.setValue(0)
        self.dziennik.clear()
        self.etykieta_liczebnosci.setText(
            "Trwa przetwarzanie obrazów..."
        )

        self.pracownik = PracownikAugmentacji(
            zbior=nazwa,
            metoda=self.wybor_metody.currentText(),
            liczba_kopii=self.liczba_kopii.value(),
            parent=self
        )

        self.pracownik.postep.connect(
            self.pasek.setValue
        )
        self.pracownik.komunikat.connect(
            self.dziennik.append
        )
        self.pracownik.sukces.connect(
            self.pokaz_wyniki
        )
        self.pracownik.blad.connect(
            self.pokaz_blad
        )
        self.pracownik.finished.connect(
            lambda: self.przycisk_start.setEnabled(True)
        )

        self.przycisk_start.setEnabled(False)
        self.pracownik.start()

    def pokaz_obraz(self, etykieta, sciezka, w, h):
        pixmap = QPixmap(str(sciezka))

        if pixmap.isNull():
            etykieta.setText(
                "Nie można wczytać obrazu."
            )
            return

        etykieta.setPixmap(
            pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )



    def pokaz_tabele_augmentacji(self, dane):
        """
        Wyswietla obrazy oryginalne i ich augmentacje
        w tabeli, osobno dla kazdej klasy.
        """

        metody = dane["metody"]
        wiersze = dane["wiersze"]

        tabela = self.tabela_augmentacji
        tabela.clear()

        tabela.setRowCount(len(wiersze))
        tabela.setColumnCount(len(metody) + 1)

        tabela.setHorizontalHeaderLabels(
            ["Klasa"] + metody
        )

        tabela.setColumnWidth(0, 125)

        for kolumna in range(1, len(metody) + 1):
            tabela.setColumnWidth(kolumna, 205)

        tabela.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )

        tabela.verticalHeader().setDefaultSectionSize(175)

        for numer_wiersza, rekord in enumerate(wiersze):
            nazwa_klasy = rekord["klasa"]

            # Pierwsza kolumna zawiera nazwe klasy
            etykieta_klasy = QLabel(nazwa_klasy)
            etykieta_klasy.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            etykieta_klasy.setStyleSheet(
                "font-size: 14px;"
                "font-weight: bold;"
            )

            tabela.setCellWidget(
                numer_wiersza,
                0,
                etykieta_klasy
            )

            # Kolejne kolumny zawieraja obrazy
            for numer_kolumny, metoda in enumerate(
                    metody, start=1
            ):
                sciezka = rekord["obrazy"].get(metoda)

                etykieta_obrazu = QLabel()
                etykieta_obrazu.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                etykieta_obrazu.setStyleSheet(
                    "background-color: white;"
                )

                if sciezka:
                    obraz = QPixmap(sciezka)

                    if not obraz.isNull():
                        etykieta_obrazu.setPixmap(
                            obraz.scaled(
                                185,
                                150,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                        )

                        etykieta_obrazu.setToolTip(sciezka)
                    else:
                        etykieta_obrazu.setText(
                            "Błąd wczytywania"
                        )
                else:
                    etykieta_obrazu.setText(
                        "Brak obrazu"
                    )

                tabela.setCellWidget(
                    numer_wiersza,
                    numer_kolumny,
                    etykieta_obrazu
                )

    def pokaz_wyniki(self, raport):
        self.raport = raport

        # Liczebnosc obrazow
        self.etykieta_liczebnosci.setText(
            f"Przed augmentacją: {raport['liczba_przed']} obrazów"
            f"   |   "
            f"Po augmentacji: {raport['liczba_po']} obrazów"
        )

        # Tabela dla wszystkich klas
        przyklady = raport.get("przyklady_augmentacji")

        if przyklady:
            self.pokaz_tabele_augmentacji(przyklady)

        # Wykres liczebnosci klas przed i po augmentacji
        self.pokaz_obraz(
            self.etykieta_wykresu,
            raport["wykres"],
            800,
            450
        )

        # Katalog wynikowy
        self.etykieta_katalogu.setText(
            "Dane po augmentacji:\n"
            + raport["katalog_danych"]
            + "\n\nRaport zapisany w:\n"
            + raport["katalog_raportu"]
        )

        self.dziennik.append(
            "Wygenerowano tabelę porównawczą obrazów."
        )

        self.dziennik.append(
            "Zapisano wykres liczebności klas."
        )

        QMessageBox.information(
            self,
            "Augmentacja zakończona",
            "Augmentacja została zakończona pomyślnie.\n"
            "Tabela obrazów i wykres są gotowe."
        )

    def pokaz_blad(self, tekst):
        self.etykieta_liczebnosci.setText(
            "Augmentacja nie powiodła się."
        )
        self.dziennik.append(
            "BŁĄD: " + tekst
        )

        QMessageBox.critical(
            self, "Błąd augmentacji", tekst
        )
