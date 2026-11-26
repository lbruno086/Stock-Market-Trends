"""Historial de precios y avisos ya enviados (SQLite)."""
from __future__ import annotations

import sqlite3
import time


class Almacen:
    def __init__(self, ruta: str):
        self.db = sqlite3.connect(ruta)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS precios (
                clave TEXT, precio REAL, ts INTEGER);
            CREATE INDEX IF NOT EXISTS ix_precios ON precios(clave);
            CREATE TABLE IF NOT EXISTS avisos (
                clave TEXT PRIMARY KEY, precio REAL, descuento REAL, ts INTEGER);
        """)

    def historial(self, clave: str) -> list[float]:
        return [r[0] for r in self.db.execute(
            "SELECT precio FROM precios WHERE clave=?", (clave,))]

    def registrar(self, clave: str, precio: float):
        self.db.execute("INSERT INTO precios VALUES (?,?,?)", (clave, precio, int(time.time())))

    def ya_avisado(self, clave: str, precio: float) -> bool:
        """True si ya avisamos esta oferta a un precio igual o menor."""
        r = self.db.execute("SELECT precio FROM avisos WHERE clave=?", (clave,)).fetchone()
        return bool(r) and precio >= r[0]

    def marcar_avisado(self, clave: str, precio: float, descuento: float):
        self.db.execute("INSERT OR REPLACE INTO avisos VALUES (?,?,?,?)",
                        (clave, precio, descuento, int(time.time())))

    def guardar(self):
        self.db.commit()
