import streamlit as st
import sqlite3
import random
from datetime import datetime

# ---------- DB ----------
conn = sqlite3.connect("weigher.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_number TEXT PRIMARY KEY,
    status TEXT,
    total_eur REAL,
    items_text TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS weigh_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT,
    weight_grams INTEGER,
    source TEXT,
    created_at TEXT
)
""")

conn.commit()

def fake_scale_read():
    return random.randint(150, 1200)

# ---------- UI ----------
st.title("MANNA Weigher App (Fake)")

order_number = st.text_input("Order Number", "151456668")

col1, col2 = st.columns(2)

with col1:
    total = st.number_input("Order Total (EUR)", value=7.95)
    items = st.text_area(
        "Items",
        "x1: Gym Nut Smoothie Peanut Butter, Banana, Low Fat Milk, Natural Frozen Yogurt, Whey Protein Boost. Contains: Milk, Soya, Peanuts."
    )
    if st.button("Create / Update Order"):
        c.execute("""
        INSERT OR REPLACE INTO orders (order_number, status, total_eur, items_text)
        VALUES (?, ?, ?, ?)
        """, (order_number, "STORE_PREPARING", float(total), items))
        conn.commit()
        st.success("Order saved")

with col2:
    c.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,))
    order = c.fetchone()

    if order:
        st.subheader("Order Details")
        st.write("Status:", order[1])
        st.write("Total: EUR", order[2])
        st.write("Items:", order[3])

        if st.button("Weigh"):
            weight = fake_scale_read()
            c.execute("""
            INSERT INTO weigh_events (order_number, weight_grams, source, created_at)
            VALUES (?, ?, ?, ?)
            """, (order_number, int(weight), "FAKE_SCALE", datetime.utcnow().isoformat()))
            conn.commit()
            st.success(f"Weighed: {weight} g")
    else:
        st.info("Order not found yet. Click 'Create / Update Order' to add it.")

st.subheader("Weigh Events (latest 20)")
c.execute("""
SELECT order_number, weight_grams, source, created_at
FROM weigh_events
ORDER BY id DESC
LIMIT 20
""")
rows = c.fetchall()

if rows:
    st.table(rows)
else:
    st.write("No weigh events yet.")
