import json
from datetime import datetime
import streamlit as st
import pandas as pd
from data_loader import (
    get_vayu_flavours, get_hana_flavours, get_olvm_flavours
)
from pricing_engine import (
    calculate_vayu_price, calculate_hana_price, calculate_olvm_price,
    get_flavour_specs,
    VAYU_OS_OPTIONS, HANA_OS_OPTIONS, OLVM_OS_OPTIONS,
    PRICING_TIERS, STORAGE_PRICES, BACKUP_PRICES, FIREWALL_PRICES
)
from utils import (
    format_inr, generate_quotation_id, get_logo_base64,
    build_summary_dataframe, export_to_csv, export_to_excel,
    build_quote_export_dataframe, export_quote_to_csv, export_quote_to_excel,
    enforce_integer_columns, to_whole_number
)
from auth import init_db
from history_db import init_quote_history_db, save_quotation_history
from login_page import show_login
from register_page import show_register
from profile_page import show_profile
from history_page import show_cart

from admin_page import show_admin_panel


# ADDITIONAL SERVICES PRICING DATA


INTERNET_BANDWIDTH_PRICE_PER_MBPS = 50  # INR per Mbps per month (from BOQ: 1GB = 50000)

LICENSE_PRICES = {
    "None": 0,
    "MS SQL - Standard (per 2 pCore)": 17877.83,
    "MS SQL - Enterprise (per 2 pCore)": 67311.22,
    "MS SQL - Web Edition (per 2 pCore)": 1118.06,
    "MySQL - Standard (per vCore)": 17632.86,
    "MySQL - Enterprise (per vCore)": 42318.84,
    "PostgreSQL (per month)": 13888.41,
    "Commvault Backup (per GB)": 4.35,
}

MANAGEMENT_PRICES = {
    "None": 0,
    "OS Management - Windows (per VM)": 500,
    "OS Management - Linux (per VM)": 500,
    "DB Management - MSSQL (per DB)": 6500,
    "DB Management - MySQL (per DB)": 8000,
    "DB Management - PostgreSQL (per DB)": 8000,
}

NETWORK_ELEMENT_OPTIONS = ["None", "Virtual Network", "Firewall - Basic", "Firewall - Standard", "Firewall - Advanced"]
NETWORK_ELEMENT_PRICES = {
    "None": 0,
    "Virtual Network": 0,
    "Firewall - Basic": 2000,
    "Firewall - Standard": 5000,
    "Firewall - Advanced": 10000,
}

COLOCATION_PRICES = {
    "None": 0,
    "Space (per U)": 500,
    "Power (per KWH)": 100,
}

PUBLIC_IP_PRICE_CONNECTIVITY = 900  # from master file Connectivity sheet


# PAGE CONFIG

st.set_page_config(
    page_title="VayuPrice Calculator",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()
init_quote_history_db()


def build_quotation_history_payload(quotation_id, customer_name, company_name, grand_total,
                                   quote_items=None, last_config=None, result=None):
    if quote_items:
        export_df = build_quote_export_dataframe(quote_items)
        rows = export_df.to_dict(orient="records")
        payload = {
            "type": "full_quote",
            "columns": list(export_df.columns),
            "rows": rows,
            "metadata": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    else:
        product = last_config.get("product", "") if last_config else ""
        flavour = last_config.get("flavour", "") if last_config else ""
        specs = last_config.get("specs", {}) if last_config else {}
        config = last_config.get("config", {}) if last_config else {}
        export_df = build_summary_dataframe(product, flavour, specs, config, result or {})
        rows = export_df.to_dict(orient="records")
        payload = {
            "type": "summary",
            "columns": list(export_df.columns),
            "rows": rows,
            "metadata": {
                "product": product,
                "flavour": flavour,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }

    return {
        "quotation_id": quotation_id,
        "customer_name": customer_name,
        "company_name": company_name,
        "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "grand_total": grand_total,
        "quotation_payload": payload,
    }


def save_current_quotation_history(quotation_id, user_email, customer_name, company_name,
                                   quote_items, last_config, result, grand_total):
    payload = build_quotation_history_payload(
        quotation_id=quotation_id,
        customer_name=customer_name,
        company_name=company_name,
        grand_total=grand_total,
        quote_items=quote_items,
        last_config=last_config,
        result=result,
    )
    save_quotation_history(
        quotation_id=payload["quotation_id"],
        user_email=user_email,
        customer_name=payload["customer_name"],
        company_name=payload["company_name"],
        quotation_payload=payload["quotation_payload"],
        grand_total=payload["grand_total"],
    )



# SESSION STATE INIT

for key, default in [
        ("logged_in", False), ("user", None), ("page", "login"),
        ("result", None), ("quotation_id", None), ("last_config", {}),
        ("quote_items", []), ("customer_name", ""), ("company_name", ""),
        ("history_saved_for_qid", None), ("history_view_id", None),
        ("delete_confirm_id", None), ("preview_result", None), ("show_preview", False),
        ("added_signatures", {})
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Persist login across reruns triggered by download buttons ──
if st.session_state.get("logged_in") and st.session_state.get("user"):
    st.session_state.logged_in = True


# CUSTOM CSS

st.markdown("""
<style>

    /* === BUTTON STYLES + FOCUS FIX === */
    *:focus, *:focus-visible, *:focus-within {
        outline: none !important;
        box-shadow: none !important;
    }

    div.stButton > button,
    div.stButton button,
    div[data-testid="stButton"] > button,
    div[data-testid="stButton"] button {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        min-width: 180px !important;
        width: auto !important;
        max-width: 280px !important;
        box-sizing: border-box !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 28px !important;
        height: 52px !important;
        border-radius: 18px !important;
        margin: 0 auto !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease !important;
    }

    div.stButton,
    div[data-testid="stButton"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        min-height: 52px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div.stButton > button,
    div.stButton button,
    div[data-testid="stButton"] > button,
    div[data-testid="stButton"] button {
        position: relative !important;
        top: 0 !important;
        margin: 0 !important;
        padding: 0 28px !important;
        line-height: 1.2 !important;
    }

    div.stButton > button p,
    div.stButton button p,
    div[data-testid="stButton"] > button p,
    div[data-testid="stButton"] button p {
        white-space: nowrap !important;
        margin: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div.stButton > button[kind="secondary"],
    div.stButton > button[kind="secondaryFormSubmit"],
    div[data-testid="stButton"] > button[kind="secondary"],
    div[data-testid="stButton"] > button[kind="secondaryFormSubmit"] {
        background: rgba(255,255,255,0.98) !important;
        border: 1px solid rgba(37, 99, 235, 0.35) !important;
        color: #1B3A6B !important;
        box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08) !important;
        letter-spacing: 0.02em !important;
    }

    div.stButton > button[kind="secondary"]:hover,
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background: #f3f8ff !important;
        color: #1B3A6B !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 18px 32px rgba(15, 23, 42, 0.14) !important;
        border-color: #1D4ED8 !important;
    }

    div.stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: white !important;
        border: 1px solid transparent !important;
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.16) !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.2) !important;
    }

    div.stButton > button[kind="secondary"],
    div[data-testid="stButton"] > button[kind="secondary"] {
        min-width: 170px !important;
    }

    div.stButton > button[kind="secondary"] p,
    div[data-testid="stButton"] > button[kind="secondary"] p {
        color: inherit !important;
    }

    .main {
        background: linear-gradient(135deg, #89CFF0 0%, #E0F4FF 100%);
    }
    .block-container { background: transparent; }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #89CFF0 0%, #E0F4FF 100%);
    }
    [data-testid="stHeader"] { background: transparent; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B3A6B 0%, #2563EB 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }

    .card {
        background: rgba(255, 255, 255, 0.75);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
        color: #1B3A6B;
    }

    .price-box {
        background: linear-gradient(135deg, #1B3A6B 0%, #2563EB 100%);
        border-radius: 12px;
        padding: 28px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .price-box h1 { color: white; font-size: 2.8rem; margin: 0; }
    .price-box p  { color: #CBD5E1; margin: 4px 0; font-size: 1rem; }

    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1B3A6B;
        border-left: 4px solid #2563EB;
        padding-left: 10px;
        margin-bottom: 16px;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        padding: 8px 12px;
        text-align: center;
        border: 1px solid #BFDBFE;
        backdrop-filter: blur(6px);
    }
    .metric-card h3 { color: #1B3A6B; margin: 0; font-size: 1.1rem; }
    .metric-card p  { color: #475569; margin: 2px 0 0 0; font-size: 0.75rem; }

    .success-banner {
        background: #D1FAE5; border-radius: 8px;
        padding: 12px 16px; color: #065F46;
        font-weight: 600; margin-bottom: 12px;
    }
    .error-banner {
        background: #FEE2E2; border-radius: 8px;
        padding: 12px 16px; color: #991B1B;
        font-weight: 600; margin-bottom: 12px;
    }

    .nav-bar {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 12px;
        padding: 12px 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    }

    .ttbs-nav-brand {
        display: flex;
        align-items: center;
        gap: 18px;
        padding-top: 2px;
        min-height: 62px;
    }
    .ttbs-logo-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
        border-radius: 12px;
        padding: 8px 16px;
        box-shadow: 0 4px 14px rgba(27, 58, 107, 0.14);
        border: 1px solid rgba(37, 99, 235, 0.12);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .ttbs-logo-wrap:hover {
        box-shadow: 0 6px 18px rgba(27, 58, 107, 0.18);
        transform: translateY(-1px);
    }
    .ttbs-logo-wrap img {
        height: 48px;
        width: auto;
        max-width: 220px;
        object-fit: contain;
        display: block;
    }
    .ttbs-nav-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #1B3A6B;
        line-height: 1.3;
    }
    .ttbs-nav-greeting {
        font-weight: 400;
        font-size: 0.95rem;
        color: #3B5F8F;
    }

    label, p, div { color: #1E3A5F; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] [data-testid="stSelectboxValue"],
    .stSelectbox div[data-baseweb="select"] input,
    input[type="number"],
    .stNumberInput input {
        color: #1B3A6B !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] [data-testid="stSelectboxValue"],
    .stSelectbox div[data-baseweb="select"] input {
        color: #1B3A6B !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    div[data-baseweb="popover"] ul li,
    div[data-baseweb="popover"] ul li div,
    div[data-baseweb="popover"] ul li span,
    div[data-baseweb="menu"] ul li,
    [role="option"],
    [role="listbox"] li {
        color: #1B3A6B !important;
        font-weight: 400 !important;
        background-color: white !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: unset !important;
        padding: 10px 16px !important;
    }

    ul[role="listbox"] {
        width: max-content !important;
        max-width: 360px !important;
    }

    div[data-baseweb="popover"] ul li:hover,
    [role="option"]:hover {
        background-color: #2563EB !important;
        color: white !important;
    }

    [aria-selected="true"],
    [role="option"][aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #1B3A6B !important;
        font-weight: 600 !important;
    }

    @media (prefers-color-scheme: dark) {
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] [data-testid="stSelectboxValue"],
        input[type="number"],
        .stNumberInput input { color: #1B3A6B !important; }
        div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.95) !important;
        }
    }

    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 8px !important;
        border: 1px solid #BFDBFE !important;
    }
    div[data-baseweb="input"] input {
        background-color: transparent !important;
        color: #1B3A6B !important;
        font-weight: 600 !important;
    }
    .stNumberInput > div > div,
    .stNumberInput > div > div > div,
    [data-testid="stNumberInput"] > div,
    [data-testid="stNumberInput"] div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
    }
    .stNumberInput button {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #1B3A6B !important;
        border: none !important;
    }
    .stNumberInput button:hover {
        background-color: #2563EB !important;
        color: white !important;
    }

    .history-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 8px;
    }
    .history-table th,
    .history-table td {
        padding: 12px 10px;
        border-bottom: 1px solid #E2E8F0;
        color: #1B3A6B;
        text-align: left;
    }
    .history-table th {
        background: rgba(243, 244, 246, 0.95);
        font-weight: 700;
    }
    .history-table tr:last-child td {
        border-bottom: none;
    }

    @media (prefers-color-scheme: dark) {
        div[data-baseweb="input"],
        .stNumberInput > div > div,
        .stNumberInput > div > div > div,
        [data-testid="stNumberInput"] div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.9) !important;
        }
        div[data-baseweb="input"] input {
            background-color: transparent !important;
            color: #1B3A6B !important;
        }
        .stNumberInput button {
            background-color: rgba(255, 255, 255, 0.9) !important;
            color: #1B3A6B !important;
        }
    }

    div[data-baseweb="select"] svg,
    div[data-baseweb="select"] [data-testid="stSelectboxArrow"],
    .stSelectbox svg {
        color: #1B3A6B !important;
        fill: #1B3A6B !important;
        opacity: 1 !important;
    }

    @media (prefers-color-scheme: dark) {
        div[data-baseweb="select"] svg,
        div[data-baseweb="select"] [data-testid="stSelectboxArrow"],
        .stSelectbox svg {
            color: #1B3A6B !important;
            fill: #1B3A6B !important;
            opacity: 1 !important;
        }
    }

    [data-testid="stTooltipHoverTarget"] {
        background-color: #1B3A6B !important;
        border-radius: 50% !important;
        width: 18px !important;
        height: 18px !important;
        min-width: 18px !important;
        min-height: 18px !important;
        padding: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
        outline: none !important;
        border: none !important;
    }
    [data-testid="stTooltipHoverTarget"] svg,
    [data-testid="stTooltipHoverTarget"] svg *,
    [data-testid="stTooltipHoverTarget"] svg path,
    [data-testid="stTooltipHoverTarget"] svg circle {
        stroke: white !important;
        fill: none !important;
        color: white !important;
        opacity: 1 !important;
    }
            

    
    /* Bigger, bolder expander section headers (Step 3) */
    div[data-testid="stExpander"] summary p {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #1B3A6B !important;
    }


            
    
</style>
""", unsafe_allow_html=True)


# ROUTING — show login/register if not logged in

if not st.session_state.logged_in:
    show_login()
    st.stop()

if "result" not in st.session_state:
    st.session_state.result = None
if "quotation_id" not in st.session_state:
    st.session_state.quotation_id = generate_quotation_id()
if "last_config" not in st.session_state:
    st.session_state.last_config = {}
if "quote_items" not in st.session_state:
    st.session_state.quote_items = []


# NAVBAR

user = st.session_state.user

ADMIN_EMAIL = "vaibhav.chaudhary@tatatel.co.in"
is_admin = (st.session_state.user.get("email") or "").strip().lower() == ADMIN_EMAIL.strip().lower()

nav_cols = st.columns([3, 1, 1, 1, 1, 1]) if is_admin else st.columns([3, 1, 1, 1, 1])

with nav_cols[0]:
    logo_b64 = get_logo_base64()
    logo_html = (
        f'<div class="ttbs-logo-wrap">'
        f'<img src="data:image/png;base64,{logo_b64}" alt="TATA Tele Business Services"/>'
        f'</div>'
        if logo_b64 else ""
    )
    st.markdown(
        f"<div class='ttbs-nav-brand'>"
        f"{logo_html}"
        f"<span class='ttbs-nav-title'>"
        f"☁️ VayuPrice Calculator &nbsp;|&nbsp; "
        f"<span class='ttbs-nav-greeting'>Hi, {user['full_name'].split()[0]}!</span>"
        f"</span></div>",
        unsafe_allow_html=True
    )
with nav_cols[1]:
    if st.button("Dashboard", use_container_width=True,
                 type="primary" if st.session_state.page == "dashboard" else "secondary"):
        st.session_state.page = "dashboard"
        st.rerun()
with nav_cols[2]:
    if st.button("👤 Profile", use_container_width=True,
                 type="primary" if st.session_state.page == "profile" else "secondary"):
        st.session_state.page = "profile"
        st.rerun()
with nav_cols[3]:
    if st.button("History", use_container_width=True,
                 type="primary" if st.session_state.page == "cart" else "secondary"):
        st.session_state.page = "cart"
        st.rerun()
if is_admin:
    with nav_cols[4]:
        if st.button("🔐 Admin", use_container_width=True,
                     type="primary" if st.session_state.page == "admin" else "secondary"):
            st.session_state.page = "admin"
            st.rerun()
    with nav_cols[5]:
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            for key in ["logged_in", "user", "page", "result", "quotation_id",
                        "last_config", "quote_items", "customer_name", "company_name",
                        "history_saved_for_qid", "history_view_id", "delete_confirm_id"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.page = "login"
            st.rerun()
else:
    with nav_cols[4]:
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            for key in ["logged_in", "user", "page", "result", "quotation_id",
                        "last_config", "quote_items", "customer_name", "company_name",
                        "history_saved_for_qid", "history_view_id", "delete_confirm_id"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.page = "login"
            st.rerun()

st.markdown("---")


# PAGE ROUTING

if st.session_state.page == "profile":
    show_profile()
    st.stop()

if st.session_state.page == "cart":
    show_cart()
    st.stop()

if st.session_state.page == "admin":
    if not is_admin:
        st.error("⛔ Access denied. You are not authorized to view this page.")
        st.stop()
    show_admin_panel()
    st.stop()


# SIDEBAR

with st.sidebar:
    st.markdown("## ☁️ Cloud Pricing")
    st.markdown("---")
    st.markdown("### 🏢 Tata TeleServices")
    st.markdown("*A Tata Communications Company*")
    st.markdown("---")
    st.markdown("### 📌 Navigation")
    st.markdown("- Configure your product")
    st.markdown("- Click **Calculate Price**")
    st.markdown("- View & download quotation")
    st.markdown("---")
    st.markdown("### ℹ️ Notes")
    st.markdown("- All prices in **INR**")
    st.markdown("- Prices **exclude taxes**")
    st.markdown("- Valid for **30 days**")
    st.markdown("- Per month unless stated")
    st.markdown("---")
    st.markdown("### 📋 Guidelines")
    st.markdown("- India pricing only")
    st.markdown("- Term discount applicable only for fixed-term contracts")
    st.markdown("- Components include VMs, Storage, Backup, and Connectivity")


# MAIN HEADER

st.markdown("""
<div class="card">
    <h2 style="margin:0; color:#1B3A6B;"> VayuPrice Calculator </h2>
    <h4 style="margin:0; color: #4D516D;"> ☁️ Cloud Infrastructure Price Calculator </h4>
    <p style="margin:4px 0 0 0; color:#64748B;">
        Tata TeleServices · India Region · All prices in INR per month
    </p>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    customer_col, company_col = st.columns(2)
    with customer_col:
        st.session_state.customer_name = st.text_input(
            "Customer Name",
            value=st.session_state.customer_name,
            placeholder="Enter customer name",
            key="customer_name_input"
        )
    with company_col:
        st.session_state.company_name = st.text_input(
            "Company Name",
            value=st.session_state.company_name,
            placeholder="Enter company name",
            key="company_name_input"
        )
    st.markdown('</div>', unsafe_allow_html=True)


# STEP 1 — PRODUCT SELECTION

st.markdown('<div class="section-title">Step 1 — Select Product</div>',
            unsafe_allow_html=True)

product = st.selectbox(
    "Select Product",
    ["Vayu Cloud", "Hana Grid", "OLVM"],
    key="product_select",
    help="Choose the cloud product you want to price"
)

st.markdown("---")


# STEP 2 — VM CONFIGURATION

st.markdown('<div class="section-title">Step 2 — Configure VM</div>',
            unsafe_allow_html=True)

config = {}


# VAYU CLOUD FORM

if product == "Vayu Cloud":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🖥️ VM Configuration**")

        flavour = st.selectbox(
            "Flavour",
            get_vayu_flavours(),
            key="vayu_flavour",
            help="Select VM size/flavour"
        )

        os_type = st.selectbox(
            "Operating System",
            VAYU_OS_OPTIONS,
            key="vayu_os"
        )

        pricing_tier = st.selectbox(
            "Pricing Tier",
            PRICING_TIERS,
            key="vayu_tier",
            help="Hourly PPU = Pay Per Use"
        )

        quantity = st.number_input(
            "Quantity (No. of VMs)",
            min_value=1, max_value=500,
            value=1, step=1,
            key="vayu_qty"
        )

    with col2:
        st.markdown("**💾 Storage & Add-ons**")

        storage_type = st.selectbox(
            "Storage Type",
            ["None"] + list(STORAGE_PRICES.keys()),
            key="vayu_storage_type"
        )

        storage_gb = st.number_input(
            "Storage Size (GB)",
            min_value=0, max_value=100000,
            value=0, step=50,
            key="vayu_storage_gb"
        ) if storage_type != "None" else 0

        backup_type = st.selectbox(
            "Backup Type",
            list(BACKUP_PRICES.keys()),
            key="vayu_backup_type"
        )

        backup_gb = st.number_input(
            "Backup Size (GB)",
            min_value=0, max_value=100000,
            value=0, step=50,
            key="vayu_backup_gb"
        ) if backup_type != "None" else 0

        

        public_ips = st.number_input(
            "No. of Public IPs",
            min_value=0, max_value=50,
            value=0, step=1,
            key="vayu_ips"
        )

    config = {
        "Element": "ICS",
        "Hypervisor": "Open Stack",
        "Operating System": os_type,
        "Pricing Tier": pricing_tier,
        "Storage Type": storage_type,
        "Storage (GB)": storage_gb,
        "Backup Type": backup_type,
        "Backup (GB)": backup_gb,
        "Public IPs": public_ips,
    }


# HANA GRID FORM

elif product == "Hana Grid":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🖥️ VM Configuration**")

        flavour = st.selectbox(
            "Flavour",
            get_hana_flavours(),
            key="hana_flavour"
        )

        os_type = st.selectbox(
            "Operating System",
            HANA_OS_OPTIONS,
            key="hana_os"
        )

        pricing_tier = st.selectbox(
            "Pricing Tier",
            PRICING_TIERS,
            key="hana_tier"
        )

        quantity = st.number_input(
            "Quantity (No. of VMs)",
            min_value=1, max_value=500,
            value=1, step=1,
            key="hana_qty"
        )

    with col2:
        st.markdown("**💾 Storage & Add-ons**")

        storage_type = st.selectbox(
            "Storage Type",
            ["None"] + list(STORAGE_PRICES.keys()),
            key="hana_storage_type"
        )

        storage_gb = st.number_input(
            "Storage Size (GB)",
            min_value=0, max_value=100000,
            value=0, step=50,
            key="hana_storage_gb"
        ) if storage_type != "None" else 0

        backup_type = st.selectbox(
            "Backup Type",
            list(BACKUP_PRICES.keys()),
            key="hana_backup_type"
        )

        backup_gb = st.number_input(
            "Backup Size (GB)",
            min_value=0, max_value=100000,
            value=0, step=50,
            key="hana_backup_gb"
        ) if backup_type != "None" else 0

    config = {
        "Element": "ICS",
        "Hypervisor": "Open Stack",
        "Operating System": os_type,
        "Pricing Tier": pricing_tier,
        "Storage Type": storage_type,
        "Storage (GB)": storage_gb,
        "Backup Type": backup_type,
        "Backup (GB)": backup_gb,
    }


# OLVM FORM

elif product == "OLVM":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🖥️ VM Configuration**")
        st.info("ℹ️ OLVM supports Linux only (High Performance, 1:2 contention ratio)")

        flavour = st.selectbox(
            "Flavour",
            get_olvm_flavours(),
            key="olvm_flavour"
        )

        pricing_tier = st.selectbox(
            "Pricing Tier",
            PRICING_TIERS,
            key="olvm_tier"
        )

        quantity = st.number_input(
            "Quantity (No. of VMs)",
            min_value=1, max_value=500,
            value=1, step=1,
            key="olvm_qty"
        )

    with col2:
        st.markdown("**💾 Storage & Add-ons**")

        storage_type = st.selectbox(
            "Storage Type",
            ["None"] + list(STORAGE_PRICES.keys()),
            key="olvm_storage_type"
        )

        storage_gb = st.number_input(
            "Storage Size (GB)",
            min_value=0, max_value=100000,
            value=0, step=50,
            key="olvm_storage_gb"
        ) if storage_type != "None" else 0

        backup_type = st.selectbox(
            "Backup Type",
            list(BACKUP_PRICES.keys()),
            key="olvm_backup_type"
        )

        backup_gb = st.number_input(
            "Backup Size (GB)",
            min_value=0, max_value=100000,
            value=0, step=50,
            key="olvm_backup_gb"
        ) if backup_type != "None" else 0

    config = {
        "Element": "ICS",
        "Hypervisor": "OLVM",
        "Pricing Tier": pricing_tier,
        "Storage Type": storage_type,
        "Storage (GB)": storage_gb,
        "Backup Type": backup_type,
        "Backup (GB)": backup_gb,
    }


# FLAVOUR SPECS PREVIEW

specs = get_flavour_specs(product, flavour)
specs_to_display = {k: v for k, v in (specs or {}).items() if k != "Root Disk Windows (GB)"}
if specs_to_display:
    st.markdown('<div class="section-title">Selected Flavour Specs</div>',
                unsafe_allow_html=True)
    spec_cols = st.columns(len(specs_to_display))
    for i, (k, v) in enumerate(specs_to_display.items()):
        with spec_cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{v}</h3>
                <p>{k}</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")


# STEP 3 — ADDITIONAL SERVICES (NEW)

st.markdown('<div class="section-title">Step 3 — Additional Services (Optional)</div>',
            unsafe_allow_html=True)

with st.expander("**🌐 Network & Security Services**", expanded=False):
    ns_col1, ns_col2 = st.columns(2)

    with ns_col1:
        st.markdown("**Internet / Connectivity**")
        ns_element = st.selectbox(
            "Element",
            ["None", "Internet", "DCI Interconnect", "VPN"],
            key="ns_element",
            help="Type of network service"
        )
        ns_feature = st.selectbox(
            "Feature",
            ["None", "Bandwidth", "Port Speed"],
            key="ns_feature"
        )
        ns_subtype = st.selectbox(
            "Sub Type",
            ["None", "IPC Internet", "Optical 10G", "Site to Site VPN", "Client to Site VPN"],
            key="ns_subtype"
        )

    with ns_col2:
        st.markdown("**Bandwidth & Quantity**")
        ns_bandwidth_mbps = st.number_input(
            "Bandwidth (Mbps)",
            min_value=0, max_value=100000,
            value=0, step=100,
            key="ns_bandwidth",
            help="Enter bandwidth in Mbps. e.g. 1000 = 1 Gbps"
        )
        ns_unit = st.selectbox(
            "Unit",
            ["Mbps", "Gbps"],
            key="ns_unit"
        )
        ns_qty = st.number_input(
            "Quantity",
            min_value=0, max_value=100,
            value=0, step=1,
            key="ns_qty"
        )
        ns_remark = st.text_input(
            "Remark",
            value="",
            key="ns_remark",
            placeholder="e.g. Unlimited Download & Upload"
        )

    st.markdown("---")
    st.markdown("**🔥 Firewall**")
    fw_col1, fw_col2 = st.columns(2)

    with fw_col1:
        ns_firewall = st.selectbox(
            "Firewall Type",
            list(FIREWALL_PRICES.keys()),
            key="ns_firewall"
        )

    with fw_col2:
        ns_firewall_mbps = st.number_input(
            "Firewall Bandwidth (Mbps)",
            min_value=0, max_value=100000,
            step=100,
            key="ns_firewall_mbps",
            help="Enter the bandwidth this firewall should handle",
        )

    if ns_firewall == "None" and ns_firewall_mbps > 0:
        st.caption("⚠️ Select a Firewall Type above to include this bandwidth in the quote.")

    # Calculate internet cost
    ns_cost = 0
    if ns_element != "None" and ns_bandwidth_mbps > 0 and ns_qty > 0:
        ns_cost = INTERNET_BANDWIDTH_PRICE_PER_MBPS * ns_bandwidth_mbps * ns_qty

    # Calculate firewall cost (price per Mbps, based on firewall type selected)
    firewall_cost = 0
    if ns_firewall != "None" and ns_firewall_mbps > 0:
        firewall_cost = round(FIREWALL_PRICES.get(ns_firewall, 0) * ns_firewall_mbps, 2)

    st.info(f"Estimated Network Cost: {format_inr(ns_cost)} / month")
    if ns_firewall != "None":
        st.info(f"Estimated Firewall Cost: {format_inr(firewall_cost)} / month")

with st.expander("**🔐 Software & Licenses**", expanded=False):
    lic_col1, lic_col2 = st.columns(2)

    with lic_col1:
        st.markdown("**License Type**")
        lic_element = st.selectbox(
            "Element (License)",
            ["None", "Windows Server", "Linux", "MS SQL", "MySQL",
             "PostgreSQL", "Commvault Backup License"],
            key="lic_element"
        )
        lic_subtype = st.selectbox(
            "License Type",
            list(LICENSE_PRICES.keys()),
            key="lic_subtype"
        )
        lic_description = st.text_input(
            "Description",
            value="",
            key="lic_description",
            placeholder="e.g. OS lic."
        )

    with lic_col2:
        st.markdown("**Quantity & Remarks**")
        lic_unit = st.selectbox(
            "Unit",
            ["# of Licenses", "per vCore", "per 2 pCore", "per DB", "per GB"],
            key="lic_unit"
        )
        lic_qty = st.number_input(
            "Quantity",
            min_value=0, max_value=100000,
            value=0, step=1,
            key="lic_qty"
        )
        lic_remark = st.text_input(
            "Remark",
            value="",
            key="lic_remark",
            placeholder="e.g. BYOL / Included / Customer Scope"
        )

    lic_cost = 0
    if lic_subtype != "None" and lic_qty > 0:
        lic_cost = LICENSE_PRICES.get(lic_subtype, 0) * lic_qty
    st.info(f"Estimated License Cost: {format_inr(lic_cost)} / month")

with st.expander("**💾 Backup Storage**", expanded=False):
    bk_col1, bk_col2 = st.columns(2)

    with bk_col1:
        st.markdown("**Backup Storage Configuration**")
        bk_element = st.selectbox(
            "Element",
            ["None", "ICS", "BET"],
            key="bk_element"
        )
        bk_make = st.selectbox(
            "Make",
            ["None", "BET", "Commvault"],
            key="bk_make"
        )
        bk_model = st.selectbox(
            "Model",
            ["None", "Value Based", "Resilient", "Geo-Resilient"],
            key="bk_model"
        )

    with bk_col2:
        st.markdown("**Storage Details**")
        bk_storage_config = st.selectbox(
            "Storage Configuration",
            ["None", "Object-Resilient", "Object-Value", "Block"],
            key="bk_storage_config"
        )
        bk_description = st.text_input(
            "Description",
            value="",
            key="bk_description",
            placeholder="e.g. Object Storage for backup"
        )
        bk_unit = st.selectbox("Unit", ["GB", "TB"], key="bk_unit")
        bk_qty = st.number_input(
            "Quantity (GB)",
            min_value=0, max_value=1000000,
            value=0, step=100,
            key="bk_qty"
        )
        bk_remark = st.text_input(
            "Remark",
            value="",
            key="bk_remark",
            placeholder="e.g. Daily Incremental, Weekly Full"
        )

    bk_cost = 0
    if bk_model != "None" and bk_qty > 0:
        bk_price_map = {
            "Value Based": 1.826923,
            "Resilient": 3.425481,
            "Geo-Resilient": 3.882212,
        }
        bk_cost = bk_price_map.get(bk_model, 0) * bk_qty
    st.info(f"Estimated Backup Storage Cost: {format_inr(bk_cost)} / month")

with st.expander("**🖧 Network Elements**", expanded=False):
    ne_col1, ne_col2 = st.columns(2)

    with ne_col1:
        st.markdown("**Network Element**")
        ne_element = st.selectbox(
            "Element",
            ["None", "Virtual Network"],
            key="ne_element"
        )
        ne_description = st.text_input(
            "Description",
            value="",
            key="ne_description",
            placeholder="e.g. Network isolation"
        )

    with ne_col2:
        st.markdown("**Quantity & Remark**")
        ne_unit = st.selectbox(
            "Unit",
            ["None", "Qty", "Port", "Gig"],
            key="ne_unit"
        )
        ne_qty = st.number_input(
            "Quantity",
            min_value=0, max_value=100,
            value=0, step=1,
            key="ne_qty"
        )
        ne_remark = st.text_input(
            "Remark",
            value="",
            key="ne_remark",
            placeholder="e.g. Included / Customer Scope"
        )

    ne_cost = NETWORK_ELEMENT_PRICES.get(ne_element, 0) if ne_element != "None" else 0
    st.info(f"Estimated Network Element Cost: {format_inr(ne_cost)} / month")

with st.expander("**⚙️ Management Services**", expanded=False):
    mg_col1, mg_col2 = st.columns(2)

    with mg_col1:
        st.markdown("**Management Type**")
        mg_element = st.selectbox(
            "Element",
            ["None", "OS-Management", "DB Management", "Firewall Management"],
            key="mg_element"
        )
        mg_description = st.text_input(
            "Description",
            value="",
            key="mg_description",
            placeholder="e.g. Managed services for Windows"
        )

    with mg_col2:
        st.markdown("**Quantity & Remark**")
        mg_unit = st.selectbox(
            "Unit",
            ["VM", "DB", "Firewall"],
            key="mg_unit"
        )
        mg_qty = st.number_input(
            "Quantity",
            min_value=0, max_value=500,
            value=0, step=1,
            key="mg_qty"
        )
        mg_remark = st.text_input(
            "Remark",
            value="",
            key="mg_remark",
            placeholder="e.g. Included / Customer Scope"
        )

    mg_cost = 0
    if mg_element != "None" and mg_qty > 0:
        mg_price_map = {
            "OS-Management": 500,
            "DB Management": 6500,
            "Firewall Management": 2000,
        }
        mg_cost = mg_price_map.get(mg_element, 0) * mg_qty
    st.info(f"Estimated Management Cost: {format_inr(mg_cost)} / month")

with st.expander("**📦 Miscellaneous Items**", expanded=False):
    mi_col1, mi_col2 = st.columns(2)

    with mi_col1:
        st.markdown("**Miscellaneous**")
        mi_element = st.selectbox(
            "Element",
            ["None", "IP", "Space", "Power", "Support",
             "Tenant", "Wire", "Cross Connect", "Switch Port"],
            key="mi_element"
        )
        mi_description = st.text_input(
            "Description",
            value="",
            key="mi_description",
            placeholder="e.g. Public IP /27 pool"
        )

    with mi_col2:
        st.markdown("**Quantity & Remark**")
        mi_unit = st.selectbox(
            "Unit",
            ["None", "IPs", "U", "KWH", "Sessions", "Gig", "Wire"],
            key="mi_unit"
        )
        mi_qty = st.number_input(
            "Quantity",
            min_value=0, max_value=10000,
            value=0, step=1,
            key="mi_qty"
        )
        mi_price_per_unit = st.number_input(
            "Price per Unit (INR)",
            min_value=0.0,
            value=0.0, step=100.0,
            key="mi_price_per_unit",
            help="Enter price per unit manually for miscellaneous items"
        )
        mi_remark = st.text_input(
            "Remark",
            value="",
            key="mi_remark",
            placeholder="e.g. Min 2 IPs Required"
        )

    mi_cost = mi_price_per_unit * mi_qty if mi_qty > 0 else 0
    st.info(f"Estimated Miscellaneous Cost: {format_inr(mi_cost)} / month")

# Total additional services cost
total_additional = ns_cost + firewall_cost + lic_cost + bk_cost + ne_cost + mg_cost + mi_cost
if total_additional > 0:
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.85); border-radius:10px;
                padding:14px 20px; border-left: 4px solid #2563EB; margin-top:8px;">
        <b style="color:#1B3A6B;">Total Additional Services Cost:</b>
        <span style="color:#2563EB; font-weight:700; font-size:1.1rem;">
            &nbsp;{format_inr(total_additional)} / month
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# BUTTONS ROW

btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1], gap="large")

with btn_col1:
    preview_clicked = st.button(
        "📊 Price Summary",
        type="secondary",
        use_container_width=True,
        help="Preview the price of each selected item before finalizing the quote"
    )

with btn_col2:
    calculate_clicked = st.button(
        "🧮 Calculate Price",
        type="primary",
        use_container_width=True
    )

with btn_col3:
    reset_clicked = st.button(
        "🔄 Reset",
        type="secondary",
        use_container_width=True
    )

if reset_clicked:
    st.session_state.result = None
    st.session_state.preview_result = None
    st.session_state.show_preview = False
    st.session_state.added_signatures = {}
    st.session_state.quotation_id = generate_quotation_id()
    st.session_state.last_config = {}
    st.session_state.quote_items = []

    # Reset Step 3 additional services
    keys_to_reset = [
        "ns_element", "ns_feature", "ns_subtype", "ns_bandwidth",
        "ns_unit", "ns_qty", "ns_remark", "ns_firewall", "ns_firewall_mbps",
        "lic_element", "lic_subtype", "lic_description",
        "lic_unit", "lic_qty", "lic_remark",
        "bk_element", "bk_make", "bk_model", "bk_storage_config",
        "bk_description", "bk_unit", "bk_qty", "bk_remark",
        "ne_element", "ne_description", "ne_unit", "ne_qty", "ne_remark",
        "mg_element", "mg_description", "mg_unit", "mg_qty", "mg_remark",
        "mi_element", "mi_description", "mi_unit", "mi_qty",
        "mi_price_per_unit", "mi_remark",
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

if preview_clicked:
    errors = []
    if storage_type != "None" and storage_gb == 0:
        errors.append("Please enter Storage Size (GB) greater than 0.")

    if errors:
        for e in errors:
            st.markdown(f'<div class="error-banner">⚠️ {e}</div>',
                        unsafe_allow_html=True)
    else:
        with st.spinner("Building price summary..."):
            if product == "Vayu Cloud":
                preview_vm_result = calculate_vayu_price(
                    flavour, os_type, pricing_tier, quantity,
                    storage_type if storage_type != "None" else "None",
                    storage_gb, backup_type, backup_gb,
                    "None", public_ips
                )
            elif product == "Hana Grid":
                preview_vm_result = calculate_hana_price(
                    flavour, os_type, pricing_tier, quantity,
                    storage_type if storage_type != "None" else "None",
                    storage_gb, backup_type, backup_gb
                )
            else:
                preview_vm_result = calculate_olvm_price(
                    flavour, pricing_tier, quantity,
                    storage_type if storage_type != "None" else "None",
                    storage_gb, backup_type, backup_gb
                )

        if preview_vm_result:
            preview_rows = []
            for k, v in preview_vm_result.items():
                if k != "Grand Total" and isinstance(v, (int, float)) and v != 0:
                    preview_rows.append({"Item": k, "Amount (INR / month)": round(v, 2)})

            addl_items = [
                ("Network / Internet", ns_cost),
                ("Firewall", firewall_cost),
                ("Software License", lic_cost),
                ("Backup Storage", bk_cost),
                ("Network Element", ne_cost),
                ("Management Services", mg_cost),
                ("Miscellaneous", mi_cost),
            ]
            for label, cost in addl_items:
                if cost > 0:
                    preview_rows.append({"Item": label, "Amount (INR / month)": round(cost, 2)})

            preview_grand_total = preview_vm_result.get("Grand Total", 0) + total_additional

            st.session_state.preview_result = {
                "rows": preview_rows,
                "grand_total": round(preview_grand_total, 2),
            }
            st.session_state.show_preview = True
        else:
            st.session_state.show_preview = False
            st.markdown('<div class="error-banner">❌ Could not build price summary. Please check your selections.</div>',
                        unsafe_allow_html=True)

if st.session_state.show_preview and st.session_state.preview_result:
    st.markdown("---")
    st.markdown('<div class="section-title">📊 Individual Price Summary (Preview)</div>',
                unsafe_allow_html=True)
    preview_df = pd.DataFrame(st.session_state.preview_result["rows"])
    st.dataframe(preview_df, use_container_width=True, hide_index=True)
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.85); border-radius:10px;
                padding:14px 20px; border-left: 4px solid #2563EB; margin-top:8px;">
        <b style="color:#1B3A6B;">Estimated Grand Total:</b>
        <span style="color:#2563EB; font-weight:700; font-size:1.1rem;">
            &nbsp;{format_inr(st.session_state.preview_result['grand_total'])} / month
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("This is a preview only — nothing has been added to your quote yet. Adjust Step 2/3 selections and re-click the summary button anytime, or click **Calculate Price** below to finalize this configuration.")


# CALCULATE

if calculate_clicked:
    st.session_state.show_preview = False
    errors = []
    if storage_type != "None" and storage_gb == 0:
        errors.append("Please enter Storage Size (GB) greater than 0.")
    

    if errors:
        for e in errors:
            st.markdown(f'<div class="error-banner">⚠️ {e}</div>',
                        unsafe_allow_html=True)
    else:
        with st.spinner("Calculating price..."):
            if product == "Vayu Cloud":
                result = calculate_vayu_price(
                    flavour, os_type, pricing_tier, quantity,
                    storage_type if storage_type != "None" else "None",
                    storage_gb, backup_type, backup_gb,
                    "None", public_ips
                )
            elif product == "Hana Grid":
                result = calculate_hana_price(
                    flavour, os_type, pricing_tier, quantity,
                    storage_type if storage_type != "None" else "None",
                    storage_gb, backup_type, backup_gb
                )
            else:
                result = calculate_olvm_price(
                    flavour, pricing_tier, quantity,
                    storage_type if storage_type != "None" else "None",
                    storage_gb, backup_type, backup_gb
                )

        if result:
            vm_grand_total = result.get("Grand Total", 0)
            result["Additional Services Cost"] = round(total_additional, 2)
            result["Grand Total"] = round(vm_grand_total + total_additional, 2)

            st.session_state.result = result
            st.session_state.quotation_id = st.session_state.quotation_id or generate_quotation_id()

            def _blank_row():
                return {
                    "Category": "", "_bucket": "", "_signature": None,
                    "Product": "", "Flavour": "", "Element": "", "Hypervisor": "",
                    "Operating System": "", "Pricing Tier": "",
                    "Storage Type": "", "Storage (GB)": 0,
                    "Backup Type": "", "Backup (GB)": 0,
                    "Public IPs": 0, "Quantity": "", "vCPU": "", "RAM (GB)": "",
                    "Network Element": "", "Network Feature": "", "Network Sub Type": "",
                    "Bandwidth (Mbps)": 0, "Network Cost (INR)": 0.0,
                    "Firewall Type": "", "Firewall Bandwidth (Mbps)": 0, "Firewall Cost (INR)": 0.0,
                    "License Element": "", "License Sub Type": "", "License Qty": 0, "License Cost (INR)": 0.0,
                    "Backup Storage Model": "", "Backup Storage (GB)": 0, "Backup Storage Cost (INR)": 0.0,
                    "Network Element Type": "", "Network Element Cost (INR)": 0.0,
                    "Management Type": "", "Management Qty": 0, "Management Cost (INR)": 0.0,
                    "Misc Element": "", "Misc Qty": 0, "Misc Cost (INR)": 0.0,
                    "Line Total (INR)": 0.0,
                }

            added_sigs = st.session_state.added_signatures
            new_rows = []
            added_labels = []

            # ── VM Configuration ──
            vm_signature = (product, flavour, quantity, tuple(sorted(config.items())))
            if vm_signature not in added_sigs.get("VM", []):
                row = _blank_row()
                row.update({
                    "Category": "VM Configuration", "_bucket": "VM", "_signature": vm_signature,
                    "Product": product,
                    "Flavour": flavour,
                    "Element": config.get("Element", "ICS"),
                    "Hypervisor": config.get("Hypervisor", "Open Stack"),
                    "Operating System": config.get("Operating System", "N/A"),
                    "Pricing Tier": config.get("Pricing Tier", "N/A"),
                    "Storage Type": config.get("Storage Type", "None"),
                    "Storage (GB)": config.get("Storage (GB)", 0),
                    "Backup Type": config.get("Backup Type", "None"),
                    "Backup (GB)": config.get("Backup (GB)", 0),
                    "Public IPs": config.get("Public IPs", 0),
                    "Quantity": quantity,
                    "vCPU": specs.get("vCPU", ""),
                    "RAM (GB)": specs.get("RAM (GB)", ""),
                    "Line Total (INR)": round(vm_grand_total, 2),
                })
                new_rows.append(row)
                added_sigs.setdefault("VM", []).append(vm_signature)
                added_labels.append("VM Configuration")

            # ── Network / Internet ──
            if ns_element != "None" and ns_bandwidth_mbps > 0 and ns_qty > 0:
                net_signature = (ns_element, ns_feature, ns_subtype, ns_bandwidth_mbps, ns_qty)
                if net_signature not in added_sigs.get("Network", []):
                    row = _blank_row()
                    row.update({
                        "Category": "Network / Internet", "_bucket": "Network", "_signature": net_signature,
                        "Network Element": ns_element,
                        "Network Feature": ns_feature if ns_feature != "None" else "",
                        "Network Sub Type": ns_subtype if ns_subtype != "None" else "",
                        "Bandwidth (Mbps)": ns_bandwidth_mbps,
                        "Network Cost (INR)": round(ns_cost, 2),
                        "Line Total (INR)": round(ns_cost, 2),
                    })
                    new_rows.append(row)
                    added_sigs.setdefault("Network", []).append(net_signature)
                    added_labels.append("Network / Internet")

            # ── Firewall ──
            if ns_firewall != "None" and ns_firewall_mbps > 0:
                fw_signature = (ns_firewall, ns_firewall_mbps)
                if fw_signature not in added_sigs.get("Firewall", []):
                    row = _blank_row()
                    row.update({
                        "Category": "Firewall", "_bucket": "Firewall", "_signature": fw_signature,
                        "Firewall Type": ns_firewall,
                        "Firewall Bandwidth (Mbps)": ns_firewall_mbps,
                        "Firewall Cost (INR)": round(firewall_cost, 2),
                        "Line Total (INR)": round(firewall_cost, 2),
                    })
                    new_rows.append(row)
                    added_sigs.setdefault("Firewall", []).append(fw_signature)
                    added_labels.append("Firewall")

            # ── Software & Licenses ──
            if lic_subtype != "None" and lic_qty > 0:
                lic_signature = (lic_element, lic_subtype, lic_qty)
                if lic_signature not in added_sigs.get("License", []):
                    row = _blank_row()
                    row.update({
                        "Category": "License", "_bucket": "License", "_signature": lic_signature,
                        "License Element": lic_element if lic_element != "None" else "",
                        "License Sub Type": lic_subtype,
                        "License Qty": lic_qty,
                        "License Cost (INR)": round(lic_cost, 2),
                        "Line Total (INR)": round(lic_cost, 2),
                    })
                    new_rows.append(row)
                    added_sigs.setdefault("License", []).append(lic_signature)
                    added_labels.append("License")

            # ── Backup Storage ──
            if bk_model != "None" and bk_qty > 0:
                bk_signature = (bk_model, bk_qty)
                if bk_signature not in added_sigs.get("Backup Storage", []):
                    row = _blank_row()
                    row.update({
                        "Category": "Backup Storage", "_bucket": "Backup Storage", "_signature": bk_signature,
                        "Backup Storage Model": bk_model,
                        "Backup Storage (GB)": bk_qty,
                        "Backup Storage Cost (INR)": round(bk_cost, 2),
                        "Line Total (INR)": round(bk_cost, 2),
                    })
                    new_rows.append(row)
                    added_sigs.setdefault("Backup Storage", []).append(bk_signature)
                    added_labels.append("Backup Storage")

            # ── Network Element ──
            if ne_element != "None":
                ne_signature = (ne_element, ne_qty)
                if ne_signature not in added_sigs.get("Network Element", []):
                    row = _blank_row()
                    row.update({
                        "Category": "Network Element", "_bucket": "Network Element", "_signature": ne_signature,
                        "Network Element Type": ne_element,
                        "Network Element Cost (INR)": round(ne_cost, 2),
                        "Line Total (INR)": round(ne_cost, 2),
                    })
                    new_rows.append(row)
                    added_sigs.setdefault("Network Element", []).append(ne_signature)
                    added_labels.append("Network Element")

            # ── Management Services ──
            if mg_element != "None" and mg_qty > 0:
                mg_signature = (mg_element, mg_qty)
                if mg_signature not in added_sigs.get("Management", []):
                    row = _blank_row()
                    row.update({
                        "Category": "Management", "_bucket": "Management", "_signature": mg_signature,
                        "Management Type": mg_element,
                        "Management Qty": mg_qty,
                        "Management Cost (INR)": round(mg_cost, 2),
                        "Line Total (INR)": round(mg_cost, 2),
                    })
                    new_rows.append(row)
                    added_sigs.setdefault("Management", []).append(mg_signature)
                    added_labels.append("Management")

            # ── Miscellaneous ──
            if mi_element != "None" and mi_qty > 0:
                mi_signature = (mi_element, mi_qty, mi_price_per_unit)
                if mi_signature not in added_sigs.get("Misc", []):
                    row = _blank_row()
                    row.update({
                        "Category": "Miscellaneous", "_bucket": "Misc", "_signature": mi_signature,
                        "Misc Element": mi_element,
                        "Misc Qty": mi_qty,
                        "Misc Cost (INR)": round(mi_cost, 2),
                        "Line Total (INR)": round(mi_cost, 2),
                    })
                    new_rows.append(row)
                    added_sigs.setdefault("Misc", []).append(mi_signature)
                    added_labels.append("Miscellaneous")

            st.session_state.added_signatures = added_sigs

            if new_rows:
                st.session_state.quote_items.extend(new_rows)
                st.session_state.last_config = {
                    "product": product,
                    "flavour": flavour,
                    "specs": specs,
                    "config": config,
                }
                st.markdown(
                    f'<div class="success-banner">✅ Added to quote: {", ".join(added_labels)}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="success-banner">ℹ️ No new items to add — this configuration is already in your quote.</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<div class="error-banner">❌ Could not calculate price. Please check your selections.</div>',
                        unsafe_allow_html=True)


# RESULTS SECTION

if st.session_state.quote_items:
    qid = st.session_state.quotation_id
    items = st.session_state.quote_items
    grand_total = sum(item.get("Line Total (INR)", 0) for item in items)

    st.markdown("---")
    st.markdown('<div class="section-title">📊 Quotation Results</div>',
                unsafe_allow_html=True)

    try:
        save_current_quotation_history(
            quotation_id=qid,
            user_email=st.session_state.user.get("email"),
            customer_name=st.session_state.customer_name,
            company_name=st.session_state.company_name,
            quote_items=items,
            last_config=st.session_state.last_config,
            result=st.session_state.result,
            grand_total=grand_total,
        )
        st.session_state.history_saved_for_qid = qid
    except Exception:
        pass

    

    st.markdown("**📦 Added Configurations**")
    quote_df = pd.DataFrame(items)
    quote_df.insert(0, "S.No.", range(1, len(quote_df) + 1))
    # Quantity-type input columns (vCPU, RAM, Storage, Bandwidth, Quantity,
    # Backup Size, Public IPs, etc.) must always render as whole numbers.
    # Mixing rows that omit a field (NaN) with rows that set it can silently
    # upcast an integer column to float64 (e.g. "50.0"), so we re-normalize
    # here. Price/cost/total columns are untouched.
    quote_df = enforce_integer_columns(quote_df)
    display_cols = [
        "S.No.",
        "Category",
        "Product", "Flavour", "Element", "Hypervisor",
        "Operating System", "Pricing Tier",
        "Storage Type", "Storage (GB)", "Backup Type", "Backup (GB)",
        "Public IPs", "Quantity", "vCPU", "RAM (GB)",
        "Network Element", "Network Feature", "Network Sub Type", "Bandwidth (Mbps)", "Network Cost (INR)",
        "Firewall Type", "Firewall Bandwidth (Mbps)", "Firewall Cost (INR)",
        "License Element", "License Sub Type", "License Qty", "License Cost (INR)",
        "Backup Storage Model", "Backup Storage (GB)", "Backup Storage Cost (INR)",
        "Network Element Type", "Network Element Cost (INR)",
        "Management Type", "Management Qty", "Management Cost (INR)",
        "Misc Element", "Misc Qty", "Misc Cost (INR)",
        "Line Total (INR)"
    ]
    display_cols = [c for c in display_cols if c in quote_df.columns]

    ALWAYS_SHOW_COLS = {"S.No.", "Category", "Line Total (INR)", "Product", "Flavour"}

    def _col_has_data(col_name):
        series = quote_df[col_name]
        return series.apply(
            lambda v: (isinstance(v, (int, float)) and v != 0)
            or (isinstance(v, str) and v.strip() not in ("", "None"))
        ).any()

    
    display_cols = [c for c in display_cols if c in ALWAYS_SHOW_COLS or _col_has_data(c)]
    st.dataframe(quote_df[display_cols], use_container_width=True, hide_index=True)

    estimated_upfront_cost = 0.0
    estimated_monthly_cost = grand_total
    estimated_annual_cost = grand_total * 12

    st.markdown(
        f"""
        <div style="width:100%; padding:16px; background:#F8FAFC; border:1px solid #BFDBFE; border-radius:10px; margin-bottom:16px;">
            <div style="font-weight:700; color:#1E3A8A; margin-bottom:12px;">💰 Estimated Cost Summary</div>
            <table style="width:100%; border-collapse: collapse; font-family: inherit;">
                <tr>
                    <td style="padding: 6px 0; text-align:left; color:#0F172A;">Estimated upfront cost</td>
                    <td style="padding: 6px 0; text-align:right; color:#0F172A;">{format_inr(estimated_upfront_cost)}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; text-align:left; color:#0F172A;">Estimated monthly cost</td>
                    <td style="padding: 6px 0; text-align:right; color:#0F172A;">{format_inr(estimated_monthly_cost)}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; text-align:left; color:#0F172A;">Estimated annual cost</td>
                    <td style="padding: 6px 0; text-align:right; color:#0F172A;">{format_inr(estimated_annual_cost)}</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Highlighted style for the edit expander
    st.markdown("""
    <style>
    /* Traverses Streamlit's wrapper divs to target the expander immediately following the marker */
    div[data-testid="stVerticalBlock"] > div:has(.edit-quote-marker) + div div[data-testid="stExpander"],
    div[data-testid="element-container"]:has(.edit-quote-marker) + div[data-testid="element-container"] div[data-testid="stExpander"],
    .element-container:has(.edit-quote-marker) + .element-container div[data-testid="stExpander"] {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 50%, #BFDBFE 100%) !important;
        border: 3px solid #2563EB !important;
        border-radius: 12px !important;
        padding: 6px 14px !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 8px 24px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Highlight the header/summary span text */
    div[data-testid="stVerticalBlock"] > div:has(.edit-quote-marker) + div div[data-testid="stExpander"] summary span,
    div[data-testid="element-container"]:has(.edit-quote-marker) + div[data-testid="element-container"] div[data-testid="stExpander"] summary span,
    .element-container:has(.edit-quote-marker) + .element-container div[data-testid="stExpander"] summary span {
        font-weight: 800 !important;
        color: #1B3A6B !important;
        font-size: 1.15em !important;
    }
    
    /* Keep internal details content clean */
    div[data-testid="stVerticalBlock"] > div:has(.edit-quote-marker) + div div[data-testid="stExpander"] details,
    div[data-testid="element-container"]:has(.edit-quote-marker) + div[data-testid="element-container"] div[data-testid="stExpander"] details {
        border: none !important;
    }
    </style>
    <div class="edit-quote-marker"></div>
    """, unsafe_allow_html=True)

    with st.expander("✏️ Edit above quote (fix a wrong quantity / Mbps / GB)"):
        edit_options = [
            f"{index + 1}. {item.get('Category', 'Item')} — {format_inr(item.get('Line Total (INR)', 0))}"
            for index, item in enumerate(items)
        ]
        selected_edit = st.selectbox(
            "Select item to edit",
            options=edit_options,
            key="edit_item_select"
        )
        edit_index = edit_options.index(selected_edit)
        edit_item = items[edit_index]
        edit_bucket = edit_item.get("_bucket")

        updated = False

        # ── VM Configuration ──
        if edit_bucket == "VM":
            ec1, ec2 = st.columns(2)
            with ec1:
                ed_flavour = st.selectbox("Flavour",
                    get_vayu_flavours() if edit_item["Product"] == "Vayu Cloud"
                    else get_hana_flavours() if edit_item["Product"] == "Hana Grid"
                    else get_olvm_flavours(),
                    index=(
                        get_vayu_flavours() if edit_item["Product"] == "Vayu Cloud"
                        else get_hana_flavours() if edit_item["Product"] == "Hana Grid"
                        else get_olvm_flavours()
                    ).index(edit_item["Flavour"])
                    if edit_item["Flavour"] in (
                        get_vayu_flavours() if edit_item["Product"] == "Vayu Cloud"
                        else get_hana_flavours() if edit_item["Product"] == "Hana Grid"
                        else get_olvm_flavours()
                    ) else 0,
                    key=f"ed_flavour_{edit_index}"
                )
                if edit_item["Product"] in ("Vayu Cloud", "Hana Grid"):
                    os_opts = VAYU_OS_OPTIONS if edit_item["Product"] == "Vayu Cloud" else HANA_OS_OPTIONS
                    ed_os = st.selectbox("Operating System", os_opts,
                        index=os_opts.index(edit_item["Operating System"])
                        if edit_item["Operating System"] in os_opts else 0,
                        key=f"ed_os_{edit_index}"
                    )
                else:
                    ed_os = "Linux"
                ed_tier_opts = PRICING_TIERS
                ed_tier = st.selectbox("Pricing Tier", ed_tier_opts,
                    index=ed_tier_opts.index(edit_item["Pricing Tier"])
                    if edit_item["Pricing Tier"] in ed_tier_opts else 0,
                    key=f"ed_tier_{edit_index}"
                )
                ed_qty = st.number_input("Quantity (No. of VMs)",
                    min_value=1, max_value=500,
                    value=int(edit_item.get("Quantity", 1)),
                    step=1, key=f"ed_qty_{edit_index}"
                )
            with ec2:
                storage_opts = ["None"] + list(STORAGE_PRICES.keys())
                ed_storage_type = st.selectbox("Storage Type", storage_opts,
                    index=storage_opts.index(edit_item["Storage Type"])
                    if edit_item["Storage Type"] in storage_opts else 0,
                    key=f"ed_storage_type_{edit_index}"
                )
                ed_storage_gb = st.number_input("Storage Size (GB)",
                    min_value=0, max_value=100000,
                    value=int(edit_item.get("Storage (GB)", 0)),
                    step=50, key=f"ed_storage_gb_{edit_index}"
                ) if ed_storage_type != "None" else 0
                backup_opts = list(BACKUP_PRICES.keys())
                ed_backup_type = st.selectbox("Backup Type", backup_opts,
                    index=backup_opts.index(edit_item["Backup Type"])
                    if edit_item["Backup Type"] in backup_opts else 0,
                    key=f"ed_backup_type_{edit_index}"
                )
                ed_backup_gb = st.number_input("Backup Size (GB)",
                    min_value=0, max_value=100000,
                    value=int(edit_item.get("Backup (GB)", 0)),
                    step=50, key=f"ed_backup_gb_{edit_index}"
                ) if ed_backup_type != "None" else 0
                if edit_item["Product"] == "Vayu Cloud":
                    ed_public_ips = st.number_input("No. of Public IPs",
                        min_value=0, max_value=50,
                        value=int(edit_item.get("Public IPs", 0)),
                        step=1, key=f"ed_ips_{edit_index}"
                    )
                else:
                    ed_public_ips = 0

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                if edit_item["Product"] == "Vayu Cloud":
                    vm_result = calculate_vayu_price(
                        ed_flavour, ed_os, ed_tier, ed_qty,
                        ed_storage_type, ed_storage_gb,
                        ed_backup_type, ed_backup_gb,
                        "None", ed_public_ips
                    )
                elif edit_item["Product"] == "Hana Grid":
                    vm_result = calculate_hana_price(
                        ed_flavour, ed_os, ed_tier, ed_qty,
                        ed_storage_type, ed_storage_gb,
                        ed_backup_type, ed_backup_gb
                    )
                else:
                    vm_result = calculate_olvm_price(
                        ed_flavour, ed_tier, ed_qty,
                        ed_storage_type, ed_storage_gb,
                        ed_backup_type, ed_backup_gb
                    )
                if vm_result:
                    edit_item.update({
                        "Flavour": ed_flavour,
                        "Operating System": ed_os,
                        "Pricing Tier": ed_tier,
                        "Quantity": ed_qty,
                        "Storage Type": ed_storage_type,
                        "Storage (GB)": ed_storage_gb,
                        "Backup Type": ed_backup_type,
                        "Backup (GB)": ed_backup_gb,
                        "Public IPs": ed_public_ips,
                        "Line Total (INR)": round(vm_result.get("Grand Total", 0), 2),
                    })
                    new_specs = get_flavour_specs(edit_item["Product"], ed_flavour)
                    edit_item["vCPU"] = new_specs.get("vCPU", "")
                    edit_item["RAM (GB)"] = new_specs.get("RAM (GB)", "")
                    updated = True

        # ── Network / Internet ──
        elif edit_bucket == "Network":
            ec1, ec2 = st.columns(2)
            with ec1:
                net_el_opts = ["None", "Internet", "DCI Interconnect", "VPN"]
                ed_ns_element = st.selectbox("Element", net_el_opts,
                    index=net_el_opts.index(edit_item["Network Element"])
                    if edit_item["Network Element"] in net_el_opts else 0,
                    key=f"ed_ns_el_{edit_index}"
                )
                feat_opts = ["None", "Bandwidth", "Port Speed"]
                ed_ns_feature = st.selectbox("Feature", feat_opts,
                    index=feat_opts.index(edit_item["Network Feature"])
                    if edit_item["Network Feature"] in feat_opts else 0,
                    key=f"ed_ns_feat_{edit_index}"
                )
                sub_opts = ["None", "IPC Internet", "Optical 10G", "Site to Site VPN", "Client to Site VPN"]
                ed_ns_subtype = st.selectbox("Sub Type", sub_opts,
                    index=sub_opts.index(edit_item["Network Sub Type"])
                    if edit_item["Network Sub Type"] in sub_opts else 0,
                    key=f"ed_ns_sub_{edit_index}"
                )
            with ec2:
                ed_ns_bw = st.number_input("Bandwidth (Mbps)",
                    min_value=0, max_value=100000,
                    value=int(edit_item.get("Bandwidth (Mbps)", 0)),
                    step=100, key=f"ed_ns_bw_{edit_index}"
                )
                unit_opts = ["Mbps", "Gbps"]
                ed_ns_unit = st.selectbox("Unit", unit_opts, key=f"ed_ns_unit_{edit_index}")
                ed_ns_qty = st.number_input("Quantity",
                    min_value=0, max_value=100,
                    value=1, step=1, key=f"ed_ns_qty_{edit_index}"
                )
            new_ns_cost = INTERNET_BANDWIDTH_PRICE_PER_MBPS * ed_ns_bw * ed_ns_qty if ed_ns_bw > 0 and ed_ns_qty > 0 else 0
            st.caption(f"New estimated cost: {format_inr(new_ns_cost)} / month")

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                edit_item.update({
                    "Network Element": ed_ns_element,
                    "Network Feature": ed_ns_feature,
                    "Network Sub Type": ed_ns_subtype,
                    "Bandwidth (Mbps)": ed_ns_bw,
                    "Network Cost (INR)": round(new_ns_cost, 2),
                    "Line Total (INR)": round(new_ns_cost, 2),
                })
                updated = True

        # ── Firewall ──
        elif edit_bucket == "Firewall":
            ec1, ec2 = st.columns(2)
            fw_opts = list(FIREWALL_PRICES.keys())
            with ec1:
                ed_fw_type = st.selectbox("Firewall Type", fw_opts,
                    index=fw_opts.index(edit_item["Firewall Type"])
                    if edit_item["Firewall Type"] in fw_opts else 0,
                    key=f"ed_fw_type_{edit_index}"
                )
            with ec2:
                ed_fw_mbps = st.number_input("Firewall Bandwidth (Mbps)",
                    min_value=0, max_value=100000,
                    value=int(edit_item.get("Firewall Bandwidth (Mbps)", 0)),
                    step=100, key=f"ed_fw_mbps_{edit_index}"
                )
            new_fw_cost = round(FIREWALL_PRICES.get(ed_fw_type, 0) * ed_fw_mbps, 2) if ed_fw_type != "None" else 0
            st.caption(f"New estimated cost: {format_inr(new_fw_cost)} / month")

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                edit_item.update({
                    "Firewall Type": ed_fw_type,
                    "Firewall Bandwidth (Mbps)": ed_fw_mbps,
                    "Firewall Cost (INR)": new_fw_cost,
                    "Line Total (INR)": new_fw_cost,
                })
                updated = True

        # ── License ──
        elif edit_bucket == "License":
            ec1, ec2 = st.columns(2)
            lic_el_opts = ["None", "Windows Server", "Linux", "MS SQL", "MySQL", "PostgreSQL", "Commvault Backup License"]
            lic_sub_opts = list(LICENSE_PRICES.keys())
            with ec1:
                ed_lic_el = st.selectbox("Element (License)", lic_el_opts,
                    index=lic_el_opts.index(edit_item["License Element"])
                    if edit_item["License Element"] in lic_el_opts else 0,
                    key=f"ed_lic_el_{edit_index}"
                )
                ed_lic_sub = st.selectbox("License Type", lic_sub_opts,
                    index=lic_sub_opts.index(edit_item["License Sub Type"])
                    if edit_item["License Sub Type"] in lic_sub_opts else 0,
                    key=f"ed_lic_sub_{edit_index}"
                )
            with ec2:
                lic_unit_opts = ["# of Licenses", "per vCore", "per 2 pCore", "per DB", "per GB"]
                ed_lic_unit = st.selectbox("Unit", lic_unit_opts, key=f"ed_lic_unit_{edit_index}")
                ed_lic_qty = st.number_input("Quantity",
                    min_value=0, max_value=100000,
                    value=int(edit_item.get("License Qty", 0)),
                    step=1, key=f"ed_lic_qty_{edit_index}"
                )
            new_lic_cost = round(LICENSE_PRICES.get(ed_lic_sub, 0) * ed_lic_qty, 2) if ed_lic_sub != "None" else 0
            st.caption(f"New estimated cost: {format_inr(new_lic_cost)} / month")

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                edit_item.update({
                    "License Element": ed_lic_el,
                    "License Sub Type": ed_lic_sub,
                    "License Qty": ed_lic_qty,
                    "License Cost (INR)": new_lic_cost,
                    "Line Total (INR)": new_lic_cost,
                })
                updated = True

        # ── Backup Storage ──
        elif edit_bucket == "Backup Storage":
            ec1, ec2 = st.columns(2)
            bk_model_opts = ["None", "Value Based", "Resilient", "Geo-Resilient"]
            bk_el_opts = ["None", "ICS", "BET"]
            bk_make_opts = ["None", "BET", "Commvault"]
            bk_cfg_opts = ["None", "Object-Resilient", "Object-Value", "Block"]
            with ec1:
                ed_bk_el = st.selectbox("Element", bk_el_opts, key=f"ed_bk_el_{edit_index}")
                ed_bk_make = st.selectbox("Make", bk_make_opts, key=f"ed_bk_make_{edit_index}")
                ed_bk_model = st.selectbox("Model", bk_model_opts,
                    index=bk_model_opts.index(edit_item["Backup Storage Model"])
                    if edit_item["Backup Storage Model"] in bk_model_opts else 0,
                    key=f"ed_bk_model_{edit_index}"
                )
            with ec2:
                ed_bk_cfg = st.selectbox("Storage Config", bk_cfg_opts, key=f"ed_bk_cfg_{edit_index}")
                ed_bk_unit = st.selectbox("Unit", ["GB", "TB"], key=f"ed_bk_unit_{edit_index}")
                ed_bk_qty = st.number_input("Quantity (GB)",
                    min_value=0, max_value=1000000,
                    value=int(edit_item.get("Backup Storage (GB)", 0)),
                    step=100, key=f"ed_bk_qty_{edit_index}"
                )
            bk_price_map = {"Value Based": 1.826923, "Resilient": 3.425481, "Geo-Resilient": 3.882212}
            new_bk_cost = round(bk_price_map.get(ed_bk_model, 0) * ed_bk_qty, 2) if ed_bk_model != "None" else 0
            st.caption(f"New estimated cost: {format_inr(new_bk_cost)} / month")

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                edit_item.update({
                    "Backup Storage Model": ed_bk_model,
                    "Backup Storage (GB)": ed_bk_qty,
                    "Backup Storage Cost (INR)": new_bk_cost,
                    "Line Total (INR)": new_bk_cost,
                })
                updated = True

        # ── Management ──
        elif edit_bucket == "Management":
            ec1, ec2 = st.columns(2)
            mg_el_opts = ["None", "OS-Management", "DB Management", "Firewall Management"]
            mg_unit_opts = ["VM", "DB", "Firewall"]
            with ec1:
                ed_mg_el = st.selectbox("Element", mg_el_opts,
                    index=mg_el_opts.index(edit_item["Management Type"])
                    if edit_item["Management Type"] in mg_el_opts else 0,
                    key=f"ed_mg_el_{edit_index}"
                )
                ed_mg_desc = st.text_input("Description", value="", key=f"ed_mg_desc_{edit_index}")
            with ec2:
                ed_mg_unit = st.selectbox("Unit", mg_unit_opts, key=f"ed_mg_unit_{edit_index}")
                ed_mg_qty = st.number_input("Quantity",
                    min_value=0, max_value=500,
                    value=int(edit_item.get("Management Qty", 0)),
                    step=1, key=f"ed_mg_qty_{edit_index}"
                )
            mg_price_map = {"OS-Management": 500, "DB Management": 6500, "Firewall Management": 2000}
            new_mg_cost = round(mg_price_map.get(ed_mg_el, 0) * ed_mg_qty, 2) if ed_mg_el != "None" else 0
            st.caption(f"New estimated cost: {format_inr(new_mg_cost)} / month")

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                edit_item.update({
                    "Management Type": ed_mg_el,
                    "Management Qty": ed_mg_qty,
                    "Management Cost (INR)": new_mg_cost,
                    "Line Total (INR)": new_mg_cost,
                })
                updated = True

        # ── Miscellaneous ──
        elif edit_bucket == "Misc":
            ec1, ec2 = st.columns(2)
            mi_el_opts = ["None", "IP", "Space", "Power", "Support", "Tenant", "Wire", "Cross Connect", "Switch Port"]
            mi_unit_opts = ["None", "IPs", "U", "KWH", "Sessions", "Gig", "Wire"]
            with ec1:
                ed_mi_el = st.selectbox("Element", mi_el_opts,
                    index=mi_el_opts.index(edit_item["Misc Element"])
                    if edit_item["Misc Element"] in mi_el_opts else 0,
                    key=f"ed_mi_el_{edit_index}"
                )
                ed_mi_desc = st.text_input("Description", value="", key=f"ed_mi_desc_{edit_index}")
            with ec2:
                ed_mi_unit = st.selectbox("Unit", mi_unit_opts, key=f"ed_mi_unit_{edit_index}")
                ed_mi_qty = st.number_input("Quantity",
                    min_value=0, max_value=10000,
                    value=int(edit_item.get("Misc Qty", 0)),
                    step=1, key=f"ed_mi_qty_{edit_index}"
                )
                ed_mi_price = st.number_input("Price per Unit (INR)",
                    min_value=0.0,
                    value=float(edit_item.get("Misc Cost (INR)", 0) / edit_item.get("Misc Qty", 1))
                    if edit_item.get("Misc Qty", 0) > 0 else 0.0,
                    step=100.0, key=f"ed_mi_price_{edit_index}"
                )
            new_mi_cost = round(ed_mi_price * ed_mi_qty, 2)
            st.caption(f"New estimated cost: {format_inr(new_mi_cost)} / month")

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                edit_item.update({
                    "Misc Element": ed_mi_el,
                    "Misc Qty": ed_mi_qty,
                    "Misc Cost (INR)": new_mi_cost,
                    "Line Total (INR)": new_mi_cost,
                })
                updated = True

        # ── Network Element ──
        elif edit_bucket == "Network Element":
            ec1, ec2 = st.columns(2)
            ne_el_opts = ["None", "Virtual Network"]
            ne_unit_opts = ["None", "Qty", "Port", "Gig"]
            with ec1:
                ed_ne_el = st.selectbox("Element", ne_el_opts,
                    index=ne_el_opts.index(edit_item["Network Element Type"])
                    if edit_item["Network Element Type"] in ne_el_opts else 0,
                    key=f"ed_ne_el_{edit_index}"
                )
                ed_ne_desc = st.text_input("Description", value="", key=f"ed_ne_desc_{edit_index}")
            with ec2:
                ed_ne_unit = st.selectbox("Unit", ne_unit_opts, key=f"ed_ne_unit_{edit_index}")
                ed_ne_qty = st.number_input("Quantity",
                    min_value=0, max_value=100,
                    value=0, step=1, key=f"ed_ne_qty_{edit_index}"
                )
            new_ne_cost = NETWORK_ELEMENT_PRICES.get(ed_ne_el, 0)
            st.caption(f"New estimated cost: {format_inr(new_ne_cost)} / month")

            if st.button("Update this item", type="secondary", key=f"ed_update_{edit_index}"):
                edit_item.update({
                    "Network Element Type": ed_ne_el,
                    "Network Element Cost (INR)": new_ne_cost,
                    "Line Total (INR)": new_ne_cost,
                })
                updated = True

        if updated:
            st.session_state.quote_items[edit_index] = edit_item
            st.success("✅ Item updated successfully!")
            st.rerun()

    with st.expander("Remove item from quote"):
        remove_options = [
            f"{index + 1}. {item.get('Category', 'Item')} — {format_inr(item.get('Line Total (INR)', 0))}"
            for index, item in enumerate(items)
        ]
        selected_remove = st.selectbox(
            "Select item to remove",
            options=remove_options,
            key="remove_item_select"
        )
        if st.button("Remove selected configuration", type="secondary"):
            remove_index = remove_options.index(selected_remove)
            removed_item = st.session_state.quote_items.pop(remove_index)
            bucket = removed_item.get("_bucket")
            sig = removed_item.get("_signature")
            if bucket and sig is not None:
                bucket_list = st.session_state.added_signatures.get(bucket, [])
                if sig in bucket_list:
                    bucket_list.remove(sig)
            st.rerun()

    if st.button("Clear quote list", type="secondary"):
        st.session_state.quote_items = []
        st.session_state.result = None
        st.session_state.preview_result = None
        st.session_state.show_preview = False
        st.session_state.added_signatures = {}
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-title">⬇️ Download Quotation</div>',
                unsafe_allow_html=True)

    quote_export_df = build_quote_export_dataframe(items)
    csv_data = export_quote_to_csv(quote_export_df, grand_total)
    excel_data = export_quote_to_excel(quote_export_df, qid, grand_total)

    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"VayuPrice_{user['full_name'].replace(' ', '_')}_{qid}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with dl_col2:
        st.download_button(
            label="📊 Download as Excel",
            data=excel_data,
            file_name=f"VayuPrice_{user['full_name'].replace(' ', '_')}_{qid}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

elif st.session_state.result:
    result = st.session_state.result
    saved = st.session_state.last_config
    qid = st.session_state.quotation_id

    st.markdown("---")
    st.markdown('<div class="section-title">📊 Latest Configuration</div>',
                unsafe_allow_html=True)

    try:
        save_current_quotation_history(
            quotation_id=qid,
            user_email=st.session_state.user.get("email"),
            customer_name=st.session_state.customer_name,
            company_name=st.session_state.company_name,
            quote_items=st.session_state.quote_items,
            last_config=st.session_state.last_config,
            result=st.session_state.result,
            grand_total=result.get('Grand Total', 0),
        )
        st.session_state.history_saved_for_qid = qid
    except Exception:
        pass

    st.markdown(f"""
    <div class="price-box">
        <p>Quotation ID: {qid}</p>
        <p>{saved.get('product', 'N/A')} · {saved.get('flavour', 'N/A')} · Qty: {result.get('Quantity', 1)}</p>
        <h1>{format_inr(result.get('Grand Total', 0))}</h1>
        <p>Latest calculated configuration total</p>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**📋 Price Breakdown**")
        breakdown_rows = []
        for k, v in result.items():
            if k != "Grand Total":
                breakdown_rows.append({
                    "Component": k,
                    "Amount (INR)": f"{v:,.2f}" if isinstance(v, float) else str(v)
                })
        breakdown_df = pd.DataFrame(breakdown_rows)
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    with col_right:
        st.markdown("**⚙️ Configuration Summary**")
        config_rows = [{"Parameter": k, "Value": str(v)}
                       for k, v in saved["config"].items()]
        config_rows += [{"Parameter": k, "Value": str(v)}
                        for k, v in saved["specs"].items()]
        st.dataframe(pd.DataFrame(config_rows),
                     use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="section-title">⬇️ Download Quotation</div>',
                unsafe_allow_html=True)

    summary_df = build_summary_dataframe(
        saved["product"], saved["flavour"],
        saved["specs"], saved["config"], result
    )

    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        csv_data = export_to_csv(summary_df)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"VayuPrice_{user['full_name'].replace(' ', '_')}_{qid}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with dl_col2:
        excel_data = export_to_excel(
            summary_df, saved["product"],
            saved["flavour"], qid
        )
        st.download_button(
            label="📊 Download as Excel",
            data=excel_data,
            file_name=f"VayuPrice_{user['full_name'].replace(' ', '_')}_{qid}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )