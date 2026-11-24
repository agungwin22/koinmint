"""
models.py
=========
Modul Data Model & Metadata Aplikasi.

Berisi:
    - Metadata aplikasi (APP_NAME, APP_SLUG, APP_VERSION, APP_AUTHOR).
    - Struktur data `Transaction` (dataclass).

Modul ini sengaja tidak meng-import modul lain di dalam proyek
agar bisa dijadikan fondasi (leaf module) — dipakai oleh store.py
dan ui.py tanpa risiko circular import.
"""

from dataclasses import dataclass


# ============================================================
# Metadata Aplikasi
# ============================================================
APP_NAME = "KoinMint"
APP_SLUG = "koinmint"       # dipakai untuk nama folder data (XDG) & identifier
APP_VERSION = "v0.7.0"
APP_AUTHOR = "Agung Python Developer"


# ============================================================
# Data Model
# ============================================================
@dataclass
class Transaction:
    """Representasi satu transaksi keuangan."""

    id: str
    date: str          # ISO format: YYYY-MM-DD
    description: str
    category: str
    kind: str          # "income" | "expense"
    amount: float