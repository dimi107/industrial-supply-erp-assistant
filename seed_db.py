import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "erp.db"

PRODUCTS = [
    ("P001", "Industrial Pump A200", "Pumps", 142, 1250.00, "unit"),
    ("P002", "Industrial Pump B400", "Pumps", 8, 2100.00, "unit"),
    ("P003", "Pressure Valve V10", "Valves", 310, 89.50, "unit"),
    ("P004", "Pressure Valve V20", "Valves", 4, 145.00, "unit"),
    ("P005", "Steel Pipe 50mm x 6m", "Pipes", 620, 34.00, "unit"),
    ("P006", "Steel Pipe 100mm x 6m", "Pipes", 12, 67.50, "unit"),
    ("P007", "Control Unit CU-1", "Electronics", 55, 3400.00, "unit"),
    ("P008", "Control Unit CU-2", "Electronics", 3, 5800.00, "unit"),
    ("P009", "Gasket Set GS-50", "Spare Parts", 890, 12.00, "set"),
    ("P010", "Bearing Kit BK-200", "Spare Parts", 6, 78.00, "kit"),
    ("P011", "Hydraulic Fluid 20L", "Fluids", 200, 45.00, "can"),
    ("P012", "Lubricant Spray LX", "Fluids", 340, 8.50, "can"),
]

CUSTOMERS = [
    ("C001", "Müller Maschinenbau GmbH", "Enterprise", "DE", 0),
    ("C002", "Alpine Engineering AG", "Enterprise", "CH", 0),
    ("C003", "Schmidt & Partner KG", "SMB", "DE", 0),
    ("C004", "Bauer Technik GmbH", "SMB", "AT", 0),
    ("C005", "Nordic Industrial AS", "Enterprise", "NO", 0),
    ("C006", "Fischer Montage GmbH", "SMB", "DE", 0),
    ("C007", "Iberian Solutions SL", "SMB", "ES", 0),
    ("C008", "Zentrum Automation AG", "Enterprise", "CH", 0),
]

STATUSES = ["delivered", "delivered", "delivered", "shipped", "pending"]


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS customers")
    c.execute("DROP TABLE IF EXISTS orders")

    c.execute("""
        CREATE TABLE products (
            id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            stock_qty INTEGER,
            price REAL,
            unit TEXT
        )
    """)

    c.execute("""
        CREATE TABLE customers (
            id TEXT PRIMARY KEY,
            name TEXT,
            segment TEXT,
            country TEXT,
            total_spend REAL
        )
    """)

    c.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            product_id TEXT,
            quantity INTEGER,
            status TEXT,
            order_date TEXT,
            total_value REAL
        )
    """)

    c.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", PRODUCTS)
    c.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", CUSTOMERS)

    random.seed(42)
    orders = []
    customer_spend = {cid: 0 for cid, *_ in CUSTOMERS}

    for i in range(1, 61):
        cid = random.choice([c[0] for c in CUSTOMERS])
        pid = random.choice([p[0] for p in PRODUCTS])
        product = next(p for p in PRODUCTS if p[0] == pid)
        qty = random.randint(1, 10)
        total = round(qty * product[4], 2)
        status = random.choice(STATUSES)
        days_ago = random.randint(1, 180)
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        orders.append((f"O{i:04d}", cid, pid, qty, status, date, total))
        customer_spend[cid] += total

    c.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?)", orders)

    for cid, spend in customer_spend.items():
        c.execute("UPDATE customers SET total_spend=? WHERE id=?", (round(spend, 2), cid))

    conn.commit()
    conn.close()
    print(f"Database seeded: {len(PRODUCTS)} products, {len(CUSTOMERS)} customers, {len(orders)} orders.")


if __name__ == "__main__":
    seed()
