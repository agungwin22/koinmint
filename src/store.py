"""
store.py
========
Modul Manajemen Data (Persistent Storage berbasis JSON).

Berisi:
    - Konstanta `DATA_DIR`, `DATA_FILE` (lokasi penyimpanan data user).
    - Konstanta `LEGACY_DATA_FILE` (lokasi data versi lama di folder proyek,
      untuk keperluan migrasi otomatis sekali jalan).
    - Kelas `TransactionStore` yang menangani load/save transaksi
      ke berkas JSON secara persisten & atomik.

API publik kelas: add / update / remove / all / totals / path

Changelog:
    v0.3.0 — Tambah method `update()` untuk memperbarui transaksi
             berdasarkan id, dengan auto-save atomik.
    v0.5.0 — Rebranding: aplikasi menjadi "KoinMint". Data dipindah ke
             user data dir (~/.local/share/koinmint/) agar aman saat
             di-package (.deb / .exe). Auto-migrasi dari lokasi lama
             (folder proyek) sekali jalan.
"""

import json
import os
import sys
from dataclasses import asdict
from typing import List, Tuple

from models import APP_SLUG, Transaction


# ============================================================
# Lokasi Penyimpanan Data
# ============================================================
def _user_data_dir(slug: str) -> str:
    """
    Direktori data pengguna mengikuti XDG Base Directory Specification:
      - Jika env var XDG_DATA_HOME di-set → pakai itu.
      - Jika tidak → default Linux: ~/.local/share/<slug>/
    """
    base = os.environ.get("XDG_DATA_HOME")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, slug)


DATA_DIR = _user_data_dir(APP_SLUG)                    # ~/.local/share/koinmint
DATA_FILE = os.path.join(DATA_DIR, "transactions.json")

# Lokasi data lama (v0.4.0 ke bawah): di folder proyek tempat skrip berada.
# Hanya dipakai untuk migrasi otomatis sekali jalan.
LEGACY_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "transactions.json",
)


class TransactionStore:
    """
    Penyimpanan transaksi persisten ke berkas JSON.

    Setiap `add()` / `update()` / `remove()` otomatis memicu `_save()`.
    Data lama otomatis dimuat lewat `_load()` pada saat inisialisasi.

    Jika file `transactions.json` lama masih ada di folder proyek
    (sisa versi < v0.5.0), otomatis dimigrasikan sekali ke lokasi baru
    dengan backup yang aman (file lama di-rename ke *.migrated).
    """

    def __init__(self, path: str = DATA_FILE) -> None:
        self._path = path
        self._items: List[Transaction] = []
        self._ensure_data_dir()
        # Migrasi hanya untuk lokasi default agar tidak mengganggu
        # penggunaan custom path (mis. unit-test dengan tempdir).
        if os.path.abspath(self._path) == os.path.abspath(DATA_FILE):
            self._migrate_legacy()
        self._load()

    # ---------- Public API ----------
    def add(self, transaction: Transaction) -> None:
        self._items.append(transaction)
        self._save()

    def update(self, updated_transaction: Transaction) -> bool:
        """
        Perbarui transaksi yang sudah ada berdasarkan `id`.

        Mengembalikan:
            True  → jika transaksi dengan id tersebut ditemukan & diperbarui.
            False → jika id tidak ditemukan (tidak ada perubahan disimpan).
        """
        for index, current in enumerate(self._items):
            if current.id == updated_transaction.id:
                self._items[index] = updated_transaction
                self._save()
                return True
        return False

    def remove(self, transaction_id: str) -> None:
        self._items = [t for t in self._items if t.id != transaction_id]
        self._save()

    def all(self) -> List[Transaction]:
        # Urutkan dari tanggal terbaru (tanggal ISO terurut secara leksikografis)
        return sorted(self._items, key=lambda t: t.date, reverse=True)

    def totals(self) -> Tuple[float, float]:
        income = sum(t.amount for t in self._items if t.kind == "income")
        expense = sum(t.amount for t in self._items if t.kind == "expense")
        return income, expense

    @property
    def path(self) -> str:
        return self._path

    # ---------- Persistence (private) ----------
    def _ensure_data_dir(self) -> None:
        """Pastikan direktori induk dari `self._path` sudah ada."""
        parent = os.path.dirname(self._path)
        if not parent:
            return
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError as exc:
            print(
                f"[ERROR] Gagal membuat direktori data {parent}: {exc}",
                file=sys.stderr,
            )

    def _migrate_legacy(self) -> None:
        """
        Salin `transactions.json` lama (folder proyek) ke lokasi baru
        jika: (a) file baru belum ada, dan (b) file lama masih tersedia.

        Setelah disalin, file lama di-rename ke `transactions.json.migrated`
        (bukan dihapus) sebagai backup — user masih bisa memverifikasi.
        """
        if not os.path.exists(LEGACY_DATA_FILE):
            return
        if os.path.exists(self._path):
            return  # data baru sudah ada — jangan timpa

        try:
            with open(LEGACY_DATA_FILE, "r", encoding="utf-8") as src:
                content = src.read()
            with open(self._path, "w", encoding="utf-8") as dst:
                dst.write(content)

            # Tandai file lama agar tidak dimigrasikan ulang
            migrated_marker = LEGACY_DATA_FILE + ".migrated"
            if not os.path.exists(migrated_marker):
                os.replace(LEGACY_DATA_FILE, migrated_marker)

            print(
                f"[INFO] Migrasi data: {LEGACY_DATA_FILE} → {self._path}",
                file=sys.stderr,
            )
        except OSError as exc:
            print(f"[WARN] Migrasi data lama gagal: {exc}", file=sys.stderr)

    def _load(self) -> None:
        """Muat data dari JSON. Jika korup, backup ke *.corrupt lalu mulai kosong."""
        if not os.path.exists(self._path):
            self._items = []
            return

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if not isinstance(raw, list):
                raise ValueError("Root JSON bukan list.")

            self._items = [
                Transaction(
                    id=str(row["id"]),
                    date=str(row["date"]),
                    description=str(row["description"]),
                    category=str(row.get("category", "Umum")),
                    kind=str(row["kind"]),
                    amount=float(row["amount"]),
                )
                for row in raw
            ]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            # Backup file yang rusak agar tidak menimpa data user
            backup_path = self._path + ".corrupt"
            try:
                os.replace(self._path, backup_path)
                print(
                    f"[WARN] Data JSON rusak ({exc}). "
                    f"Backup disimpan di: {backup_path}",
                    file=sys.stderr,
                )
            except OSError:
                pass
            self._items = []

    def _save(self) -> None:
        """Simpan data ke JSON secara atomik (tulis ke .tmp lalu replace)."""
        tmp_path = self._path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    [asdict(t) for t in self._items],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            os.replace(tmp_path, self._path)
        except OSError as exc:
            print(f"[ERROR] Gagal menyimpan data: {exc}", file=sys.stderr)