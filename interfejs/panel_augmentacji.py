
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox,
    QSpinBox, QProgressBar, QTextEdit,
    QScrollArea, QMessageBox, QTableWidget,
    QHeaderView,QAbstractItemView,QDoubleSpinBox,
    QGroupBox,QFormLayout,
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
            self,
            zbior,
            metoda,
            liczba_kopii,
            ustawienia,
            ziarno=42,
            parent=None
    ):
        super().__init__(parent)

        self.zbior = zbior
        self.metoda = metoda
        self.liczba_kopii = liczba_kopii
        self.ustawienia = ustawienia.copy()
        self.ziarno = ziarno

    def run(self):
        try:
            raport = wykonaj_augmentacje(
                nazwa_zbioru=self.zbior,
                metoda=self.metoda,
                liczba_kopii=self.liczba_kopii,
                ustawienia=self.ustawienia,
                ziarno=self.ziarno,
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

    def utworz_pole(self, minimum, maksimum, wartosc,
                    krok=1.0, sufiks="", miejsca=1):
        """Tworzy pole liczbowe parametru augmentacji."""

        pole = QDoubleSpinBox()
        pole.setRange(minimum, maksimum)
        pole.setValue(wartosc)
        pole.setSingleStep(krok)
        pole.setDecimals(miejsca)
        pole.setSuffix(sufiks)
        pole.setMinimumWidth(135)

        return pole


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

        # ZIARNO LOSOWOSCI
        wiersz_ziarna = QHBoxLayout()

        wiersz_ziarna.addWidget(
            QLabel("Ziarno losowości (seed):")
        )

        self.pole_ziarno = QSpinBox()
        self.pole_ziarno.setRange(0, 999999999)
        self.pole_ziarno.setValue(42)
        self.pole_ziarno.setToolTip(
            "Ziarno decyduje o powtarzalności "
            "losowania zdjęć i transformacji."
        )

        wiersz_ziarna.addWidget(self.pole_ziarno)
        wiersz_ziarna.addStretch()

        uklad.addLayout(wiersz_ziarna)

        uklad.addWidget(self.wybor_metody)


        # PARAMETRY AUGMENTACJI
        self.grupy_ustawien = {}

        # OBRÓT
        grupa_obrot = QGroupBox("Ustawienia obrotu")
        formularz_obrot = QFormLayout(grupa_obrot)

        self.pole_obrot = self.utworz_pole(
            0, 90, 15, 1, "°"
        )

        formularz_obrot.addRow(
            "Maksymalny kąt obrotu (±):",
            self.pole_obrot
        )

        self.grupy_ustawien["Obrót"] = grupa_obrot
        uklad.addWidget(grupa_obrot)

        # SKALOWANIE
        grupa_skala = QGroupBox("Ustawienia skalowania")
        formularz_skala = QFormLayout(grupa_skala)

        self.pole_skala_min = self.utworz_pole(
            0.5, 2.0, 0.85, 0.05, " ×", 2
        )

        self.pole_skala_max = self.utworz_pole(
            0.5, 2.0, 1.15, 0.05, " ×", 2
        )

        formularz_skala.addRow(
            "Minimalna skala:",
            self.pole_skala_min
        )
        formularz_skala.addRow(
            "Maksymalna skala:",
            self.pole_skala_max
        )

        self.grupy_ustawien["Skalowanie"] = grupa_skala
        uklad.addWidget(grupa_skala)

        # PRZESUNIĘCIE
        grupa_przesuniecie = QGroupBox(
            "Ustawienia przesunięcia"
        )
        formularz_przesuniecie = QFormLayout(
            grupa_przesuniecie
        )

        self.pole_przesuniecie = self.utworz_pole(
            0, 40, 10, 1, " %"
        )

        formularz_przesuniecie.addRow(
            "Maksymalne przesunięcie (±):",
            self.pole_przesuniecie
        )

        self.grupy_ustawien["Przesunięcie"] = (
            grupa_przesuniecie
        )
        uklad.addWidget(grupa_przesuniecie)

        # ZMIANA KOLORÓW
        grupa_kolory = QGroupBox(
            "Ustawienia zmiany kolorów"
        )
        formularz_kolory = QFormLayout(grupa_kolory)

        self.pole_jasnosc = self.utworz_pole(
            0, 60, 20, 1, " %"
        )

        self.pole_kontrast = self.utworz_pole(
            0, 60, 20, 1, " %"
        )

        self.pole_nasycenie = self.utworz_pole(
            0, 60, 30, 1, " %"
        )

        formularz_kolory.addRow(
            "Zmiana jasności (±):",
            self.pole_jasnosc
        )
        formularz_kolory.addRow(
            "Zmiana kontrastu (±):",
            self.pole_kontrast
        )
        formularz_kolory.addRow(
            "Zmiana nasycenia (±):",
            self.pole_nasycenie
        )

        self.grupy_ustawien["Zmiana kolorów"] = grupa_kolory
        uklad.addWidget(grupa_kolory)

        # SZUM GAUSSOWSKI
        grupa_szum = QGroupBox(
            "Ustawienia szumu gaussowskiego"
        )
        formularz_szum = QFormLayout(grupa_szum)

        self.pole_szum = self.utworz_pole(
            0, 60, 12, 1, " σ"
        )

        formularz_szum.addRow(
            "Odchylenie standardowe szumu:",
            self.pole_szum
        )

        self.grupy_ustawien["Szum gaussowski"] = grupa_szum
        uklad.addWidget(grupa_szum)

        # ZMIANA WIDOCZNOŚCI PO WYBORZE METODY
        self.wybor_metody.currentTextChanged.connect(
            self.aktualizuj_widocznosc_ustawien
        )

        self.aktualizuj_widocznosc_ustawien(
            self.wybor_metody.currentText()
        )

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


    def aktualizuj_widocznosc_ustawien(self, metoda):
        """Pokazuje parametry właściwe dla wybranej metody."""

        pokaz_wszystkie = (
                metoda == "Wszystkie metody"
        )

        for nazwa, grupa in self.grupy_ustawien.items():
            grupa.setVisible(
                pokaz_wszystkie or nazwa == metoda
            )

    def pobierz_ustawienia(self):
        """Odczytuje aktualne parametry z formularza."""

        ustawienia = {
            "kat_obrotu": self.pole_obrot.value(),
            "skala_min": self.pole_skala_min.value(),
            "skala_max": self.pole_skala_max.value(),
            "przesuniecie": self.pole_przesuniecie.value(),
            "jasnosc": self.pole_jasnosc.value(),
            "kontrast": self.pole_kontrast.value(),
            "nasycenie": self.pole_nasycenie.value(),
            "szum": self.pole_szum.value()
        }

        if ustawienia["skala_min"] > ustawienia["skala_max"]:
            raise ValueError(
                "Minimalna skala nie może być większa "
                "od maksymalnej."
            )

        return ustawienia

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


        try:
            ustawienia = self.pobierz_ustawienia()
        except ValueError as blad:
            QMessageBox.warning(
                self,
                "Nieprawidłowe parametry",
                str(blad)
            )
            return

        self.pracownik = PracownikAugmentacji(
            zbior=nazwa,
            metoda=self.wybor_metody.currentText(),
            liczba_kopii=self.liczba_kopii.value(),
            ustawienia=ustawienia,
            ziarno=self.pole_ziarno.value(),
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

        # Po zakończeniu augmentacji odblokuj ustawienia
        self.pracownik.finished.connect(
            self.zakoncz_augmentacje
        )

        self.wybor_metody.setEnabled(False)
        self.liczba_kopii.setEnabled(False)

        for grupa in self.grupy_ustawien.values():
            grupa.setEnabled(False)

        # Zablokuj zmienianie ustawień podczas augmentacji
        self.przycisk_start.setEnabled(False)
        self.pole_ziarno.setEnabled(False)

        # Uruchom augmentację
        self.pracownik.start()

    def zakoncz_augmentacje(self):
        """Odblokowuje kontrolki po zakończeniu augmentacji."""

        self.przycisk_start.setEnabled(True)
        self.pole_ziarno.setEnabled(True)
        self.wybor_metody.setEnabled(True)
        self.liczba_kopii.setEnabled(True)

        for grupa in self.grupy_ustawien.values():
            grupa.setEnabled(True)


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
