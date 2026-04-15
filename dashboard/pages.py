"""Main Streamlit dashboard for the 3D Printer Production Simulator."""
import json
import requests
import streamlit as st

from dashboard.style import inject_styles

# ── Configuration ────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"


def api(method: str, path: str, **kwargs) -> requests.Response:
    """Make an authenticated API call."""
    token = st.session_state.get("token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.request(method, f"{API_BASE}{path}", headers=headers, timeout=10, **kwargs)


def get(path: str, **kwargs):
    return api("GET", path, **kwargs).json()


def post(path: str, **kwargs):
    r = api("POST", path, **kwargs)
    if not r.ok:
        st.error(f"API error {r.status_code}: {r.json().get('detail', r.text)}")
        return None
    return r.json()


# ── Auth ─────────────────────────────────────────────────────────────────────

def login_page():
    inject_styles()
    st.title("🖨️ Production Simulator")
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        r = requests.post(
            f"{API_BASE}/api/auth/login",
            data={"username": username, "password": password},
            timeout=5,
        )
        if r.ok:
            data = r.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["user"] = data["user"]
            st.rerun()
        else:
            st.error("Invalid credentials. Default login: admin / admin123")


# ── Main dashboard ────────────────────────────────────────────────────────────

def main_dashboard():
    inject_styles()
    user = st.session_state.get("user", {})

    # ── Header ──
    col_title, col_day, col_user = st.columns([3, 2, 1])
    with col_title:
        st.title("🖨️ 3D Printer Production Simulator")
    with col_day:
        try:
            status = get("/api/simulation/status")
            st.metric("Simulation Day", status["current_day"], delta=None)
            st.caption(f"Date: {status['current_date']}  |  Capacity: {status['capacity_per_day']} units/day")
        except Exception:
            st.metric("Simulation Day", "?")
    with col_user:
        st.caption(f"👤 {user.get('username', '?')} ({user.get('role', '?')})")
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.divider()

    # ── Advance Day button ──
    if st.button("⏩ Advance Day", type="primary", use_container_width=False):
        with st.spinner("Advancing simulation..."):
            result = post("/api/simulation/advance")
        if result:
            st.success(f"Day {result['previous_day']} → {result['new_day']} | {len(result['events_generated'])} events")
            st.session_state["last_events"] = result["events_generated"]
            st.rerun()

    # ── 3-panel layout ──
    left, center, right = st.columns([1, 1.2, 0.8])

    # ── LEFT: Inventory ──
    with left:
        st.subheader("📦 Inventory")
        try:
            inv_data = get("/api/inventory")
            usage_pct = inv_data.get("usage_pct", 0)
            color = "red" if usage_pct > 90 else "orange" if usage_pct > 70 else "green"
            st.progress(min(usage_pct / 100, 1.0), text=f"Warehouse: {usage_pct:.1f}%")

            for item in sorted(inv_data.get("items", []), key=lambda x: x["product_name"]):
                qty = item["quantity"]
                avail = item["available"]
                reserved = item["reserved_quantity"]
                pct = avail / max(qty, 1)
                bar_color = "🔴" if pct < 0.2 else "🟡" if pct < 0.5 else "🟢"
                with st.expander(f"{bar_color} **{item['product_name']}** — {avail:.0f} avail / {qty:.0f} total"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total", f"{qty:.0f}")
                    c2.metric("Reserved", f"{reserved:.0f}")
                    c3.metric("Available", f"{avail:.0f}")
        except Exception as e:
            st.error(f"Failed to load inventory: {e}")

    # ── CENTER: Manufacturing Orders ──
    with center:
        st.subheader("📋 Manufacturing Orders")

        # Filter controls
        status_filter = st.selectbox(
            "Filter by status",
            ["all", "pending", "released", "waiting_materials", "completed", "cancelled"],
            key="order_status_filter",
        )

        try:
            all_orders = get("/api/orders")
            if status_filter != "all":
                orders = [o for o in all_orders if o["status"] == status_filter]
            else:
                orders = all_orders

            pending = [o for o in all_orders if o["status"] == "pending"]
            released = [o for o in all_orders if o["status"] == "released"]
            waiting = [o for o in all_orders if o["status"] == "waiting_materials"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Pending", len(pending))
            col2.metric("Released", len(released))
            col3.metric("Waiting", len(waiting))

            st.divider()

            if not orders:
                st.info("No orders match the selected filter.")
            else:
                for order in orders[:20]:  # show max 20
                    status_icon = {
                        "pending": "🟡",
                        "released": "🔵",
                        "waiting_materials": "🔴",
                        "completed": "✅",
                        "cancelled": "⬛",
                        "failed": "❌",
                    }.get(order["status"], "⚪")

                    label = f"{status_icon} #{order['id']} — {order['product_model']} × {order['quantity_needed']:.0f}"
                    with st.expander(label):
                        st.caption(f"Status: **{order['status']}**  |  Created: {order['created_date'][:10] if order['created_date'] else 'N/A'}")
                        prog = order["quantity_produced"] / max(order["quantity_needed"], 1)
                        st.progress(prog, text=f"Produced: {order['quantity_produced']:.0f} / {order['quantity_needed']:.0f}")

                        if order["status"] == "pending":
                            c1, c2 = st.columns(2)
                            if c1.button("✅ Release", key=f"release_{order['id']}", use_container_width=True):
                                result = post(f"/api/orders/{order['id']}/release")
                                if result:
                                    st.success("Order released to production!")
                                    st.rerun()
                            if c2.button("❌ Cancel", key=f"cancel_{order['id']}", use_container_width=True):
                                result = post(f"/api/orders/{order['id']}/cancel")
                                if result:
                                    st.info("Order cancelled.")
                                    st.rerun()

        except Exception as e:
            st.error(f"Failed to load orders: {e}")

    # ── RIGHT: Actions Panel ──
    with right:
        st.subheader("⚡ Actions")

        # Create manual order
        with st.expander("➕ New Manufacturing Order", expanded=False):
            try:
                models_data = get("/api/config/models")
                model_ids = [m["id"] for m in models_data]
            except Exception:
                model_ids = ["P3D-Classic", "P3D-Pro"]

            with st.form("new_order_form"):
                selected_model = st.selectbox("Product Model", model_ids)
                quantity = st.number_input("Quantity", min_value=1, value=10, step=1)
                submit_order = st.form_submit_button("Create Order")

            if submit_order:
                result = post("/api/orders", json={"product_model": selected_model, "quantity": quantity})
                if result:
                    st.success(f"Order #{result['id']} created!")
                    st.rerun()

        # Create purchase order
        with st.expander("🛒 New Purchase Order", expanded=False):
            try:
                config_data = get("/api/config")
                suppliers = config_data.get("suppliers", [])
                supplier_map = {s["name"]: s for s in suppliers}
            except Exception:
                suppliers = []
                supplier_map = {}

            if suppliers:
                with st.form("new_po_form"):
                    selected_supplier_name = st.selectbox("Supplier", list(supplier_map.keys()))
                    supplier = supplier_map.get(selected_supplier_name, {})
                    product_options = [p["product_name"] for p in supplier.get("products", [])]
                    selected_product = st.selectbox("Product", product_options) if product_options else None
                    po_qty = st.number_input("Quantity", min_value=1, value=100, step=10)

                    if selected_product:
                        # Show pricing preview
                        matching = [p for p in supplier.get("products", []) if p["product_name"] == selected_product]
                        if matching:
                            prod = matching[0]
                            tiers = prod.get("discount_tiers", [])
                            applicable = [t for t in sorted(tiers, key=lambda x: x["min_qty"]) if po_qty >= t["min_qty"]]
                            discount = applicable[-1]["discount_pct"] if applicable else 0
                            unit = prod["base_unit_cost"] * (1 - discount / 100)
                            st.caption(f"Unit cost: ${unit:.2f} (discount: {discount}%) | Total: ${unit * po_qty:,.2f}")

                    submit_po = st.form_submit_button("Place Order")

                if submit_po and selected_product:
                    result = post("/api/purchase-orders", json={
                        "supplier_id": supplier["id"],
                        "product_name": selected_product,
                        "quantity": po_qty,
                    })
                    if result:
                        st.success(f"PO #{result['id']} placed! Expected: {result['expected_delivery'][:10]}")
                        st.rerun()
            else:
                st.info("No suppliers configured.")

        # Purchase orders summary
        st.subheader("📬 Purchase Orders")
        try:
            pos = get("/api/purchase-orders")
            pending_pos = [p for p in pos if p["status"] in ("pending", "partial")]
            if pending_pos:
                for po in pending_pos[:10]:
                    st.caption(
                        f"PO #{po['id']} — {po['product_name']} × {po['quantity_ordered']:.0f} "
                        f"({po['status']}) | Due: {po['expected_delivery'][:10] if po['expected_delivery'] else 'N/A'}"
                    )
            else:
                st.info("No pending POs.")
        except Exception as e:
            st.error(f"Failed to load POs: {e}")

    # ── Event Ticker ──
    st.divider()
    st.subheader("📜 Event Log")
    col_events, col_filter = st.columns([3, 1])
    with col_filter:
        event_type_filter = st.text_input("Filter type", placeholder="e.g. demand_generated")
        event_limit = st.number_input("Show last", min_value=5, max_value=200, value=20, step=5)

    with col_events:
        try:
            params = {"page_size": event_limit}
            if event_type_filter:
                params["event_type"] = event_type_filter
            events_data = get("/api/events", params=params)
            events = events_data.get("items", [])

            EVENT_ICONS = {
                "day_advanced": "⏩",
                "demand_generated": "📊",
                "demand_batch": "📊",
                "order_released": "🚀",
                "order_cancelled": "❌",
                "order_completed": "✅",
                "material_consumed": "⚙️",
                "po_created": "📦",
                "po_arrived": "📬",
                "po_partial_delivery": "📬",
                "po_cancelled": "❌",
                "inventory_snapshot": "📸",
                "inventory_adjustment": "✏️",
                "order_created_manual": "➕",
            }

            if events:
                for ev in events:
                    icon = EVENT_ICONS.get(ev["event_type"], "📌")
                    date = (ev.get("event_date") or "")[:19]
                    st.text(f"{icon}  [{date}] {ev['event_type']:30s}  {ev['details'][:80]}")
            else:
                st.info("No events yet. Try advancing a day!")
        except Exception as e:
            st.error(f"Failed to load events: {e}")

    # ── Import / Export ──
    st.divider()
    with st.expander("💾 Import / Export Game State"):
        col_exp, col_imp = st.columns(2)

        with col_exp:
            if st.button("⬇️ Export Full State"):
                try:
                    state = get("/api/export/full-state")
                    st.download_button(
                        "Download JSON",
                        data=json.dumps(state, indent=2),
                        file_name="simulation_state.json",
                        mime="application/json",
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")

        with col_imp:
            uploaded = st.file_uploader("Import state JSON", type=["json"])
            if uploaded and st.button("⬆️ Import"):
                data = json.load(uploaded)
                result = post("/api/import/full-state", json=data)
                if result:
                    st.success(f"Imported! {result}")
                    st.rerun()


# ── Entry point ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="3D Printer Production Simulator",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "token" not in st.session_state:
    login_page()
else:
    main_dashboard()
