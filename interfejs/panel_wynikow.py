
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QGroupBox
)

from moduly.testowanie_yolo import (
    PracownikTestowania,
    KATALOG_PROJEKTU
)


class PanelWynikow(QWidget):

    def __init__(self, pobierz_zbior, parent=None):
        super().__init__(parent)

        self.pobierz_zbior = pobierz_zbior
        self.sciezka_modelu = None
        self.pracownik = None
        self.sciezka_macierzy = None

        self.utworz_interfejs()
        self.odswiez_zbior()

    def utworz_interfejs(self):
        glowny_uklad = QVBoxLayout(self)
        glowny_uklad.setContentsMargins(0, 0, 0, 0)

        przewijanie = QScrollArea()
        przewijanie.setWidgetResizable(True)

        kontener = QWidget()
        uklad = QVBoxLayout(kontener)
        uklad.setContentsMargins(30, 25, 30, 25)
        uklad.setSpacing(18)

        # NAGLOWEK
        tytul = QLabel("Testowanie modeli YOLO")
        tytul.setObjectName("naglowekWynikow")
        uklad.addWidget(tytul)

        opis = QLabel(
            "Ocena skuteczności klasyfikacji "
            "na niezależnym zbiorze testowym."
        )
        uklad.addWidget(opis)

        self.etykieta_zbioru = QLabel()
        self.etykieta_zbioru.setObjectName(
            "etykietaZbioru"
        )
        uklad.addWidget(self.etykieta_zbioru)

        # WYBOR MODELU
        grupa_modelu = QGroupBox("Model do testowania")
        uklad_modelu = QVBoxLayout(grupa_modelu)

        self.etykieta_modelu = QLabel(
            "Nie wybrano modelu."
        )
        self.etykieta_modelu.setWordWrap(True)
        uklad_modelu.addWidget(self.etykieta_modelu)

        self.przycisk_model = QPushButton(
            "Wybierz zapisany model best.pt"
        )
        self.przycisk_model.clicked.connect(
            self.wybierz_model
        )
        uklad_modelu.addWidget(self.przycisk_model)

        self.przycisk_test = QPushButton(
            "Rozpocznij testowanie"
        )
        self.przycisk_test.clicked.connect(
            self.rozpocznij_test
        )
        uklad_modelu.addWidget(self.przycisk_test)

        uklad.addWidget(grupa_modelu)

        # POSTEP
        self.pasek_postepu = QProgressBar()
        self.pasek_postepu.setRange(0, 100)
        self.pasek_postepu.setValue(0)
        uklad.addWidget(self.pasek_postepu)

        # METRYKI
        uklad_metryk = QHBoxLayout()

        self.wartosc_accuracy = self.utworz_metryke(
            uklad_metryk, "Dokładność klasyfikacji"
        )

        self.wartosc_precision = self.utworz_metryke(
            uklad_metryk, "Precyzja"
        )

        self.wartosc_recall = self.utworz_metryke(
            uklad_metryk, "Czułość"
        )

        self.wartosc_f1 = self.utworz_metryke(
            uklad_metryk, "Miara F1"
        )

        uklad.addLayout(uklad_metryk)

        opis_macro = QLabel(
            "Precyzja, czułość i miara F1 są obliczane "
            "jako średnia nieważona ze wszystkich klas (macro)."
        )
        uklad.addWidget(opis_macro)

        # TABELA WYNIKOW
        uklad.addWidget(
            QLabel("Wyniki dla poszczególnych klas")
        )

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels([
            "Klasa",
            "Precyzja",
            "Czułość",
            "Miara F1",
            "Liczba obrazów"
        ])

        self.tabela.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.tabela.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.tabela.setMinimumHeight(180)
        uklad.addWidget(self.tabela)

        # MACIERZ POMYLEK
        uklad.addWidget(
            QLabel("Macierz pomyłek")
        )

        self.etykieta_macierzy = QLabel(
            "Macierz pojawi się po zakończeniu testu."
        )
        self.etykieta_macierzy.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.etykieta_macierzy.setMinimumHeight(260)

        uklad.addWidget(self.etykieta_macierzy)

        # RAPORT
        self.etykieta_raportu = QLabel(
            "Raport nie został jeszcze wygenerowany."
        )
        self.etykieta_raportu.setWordWrap(True)
        uklad.addWidget(self.etykieta_raportu)

        # DZIENNIK
        uklad.addWidget(
            QLabel("Dziennik testowania")
        )

        self.dziennik = QTextEdit()
        self.dziennik.setReadOnly(True)
        self.dziennik.setMinimumHeight(130)
        uklad.addWidget(self.dziennik)

        uklad.addStretch()

        przewijanie.setWidget(kontener)
        glowny_uklad.addWidget(przewijanie)

        self.setStyleSheet("""
            QWidget {
                background: #f3f4f6;
                color: #111827;
            }

            #naglowekWynikow {
                font-size: 25px;
                font-weight: bold;
            }

            #etykietaZbioru {
                font-size: 14px;
                font-weight: bold;
                color: #2563eb;
            }

            QGroupBox {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }

            QPushButton {
                background: #2563eb;
                color: white;
                min-height: 40px;
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

            QTableWidget, QTextEdit {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
            }
        """)

    def utworz_metryke(self, uklad, nazwa):
        karta = QGroupBox(nazwa)
        karta_uklad = QVBoxLayout(karta)

        wartosc = QLabel("—")
        wartosc.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        wartosc.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
            "color: #2563eb;"
        )

        karta_uklad.addWidget(wartosc)
        uklad.addWidget(karta)

        return wartosc

    def odswiez_zbior(self):
        nazwa = self.pobierz_zbior()

        self.etykieta_zbioru.setText(
            f"Aktywny zbiór: {nazwa or 'Brak'}"
        )

        # Nie dopuszczamy do wyboru modelu
        # z poprzedniego zbioru po zmianie danych.
        if getattr(self, "zbior_modelu", None) != nazwa:
            self.sciezka_modelu = None
            self.zbior_modelu = nazwa
            self.etykieta_modelu.setText(
                "Nie wybrano modelu."
            )

    def wybierz_model(self):
        if self.pracownik and self.pracownik.isRunning():
            return

        nazwa = self.pobierz_zbior()

        if not nazwa:
            QMessageBox.warning(
                self, "Brak zbioru",
                "Najpierw wybierz zbiór danych."
            )
            return

        katalog = (
            KATALOG_PROJEKTU / "wyniki" / nazwa
        )
        katalog.mkdir(
            parents=True, exist_ok=True
        )

        sciezka, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz zapisany model",
            str(katalog),
            "Modele PyTorch (*.pt)"
        )

        if not sciezka:
            return

        wybrany = Path(sciezka).resolve()

        # Ograniczenie do wynikow aktywnego zbioru
        if katalog.resolve() not in wybrany.parents:
            QMessageBox.warning(
                self,
                "Nieprawidłowy model",
                "Wybierz model z wyników aktywnego zbioru."
            )
            return

        self.sciezka_modelu = wybrany
        self.zbior_modelu = nazwa

        self.etykieta_modelu.setText(
            str(wybrany)
        )

    def rozpocznij_test(self):
        if self.pracownik and self.pracownik.isRunning():
            return

        if self.sciezka_modelu is None:
            QMessageBox.warning(
                self,
                "Brak modelu",
                "Najpierw wybierz zapisany model."
            )
            return

        nazwa = self.pobierz_zbior()

        self.pasek_postepu.setValue(0)
        self.dziennik.clear()

        self.dziennik.append(
            f"Zbiór: {nazwa}"
        )
        self.dziennik.append(
            f"Model: {self.sciezka_modelu}"
        )

        self.tabela.setRowCount(0)

        for etykieta in [
            self.wartosc_accuracy,
            self.wartosc_precision,
            self.wartosc_recall,
            self.wartosc_f1
        ]:
            etykieta.setText("—")

        self.etykieta_macierzy.setText(
            "Trwa testowanie..."
        )
        self.etykieta_macierzy.setPixmap(QPixmap())
        self.sciezka_macierzy = None

        self.pracownik = PracownikTestowania(
            nazwa_zbioru=nazwa,
            sciezka_modelu=self.sciezka_modelu,
            parent=self
        )

        self.pracownik.postep.connect(
            self.pasek_postepu.setValue
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
            self.zakoncz_prace
        )

        self.przycisk_test.setEnabled(False)
        self.przycisk_model.setEnabled(False)

        self.pracownik.start()

    def zakoncz_prace(self):
        self.przycisk_test.setEnabled(True)
        self.przycisk_model.setEnabled(True)

    def pokaz_blad(self, komunikat):
        self.dziennik.append(
            "BŁĄD: " + komunikat
        )

        QMessageBox.critical(
            self,
            "Błąd testowania",
            komunikat
        )

    def pokaz_wyniki(self, raport):
        self.wartosc_accuracy.setText(
            f"{raport['accuracy']:.2%}"
        )
        self.wartosc_precision.setText(
            f"{raport['precision']:.2%}"
        )
        self.wartosc_recall.setText(
            f"{raport['recall']:.2%}"
        )
        self.wartosc_f1.setText(
            f"{raport['f1']:.2%}"
        )

        metryki = raport["metryki_klas"]
        self.tabela.setRowCount(len(metryki))

        for wiersz, metryka in enumerate(metryki):
            wartosci = [
                metryka["klasa"],
                f"{metryka['precision']:.2%}",
                f"{metryka['recall']:.2%}",
                f"{metryka['f1']:.2%}",
                str(metryka["liczba_obrazow"])
            ]

            for kolumna, wartosc in enumerate(wartosci):
                self.tabela.setItem(
                    wiersz,
                    kolumna,
                    QTableWidgetItem(wartosc)
                )

        self.sciezka_macierzy = Path(
            raport["sciezka_macierzy"]
        )

        self.pokaz_macierz()

        self.etykieta_raportu.setText(
            "Raport zapisany w:\n"
            + raport["katalog_raportu"]
        )

        self.dziennik.append(
            "Wyniki zostały zapisane na dysku."
        )

        QMessageBox.information(
            self,
            "Testowanie zakończone",
            "Model został przetestowany pomyślnie."
        )

    def pokaz_macierz(self):
        if self.sciezka_macierzy is None:
            return

        pixmap = QPixmap(
            str(self.sciezka_macierzy)
        )

        if pixmap.isNull():
            self.etykieta_macierzy.setText(
                "Nie można wyświetlić macierzy."
            )
            return

        szerokosc = max(
            200, self.etykieta_macierzy.width() - 15
        )

        obraz = pixmap.scaled(
            szerokosc,
            480,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.etykieta_macierzy.setPixmap(obraz)

    def resizeEvent(self, zdarzenie):
        super().resizeEvent(zdarzenie)

        if self.sciezka_macierzy is not None:
            self.pokaz_macierz()
