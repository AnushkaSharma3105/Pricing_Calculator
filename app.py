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
    format_inr, generate_quotation_id,
    build_summary_dataframe, export_to_csv, export_to_excel,
    build_quote_export_dataframe, export_quote_to_csv, export_quote_to_excel
)
from auth import init_db
from login_page import show_login
from register_page import show_register
from profile_page import show_profile
from history_page import show_cart

# ─────────────────────────────────────────────
# ADDITIONAL SERVICES PRICING DATA
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CloudQuote",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, default in [("logged_in", False), ("user", None), ("page", "login"),
                     ("result", None), ("quotation_id", None), ("last_config", {})]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>

    /* === BUTTON STYLES + FOCUS FIX === */
    *:focus, *:focus-visible, *:focus-within {
        outline: none !important;
        box-shadow: none !important;
    }

    div.stButton > button[kind="secondary"] {
        color: #1B3A6B !important;
        font-weight: 600 !important;
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 1.5px solid #2563EB !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div.stButton > button[kind="secondary"] p,
    div.stButton > button[kind="secondary"] div { color: #1B3A6B !important; }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #2563EB !important;
        color: white !important;
        border-color: #2563EB !important;
    }
    div.stButton > button[kind="secondary"]:focus,
    div.stButton > button[kind="secondary"]:focus-visible,
    div.stButton > button[kind="secondary"]:active {
        outline: none !important;
        box-shadow: none !important;
        border: 1.5px solid #2563EB !important;
    }

    div[data-testid="stDownloadButton"] > button {
        color: #1B3A6B !important;
        font-weight: 600 !important;
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 1.5px solid #2563EB !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stDownloadButton"] > button p,
    div[data-testid="stDownloadButton"] > button div { color: #1B3A6B !important; }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #2563EB !important;
        color: white !important;
        border-color: #2563EB !important;
    }
    div[data-testid="stDownloadButton"] > button:focus,
    div[data-testid="stDownloadButton"] > button:focus-visible,
    div[data-testid="stDownloadButton"] > button:active {
        outline: none !important;
        box-shadow: none !important;
        border: 1.5px solid #2563EB !important;
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
        padding: 16px;
        text-align: center;
        border: 1px solid #BFDBFE;
        backdrop-filter: blur(6px);
    }
    .metric-card h3 { color: #1B3A6B; margin: 0; font-size: 1.4rem; }
    .metric-card p  { color: #475569; margin: 4px 0; font-size: 0.85rem; }

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

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ROUTING — show login/register if not logged in
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.session_state.page == "register":
        show_register()
    else:
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

# ─────────────────────────────────────────────
# NAVBAR
# ─────────────────────────────────────────────
user = st.session_state.user
nav_cols = st.columns([3, 1, 1, 1, 1])
with nav_cols[0]:
    st.markdown(
        f"<div style='padding-top:8px; font-size:1.1rem; font-weight:800; color:#1B3A6B;'>"
        f"☁️ CloudQuote &nbsp;|&nbsp; "
        f"<span style='font-weight:400; font-size:0.95rem;'>Hi, {user['full_name'].split()[0]}!</span>"
        f"</div>",
        unsafe_allow_html=True
    )
with nav_cols[1]:
    if st.button("📊 Dashboard", use_container_width=True,
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
with nav_cols[4]:
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.session_state.result = None
        st.rerun()

st.markdown("---")

# ─────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────
if st.session_state.page == "profile":
    show_profile()
    st.stop()

if st.session_state.page == "cart":
    show_cart()
    st.stop()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="card">
    <h2 style="margin:0; color:#1B3A6B;"> CloudQuote </h2>
    <h4 style="margin:0; color: #4D516D;"> ☁️ Cloud Infrastructure Price Calculator </h4>
    <p style="margin:4px 0 0 0; color:#64748B;">
        Tata TeleServices · India Region · All prices in INR per month
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 1 — PRODUCT SELECTION
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">Step 1 — Select Product</div>',
            unsafe_allow_html=True)

product = st.selectbox(
    "Select Product",
    ["Vayu Cloud", "Hana Grid", "OLVM"],
    key="product_select",
    help="Choose the cloud product you want to price"
)

st.markdown("---")

# ─────────────────────────────────────────────
# STEP 2 — VM CONFIGURATION
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">Step 2 — Configure VM</div>',
            unsafe_allow_html=True)

config = {}

# ══════════════════════════════════════════════
# VAYU CLOUD FORM
# ══════════════════════════════════════════════
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

        firewall_type = st.selectbox(
            "Firewall",
            list(FIREWALL_PRICES.keys()),
            key="vayu_firewall"
        )

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
        "Firewall": firewall_type,
        "Public IPs": public_ips,
    }

# ══════════════════════════════════════════════
# HANA GRID FORM
# ══════════════════════════════════════════════
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

# ══════════════════════════════════════════════
# OLVM FORM
# ══════════════════════════════════════════════
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

# ─────────────────────────────────────────────
# FLAVOUR SPECS PREVIEW
# ─────────────────────────────────────────────
specs = get_flavour_specs(product, flavour)
if specs:
    st.markdown('<div class="section-title">Selected Flavour Specs</div>',
                unsafe_allow_html=True)
    spec_cols = st.columns(len(specs))
    for i, (k, v) in enumerate(specs.items()):
        with spec_cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{v}</h3>
                <p>{k}</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# STEP 3 — ADDITIONAL SERVICES (NEW)
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">Step 3 — Additional Services (Optional)</div>',
            unsafe_allow_html=True)

with st.expander("🌐 Network & Security Services", expanded=False):
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

    # Calculate internet cost
    ns_cost = 0
    if ns_element != "None" and ns_bandwidth_mbps > 0 and ns_qty > 0:
        ns_cost = INTERNET_BANDWIDTH_PRICE_PER_MBPS * ns_bandwidth_mbps * ns_qty
    st.info(f"Estimated Network Cost: {format_inr(ns_cost)} / month")

with st.expander("🔐 Software & Licenses", expanded=False):
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
            "Sub Type",
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

with st.expander("💾 Backup Storage", expanded=False):
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

with st.expander("🖧 Network Elements", expanded=False):
    ne_col1, ne_col2 = st.columns(2)

    with ne_col1:
        st.markdown("**Network Element**")
        ne_element = st.selectbox(
            "Element",
            ["None", "Virtual Network", "Firewall"],
            key="ne_element"
        )
        ne_description = st.text_input(
            "Description",
            value="",
            key="ne_description",
            placeholder="e.g. Network isolation, Forti firewall HA"
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
            placeholder="e.g. BYOF / Included / Customer Scope"
        )

    ne_cost = NETWORK_ELEMENT_PRICES.get(ne_element, 0) if ne_element != "None" else 0
    st.info(f"Estimated Network Element Cost: {format_inr(ne_cost)} / month")

with st.expander("⚙️ Management Services", expanded=False):
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

with st.expander("📦 Miscellaneous Items", expanded=False):
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
total_additional = ns_cost + lic_cost + bk_cost + ne_cost + mg_cost + mi_cost
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

# ─────────────────────────────────────────────
# BUTTONS ROW
# ─────────────────────────────────────────────
btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])

with btn_col1:
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
    st.session_state.quotation_id = generate_quotation_id()
    st.session_state.last_config = {}
    st.session_state.quote_items = []

    # Reset Step 3 additional services
    keys_to_reset = [
        "ns_element", "ns_feature", "ns_subtype", "ns_bandwidth",
        "ns_unit", "ns_qty", "ns_remark",
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

# ─────────────────────────────────────────────
# CALCULATE
# ─────────────────────────────────────────────
if calculate_clicked:
    errors = []
    if storage_type != "None" and storage_gb == 0:
        errors.append("Please enter Storage Size (GB) greater than 0.")
    if backup_type != "None" and backup_gb == 0:
        errors.append("Please enter Backup Size (GB) greater than 0.")

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
                    firewall_type, public_ips
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
            # Add additional services cost to grand total
            vm_grand_total = result.get("Grand Total", 0)
            combined_total = vm_grand_total + total_additional
            result["Additional Services Cost"] = round(total_additional, 2)
            result["Grand Total"] = round(combined_total, 2)

            st.session_state.result = result
            st.session_state.quotation_id = st.session_state.quotation_id or generate_quotation_id()

            item = {
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
                "Firewall": config.get("Firewall", "None"),
                "Public IPs": config.get("Public IPs", 0),
                "Quantity": result.get("Quantity", 1),
                "vCPU": specs.get("vCPU", ""),
                "RAM (GB)": specs.get("RAM (GB)", ""),
                "Network Element": ns_element if ns_element != "None" else "",
                "Network Feature": ns_feature if ns_feature != "None" else "",
                "Network Sub Type": ns_subtype if ns_subtype != "None" else "",
                "Bandwidth (Mbps)": ns_bandwidth_mbps,
                "Network Cost (INR)": round(ns_cost, 2),
                "License Element": lic_element if lic_element != "None" else "",
                "License Sub Type": lic_subtype if lic_subtype != "None" else "",
                "License Qty": lic_qty,
                "License Cost (INR)": round(lic_cost, 2),
                "Backup Storage Model": bk_model if bk_model != "None" else "",
                "Backup Storage (GB)": bk_qty,
                "Backup Storage Cost (INR)": round(bk_cost, 2),
                "Network Element Type": ne_element if ne_element != "None" else "",
                "Network Element Cost (INR)": round(ne_cost, 2),
                "Management Type": mg_element if mg_element != "None" else "",
                "Management Qty": mg_qty,
                "Management Cost (INR)": round(mg_cost, 2),
                "Misc Element": mi_element if mi_element != "None" else "",
                "Misc Qty": mi_qty,
                "Misc Cost (INR)": round(mi_cost, 2),
                "Additional Services Total (INR)": round(total_additional, 2),
                "Line Total (INR)": round(combined_total, 2),
            }
            st.session_state.quote_items.append(item)
            st.session_state.last_config = {
                "product": product,
                "flavour": flavour,
                "specs": specs,
                "config": config,
            }
            st.markdown('<div class="success-banner">✅ Price calculated and added to the quote list!</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-banner">❌ Could not calculate price. Please check your selections.</div>',
                        unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RESULTS SECTION
# ─────────────────────────────────────────────
if st.session_state.quote_items:
    qid = st.session_state.quotation_id
    items = st.session_state.quote_items
    grand_total = sum(item.get("Line Total (INR)", 0) for item in items)

    st.markdown("---")
    st.markdown('<div class="section-title">📊 Quotation Results</div>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <div class="price-box">
        <p>Quotation ID: {qid}</p>
        <p>{len(items)} configuration(s) added</p>
        <h1>{format_inr(grand_total)}</h1>
        <p>Grand Total per Month (INR, excl. taxes)</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**📦 Added Configurations**")
    quote_df = pd.DataFrame(items)
    display_cols = [
        "Product", "Flavour", "Element", "Hypervisor",
        "Operating System", "Pricing Tier",
        "Storage Type", "Storage (GB)", "Backup Type", "Backup (GB)",
        "Firewall", "Public IPs", "Quantity", "vCPU", "RAM (GB)",
        "Network Element", "Network Feature", "Network Sub Type", "Bandwidth (Mbps)", "Network Cost (INR)",
        "License Element", "License Sub Type", "License Qty", "License Cost (INR)",
        "Backup Storage Model", "Backup Storage (GB)", "Backup Storage Cost (INR)",
        "Network Element Type", "Network Element Cost (INR)",
        "Management Type", "Management Qty", "Management Cost (INR)",
        "Misc Element", "Misc Qty", "Misc Cost (INR)",
        "Additional Services Total (INR)", "Line Total (INR)"
    ]
    display_cols = [c for c in display_cols if c in quote_df.columns]
    st.dataframe(quote_df[display_cols], use_container_width=True, hide_index=True)

    with st.expander("Remove item from quote"):
        remove_options = [
            f"{index + 1}. {item['Product']} {item['Flavour']} — {format_inr(item['Line Total (INR)'])}"
            for index, item in enumerate(items)
        ]
        selected_remove = st.selectbox(
            "Select item to remove",
            options=remove_options,
            key="remove_item_select"
        )
        if st.button("Remove selected configuration", type="secondary"):
            remove_index = remove_options.index(selected_remove)
            st.session_state.quote_items.pop(remove_index)
            st.rerun()

    if st.button("Clear quote list", type="secondary"):
        st.session_state.quote_items = []
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
            file_name=f"quotation_{qid}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with dl_col2:
        st.download_button(
            label="📊 Download as Excel",
            data=excel_data,
            file_name=f"quotation_{qid}.xlsx",
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

    st.markdown(f"""
    <div class="price-box">
        <p>Quotation ID: {qid}</p>
        <p>{saved['product']} · {saved['flavour']} · Qty: {result['Quantity']}</p>
        <h1>{format_inr(result['Grand Total'])}</h1>
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
            file_name=f"quotation_{qid}.csv",
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
            file_name=f"quotation_{qid}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )