# ☁️ Cloud Infrastructure Price Calculator

A professional web-based pricing calculator for **Novamesh Limited** (A Tata Communications Company).  
Built to help the sales team instantly generate accurate price quotations for cloud infrastructure products — without manually searching through Excel files.

---

## 🏢 About This Tool

This application calculates monthly pricing for three cloud products:

| Product | Description |
|---------|-------------|
| **Vayu Cloud** | Virtual machines on OpenStack. Multiple flavours, 6 OS options, 3 pricing tiers |
| **Hana Grid** | High-performance VMs for SAP HANA workloads. Large RAM configurations |
| **OLVM** | Oracle Linux Virtualization Manager VMs. High performance, Linux only |

All prices are in **INR per month**, exclude taxes, and are valid for **30 days** from date of quotation.

---

## 📁 Project Structure

price_calculator/

│

├── app.py                  # Main Streamlit dashboard (UI)

├── pricing_engine.py       # Pricing logic and calculations

├── data_loader.py          # Reads and parses Excel pricing data

├── utils.py                # Helper functions (export, formatting)

├── requirements.txt        # Python dependencies

├── README.md               # This file

│

├── data/

   └── Training_data.xlsx  # Source pricing data (required)

---

## ⚙️ How It Works

User selects product → Chooses flavour, OS, tier, add-ons

↓

App looks up exact price from Training_data.xlsx

↓

Adds storage + backup + firewall + public IP costs

↓

Displays full breakdown + generates downloadable quotation

**No AI. No estimation. No approximation.**  
Every price is a direct lookup from the source Excel file.


## 🖥️ System Requirements

- Windows 10 / 11
- Python 3.10 or higher
- Internet browser (Chrome recommended)
- VS Code (recommended editor)

---

## 🚀 Installation & Setup (Step by Step)

### Step 1 — Install Python
If you don't have Python installed:
1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download Python 3.10 or higher
3. During installation, **check the box** that says `Add Python to PATH`
4. Click Install

Verify installation by opening PowerShell and running:
```powershell
python --version
```
You should see something like `Python 3.11.0`

---

### Step 2 — Clone the Project
In terminal-

git clone https://github.com/AnushkaSharma3105/Pricing_Calculator

### Step 3 — Create a Virtual Environment
cd Pricing_Calculator

python -m venv .venv

Then activate it:

.venv\Scripts\activate


### Step 4 — Install Dependencies
pip install -r requirements.txt


Wait for all packages to install. This may take 1-2 minutes.

### Step 7 — Run the Application
```powershell
streamlit run app.py
```

Your browser will automatically open at:

http://localhost:8501

If the browser doesn't open automatically, copy and paste that link into Chrome manually.
