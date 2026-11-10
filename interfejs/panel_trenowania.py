
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QComboBox,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox
)

from moduly.trenowanie_yolo import (
    PracownikTrenowania,
    wczytaj_model,
    KATALOG_PROJEKTU
)



class PanelTrenowania(QWidget):

    def __init__(self, pobierz_zbior, parent=None):
        super().__init__(parent)

        self.pobierz_zbior = pobierz_zbior
        self.pracownik = None
        self.model = None
        self.sciezka_modelu = None

        self.utworz_interfejs()

    def utworz_interfejs(self):
        uklad = QVBoxLayout(self)
        uklad.setContentsMargins(35, 30, 35, 30)
        uklad.setSpacing(15)

        tytul = QLabel("Trenowanie modeli YOLO")
        tytul.setStyleSheet(
            "font-size: 25px; font-weight: bold;"
            "color: #111827;"
        )
        uklad.addWidget(tytul)

        opis = QLabel(
            "Uczenie, zapisywanie i ponowne "
            "wczytywanie modeli klasyfikacyjnych."
        )
        opis.setStyleSheet("color: #64748b;")
        uklad.addWidget(opis)

        # WYBRANY ZBIOR
        self.etykieta_zbioru = QLabel()
        self.etykieta_zbioru.setStyleSheet(
            "font-weight: bold; font-size: 14px;"
        )
        uklad.addWidget(self.etykieta_zbioru)

        # USTAWIENIA
        grupa = QGroupBox("Parametry trenowania")
        ustawienia = QVBoxLayout(grupa)

        # WYBOR MODELU YOLO
        wiersz_model = QHBoxLayout()
        wiersz_model.addWidget(QLabel("Model YOLO:"))

        self.wybor_modelu = QComboBox()
        self.wybor_modelu.addItems([
            "yolo26n-cls.pt",
            "yolo26s-cls.pt",
            "yolo26m-cls.pt"
        ])

        wiersz_model.addWidget(self.wybor_modelu)
        ustawienia.addLayout(wiersz_model)

        wiersz_epoki = QHBoxLayout()
        wiersz_epoki.addWidget(QLabel("Liczba epok:"))

        self.epoki = QSpinBox()
        self.epoki.setRange(1, 500)
        self.epoki.setValue(30)

        wiersz_epoki.addWidget(self.epoki)
        ustawienia.addLayout(wiersz_epoki)

        wiersz_rozmiar = QHBoxLayout()
        wiersz_rozmiar.addWidget(
            QLabel("Rozmiar obrazów:")
        )

        self.rozmiar = QComboBox()
        self.rozmiar.addItems(["224", "320", "416"])
        wiersz_rozmiar.addWidget(self.rozmiar)
        ustawienia.addLayout(wiersz_rozmiar)

        wiersz_partia = QHBoxLayout()
        wiersz_partia.addWidget(
            QLabel("Wielkość partii (batch):")
        )

        self.partia = QComboBox()
        self.partia.addItems(["4", "8", "16"])
        self.partia.setCurrentText("8")

        wiersz_partia.addWidget(self.partia)
        ustawienia.addLayout(wiersz_partia)

        uklad.addWidget(grupa)

        # PRZYCISK TRENINGU
        self.przycisk_start = QPushButton(
            "Rozpocznij trenowanie"
        )
        self.przycisk_start.setMinimumHeight(45)
        self.przycisk_start.clicked.connect(
            self.rozpocznij_trenowanie
        )
        uklad.addWidget(self.przycisk_start)

        # POSTEP
        self.pasek_postepu = QProgressBar()
        self.pasek_postepu.setRange(0, 100)
        self.pasek_postepu.setValue(0)
        uklad.addWidget(self.pasek_postepu)

        # ZAPISANY MODEL
        self.etykieta_modelu = QLabel(
            "Nie wczytano modelu."
        )
        self.etykieta_modelu.setWordWrap(True)
        uklad.addWidget(self.etykieta_modelu)

        self.przycisk_wczytaj = QPushButton(
            "Wczytaj zapisany model"
        )
        self.przycisk_wczytaj.setMinimumHeight(42)
        self.przycisk_wczytaj.clicked.connect(
            self.wybierz_model
        )
        uklad.addWidget(self.przycisk_wczytaj)

        self.przycisk_test = QPushButton(
            "Klasyfikuj wybrany obraz"
        )
        self.przycisk_test.setMinimumHeight(42)
        self.przycisk_test.setEnabled(False)
        self.przycisk_test.clicked.connect(
            self.klasyfikuj_obraz
        )
        uklad.addWidget(self.przycisk_test)

        # KOMUNIKATY
        uklad.addWidget(QLabel("Dziennik trenowania:"))

        self.dziennik = QTextEdit()
        self.dziennik.setReadOnly(True)
        self.dziennik.setMinimumHeight(140)
        uklad.addWidget(self.dziennik)

        self.setStyleSheet("""
            QWidget {
                background-color: #f3f4f6;
                color: #111827;
            }

            QGroupBox, QTextEdit, QComboBox, QSpinBox {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px;
            }

            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 7px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)

        self.odswiez_zbior()

    def odswiez_zbior(self):
        nazwa = self.pobierz_zbior()
        self.etykieta_zbioru.setText(
            f"Aktywny zbiór danych: {nazwa or 'Brak'}"
        )

    def rozpocznij_trenowanie(self):
        if self.pracownik is not None:
            if self.pracownik.isRunning():
                return

        nazwa_zbioru = self.pobierz_zbior()

        if not nazwa_zbioru:
            QMessageBox.warning(
                self, "Brak danych",
                "Najpierw wybierz zbiór danych."
            )
            return

        # Dane przygotowane mają pierwszeństwo.
        przygotowane = (
            KATALOG_PROJEKTU
            / "dane_przetworzone"
            / nazwa_zbioru
        )

        oryginalne = (
            KATALOG_PROJEKTU
            / "dane"
            / nazwa_zbioru
        )

        if (przygotowane / "train").is_dir():
            sciezka = przygotowane
        else:
            sciezka = oryginalne

        self.pasek_postepu.setValue(0)
        self.dziennik.clear()
        self.dziennik.append(
            f"Wybrany zbiór: {nazwa_zbioru}"
        )
        self.dziennik.append(
            f"Katalog treningowy: {sciezka}"
        )

        self.pracownik = PracownikTrenowania(
            nazwa_zbioru=nazwa_zbioru,
            sciezka_danych=oryginalne,
            epoki=self.epoki.value(),
            rozmiar=int(self.rozmiar.currentText()),
            partia=int(self.partia.currentText()),
            nazwa_modelu=self.wybor_modelu.currentText(),
            parent=self
        )

        self.pracownik.postep.connect(
            self.pasek_postepu.setValue
        )
        self.pracownik.komunikat.connect(
            self.dziennik.append
        )
        self.pracownik.sukces.connect(
            self.trening_zakonczony
        )
        self.pracownik.blad.connect(
            self.blad_treningu
        )
        self.pracownik.finished.connect(
            self.przywroc_przyciski
        )

        self.przycisk_start.setEnabled(False)
        self.przycisk_wczytaj.setEnabled(False)
        self.przycisk_test.setEnabled(False)

        self.pracownik.start()

    def przywroc_przyciski(self):
        self.przycisk_start.setEnabled(True)
        self.przycisk_wczytaj.setEnabled(True)
        self.przycisk_test.setEnabled(
            self.model is not None
        )

    def trening_zakonczony(self, sciezka):
        self.dziennik.append(
            "Trening zakończony pomyślnie."
        )
        self.zaladuj_model(sciezka)

        QMessageBox.information(
            self,
            "Trening zakończony",
            "Model został zapisany:\n" + sciezka
        )

    def blad_treningu(self, komunikat):
        self.dziennik.append(
            "BŁĄD: " + komunikat
        )

        QMessageBox.critical(
            self,
            "Błąd trenowania",
            komunikat
        )

    def wybierz_model(self):
        nazwa = self.pobierz_zbior()

        katalog = (
            KATALOG_PROJEKTU
            / "wyniki"
            / nazwa
        )

        katalog.mkdir(
            parents=True,
            exist_ok=True
        )

        sciezka, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz wytrenowany model YOLO",
            str(katalog),
            "Modele PyTorch (*.pt)"
        )

        if sciezka:
            self.zaladuj_model(sciezka)

    def zaladuj_model(self, sciezka):
        try:
            model = wczytaj_model(sciezka)
            self.model = model
            self.sciezka_modelu = Path(sciezka)

            self.etykieta_modelu.setText(
                "Wczytany model:\n"
                + str(self.sciezka_modelu)
            )

            self.przycisk_test.setEnabled(True)

            self.dziennik.append(
                f"Wczytano model: {sciezka}"
            )

        except Exception as blad:
            QMessageBox.critical(
                self,
                "Błąd wczytywania",
                str(blad)
            )

    def klasyfikuj_obraz(self):
        if self.model is None:
            return

        sciezka, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz obraz do klasyfikacji",
            str(KATALOG_PROJEKTU / "dane"),
            "Obrazy (*.jpg *.jpeg *.png *.bmp *.webp)"
        )

        if not sciezka:
            return

        try:
            wyniki = self.model.predict(
                source=sciezka,
                device=0,
                verbose=False
            )

            wynik = wyniki[0]

            indeks = wynik.probs.top1
            pewnosc = float(
                wynik.probs.top1conf.item()
            )
            nazwa_klasy = wynik.names[indeks]

            komunikat = (
                f"Przewidziana klasa: {nazwa_klasy}\n"
                f"Pewność: {pewnosc:.2%}"
            )

            self.dziennik.append(komunikat)

            QMessageBox.information(
                self,
                "Wynik klasyfikacji",
                komunikat
            )

        except Exception as blad:
            QMessageBox.critical(
                self,
                "Błąd klasyfikacji",
                str(blad)
            )
