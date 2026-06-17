from data_loader import get_vayu_row, get_hana_row, get_olvm_row

STORAGE_PRICES = {
    "SSD-1": 3.4797582445857271,
    "SSD-2": 5.667796610169491,
    "SSD-3": 6.4241690669274956,
    "SSD-4": 10.291525423728816,
    "SSD-5": 10.706948444879158,
    "NAS": 7.384615384615385,
    "CIFS": 7.384615384615385,
    "Single Site Value Tier": 0.93553460998399807,
    "Dual Site Value Tier": 2.0442718811761531,
    "Dual Site Resilience Tier": 2.2568610349099023,
    "High Performance Object Storage": 3.0494031551821434,
}

BACKUP_PRICES = {
    "Value Based": 1.826923076923078,
    "Resilient": 3.4254807692307709,
    "Geo-Resilient": 3.882211538461541,
    "Commvault": 4.34887959569018,
    "None": 0,
}

FIREWALL_PRICES = {
    "None": 0,
    "Basic": 2000,
    "Standard": 5000,
    "Advanced": 10000,
}

PUBLIC_IP_PRICE = 500  # per IP per month

VAYU_OS_OPTIONS = [
    "Linux",
    "Windows",
    "SUSE- Linux",
    "SLES for SAP",
    "Redhat Enterprise Linux",
    "RHEL for SAP",
]

HANA_OS_OPTIONS = [
    "Linux",
    "SUSE- Linux",
    "RHEL for SAP",
]

OLVM_OS_OPTIONS = [
    "Linux",
]

PRICING_TIERS = [
    "Hourly- ppu",
    "1 year Reserved",
    "3 Year Reserved",
]


def calculate_vayu_price(flavour, os_type, pricing_tier, quantity,
                          storage_type, storage_gb,
                          backup_type, backup_gb,
                          firewall_type, public_ips):
    row = get_vayu_row(flavour)
    if row is None:
        return None

    key = f"{os_type}__{pricing_tier}"
    unit_vm_price = row.get(key, None)

    if unit_vm_price is None:
        return None

    # Storage cost
    storage_price_per_gb = STORAGE_PRICES.get(storage_type, 0)
    storage_cost = storage_price_per_gb * storage_gb

    # Backup cost
    backup_price_per_gb = BACKUP_PRICES.get(backup_type, 0)
    backup_cost = backup_price_per_gb * backup_gb

    # Firewall cost
    firewall_cost = FIREWALL_PRICES.get(firewall_type, 0)

    # Public IP cost
    public_ip_cost = public_ips * PUBLIC_IP_PRICE

    # Per unit total
    unit_total = unit_vm_price + storage_cost + backup_cost + firewall_cost + public_ip_cost

    # Final total
    total_price = unit_total * quantity

    breakdown = {
        "VM Price (per unit)": round(unit_vm_price, 2),
        "Storage Cost (per unit)": round(storage_cost, 2),
        "Backup Cost (per unit)": round(backup_cost, 2),
        "Firewall Cost (per unit)": round(firewall_cost, 2),
        "Public IP Cost (per unit)": round(public_ip_cost, 2),
        "Unit Total": round(unit_total, 2),
        "Quantity": quantity,
        "Grand Total": round(total_price, 2),
    }

    return breakdown


def calculate_hana_price(flavour, os_type, pricing_tier, quantity,
                          storage_type, storage_gb,
                          backup_type, backup_gb):
    row = get_hana_row(flavour)
    if row is None:
        return None

    key = f"{os_type}__{pricing_tier}"
    unit_vm_price = row.get(key, None)

    if unit_vm_price is None:
        return None

    storage_price_per_gb = STORAGE_PRICES.get(storage_type, 0)
    storage_cost = storage_price_per_gb * storage_gb

    backup_price_per_gb = BACKUP_PRICES.get(backup_type, 0)
    backup_cost = backup_price_per_gb * backup_gb

    unit_total = unit_vm_price + storage_cost + backup_cost
    total_price = unit_total * quantity

    breakdown = {
        "VM Price (per unit)": round(unit_vm_price, 2),
        "Storage Cost (per unit)": round(storage_cost, 2),
        "Backup Cost (per unit)": round(backup_cost, 2),
        "Unit Total": round(unit_total, 2),
        "Quantity": quantity,
        "Grand Total": round(total_price, 2),
    }

    return breakdown


def calculate_olvm_price(flavour, pricing_tier, quantity,
                          storage_type, storage_gb,
                          backup_type, backup_gb):
    row = get_olvm_row(flavour)
    if row is None:
        return None

    key = f"Linux__{pricing_tier}"
    unit_vm_price = row.get(key, None)

    if unit_vm_price is None:
        return None

    storage_price_per_gb = STORAGE_PRICES.get(storage_type, 0)
    storage_cost = storage_price_per_gb * storage_gb

    backup_price_per_gb = BACKUP_PRICES.get(backup_type, 0)
    backup_cost = backup_price_per_gb * backup_gb

    unit_total = unit_vm_price + storage_cost + backup_cost
    total_price = unit_total * quantity

    breakdown = {
        "VM Price (per unit)": round(unit_vm_price, 2),
        "Storage Cost (per unit)": round(storage_cost, 2),
        "Backup Cost (per unit)": round(backup_cost, 2),
        "Unit Total": round(unit_total, 2),
        "Quantity": quantity,
        "Grand Total": round(total_price, 2),
    }

    return breakdown


def get_flavour_specs(product, flavour):
    if product == "Vayu Cloud":
        row = get_vayu_row(flavour)
    elif product == "Hana Grid":
        row = get_hana_row(flavour)
    else:
        row = get_olvm_row(flavour)

    if row is None:
        return {}

    specs = {
        "vCPU": int(row["vCPU"]),
        "RAM (GB)": int(row["RAM (GB)"]),
    }

    if product == "Vayu Cloud":
        specs["Root Disk Windows (GB)"] = int(row["Root Disk Windows (GB)"])
        specs["Root Disk Other OS (GB)"] = int(row["Root Disk Other OS (GB)"])
    else:
        specs["Root Disk (GB)"] = int(row["Root Disk (GB)"])

    return specs