"""Renumerar IDs dos produtos para 100, 102, 104, ... em ordem alfabética por categoria."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "instance" / "cantina.db"
print(f"Banco: {DB}")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = OFF")

# 1) Lê os produtos na ordem desejada: categoria (A-Z) + nome (A-Z)
rows = conn.execute("""
    SELECT p.id, p.name, p.category_id, p.price, p.cost, p.active, p.stock
    FROM products p
    JOIN categories c ON c.id = p.category_id
    ORDER BY c.name COLLATE NOCASE, p.name COLLATE NOCASE
""").fetchall()

# 2) Cria tabela temporária
conn.executescript("""
    CREATE TABLE products_new (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category_id INTEGER NOT NULL REFERENCES categories(id),
        price REAL NOT NULL CHECK(price >= 0),
        cost REAL NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1,
        stock INTEGER NOT NULL DEFAULT 1
    );
""")

# 3) Insere com IDs 100, 102, 104, ...
new_id = 100
for r in rows:
    conn.execute(
        "INSERT INTO products_new(id,name,category_id,price,cost,active,stock) "
        "VALUES (?,?,?,?,?,?,?)",
        (new_id, r["name"], r["category_id"], r["price"], r["cost"], r["active"], r["stock"]),
    )
    new_id += 2

# 4) Troca as tabelas
conn.executescript("""
    DROP TABLE products;
    ALTER TABLE products_new RENAME TO products;
""")
conn.commit()
conn.execute("PRAGMA foreign_keys = ON")

# 5) Mostra o resultado
print("\nIDs renumerados:")
for r in conn.execute("""
    SELECT p.id, c.name cat, p.name
    FROM products p JOIN categories c ON c.id=p.category_id
    ORDER BY p.id
"""):
    print(f"  {r['id']:>3}  [{r['cat']:<12}] {r['name']}")

conn.close()
print(f"\nOK — último ID: {new_id - 2}")