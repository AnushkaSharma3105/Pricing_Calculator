import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "Training_data.xlsx")

VAYU_OS_COLUMNS = {
    "Linux": {"Hourly- ppu": 6, "1 year Reserved": 7, "3 Year Reserved": 8},
    "Windows": {"Hourly- ppu": 9, "1 year Reserved": 10, "3 Year Reserved": 11},
    "SUSE- Linux": {"Hourly- ppu": 12, "1 year Reserved": 13, "3 Year Reserved": 14},
    "SLES for SAP": {"Hourly- ppu": 15, "1 year Reserved": 16, "3 Year Reserved": 17},
    "Redhat Enterprise Linux": {"Hourly- ppu": 18, "1 year Reserved": 19, "3 Year Reserved": 20},
    "RHEL for SAP": {"Hourly- ppu": 21, "1 year Reserved": 22, "3 Year Reserved": 23},
}

HANA_OS_COLUMNS = {
    "Linux": {"Hourly- ppu": 6, "1 year Reserved": 7, "3 Year Reserved": 8},
    "SUSE- Linux": {"Hourly- ppu": 12, "1 year Reserved": 13, "3 Year Reserved": 14},
    "RHEL for SAP": {"Hourly- ppu": 21, "1 year Reserved": 22, "3 Year Reserved": 23},
}

OLVM_OS_COLUMNS = {
    "Linux": {"Hourly- ppu": 6, "1 year Reserved": 7, "3 Year Reserved": 8},
}


def load_raw_data():
    df = pd.read_excel(DATA_PATH, sheet_name="Sheet1", header=None)
    return df


def load_vayu_cloud():
    df = pd.read_excel(DATA_PATH, sheet_name="Sheet1", header=None)
    rows = []
    for _, row in df.iterrows():
        if str(row[0]).strip() == "Vayu Cloud- Open Stack":
            flavour = str(row[1]).strip()
            vcpu = row[2]
            ram = row[3]
            root_win = row[4]
            root_other = row[5]
            entry = {
                "Flavour": flavour,
                "vCPU": vcpu,
                "RAM (GB)": ram,
                "Root Disk Windows (GB)": root_win,
                "Root Disk Other OS (GB)": root_other,
            }
            for os_name, cols in VAYU_OS_COLUMNS.items():
                for tier, col_idx in cols.items():
                    val = row[col_idx]
                    entry[f"{os_name}__{tier}"] = val if pd.notna(val) else None
            rows.append(entry)
    return pd.DataFrame(rows)


def load_hana_grid():
    df = pd.read_excel(DATA_PATH, sheet_name="Sheet1", header=None)
    rows = []
    for _, row in df.iterrows():
        if str(row[0]).strip() == "HANA Grid":
            flavour = str(row[1]).strip()
            vcpu = row[2]
            ram = row[3]
            root_disk = row[4]
            entry = {
                "Flavour": flavour,
                "vCPU": vcpu,
                "RAM (GB)": ram,
                "Root Disk (GB)": root_disk,
            }
            for os_name, cols in HANA_OS_COLUMNS.items():
                for tier, col_idx in cols.items():
                    val = row[col_idx]
                    entry[f"{os_name}__{tier}"] = val if pd.notna(val) else None
            rows.append(entry)
    return pd.DataFrame(rows)


def load_olvm():
    df = pd.read_excel(DATA_PATH, sheet_name="Sheet1", header=None)
    rows = []
    for _, row in df.iterrows():
        if str(row[0]).strip() == "OLVM":
            flavour = str(row[1]).strip()
            vcpu = row[2]
            ram = row[3]
            root_disk = row[4]
            entry = {
                "Flavour": flavour,
                "vCPU": vcpu,
                "RAM (GB)": ram,
                "Root Disk (GB)": root_disk,
            }
            for os_name, cols in OLVM_OS_COLUMNS.items():
                for tier, col_idx in cols.items():
                    val = row[col_idx]
                    entry[f"{os_name}__{tier}"] = val if pd.notna(val) else None
            rows.append(entry)
    return pd.DataFrame(rows)


def get_vayu_flavours():
    df = load_vayu_cloud()
    return sorted(df["Flavour"].tolist())


def get_hana_flavours():
    df = load_hana_grid()
    return sorted(df["Flavour"].tolist())


def get_olvm_flavours():
    df = load_olvm()
    return sorted(df["Flavour"].tolist())


def get_vayu_row(flavour):
    df = load_vayu_cloud()
    result = df[df["Flavour"] == flavour]
    if result.empty:
        return None
    return result.iloc[0]


def get_hana_row(flavour):
    df = load_hana_grid()
    result = df[df["Flavour"] == flavour]
    if result.empty:
        return None
    return result.iloc[0]


def get_olvm_row(flavour):
    df = load_olvm()
    result = df[df["Flavour"] == flavour]
    if result.empty:
        return None
    return result.iloc[0]