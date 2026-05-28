import sqlite3
from langchain_core.tools import tool

DB_PATH = "erp.db"


def _query(sql: str, params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@tool
def get_product_stock(product_name: str) -> str:
    """Get current stock level for a product by name (partial match supported)."""
    rows = _query(
        "SELECT name, category, stock_qty, price, unit FROM products WHERE name LIKE ?",
        (f"%{product_name}%",),
    )
    if not rows:
        return f"No product found matching '{product_name}'."
    lines = [f"- {r['name']} ({r['category']}): {r['stock_qty']} {r['unit']}s @ €{r['price']:.2f}" for r in rows]
    return "\n".join(lines)


@tool
def get_low_stock_products(threshold: int = 10) -> str:
    """List all products with stock below a given threshold (default: 10 units)."""
    rows = _query(
        "SELECT name, category, stock_qty, unit FROM products WHERE stock_qty < ? ORDER BY stock_qty ASC",
        (threshold,),
    )
    if not rows:
        return f"No products below {threshold} units."
    lines = [f"- {r['name']} ({r['category']}): {r['stock_qty']} {r['unit']}s remaining" for r in rows]
    return f"Low stock products (< {threshold} units):\n" + "\n".join(lines)


@tool
def get_customer_orders(customer_name: str) -> str:
    """Get order history for a customer by name (partial match supported)."""
    rows = _query(
        """
        SELECT o.id, c.name as customer, p.name as product, o.quantity,
               o.status, o.order_date, o.total_value
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN products p ON o.product_id = p.id
        WHERE c.name LIKE ?
        ORDER BY o.order_date DESC
        """,
        (f"%{customer_name}%",),
    )
    if not rows:
        return f"No orders found for customer matching '{customer_name}'."
    lines = [
        f"- [{r['id']}] {r['order_date']} | {r['product']} x{r['quantity']} | {r['status'].upper()} | €{r['total_value']:.2f}"
        for r in rows
    ]
    return f"Orders for {rows[0]['customer']}:\n" + "\n".join(lines)


@tool
def get_top_customers(limit: int = 5) -> str:
    """Get the top customers ranked by total spend."""
    rows = _query(
        "SELECT name, segment, country, total_spend FROM customers ORDER BY total_spend DESC LIMIT ?",
        (limit,),
    )
    lines = [f"{i+1}. {r['name']} ({r['segment']}, {r['country']}): €{r['total_spend']:,.2f}" for i, r in enumerate(rows)]
    return f"Top {limit} customers by spend:\n" + "\n".join(lines)


@tool
def get_revenue_summary() -> str:
    """Get overall revenue summary: total revenue, order counts by status."""
    total = _query("SELECT SUM(total_value) as total FROM orders")[0]["total"] or 0
    by_status = _query("SELECT status, COUNT(*) as cnt, SUM(total_value) as rev FROM orders GROUP BY status ORDER BY rev DESC")
    lines = [f"- {r['status'].upper()}: {r['cnt']} orders, €{r['rev']:,.2f}" for r in by_status]
    return f"Total revenue: €{total:,.2f}\n\nBreakdown by status:\n" + "\n".join(lines)


@tool
def get_products_by_category(category: str) -> str:
    """List all products in a given category (e.g. Pumps, Valves, Electronics, Pipes, Fluids, Spare Parts)."""
    rows = _query(
        "SELECT name, stock_qty, price, unit FROM products WHERE category LIKE ? ORDER BY name",
        (f"%{category}%",),
    )
    if not rows:
        return f"No products found in category '{category}'."
    lines = [f"- {r['name']}: {r['stock_qty']} in stock @ €{r['price']:.2f}/{r['unit']}" for r in rows]
    return f"Products in '{category}':\n" + "\n".join(lines)


ALL_TOOLS = [
    get_product_stock,
    get_low_stock_products,
    get_customer_orders,
    get_top_customers,
    get_revenue_summary,
    get_products_by_category,
]
