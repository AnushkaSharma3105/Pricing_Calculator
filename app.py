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
    build_summary_dataframe, export_to_csv, export_to_excel
)


# PAGE CONFIG

st.set_page_config(
    page_title="Cloud Price Calculator",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# CUSTOM CSS

st.markdown("""
<style>
            

    /* === BUTTON TEXT COLOR FIX (More Reliable) === */
    button[kind="secondary"],
    button[data-testid="stDownloadButton"] {
        color: white !important;
        font-weight: 600 !important;
    }

    /* Target the inner text element - this usually fixes it */
    button[kind="secondary"] p,
    button[data-testid="stDownloadButton"] p,
    button[kind="secondary"] div,
    button[data-testid="stDownloadButton"] div {
        color: white !important;
        font-weight: 600 !important;
    }

    /* Also target the button container */
    div.stButton button[kind="secondary"],
    button[data-testid="stDownloadButton"] {
        color: white !important;
        font-weight: 600 !important;
    }

    /* Hover state */
    button[kind="secondary"]:hover p,
    button[data-testid="stDownloadButton"]:hover p,
    button[kind="secondary"]:hover,
    button[data-testid="stDownloadButton"]:hover {
        color: white !important;
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

    /* Labels and general text */
    label, p, div { color: #1E3A5F; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
            
    
            
    /* White bold text inside all input fields and dropdowns */
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    .stSelectbox div[data-baseweb="select"] input,
    input[type="number"],
    .stNumberInput input {
        color: white !important;
        font-weight: 700 !important;
    }

    /* Dropdown options list - white text */
    div[data-baseweb="popover"] ul li,
    div[data-baseweb="popover"] ul li div,
    div[data-baseweb="popover"] ul li span,
    div[data-baseweb="menu"] ul li,
    [role="option"],
    [role="listbox"] li {
        color: white !important;
        font-weight: 400 !important;
    }

    /* Highlighted/hovered option */
    div[data-baseweb="popover"] ul li:hover {
        background-color: #2563EB !important;
        color: white !important;
    }
    
          
</style>
""", unsafe_allow_html=True)


# SESSION STATE INIT

if "result" not in st.session_state:
    st.session_state.result = None
if "quotation_id" not in st.session_state:
    st.session_state.quotation_id = None
if "last_config" not in st.session_state:
    st.session_state.last_config = {}


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
    <h2 style="margin:0; color:#1B3A6B;">☁️ Cloud Infrastructure Price Calculator</h2>
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
    st.session_state.quotation_id = None
    st.session_state.last_config = {}
    st.rerun()


# CALCULATE

if calculate_clicked:
    # Validation
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
            st.session_state.quotation_id = generate_quotation_id()
            st.session_state.last_config = {
                "product": product,
                "flavour": flavour,
                "specs": specs,
                "config": config,
            }
            st.markdown('<div class="success-banner">✅ Price calculated successfully!</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-banner">❌ Could not calculate price. Please check your selections.</div>',
                        unsafe_allow_html=True)


# RESULTS SECTION

if st.session_state.result:
    result = st.session_state.result
    saved = st.session_state.last_config
    qid = st.session_state.quotation_id

    st.markdown("---")
    st.markdown('<div class="section-title">📊 Quotation Results</div>',
                unsafe_allow_html=True)

    # Grand total price box
    st.markdown(f"""
    <div class="price-box">
        <p>Quotation ID: {qid}</p>
        <p>{saved['product']} · {saved['flavour']} · Qty: {result['Quantity']}</p>
        <h1>{format_inr(result['Grand Total'])}</h1>
        <p>Grand Total per Month (INR, excl. taxes)</p>
    </div>
    """, unsafe_allow_html=True)

    # Breakdown table
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

   
    # EXPORT BUTTONS
   
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