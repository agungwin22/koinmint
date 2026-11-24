"""
main.py
=======
Entry Point Aplikasi KoinMint.

Tanggung jawab modul ini murni:
    - Inisialisasi QApplication.
    - Memasang metadata (nama & versi) + stylesheet default.
    - Menampilkan MainWindow dan menjalankan event loop.

Semua logika bisnis & UI berada di modul lain (models.py, store.py, ui.py).
"""

import sys

from PyQt5.QtWidgets import QApplication

from models import APP_NAME, APP_VERSION
from ui import MainWindow, STYLESHEET


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()