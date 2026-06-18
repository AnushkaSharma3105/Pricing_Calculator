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
from cart_page import show_cart


# PAGE CONFIG

st.set_page_config(
    page_title="CloudQuote",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# SESSION STATE INIT

for key, default in [("logged_in", False), ("user", None), ("page", "login"),
                     ("result", None), ("quotation_id", None), ("last_config", {})]:
    if key not in st.session_state:
        st.session_state[key] = default


# CUSTOM CSS

st.markdown("""
<style>
            
    /* === BUTTON STYLES + FOCUS FIX === */

    /* Remove focus ring from everything */
    *:focus,
    *:focus-visible,
    *:focus-within {
        outline: none !important;
        box-shadow: none !important;
    }

    /* Secondary button (Reset) */
    div.stButton > button[kind="secondary"] {
        color: #1B3A6B !important;
        font-weight: 600 !important;
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 1.5px solid #2563EB !important;
        outline: none !important;
        box-shadow: none !important;
    }

    div.stButton > button[kind="secondary"] p,
    div.stButton > button[kind="secondary"] div {
        color: #1B3A6B !important;
    }

    div.stButton > button[kind="secondary"]:hover {
        background-color: #2563EB !important;
        color: white !important;
        border-color: #2563EB !important;
        outline: none !important;
        box-shadow: none !important;
    }

    div.stButton > button[kind="secondary"]:focus,
    div.stButton > button[kind="secondary"]:focus-visible,
    div.stButton > button[kind="secondary"]:active {
        outline: none !important;
        box-shadow: none !important;
        border: 1.5px solid #2563EB !important;
    }

    /* Download buttons */
    div[data-testid="stDownloadButton"] > button {
        color: #1B3A6B !important;
        font-weight: 600 !important;
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 1.5px solid #2563EB !important;
        outline: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stDownloadButton"] > button p,
    div[data-testid="stDownloadButton"] > button div {
        color: #1B3A6B !important;
    }

    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #2563EB !important;
        color: white !important;
        border-color: #2563EB !important;
        outline: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stDownloadButton"] > button:focus,
    div[data-testid="stDownloadButton"] > button:focus-visible,
    div[data-testid="stDownloadButton"] > button:active {
        outline: none !important;
        box-shadow: none !important;
        border: 1.5px solid #2563EB !important;
    }


    /* Main background - light blue gradient */
    .main {
        background: linear-gradient(135deg, #89CFF0 0%, #E0F4FF 100%);
    }
    .block-container {
        background: transparent;
    }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #89CFF0 0%, #E0F4FF 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B3A6B 0%, #2563EB 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }

    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.75);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
        color: #1B3A6B;
    }

    /* Price summary box */
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

    /* Section headers */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1B3A6B;
        border-left: 4px solid #2563EB;
        padding-left: 10px;
        margin-bottom: 16px;
    }

    /* Metric cards */
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

    /* Success / error banners */
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

    /* Navbar */
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

    /* Labels and general text */
    label, p, div { color: #1E3A5F; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Selected value text in dropdowns and number inputs */
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] [data-testid="stSelectboxValue"],
    .stSelectbox div[data-baseweb="select"] input,
    input[type="number"],
    .stNumberInput input {
        color: #1B3A6B !important;
        font-weight: 600 !important;
    }

    /* Dropdown container background */
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 8px !important;
    }

    /* Selected value in closed dropdown */
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] [data-testid="stSelectboxValue"],
    .stSelectbox div[data-baseweb="select"] input {
        color: #1B3A6B !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
            


    /* Dropdown options list */
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

    /* Let the dropdown panel auto-widen instead of wrapping text */
    
    ul[role="listbox"] {
        width: max-content !important;
        max-width: 360px !important;
    }
            


    /* Highlighted/hovered option */
    div[data-baseweb="popover"] ul li:hover,
    [role="option"]:hover {
        background-color: #2563EB !important;
        color: white !important;
    }

    /* Selected/active option in list */
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
        .stNumberInput input {
            color: #1B3A6B !important;
        }
        div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.95) !important;
        }
    }

    /* Number inputs */
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

    /* Dropdown arrow */
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

    /* Tooltip button */
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

# ROUTING — show login/register if not logged in

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

# NAVBAR (only shown when logged in)

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
    if st.button("🛒 My Cart", use_container_width=True,
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


# PAGE ROUTING

if st.session_state.page == "profile":
    show_profile()
    st.stop()

if st.session_state.page == "cart":
    show_cart()
    st.stop()


# DASHBOARD (default page)

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
    <h2 style="margin:0; color:#1B3A6B;"> CloudQuote </h2>
    <h4 style="margin:0; color: #4D516D;"> ☁️ Cloud Infrastructure Price Calculator </h4>
    <p style="margin:4px 0 0 0; color:#64748B;">
        Tata TeleServices · India Region · All prices in INR per month
    </p>
</div>
""", unsafe_allow_html=True)


# PRODUCT SELECTION

st.markdown('<div class="section-title">Step 1 — Select Product</div>',
            unsafe_allow_html=True)

product = st.selectbox(
    "Select Product",
    ["Vayu Cloud", "Hana Grid", "OLVM"],
    key="product_select",
    help="Choose the cloud product you want to price"
)

st.markdown("---")


# DYNAMIC FORM BASED ON PRODUCT

st.markdown('<div class="section-title">Step 2 — Configure</div>',
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
        "Operating System": os_type,
        "Pricing Tier": pricing_tier,
        "Storage Type": storage_type,
        "Storage (GB)": storage_gb,
        "Backup Type": backup_type,
        "Backup (GB)": backup_gb,
        "Firewall": firewall_type,
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
        "Pricing Tier": pricing_tier,
        "Storage Type": storage_type,
        "Storage (GB)": storage_gb,
        "Backup Type": backup_type,
        "Backup (GB)": backup_gb,
    }


# FLAVOUR SPECS PREVIEW

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


# BUTTONS ROW

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
    st.rerun()


# CALCULATE

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
            st.session_state.result = result
            st.session_state.quotation_id = st.session_state.quotation_id or generate_quotation_id()
            item = {
                "Product": product,
                "Flavour": flavour,
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
                "Line Total (INR)": result.get("Grand Total", 0.0),
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


# RESULTS SECTION

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
        <p>{len(items)} flavour configuration(s) added</p>
        <h1>{format_inr(grand_total)}</h1>
        <p>Grand Total per Month (INR, excl. taxes)</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**📦 Added Flavours / Configurations**")
    quote_df = pd.DataFrame(items)
    display_cols = [
        "Product", "Flavour", "Operating System", "Pricing Tier",
        "Storage Type", "Storage (GB)", "Backup Type", "Backup (GB)",
        "Firewall", "Public IPs", "Quantity", "vCPU", "RAM (GB)",
        "Line Total (INR)"
    ]
    quote_df = quote_df[display_cols]
    st.dataframe(quote_df, use_container_width=True, hide_index=True)

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
            st.experimental_rerun()

    if st.button("Clear quote list", type="secondary"):
        st.session_state.quote_items = []
        st.experimental_rerun()

    st.markdown("---")
    st.markdown('<div class="section-title">⬇️ Download Quotation</div>',
                unsafe_allow_html=True)

    quote_export_df = build_quote_export_dataframe(items)
    csv_data = export_quote_to_csv(quote_export_df)
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
