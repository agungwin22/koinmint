"""
ui.py
=====
Modul Antarmuka Pengguna (PyQt5).

Berisi:
    - Fungsi `_resource_path()` (dev + PyInstaller).
    - Palet tema `LIGHT_PALETTE` / `DARK_PALETTE` — Fresh Greens palette.
    - Template QSS + fungsi `build_stylesheet()` — termasuk styling
      menyeluruh untuk QFileDialog (non-native) agar teks & latar
      tetap kontras di kedua tema.
    - Kelas `EditTransactionDialog` (dialog form edit transaksi).
    - Kelas `MainWindow` (header ber-ikon, kartu ringkasan, form input,
      toolbar filter (search + kategori + bulan + tahun + reset),
      tabel transaksi dengan grid & kolom proporsional, menu File
      (Impor CSV / Ekspor CSV / Keluar), tombol aksi (Edit / Hapus),
      dialog Tentang).

Changelog:
    v0.3.0 — Search bar, filter kategori, tombol Edit.
    v0.4.0 — Ekspor CSV (utf-8-sig) + ekstraksi `_get_filtered_transactions`.
    v0.5.0 — Light/Dark Mode via QSettings, Reset Filter, tanggal dd/MM/yyyy.
    v0.6.0 — Ikon brand di header + window icon, palet mint/teal.
    v0.7.0 — Filter Bulan & Tahun, kartu ringkasan mengikuti filter aktif.
    v0.7.0+ UI polish: grid tabel + kolom proporsional.
    v0.7.0+ Fresh Greens palette.
    v0.7.0+ Import/Export: tombol "Ekspor CSV" dipindah ke menu File,
             aksi "Impor CSV..." (Ctrl+O) ditambahkan, handler toleran.
    v0.7.0+ File Dialog Fix: QFileDialog (QListView/QTreeView/QLineEdit/
             QComboBox/QLabel/QPushButton/QToolButton) sekarang eksplisit
             di-style di kedua tema; dialog dipaksa non-native via
             `DontUseNativeDialog` agar QSS dijamin berlaku di Linux Mint.
"""

import csv
import io
import os
import sys
import uuid
from string import Template

from PyQt5.QtCore import QDate, QSettings, Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models import APP_AUTHOR, APP_NAME, APP_VERSION, Transaction
from store import TransactionStore


# ============================================================
# Konstanta
# ============================================================
MONTH_NAMES_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

# Rasio & batas minimum kolom (Tanggal, Deskripsi, Kategori, Jenis, Jumlah)
COLUMN_RATIOS = [0.11, 0.40, 0.15, 0.13, 0.21]
COLUMN_MINS = [95, 220, 110, 100, 130]


# ============================================================
# Resource Helper (dev + PyInstaller)
# ============================================================
def _resource_path(relative_path: str) -> str:
    base_path = getattr(
        sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(base_path, relative_path)


def _extract_year_month(iso_date: str):
    """Ekstrak (year, month) dari ISO 'YYYY-MM-DD'; aman jika format aneh."""
    parts = (iso_date or "").split("-")
    year = parts[0] if len(parts) >= 1 else ""
    month = parts[1] if len(parts) >= 2 else ""
    if not (len(year) == 4 and year.isdigit()):
        year = ""
    if not (len(month) == 2 and month.isdigit()):
        month = ""
    return year, month


# ============================================================
# Palet Tema — Fresh Greens (Light)
# ============================================================
LIGHT_PALETTE = {
    "bg": "#d8f3dc",
    "card": "#ffffff",
    "card_border": "#95d5b2",
    "text": "#1b4332",
    "text_muted": "#2d6a4f",
    "text_title": "#081c15",
    "border": "#95d5b2",
    "border_focus": "#40916c",
    "primary": "#40916c",
    "primary_hover": "#2d6a4f",
    "primary_pressed": "#1b4332",
    "danger": "#c0392b",
    "danger_hover": "#a93226",
    "table_bg": "#ffffff",
    "table_alt": "#eefaf1",
    "table_header_bg": "#b7e4c7",
    "table_header_text": "#1b4332",
    "table_grid": "#95d5b2",
    "selection_bg": "#95d5b2",
    "selection_text": "#081c15",
    "menu_bg": "#ffffff",
    "menu_border": "#95d5b2",
    "version_bg": "#b7e4c7",
    "version_text": "#1b4332",
    "balance": "#081c15",
    "income": "#15803d",
    "expense": "#c0392b",
    "scrollbar_bg": "#d8f3dc",
    "scrollbar_handle": "#95d5b2",
}


# ============================================================
# Palet Tema — Fresh Greens (Dark)
# ============================================================
DARK_PALETTE = {
    "bg": "#081c15",
    "card": "#1b4332",
    "card_border": "#2d6a4f",
    "text": "#d8f3dc",
    "text_muted": "#95d5b2",
    "text_title": "#d8f3dc",
    "border": "#2d6a4f",
    "border_focus": "#74c69d",
    "primary": "#52b788",
    "primary_hover": "#74c69d",
    "primary_pressed": "#40916c",
    "danger": "#e05353",
    "danger_hover": "#c74242",
    "table_bg": "#1b4332",
    "table_alt": "#234e3c",
    "table_header_bg": "#2d6a4f",
    "table_header_text": "#b7e4c7",
    "table_grid": "#40916c",
    "selection_bg": "#40916c",
    "selection_text": "#d8f3dc",
    "menu_bg": "#1b4332",
    "menu_border": "#2d6a4f",
    "version_bg": "#2d6a4f",
    "version_text": "#95d5b2",
    "balance": "#d8f3dc",
    "income": "#74c69d",
    "expense": "#f87171",
    "scrollbar_bg": "#081c15",
    "scrollbar_handle": "#2d6a4f",
}


# ============================================================
# Template QSS
# ============================================================
QSS_TEMPLATE = Template("""
/* ---------- Root & Typography ---------- */
QMainWindow, QWidget#RootWidget {
    background-color: $bg;
}
QWidget {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: $text;
}
QDialog, QMessageBox {
    background-color: $card;
    color: $text;
}
QLabel { color: $text; background: transparent; }

/* ---------- Header ---------- */
#HeaderIcon { background: transparent; }
#HeaderTitle {
    font-size: 22px;
    font-weight: 700;
    color: $text_title;
    letter-spacing: 0.5px;
    background: transparent;
}
#HeaderVersion {
    font-size: 12px;
    font-weight: 600;
    color: $version_text;
    background-color: $version_bg;
    border-radius: 10px;
    padding: 4px 10px;
}

/* ---------- Cards ---------- */
#Card {
    background-color: $card;
    border-radius: 10px;
    border: 1px solid $card_border;
}
#CardTitle {
    font-size: 11px;
    font-weight: 600;
    color: $text_muted;
    letter-spacing: 1px;
    background: transparent;
}

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
    background-color: $card;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 6px 8px;
    min-height: 20px;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
    border: 1px solid $border_focus;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: $card;
    color: $text;
    border: 1px solid $border;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
    outline: 0;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: $primary;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 20px;
}
QPushButton:hover  { background-color: $primary_hover; }
QPushButton:pressed { background-color: $primary_pressed; }
QPushButton#DangerButton { background-color: $danger; }
QPushButton#DangerButton:hover { background-color: $danger_hover; }
QPushButton#GhostButton {
    background-color: transparent;
    color: $text;
    border: 1px solid $border;
    padding: 6px 12px;
}
QPushButton#GhostButton:hover {
    background-color: $selection_bg;
    border: 1px solid $border_focus;
}

/* ---------- Table ---------- */
QTableWidget {
    background-color: $table_bg;
    alternate-background-color: $table_alt;
    color: $text;
    border: 1px solid $card_border;
    border-radius: 10px;
    gridline-color: $table_grid;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
    outline: 0;
}
QTableWidget::item {
    padding: 6px 10px;
    border-right: 1px solid $table_grid;
    border-bottom: 1px solid $table_grid;
}
QTableWidget::item:selected {
    background-color: $selection_bg;
    color: $selection_text;
    border-right: 1px solid $table_grid;
    border-bottom: 1px solid $table_grid;
}
QHeaderView::section {
    background-color: $table_header_bg;
    color: $table_header_text;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid $card_border;
    border-bottom: 2px solid $card_border;
    font-weight: 600;
}

/* ---------- Menu & Status ---------- */
QMenuBar {
    background-color: $menu_bg;
    color: $text;
    border-bottom: 1px solid $menu_border;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
}
QMenuBar::item:selected {
    background-color: $selection_bg;
    border-radius: 4px;
}
QMenu {
    background-color: $menu_bg;
    color: $text;
    border: 1px solid $menu_border;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: $selection_bg;
    color: $selection_text;
}
QMenu::separator {
    height: 1px;
    background: $menu_border;
    margin: 4px 8px;
}
QStatusBar {
    background-color: $menu_bg;
    color: $text_muted;
    border-top: 1px solid $menu_border;
}
QStatusBar QLabel { color: $text_muted; }
QToolTip {
    background-color: $card;
    color: $text;
    border: 1px solid $border;
    padding: 4px 6px;
}

/* ---------- Scrollbar ---------- */
QScrollBar:vertical {
    background: $scrollbar_bg;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: $scrollbar_handle;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal {
    background: $scrollbar_bg;
    height: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: $scrollbar_handle;
    border-radius: 5px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* ---------- Calendar Popup ---------- */
QCalendarWidget QWidget { alternate-background-color: $card; }
QCalendarWidget QAbstractItemView:enabled {
    background-color: $card;
    color: $text;
    selection-background-color: $primary;
    selection-color: #ffffff;
}
QCalendarWidget QToolButton {
    color: $text;
    background-color: transparent;
}

/* ============================================================
   QFileDialog — non-native. Semua widget internal diberi
   background & color eksplisit agar kontrasnya jelas di
   Light maupun Dark mode (tidak ada teks terang di latar putih).
   ============================================================ */
QFileDialog {
    background-color: $bg;
    color: $text;
}
QFileDialog QLabel {
    background: transparent;
    color: $text;
}
QFileDialog QLineEdit,
QFileDialog QComboBox {
    background-color: $card;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 20px;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
}
QFileDialog QLineEdit:focus,
QFileDialog QComboBox:focus {
    border: 1px solid $border_focus;
}
QFileDialog QComboBox::drop-down {
    border: none;
    width: 20px;
}
QFileDialog QComboBox QAbstractItemView {
    background-color: $card;
    color: $text;
    border: 1px solid $border;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
    outline: 0;
}
QFileDialog QPushButton {
    background-color: $primary;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    min-height: 20px;
}
QFileDialog QPushButton:hover   { background-color: $primary_hover; }
QFileDialog QPushButton:pressed { background-color: $primary_pressed; }
QFileDialog QPushButton:disabled {
    background-color: $border;
    color: $text_muted;
}
QFileDialog QToolButton {
    background-color: transparent;
    color: $text;
    border: none;
    border-radius: 4px;
    padding: 4px;
}
QFileDialog QToolButton:hover {
    background-color: $selection_bg;
}
QFileDialog QListView,
QFileDialog QTreeView {
    background-color: $table_bg;
    alternate-background-color: $table_alt;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
    outline: 0;
}
QFileDialog QListView::item,
QFileDialog QTreeView::item {
    padding: 4px 6px;
}
QFileDialog QListView::item:selected,
QFileDialog QTreeView::item:selected {
    background-color: $selection_bg;
    color: $selection_text;
}
QFileDialog QHeaderView::section {
    background-color: $table_header_bg;
    color: $table_header_text;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid $card_border;
    border-bottom: 1px solid $card_border;
    font-weight: 600;
}
QFileDialog QSplitter::handle {
    background-color: $border;
}
""")


def build_stylesheet(palette: dict) -> str:
    return QSS_TEMPLATE.substitute(palette)


# Backward compat: main.py lama memakai STYLESHEET secara langsung.
STYLESHEET = build_stylesheet(LIGHT_PALETTE)


# ============================================================
# Dialog Edit Transaksi
# ============================================================
class EditTransactionDialog(QDialog):
    """Dialog modal untuk mengedit satu transaksi."""

    def __init__(self, transaction: Transaction, parent=None) -> None:
        super().__init__(parent)
        self._transaction = transaction
        self.setWindowTitle("Edit Transaksi")
        self.setModal(True)
        self.resize(420, 320)
        self._build_ui()
        self._populate(transaction)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 16)
        outer.setSpacing(14)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.input_date = QDateEdit()
        self.input_date.setCalendarPopup(True)
        self.input_date.setDisplayFormat("dd/MM/yyyy")

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Deskripsi transaksi...")

        self.input_category = QComboBox()
        self.input_category.setEditable(True)
        self.input_category.addItems(
            ["Umum", "Makan", "Transportasi", "Belanja",
             "Gaji", "Tagihan", "Lainnya"]
        )

        self.input_kind = QComboBox()
        self.input_kind.addItems(["Pengeluaran", "Pemasukan"])

        self.input_amount = QDoubleSpinBox()
        self.input_amount.setMaximum(1_000_000_000)
        self.input_amount.setDecimals(0)
        self.input_amount.setGroupSeparatorShown(True)
        self.input_amount.setPrefix("Rp ")

        form.addRow("Tanggal",   self.input_date)
        form.addRow("Deskripsi", self.input_desc)
        form.addRow("Kategori",  self.input_category)
        form.addRow("Jenis",     self.input_kind)
        form.addRow("Jumlah",    self.input_amount)
        outer.addLayout(form)
        outer.addStretch()

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch()
        cancel_btn = QPushButton("Batal")
        cancel_btn.setObjectName("GhostButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Simpan Perubahan")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        outer.addLayout(buttons)

    def _populate(self, t: Transaction) -> None:
        qdate = QDate.fromString(t.date, "yyyy-MM-dd")
        if qdate.isValid():
            self.input_date.setDate(qdate)
        self.input_desc.setText(t.description)

        idx = self.input_category.findText(t.category)
        if idx >= 0:
            self.input_category.setCurrentIndex(idx)
        else:
            self.input_category.setEditText(t.category)

        self.input_kind.setCurrentText(
            "Pemasukan" if t.kind == "income" else "Pengeluaran"
        )
        self.input_amount.setValue(t.amount)

    def _on_save(self) -> None:
        if not self.input_desc.text().strip():
            QMessageBox.warning(self, "Validasi", "Deskripsi tidak boleh kosong.")
            return
        if self.input_amount.value() <= 0:
            QMessageBox.warning(self, "Validasi", "Jumlah harus lebih dari 0.")
            return
        self.accept()

    def get_result(self) -> Transaction:
        kind = "income" if self.input_kind.currentText() == "Pemasukan" else "expense"
        category = self.input_category.currentText().strip() or "Umum"
        return Transaction(
            id=self._transaction.id,
            date=self.input_date.date().toString("yyyy-MM-dd"),
            description=self.input_desc.text().strip(),
            category=category,
            kind=kind,
            amount=self.input_amount.value(),
        )


# ============================================================
# Main Window
# ============================================================
class MainWindow(QMainWindow):
    THEME_SETTINGS_ORG = "SimpleFinanceApp"
    THEME_SETTINGS_APP = "PencatatanKeuangan"

    # Alias header CSV yang didukung saat impor (lowercase)
    IMPORT_HEADER_ALIASES = {
        "date":        {"tanggal", "date", "tgl"},
        "description": {"deskripsi", "description", "desc", "keterangan", "uraian"},
        "category":    {"kategori", "category", "cat"},
        "kind":        {"jenis", "kind", "type", "tipe"},
        "amount":      {"jumlah", "jumlah (rp)", "amount", "amount (rp)",
                        "nominal", "nilai"},
    }

    def __init__(self) -> None:
        super().__init__()

        self._settings = QSettings(self.THEME_SETTINGS_ORG, self.THEME_SETTINGS_APP)
        self.current_theme = self._settings.value("theme", "light")
        if self.current_theme not in ("light", "dark"):
            self.current_theme = "light"

        self._icon_path = _resource_path(os.path.join("assets", "koinmint.png"))

        self.store = TransactionStore()
        self._build_ui()
        self._build_menu()
        self._apply_theme()
        self._refresh()

        QTimer.singleShot(0, self._apply_proportional_widths)

    # ---------- Palette helper ----------
    def _palette(self) -> dict:
        return DARK_PALETTE if self.current_theme == "dark" else LIGHT_PALETTE

    # ---------- Menu ----------
    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        import_action = QAction("Impor CSV...", self)
        import_action.setShortcut("Ctrl+O")
        import_action.triggered.connect(self._import_csv)
        file_menu.addAction(import_action)

        export_action = QAction("Ekspor CSV...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_csv)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Keluar", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("&Tampilan")
        self.theme_action = QAction("Tema Gelap", self)
        self.theme_action.setShortcut("Ctrl+T")
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)

        help_menu = menu_bar.addMenu("&Bantuan")
        about_action = QAction("Tentang", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.resize(980, 680)

        if os.path.exists(self._icon_path):
            icon = QIcon(self._icon_path)
            if not icon.isNull():
                self.setWindowIcon(icon)

        root = QWidget()
        root.setObjectName("RootWidget")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # --- Header ---
        header = QHBoxLayout()
        header.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setObjectName("HeaderIcon")
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        icon_lbl.setToolTip(APP_NAME)

        if os.path.exists(self._icon_path):
            pixmap = QPixmap(self._icon_path)
            if not pixmap.isNull():
                icon_lbl.setPixmap(
                    pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        title_lbl = QLabel(APP_NAME)
        title_lbl.setObjectName("HeaderTitle")

        version_lbl = QLabel(APP_VERSION)
        version_lbl.setObjectName("HeaderVersion")
        version_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("GhostButton")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)

        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(version_lbl)
        header.addWidget(self.theme_btn)
        layout.addLayout(header)

        # --- Kartu ringkasan ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)
        self.card_balance = self._make_card("SALDO")
        self.card_income = self._make_card("PEMASUKAN")
        self.card_expense = self._make_card("PENGELUARAN")
        cards_layout.addWidget(self.card_balance[0])
        cards_layout.addWidget(self.card_income[0])
        cards_layout.addWidget(self.card_expense[0])
        layout.addLayout(cards_layout)

        # --- Form input ---
        form_frame = QFrame()
        form_frame.setObjectName("Card")
        form_grid = QGridLayout(form_frame)
        form_grid.setContentsMargins(16, 12, 16, 14)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(4)

        self.input_date = QDateEdit()
        self.input_date.setCalendarPopup(True)
        self.input_date.setDate(QDate.currentDate())
        self.input_date.setDisplayFormat("dd/MM/yyyy")

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Deskripsi transaksi...")

        self.input_category = QComboBox()
        self.input_category.setEditable(True)
        self.input_category.addItems(
            ["Umum", "Makan", "Transportasi", "Belanja",
             "Gaji", "Tagihan", "Lainnya"]
        )

        self.input_kind = QComboBox()
        self.input_kind.addItems(["Pengeluaran", "Pemasukan"])

        self.input_amount = QDoubleSpinBox()
        self.input_amount.setMaximum(1_000_000_000)
        self.input_amount.setDecimals(0)
        self.input_amount.setGroupSeparatorShown(True)
        self.input_amount.setPrefix("Rp ")

        add_btn = QPushButton("Tambah")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_transaction)

        labels = ["Tanggal", "Deskripsi", "Kategori", "Jenis", "Jumlah"]
        for col, text in enumerate(labels):
            form_grid.addWidget(self._small_label(text), 0, col)

        form_grid.addWidget(self.input_date,     1, 0)
        form_grid.addWidget(self.input_desc,     1, 1)
        form_grid.addWidget(self.input_category, 1, 2)
        form_grid.addWidget(self.input_kind,     1, 3)
        form_grid.addWidget(self.input_amount,   1, 4)
        form_grid.addWidget(add_btn,             1, 5)

        form_grid.setColumnStretch(1, 1)
        layout.addWidget(form_frame)

        # --- Toolbar filter ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari deskripsi atau kategori...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_filter_changed)

        self.filter_year = QComboBox()
        self.filter_year.setMinimumWidth(130)
        self.filter_year.addItem("Semua Tahun", None)
        self.filter_year.currentIndexChanged.connect(self._on_filter_changed)

        self.filter_month = QComboBox()
        self.filter_month.setMinimumWidth(150)
        self.filter_month.addItem("Semua Bulan", None)
        for i, name in enumerate(MONTH_NAMES_ID, start=1):
            self.filter_month.addItem(f"{i:02d} - {name}", f"{i:02d}")
        self.filter_month.currentIndexChanged.connect(self._on_filter_changed)

        self.filter_category = QComboBox()
        self.filter_category.setMinimumWidth(160)
        self.filter_category.addItem("Semua Kategori")
        self.filter_category.currentIndexChanged.connect(self._on_filter_changed)

        reset_btn = QPushButton("Reset Filter")
        reset_btn.setObjectName("GhostButton")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_filters)

        filter_layout.addWidget(self.search_input, 1)
        filter_layout.addWidget(self.filter_year)
        filter_layout.addWidget(self.filter_month)
        filter_layout.addWidget(self.filter_category)
        filter_layout.addWidget(reset_btn)
        layout.addLayout(filter_layout)

        # --- Tabel transaksi ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Tanggal", "Deskripsi", "Kategori", "Jenis", "Jumlah"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.ElideRight)
        self.table.verticalHeader().setDefaultSectionSize(36)

        header_view = self.table.horizontalHeader()
        header_view.setMinimumSectionSize(80)
        for col in range(5):
            header_view.setSectionResizeMode(col, QHeaderView.Interactive)
        header_view.setStretchLastSection(False)

        self.table.doubleClicked.connect(lambda *_: self._edit_selected())
        layout.addWidget(self.table, 1)

        # --- Tombol aksi (Edit & Hapus saja; Ekspor/Impor ada di menu File) ---
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()

        edit_btn = QPushButton("Edit Terpilih")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self._edit_selected)
        actions.addWidget(edit_btn)

        delete_btn = QPushButton("Hapus Terpilih")
        delete_btn.setObjectName("DangerButton")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(self._delete_selected)
        actions.addWidget(delete_btn)

        layout.addLayout(actions)

        self.statusBar().showMessage(f"Data: {self.store.path}")

    # ---------- Helpers ----------
    def _make_card(self, title: str):
        frame = QFrame()
        frame.setObjectName("Card")
        v = QVBoxLayout(frame)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")

        value_lbl = QLabel("Rp 0")

        v.addWidget(title_lbl)
        v.addWidget(value_lbl)
        return frame, value_lbl

    @staticmethod
    def _small_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("CardTitle")
        return lbl

    @staticmethod
    def _format_rupiah(value: float) -> str:
        return "Rp " + f"{value:,.0f}".replace(",", ".")

    @staticmethod
    def _format_date_display(iso_date: str) -> str:
        d = QDate.fromString(iso_date, "yyyy-MM-dd")
        return d.toString("dd/MM/yyyy") if d.isValid() else iso_date

    # ---------- Theme ----------
    def _apply_theme(self) -> None:
        p = self._palette()

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(p))

        self.card_balance[1].setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {p['balance']}; background: transparent;"
        )
        self.card_income[1].setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {p['income']}; background: transparent;"
        )
        self.card_expense[1].setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {p['expense']}; background: transparent;"
        )

        if self.current_theme == "dark":
            self.theme_btn.setText("☀️ Terang")
            self.theme_btn.setToolTip("Ganti ke tema terang (Ctrl+T)")
            self.theme_action.setText("Tema Terang")
        else:
            self.theme_btn.setText("🌙 Gelap")
            self.theme_btn.setToolTip("Ganti ke tema gelap (Ctrl+T)")
            self.theme_action.setText("Tema Gelap")

    def _toggle_theme(self) -> None:
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self._settings.setValue("theme", self.current_theme)
        self._apply_theme()
        self._fill_table()

    # ---------- Column Width Management ----------
    def _apply_proportional_widths(self) -> None:
        if not hasattr(self, "table") or self.table is None:
            return
        viewport_width = self.table.viewport().width()
        if viewport_width < 200:
            return

        widths = [
            max(m, int(viewport_width * r))
            for r, m in zip(COLUMN_RATIOS, COLUMN_MINS)
        ]
        total = sum(widths)

        while total > viewport_width:
            candidates = [
                (i, widths[i] - COLUMN_MINS[i])
                for i in range(len(widths))
                if widths[i] > COLUMN_MINS[i]
            ]
            if not candidates:
                break
            i = max(candidates, key=lambda x: x[1])[0]
            widths[i] -= 1
            total -= 1

        for i, w in enumerate(widths):
            if self.table.columnWidth(i) != w:
                self.table.setColumnWidth(i, w)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "table") and self.table is not None:
            QTimer.singleShot(0, self._apply_proportional_widths)

    # ---------- Handlers ----------
    def _add_transaction(self) -> None:
        desc = self.input_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "Validasi", "Deskripsi tidak boleh kosong.")
            return

        amount = self.input_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Validasi", "Jumlah harus lebih dari 0.")
            return

        kind = "income" if self.input_kind.currentText() == "Pemasukan" else "expense"
        category = self.input_category.currentText().strip() or "Umum"

        self.store.add(Transaction(
            id=str(uuid.uuid4()),
            date=self.input_date.date().toString("yyyy-MM-dd"),
            description=desc,
            category=category,
            kind=kind,
            amount=amount,
        ))

        self.input_desc.clear()
        self.input_amount.setValue(0)
        self.input_desc.setFocus()
        self._refresh()

    def _edit_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Info", "Silakan pilih transaksi yang ingin diedit."
            )
            return

        item = self.table.item(row, 0)
        if item is None:
            return
        transaction_id = item.data(Qt.UserRole)

        current = next(
            (t for t in self.store.all() if t.id == transaction_id), None
        )
        if current is None:
            QMessageBox.warning(
                self, "Error", "Transaksi tidak ditemukan di penyimpanan."
            )
            return

        dialog = EditTransactionDialog(current, self)
        if dialog.exec_() == QDialog.Accepted:
            updated = dialog.get_result()
            if not self.store.update(updated):
                QMessageBox.warning(
                    self, "Error", "Gagal memperbarui transaksi (id tidak ditemukan)."
                )
                return
            self._refresh()

    def _delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Info", "Silakan pilih transaksi yang ingin dihapus."
            )
            return

        item = self.table.item(row, 0)
        transaction_id = item.data(Qt.UserRole)

        confirm = QMessageBox.question(
            self,
            "Konfirmasi",
            "Hapus transaksi ini?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.store.remove(transaction_id)
            self._refresh()

    # ---------- Import CSV ----------
    @classmethod
    def _map_import_headers(cls, header_row):
        """Map canonical field → column index; case-insensitive & alias-aware."""
        col_map = {}
        for idx, cell in enumerate(header_row):
            key = (cell or "").strip().lower()
            if not key:
                continue
            for canonical, names in cls.IMPORT_HEADER_ALIASES.items():
                if key in names and canonical not in col_map:
                    col_map[canonical] = idx
                    break
        return col_map

    @staticmethod
    def _parse_import_date(raw):
        """Normalisasi 'YYYY-MM-DD' / 'dd/MM/yyyy' → 'YYYY-MM-DD'. None jika invalid."""
        s = (raw or "").strip()
        if not s:
            return None
        for fmt in ("yyyy-MM-dd", "dd/MM/yyyy", "yyyy/MM/dd",
                    "d/M/yyyy", "d-M-yyyy"):
            d = QDate.fromString(s, fmt)
            if d.isValid():
                return d.toString("yyyy-MM-dd")
        return None

    @staticmethod
    def _parse_import_amount(raw):
        """
        Parse amount string. Return (abs_value>0 or None, was_negative).
        Mendukung plain number, format ID (1.234,56), dan EN (1,234.56).
        """
        if raw is None:
            return None, False
        s = str(raw).strip()
        if not s:
            return None, False

        negative = "-" in s
        cleaned = "".join(c for c in s if c.isdigit() or c in ".,")
        if not cleaned:
            return None, negative

        if "." in cleaned and "," in cleaned:
            if cleaned.rfind(".") > cleaned.rfind(","):
                num_str = cleaned.replace(",", "")           # EN: 1,234.56
            else:
                num_str = cleaned.replace(".", "").replace(",", ".")  # ID
        elif "." in cleaned:
            after = len(cleaned) - cleaned.rfind(".") - 1
            if cleaned.count(".") > 1 or after == 3:
                num_str = cleaned.replace(".", "")           # thousands
            else:
                num_str = cleaned
        elif "," in cleaned:
            after = len(cleaned) - cleaned.rfind(",") - 1
            if cleaned.count(",") > 1 or after == 3:
                num_str = cleaned.replace(",", "")           # thousands
            else:
                num_str = cleaned.replace(",", ".")
        else:
            num_str = cleaned

        try:
            val = float(num_str)
        except ValueError:
            return None, negative
        if val <= 0:
            return None, negative
        return val, negative

    @staticmethod
    def _parse_import_kind(raw, was_negative):
        """Tentukan kind; fallback ke sign, lalu default 'expense'."""
        s = (raw or "").strip().lower()
        if s in ("pemasukan", "income", "masuk", "in", "pemasukkan"):
            return "income"
        if s in ("pengeluaran", "expense", "keluar", "out", "pengeluar"):
            return "expense"
        if was_negative:
            return "expense"
        return "expense"

    def _import_csv(self) -> None:
        # DontUseNativeDialog → jaminan QSS kita dipakai di Linux Mint
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Impor dari CSV",
            os.path.expanduser("~"),
            "CSV Files (*.csv);;All Files (*)",
            options=QFileDialog.DontUseNativeDialog,
        )
        if not filepath:
            return

        # Baca file dengan fallback encoding
        text = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc, newline="") as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
            except OSError as exc:
                QMessageBox.warning(
                    self, "Impor CSV Gagal",
                    f"Gagal membaca berkas:\n{exc}"
                )
                return

        if text is None:
            QMessageBox.warning(
                self, "Impor CSV Gagal",
                "Gagal membaca berkas (encoding tidak dikenal)."
            )
            return

        try:
            rows = list(csv.reader(io.StringIO(text)))
        except csv.Error as exc:
            QMessageBox.warning(
                self, "Impor CSV Gagal",
                f"Format CSV tidak valid:\n{exc}"
            )
            return

        if not rows:
            QMessageBox.warning(self, "Impor CSV", "Berkas CSV kosong.")
            return

        col_map = self._map_import_headers(rows[0])
        if "date" not in col_map or "amount" not in col_map:
            QMessageBox.warning(
                self, "Impor CSV Gagal",
                "Header kolom tidak dikenali.\n"
                "Pastikan CSV memiliki kolom 'Tanggal' dan 'Jumlah'."
            )
            return

        imported = 0
        skipped = 0

        def cell(row, canonical):
            idx = col_map.get(canonical)
            if idx is None or idx >= len(row):
                return ""
            return (row[idx] or "").strip()

        for row in rows[1:]:
            if not row or not any((c or "").strip() for c in row):
                continue

            try:
                date_str = self._parse_import_date(cell(row, "date"))
                amount_val, was_neg = self._parse_import_amount(cell(row, "amount"))
                desc = cell(row, "description")

                if not date_str or amount_val is None or not desc:
                    skipped += 1
                    continue

                kind = self._parse_import_kind(cell(row, "kind"), was_neg)
                category = cell(row, "category") or "Umum"

                self.store.add(Transaction(
                    id=str(uuid.uuid4()),
                    date=date_str,
                    description=desc,
                    category=category,
                    kind=kind,
                    amount=abs(amount_val),
                ))
                imported += 1
            except Exception:
                skipped += 1
                continue

        if imported == 0:
            QMessageBox.warning(
                self, "Impor CSV",
                f"Tidak ada transaksi valid yang diimpor.\n"
                f"{skipped} baris dilewati."
            )
            return

        self._refresh()

        msg = f"{imported} transaksi berhasil diimpor."
        if skipped > 0:
            msg += f"\n{skipped} baris dilewati (data tidak valid)."
        QMessageBox.information(self, "Impor CSV Berhasil", msg)

    # ---------- Export CSV ----------
    def _export_csv(self) -> None:
        transactions = self._get_filtered_transactions()
        if not transactions:
            QMessageBox.warning(
                self, "Ekspor CSV",
                "Tidak ada data untuk diekspor.\n"
                "(Tabel kosong atau filter aktif tidak menyisakan transaksi.)"
            )
            return

        default_path = os.path.join(os.path.expanduser("~"), "transaksi_keuangan.csv")

        # DontUseNativeDialog → QSS kita dijamin berlaku (mode gelap aman)
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Ekspor ke CSV",
            default_path,
            "CSV Files (*.csv);;All Files (*)",
            options=QFileDialog.DontUseNativeDialog,
        )
        if not filepath:
            return

        if not filepath.lower().endswith(".csv"):
            filepath += ".csv"

        try:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Tanggal", "Deskripsi", "Kategori", "Jenis", "Jumlah (Rp)"]
                )
                for t in transactions:
                    signed_amount = t.amount if t.kind == "income" else -t.amount
                    amount_value = (
                        int(signed_amount)
                        if float(signed_amount).is_integer()
                        else signed_amount
                    )
                    writer.writerow([
                        t.date,
                        t.description,
                        t.category,
                        "Pemasukan" if t.kind == "income" else "Pengeluaran",
                        amount_value,
                    ])
        except OSError as exc:
            QMessageBox.warning(
                self, "Ekspor CSV Gagal",
                f"Gagal menulis berkas:\n{exc}"
            )
            return

        QMessageBox.information(
            self, "Ekspor CSV Berhasil",
            f"{len(transactions)} transaksi berhasil diekspor ke:\n{filepath}"
        )

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"Tentang {APP_NAME}",
            f"<b>{APP_NAME}</b><br>"
            f"Versi: <b>{APP_VERSION}</b><br><br>"
            "Aplikasi desktop sederhana untuk mencatat pemasukan "
            "dan pengeluaran harian.<br><br>"
            f"<b>Lokasi data:</b><br><code>{self.store.path}</code><br><br>"
            f"<i>{APP_AUTHOR}</i>",
        )

    # ---------- Filtering ----------
    def _on_filter_changed(self) -> None:
        filtered = self._get_filtered_transactions()
        self._update_summary_cards(filtered)
        self._fill_table(filtered)

    def _reset_filters(self) -> None:
        self.search_input.blockSignals(True)
        self.filter_year.blockSignals(True)
        self.filter_month.blockSignals(True)
        self.filter_category.blockSignals(True)

        self.search_input.clear()
        self.filter_year.setCurrentIndex(0)
        self.filter_month.setCurrentIndex(0)
        self.filter_category.setCurrentIndex(0)

        self.search_input.blockSignals(False)
        self.filter_year.blockSignals(False)
        self.filter_month.blockSignals(False)
        self.filter_category.blockSignals(False)

        self._refresh()

    def _get_filtered_transactions(self):
        keyword = self.search_input.text().strip().lower()
        cat_filter = self.filter_category.currentText()
        apply_cat = bool(cat_filter) and cat_filter != "Semua Kategori"

        year_value = self.filter_year.currentData()
        month_value = self.filter_month.currentData()

        result = []
        for t in self.store.all():
            if keyword and (
                keyword not in t.description.lower()
                and keyword not in t.category.lower()
            ):
                continue
            if apply_cat and t.category != cat_filter:
                continue
            t_year, t_month = _extract_year_month(t.date)
            if year_value and t_year != year_value:
                continue
            if month_value and t_month != month_value:
                continue
            result.append(t)
        return result

    # ---------- Refresh ----------
    def _refresh(self) -> None:
        self._refresh_year_filter()
        self._refresh_category_filter()

        filtered = self._get_filtered_transactions()
        self._update_summary_cards(filtered)
        self._fill_table(filtered)

    def _update_summary_cards(self, transactions=None) -> None:
        if transactions is None:
            transactions = self._get_filtered_transactions()
        income = sum(t.amount for t in transactions if t.kind == "income")
        expense = sum(t.amount for t in transactions if t.kind == "expense")
        balance = income - expense

        self.card_balance[1].setText(self._format_rupiah(balance))
        self.card_income[1].setText(self._format_rupiah(income))
        self.card_expense[1].setText(self._format_rupiah(expense))

    def _refresh_year_filter(self) -> None:
        current = self.filter_year.currentData()
        self.filter_year.blockSignals(True)
        self.filter_year.clear()
        self.filter_year.addItem("Semua Tahun", None)

        years = set()
        for t in self.store.all():
            year, _ = _extract_year_month(t.date)
            if year:
                years.add(year)

        for y in sorted(years, reverse=True):
            self.filter_year.addItem(y, y)

        if current:
            idx = self.filter_year.findData(current)
            if idx >= 0:
                self.filter_year.setCurrentIndex(idx)
        self.filter_year.blockSignals(False)

    def _refresh_category_filter(self) -> None:
        current = self.filter_category.currentText()
        self.filter_category.blockSignals(True)
        self.filter_category.clear()
        self.filter_category.addItem("Semua Kategori")

        categories = sorted({t.category for t in self.store.all() if t.category})
        self.filter_category.addItems(categories)

        idx = self.filter_category.findText(current)
        if idx >= 0:
            self.filter_category.setCurrentIndex(idx)
        self.filter_category.blockSignals(False)

    def _fill_table(self, filtered=None) -> None:
        if filtered is None:
            filtered = self._get_filtered_transactions()

        p = self._palette()
        income_color = QColor(p["income"])
        expense_color = QColor(p["expense"])

        self.table.setRowCount(len(filtered))

        for row, t in enumerate(filtered):
            date_item = QTableWidgetItem(self._format_date_display(t.date))
            date_item.setData(Qt.UserRole, t.id)
            self.table.setItem(row, 0, date_item)

            desc_item = QTableWidgetItem(t.description)
            desc_item.setToolTip(t.description)
            self.table.setItem(row, 1, desc_item)

            self.table.setItem(row, 2, QTableWidgetItem(t.category))

            kind_text = "Pemasukan" if t.kind == "income" else "Pengeluaran"
            kind_item = QTableWidgetItem(kind_text)
            kind_item.setForeground(
                income_color if t.kind == "income" else expense_color
            )
            self.table.setItem(row, 3, kind_item)

            sign = "+" if t.kind == "income" else "-"
            amt_item = QTableWidgetItem(
                f"{sign}{self._format_rupiah(t.amount)}"
            )
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt_item.setForeground(
                income_color if t.kind == "income" else expense_color
            )
            self.table.setItem(row, 4, amt_item)