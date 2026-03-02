import streamlit as st
import sqlite3
import random
from datetime import datetime

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="MANNA Weigher App (Fake)", layout="wide")

# -------------------------
# DB setup
# -------------------------
conn = sqlite3.connect("weigher.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_number TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'STORE_PREPARING',
    total_eur REAL NOT NULL DEFAULT 0,
    items_text TEXT NOT NULL DEFAULT ''
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS weigh_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL,
    weight_grams INTEGER NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""")
conn.commit()

# -------------------------
# Helpers
# -------------------------
def fake_scale_read_grams():
    return random.randint(150, 1200)

def upsert_order(order_number: str, total_eur: float, items_text: str, status: str):
    c.execute("""
    INSERT OR REPLACE INTO orders (order_number, status, total_eur, items_text)
    VALUES (?, ?, ?, ?)
    """, (order_number, status, float(total_eur), items_text or ""))
    conn.commit()

def get_order(order_number: str):
    c.execute("SELECT order_number, status, total_eur, items_text FROM orders WHERE order_number = ?", (order_number,))
    return c.fetchone()

def insert_weigh_event(order_number: str, weight_grams: int, source: str = "FAKE_SCALE"):
    c.execute("""
    INSERT INTO weigh_events (order_number, weight_grams, source, created_at)
    VALUES (?, ?, ?, ?)
    """, (order_number, int(weight_grams), source, datetime.utcnow().isoformat()))
    conn.commit()

def latest_events(limit=20):
    c.execute("""
    SELECT order_number, weight_grams, source, created_at
    FROM weigh_events
    ORDER BY id DESC
    LIMIT ?
    """, (int(limit),))
    return c.fetchall()

# -------------------------
# Styling (Streamlit CSS)
# -------------------------
st.markdown("""
<style>
/* tighten top padding */
.block-container { padding-top: 1.1rem; }

/* header bar */
.header {
  display:flex; align-items:center; justify-content:space-between;
  padding: 14px 18px; background: white; border: 1px solid #e7e8ef;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(16,24,40,.06);
  margin-bottom: 14px;
}
.brand { font-weight: 900; font-size: 24px; letter-spacing: .3px; }
.sub { font-size: 14px; color: #667085; font-weight: 600; }
.pill {
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px; border-radius: 999px; border: 1px solid #e7e8ef;
  font-weight: 700; background: #fff;
}
.dot { width:10px; height:10px; border-radius:50%; background:#12B76A; display:inline-block; }

/* main order card */
.order-card {
  background: white;
  border: 1px solid #e7e8ef;
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 2px 10px rgba(16,24,40,.06);
}

.order-top { display:flex; justify-content:space-between; align-items:flex-start; gap: 16px; }
.order-id-wrap { display:flex; align-items:center; gap: 12px; }
.order-id {
  font-size: 42px;
  font-weight: 900;
  line-height: 1;
}
.status-wrap { text-align:right; }
.status-label { color:#667085; font-weight:700; font-size:14px; }
.status {
  font-weight: 900;
  font-size: 18px;
}

/* big action buttons */
.bigbtn button {
  width: 100% !important;
  padding: 26px 18px !important;
  border-radius: 14px !important;
  font-size: 34px !important;
  font-weight: 900 !important;
  background: #3b82f6 !important;
  border: 0 !important;
}
.bigbtn-secondary button {
  width: 100% !important;
  padding: 26px 18px !important;
  border-radius: 14px !important;
  font-size: 34px !important;
  font-weight: 900 !important;
  background: #2563eb !important;
  border: 0 !important;
}
.bigbtn-ghost button {
  width: 100% !important;
  padding: 26px 18px !important;
  border-radius: 14px !important;
  font-size: 34px !important;
  font-weight: 900 !important;
  background: #e5edff !important;
  color: #1d4ed8 !important;
  border: 0 !important;
}

/* remove extra spacing under buttons */
div[data-testid="stButton"] { margin-bottom: 0.4rem; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Header (like real app)
# -------------------------
site = st.selectbox("Site", ["Blanchardstown", "Junction 6", "Pecan Square"], index=0)

st.markdown(f"""
<div class="header">
  <div>
    <div class="brand">MANNA</div>
    <div class="sub">Weigher App · <span class="pill"><span class="dot"></span> Live Updates</span></div>
  </div>
  <div class="sub"><b>{site}</b></div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# One-page flow:
# left = create/update fake order
# right = "real" support view + weigh actions
# -------------------------
left, right = st.columns([1, 1.8], gap="large")

with left:
    st.subheader("Create / Update Fake Order")

    order_number = st.text_input("Order Number", value="151456668")
    total = st.number_input("Order Total (EUR)", value=7.95, step=0.01)
    items = st.text_area(
        "Items",
        "x1: Gym Nut Smoothie Peanut Butter, Banana, Low Fat Milk, Natural Frozen Yogurt, Whey Protein Boost. Contains: Milk, Soya, Peanuts.",
        height=140
    )
    status = st.selectbox("Status", ["STORE_PREPARING", "READY_FOR_COLLECTION", "CANCELLED"], index=0)

    if st.button("Create / Update Order"):
        if not order_number.strip():
            st.error("Order number is required.")
        else:
            upsert_order(order_number.strip(), float(total), items, status)
            st.success("Order saved ✅")

with right:
    # Load order from DB
    order = get_order(order_number.strip()) if order_number.strip() else None

    st.markdown('<div class="order-card">', unsafe_allow_html=True)

    if order:
        o_num, o_status, o_total, o_items = order

        st.markdown(f"""
        <div class="order-top">
          <div class="order-id-wrap">
            <div class="order-id">{o_num}</div>
          </div>
          <div class="status-wrap">
            <div class="status-label">Status</div>
            <div class="status">{o_status}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.markdown(f"**Order total:** EUR {o_total:.2f}")
        st.markdown("**Items:**")
        st.write(o_items)

        # Last weigh
        c.execute("""
        SELECT weight_grams, created_at, source
        FROM weigh_events
        WHERE order_number = ?
        ORDER BY id DESC
        LIMIT 1
        """, (o_num,))
        lw = c.fetchone()

        st.write("")
        if lw:
            st.markdown(f"**Last weight:** {lw[0]} g  _(at {lw[1]} · {lw[2]})_")
        else:
            st.markdown("**Last weight:** —")

        st.write("")
        b1, b2, b3 = st.columns(3, gap="medium")

        with b1:
            st.markdown('<div class="bigbtn-ghost">', unsafe_allow_html=True)
            if st.button("Received"):
                st.info("Received pressed (fake for now).")
            st.markdown("</div>", unsafe_allow_html=True)

        with b2:
            st.markdown('<div class="bigbtn">', unsafe_allow_html=True)
            if st.button("Weigh"):
                weight = fake_scale_read_grams()
                insert_weigh_event(o_num, weight, source="FAKE_SCALE")
                st.success(f"Captured weight: {weight} g")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with b3:
            st.markdown('<div class="bigbtn-secondary">', unsafe_allow_html=True)
            if st.button("Extra Order"):
                st.info("Extra Order pressed (fake for now).")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("Enter an order number and click **Create / Update Order** on the left.")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.subheader("Weigh Events (latest 20)")
events = latest_events(20)
if events:
    st.table(events)
else:
    st.write("No weigh events yet.")
