"""Camada de dados SQLite da Cantina Escolar."""
from __future__ import annotations

import csv
import hashlib
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Any

try:
    from .seed import CATEGORIES, PRODUCTS
except ImportError:
    from seed import CATEGORIES, PRODUCTS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTANCE_DIR = PROJECT_ROOT / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
DB_PATH = INSTANCE_DIR / "cantina.db"


class Database:
    """Repositório centralizado: alunos, produtos, pedidos, fiados e relatórios."""

    PENDURA_LIMIT = 20.0

    def __init__(self, path: str | Path = DB_PATH):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_schema()
        self.seed_data()
        self.ensure_admin_password()

    # ------------------------------------------------------------------ schema
    def init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id),
                price REAL NOT NULL CHECK(price >= 0),
                cost REAL NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                stock INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS students (
                cpf TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL UNIQUE,
                student_cpf TEXT REFERENCES students(cpf),
                student_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                notes TEXT DEFAULT '',
                payment_method TEXT NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'Pago',
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Recebido',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id),
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                spent_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS penduras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_cpf TEXT NOT NULL REFERENCES students(cpf),
                student_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                order_id INTEGER REFERENCES orders(id),
                amount REAL NOT NULL,
                paid INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                paid_at TEXT
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        pcols = {r["name"] for r in self.conn.execute("PRAGMA table_info(products)")}
        if "cost" not in pcols:
            self.conn.execute("ALTER TABLE products ADD COLUMN cost REAL NOT NULL DEFAULT 0")
        ocols = {r["name"] for r in self.conn.execute("PRAGMA table_info(orders)")}
        if "payment_status" not in ocols:
            self.conn.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'Pago'")
        if "student_cpf" not in ocols:
            self.conn.execute("ALTER TABLE orders ADD COLUMN student_cpf TEXT")
        self.conn.commit()

    def seed_data(self) -> None:
        if self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            self.conn.executemany("INSERT INTO categories(name) VALUES (?)",
                                  [(c,) for c in CATEGORIES])
        if self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            cats = {r["name"]: r["id"] for r in self.conn.execute("SELECT id,name FROM categories")}
            ordered = sorted(PRODUCTS, key=lambda x: (x[1].lower(), x[0].lower()))
            rows = []
            pid = 100
            for n, c, p in ordered:
                rows.append((pid, n, cats[c], p, round(p * 0.45, 2)))
                pid += 2
            self.conn.executemany(
                "INSERT INTO products(id,name,category_id,price,cost) VALUES (?,?,?,?,?)",
                rows,
            )
        self.conn.commit()

    # --------------------------------------------------------------- catálogo
    def categories(self):
        return self.conn.execute(
            "SELECT * FROM categories ORDER BY name COLLATE NOCASE"
        ).fetchall()

    def products(self, active_only=True):
        where = "WHERE p.active=1 AND p.stock=1" if active_only else ""
        return self.conn.execute(
            f"SELECT p.*, c.name category FROM products p "
            f"JOIN categories c ON c.id=p.category_id {where} "
            f"ORDER BY c.name COLLATE NOCASE, p.name COLLATE NOCASE"
        ).fetchall()

    def save_product(self, product_id, name, category, price, cost, active, stock):
        cid = self.conn.execute(
            "SELECT id FROM categories WHERE name=?", (category,)
        ).fetchone()[0]
        if product_id:
            self.conn.execute(
                "UPDATE products SET name=?,category_id=?,price=?,cost=?,active=?,stock=? "
                "WHERE id=?",
                (name, cid, price, cost, active, stock, product_id),
            )
        else:
            row = self.conn.execute(
                "SELECT COALESCE(MAX(id), 98) FROM products"
            ).fetchone()
            next_id = row[0] + 2
            self.conn.execute(
                "INSERT INTO products(id,name,category_id,price,cost,active,stock) "
                "VALUES (?,?,?,?,?,?,?)",
                (next_id, name, cid, price, cost, active, stock),
            )
        self.conn.commit()

    def set_stock(self, product_id: int, stock: int) -> None:
        self.conn.execute("UPDATE products SET stock=? WHERE id=?",
                          (1 if stock else 0, product_id))
        self.conn.commit()

    def toggle_product_active(self, product_id: int) -> None:
        self.conn.execute(
            "UPDATE products SET active = CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?",
            (product_id,),
        )
        self.conn.commit()

    # ------------------------------------------------------------------ alunos
    def get_student(self, cpf: str):
        return self.conn.execute(
            "SELECT * FROM students WHERE cpf=?", (cpf,)
        ).fetchone()

    def create_student(self, cpf: str, name: str, class_name: str) -> None:
        self.conn.execute(
            "INSERT INTO students(cpf,name,class_name,created_at) VALUES (?,?,?,?)",
            (cpf, name, class_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        self.conn.commit()

    def list_students(self):
        return self.conn.execute(
            "SELECT * FROM students ORDER BY name COLLATE NOCASE"
        ).fetchall()

    # ----------------------------------------------------------------- pedidos
    def create_order(self, student_cpf, student, class_name, notes, payment, payment_status, cart):
        total = sum(i["price"] * i["quantity"] for i in cart)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.execute(
            "INSERT INTO orders(order_number,student_cpf,student_name,class_name,notes,"
            "payment_method,payment_status,total,status,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("TEMP", student_cpf, student, class_name, notes, payment,
             payment_status, total, "Recebido", now),
        )
        order_id = cur.lastrowid
        number = f"{datetime.now():%y%m%d}-{order_id:04d}"
        self.conn.execute("UPDATE orders SET order_number=? WHERE id=?", (number, order_id))
        self.conn.executemany(
            "INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price) "
            "VALUES (?,?,?,?,?)",
            [(order_id, i["id"], i["name"], i["quantity"], i["price"]) for i in cart],
        )
        if payment == "Fiado":
            self.add_fiado(student_cpf, student, class_name, order_id, total)
        self.conn.commit()
        return number

    def orders(self, active_only=False, status=None):
        conds, params = [], []
        if active_only:
            conds.append("o.status != 'Entregue'")
        if status:
            conds.append("o.status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(conds)}" if conds else ""
        return self.conn.execute(
            f"SELECT o.*, GROUP_CONCAT(oi.quantity || 'x ' || oi.product_name, ', ') items "
            f"FROM orders o LEFT JOIN order_items oi ON oi.order_id=o.id {where} "
            f"GROUP BY o.id ORDER BY o.id DESC", params
        ).fetchall()

    def set_order_status(self, order_id: int, status: str) -> None:
        self.conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        self.conn.commit()

    def set_payment_status(self, order_id: int, status: str) -> None:
        self.conn.execute("UPDATE orders SET payment_status=? WHERE id=?", (status, order_id))
        self.conn.commit()

    # ---------------------------------------------------------------- despesas
    def add_expense(self, description: str, category: str, amount: float) -> None:
        self.conn.execute(
            "INSERT INTO expenses(description,category,amount,spent_at) VALUES (?,?,?,?)",
            (description, category, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        self.conn.commit()

    def expenses(self, day: str | None = None):
        if day:
            return self.conn.execute(
                "SELECT * FROM expenses WHERE date(spent_at)=? ORDER BY id DESC", (day,)
            ).fetchall()
        return self.conn.execute("SELECT * FROM expenses ORDER BY id DESC").fetchall()

    # ----------------------------------------------------------------- fiados
    def fiado_total(self, cpf: str) -> float:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM penduras WHERE paid=0 AND student_cpf=?",
            (cpf,),
        ).fetchone()
        return float(row[0])

    def fiado_can_order(self, cpf: str) -> tuple[bool, float]:
        total = self.fiado_total(cpf)
        return total < self.PENDURA_LIMIT, total

    def add_fiado(self, cpf, student_name, class_name, order_id, amount):
        self.conn.execute(
            "INSERT INTO penduras(student_cpf,student_name,class_name,order_id,amount,paid,created_at) "
            "VALUES (?,?,?,?,?,0,?)",
            (cpf, student_name, class_name, order_id, amount,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        self.conn.commit()

    def fiados_por_aluno(self):
        return self.conn.execute(
            "SELECT student_cpf, student_name, class_name, SUM(amount) total, COUNT(*) n "
            "FROM penduras WHERE paid=0 "
            "GROUP BY student_cpf, student_name, class_name ORDER BY total DESC"
        ).fetchall()

    def pay_fiado(self, cpf: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "UPDATE penduras SET paid=1, paid_at=? WHERE paid=0 AND student_cpf=?",
            (now, cpf),
        )
        self.conn.commit()

    # --------------------------------------------------------------- relatório
    def report(self, day: str | None = None):
        day = day or date.today().isoformat()
        total = self.conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM orders WHERE date(created_at)=?", (day,)
        ).fetchone()[0]
        count = self.conn.execute(
            "SELECT COUNT(*) FROM orders WHERE date(created_at)=?", (day,)
        ).fetchone()[0]
        methods = {
            r["payment_method"]: r["amount"]
            for r in self.conn.execute(
                "SELECT payment_method, COALESCE(SUM(total),0) amount FROM orders "
                "WHERE date(created_at)=? GROUP BY payment_method", (day,)
            )
        }
        pendura = self.conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM orders "
            "WHERE date(created_at)=? AND payment_status='Pendente'", (day,)
        ).fetchone()[0]
        expenses_total = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date(spent_at)=?", (day,)
        ).fetchone()[0]
        cost = self.conn.execute(
            "SELECT COALESCE(SUM(oi.quantity * p.cost),0) FROM order_items oi "
            "JOIN orders o ON o.id=oi.order_id "
            "LEFT JOIN products p ON p.id=oi.product_id "
            "WHERE date(o.created_at)=?", (day,)
        ).fetchone()[0]
        return {
            "day": day, "total": total, "count": count, "methods": methods,
            "pendura": pendura, "expenses": expenses_total, "cost": cost,
            "profit": total - cost - expenses_total,
        }

    def top_products(self, day: str | None = None, limit: int = 10):
        day = day or date.today().isoformat()
        return self.conn.execute(
            "SELECT oi.product_name, SUM(oi.quantity) qty, SUM(oi.quantity*oi.unit_price) total "
            "FROM order_items oi JOIN orders o ON o.id=oi.order_id "
            "WHERE date(o.created_at)=? GROUP BY oi.product_name "
            "ORDER BY qty DESC LIMIT ?", (day, limit)
        ).fetchall()

    def export_orders_csv(self, path: str, day: str | None = None) -> None:
        day = day or date.today().isoformat()
        rows = self.conn.execute(
            "SELECT order_number, student_name, class_name, payment_method, payment_status, "
            "total, status, created_at FROM orders WHERE date(created_at)=? ORDER BY id", (day,)
        ).fetchall()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Senha", "Aluno", "Turma", "Pagamento", "Status Pgto",
                        "Total", "Status", "Data"])
            for r in rows:
                w.writerow([r["order_number"], r["student_name"], r["class_name"],
                            r["payment_method"], r["payment_status"],
                            f"{r['total']:.2f}".replace(".", ","),
                            r["status"], r["created_at"]])

    # ------------------------------------------------------------------ senha
    def _hash(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings(key,value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    def ensure_admin_password(self, default: str = "cantina123") -> None:
        if self.get_setting("admin_password_hash") is None:
            self.set_setting("admin_password_hash", self._hash(default))

    def check_admin_password(self, password: str) -> bool:
        stored = self.get_setting("admin_password_hash")
        return stored is not None and stored == self._hash(password)

    def change_admin_password(self, new_password: str) -> None:
        self.set_setting("admin_password_hash", self._hash(new_password))

    def close(self):
        self.conn.close()