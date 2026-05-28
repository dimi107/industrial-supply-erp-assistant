import sqlite3
import streamlit as st
from agent import run

DB_PATH = "erp.db"

st.set_page_config(page_title="ERP AI Assistant", page_icon="🏭", layout="wide")

EXAMPLE_QUESTIONS = [
    "Which products are running low on stock?",
    "Show me all orders for Müller Maschinenbau",
    "Who are our top 3 customers by spend?",
    "What is our total revenue and how many orders are still pending?",
    "How many Control Units do we have in stock?",
    "List all products in the Valves category",
]


def get_db_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        revenue = conn.execute("SELECT SUM(total_value) FROM orders WHERE status='delivered'").fetchone()[0] or 0
        low_stock = conn.execute("SELECT COUNT(*) FROM products WHERE stock_qty < 10").fetchone()[0]
        conn.close()
        return products, customers, orders, revenue, low_stock
    except Exception:
        return None, None, None, None, None


# --- Sidebar ---
with st.sidebar:
    st.title("🏭 ERP Dashboard")
    st.caption("Industrial Supply Co.")
    st.divider()

    products, customers, orders, revenue, low_stock = get_db_stats()

    if products is not None:
        st.metric("Products", products)
        st.metric("Customers", customers)
        st.metric("Total Orders", orders)
        st.metric("Delivered Revenue", f"€{revenue:,.0f}")
        if low_stock and low_stock > 0:
            st.warning(f"⚠️ {low_stock} products low on stock")
    else:
        st.error("Database not found. Run `python seed_db.py` first.")

    st.divider()
    st.markdown("**Try asking:**")
    for q in EXAMPLE_QUESTIONS:
        st.caption(f"• {q}")

    st.divider()
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

# --- Main chat area ---
st.title("ERP AI Assistant")
st.caption("Ask questions about inventory, customers, and orders in plain language.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about stock, customers, orders..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying ERP data..."):
            reply, updated_history = run(prompt, st.session_state.history)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.history = updated_history
