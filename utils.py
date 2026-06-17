import pandas as pd
import io
from datetime import datetime


def format_inr(amount):
    """Format number as Indian Rupees"""
    return f"₹ {amount:,.2f}"


def generate_quotation_id():
    """Generate a unique quotation ID based on timestamp"""
    now = datetime.now()
    return f"QUO-{now.strftime('%Y%m%d-%H%M%S')}"


def build_summary_dataframe(product, flavour, specs, config, breakdown):
    """Build a clean summary dataframe for display and export"""

    rows = []

    # Product info
    rows.append({"Component": "Product", "Details": product, "Amount (INR)": ""})
    rows.append({"Component": "Flavour", "Details": flavour, "Amount (INR)": ""})

    # Specs
    for k, v in specs.items():
        rows.append({"Component": k, "Details": str(v), "Amount (INR)": ""})

    # Config
    for k, v in config.items():
        rows.append({"Component": k, "Details": str(v), "Amount (INR)": ""})

    # Blank separator
    rows.append({"Component": "", "Details": "", "Amount (INR)": ""})

    # Pricing breakdown
    rows.append({"Component": "--- PRICE BREAKDOWN ---", "Details": "", "Amount (INR)": ""})
    for k, v in breakdown.items():
        if k not in ("Quantity", "Grand Total"):
            rows.append({
                "Component": k,
                "Details": "",
                "Amount (INR)": f"{v:,.2f}" if isinstance(v, (int, float)) else v
            })

    rows.append({"Component": "", "Details": "", "Amount (INR)": ""})
    rows.append({
        "Component": "Quantity",
        "Details": str(breakdown.get("Quantity", 1)),
        "Amount (INR)": ""
    })
    rows.append({
        "Component": "GRAND TOTAL",
        "Details": "",
        "Amount (INR)": f"{breakdown.get('Grand Total', 0):,.2f}"
    })

    return pd.DataFrame(rows)


def export_to_csv(df):
    """Export dataframe to CSV bytes"""
    return df.to_csv(index=False).encode("utf-8")


def export_to_excel(df, product, flavour, quotation_id):
    """Export dataframe to Excel bytes with formatting"""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Quotation", startrow=4)

        workbook = writer.book
        worksheet = writer.sheets["Quotation"]

        # Formats
        title_fmt = workbook.add_format({
            "bold": True, "font_size": 16,
            "font_color": "#FFFFFF", "bg_color": "#1B3A6B",
            "align": "center", "valign": "vcenter"
        })
        subtitle_fmt = workbook.add_format({
            "bold": True, "font_size": 11,
            "font_color": "#1B3A6B"
        })
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#1B3A6B",
            "font_color": "#FFFFFF", "border": 1,
            "align": "center"
        })
        total_fmt = workbook.add_format({
            "bold": True, "bg_color": "#FFF3CD",
            "font_color": "#856404", "border": 1,
            "num_format": "#,##0.00"
        })

        # Title rows
        worksheet.merge_range("A1:C1", "PRICE QUOTATION", title_fmt)
        worksheet.write("A2", f"Quotation ID: {quotation_id}", subtitle_fmt)
        worksheet.write("A3", f"Product: {product}  |  Flavour: {flavour}", subtitle_fmt)
        worksheet.write("A4", f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", subtitle_fmt)

        # Header row (row 5 = index 4, startrow=4 means headers at row 5)
        for col_num, col_name in enumerate(df.columns):
            worksheet.write(4, col_num, col_name, header_fmt)

        # Column widths
        worksheet.set_column("A:A", 35)
        worksheet.set_column("B:B", 25)
        worksheet.set_column("C:C", 20)

        # Highlight grand total row
        for row_idx, row in df.iterrows():
            if str(row.get("Component", "")).strip() == "GRAND TOTAL":
                excel_row = row_idx + 5  # offset: 4 header rows + 1 for startrow
                worksheet.write(excel_row, 0, "GRAND TOTAL", total_fmt)
                worksheet.write(excel_row, 1, "", total_fmt)
                worksheet.write(excel_row, 2, row["Amount (INR)"], total_fmt)

    return output.getvalue()