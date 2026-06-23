import json
import streamlit as st
import pandas as pd
from history_db import fetch_all_quotations, fetch_quotation_by_db_id, delete_quotation_by_id
from utils import format_inr, export_quote_to_csv, export_quote_to_excel, export_to_excel


def show_cart():
    st.markdown("""
    <div class="card">
        <h2 style="margin:0; color:#1B3A6B;">Quotation History</h2>
        <p style="color:#64748B;">Review saved quotations, view exact exported structure, download Excel/CSV, or delete history items.</p>
    </div>
    """, unsafe_allow_html=True)

    # transient flash/toast message (set by button handlers below)
    flash = st.session_state.get("flash_msg")
    flash_type = st.session_state.get("flash_type", "info")
    if flash:
        if flash_type == "success":
            st.success(flash)
        elif flash_type == "warning":
            st.warning(flash)
        else:
            st.info(flash)
        # clear flash so it only appears once
        st.session_state["flash_msg"] = None
        st.session_state["flash_type"] = None

    quotations = fetch_all_quotations()

    if not quotations:
        st.markdown("""
        <div class="card" style="text-align:center; padding:60px;">
            <h3 style="color:#94A3B8;">No quotations available yet.</h3>
            <p style="color:#CBD5E1;">Go to the Dashboard to generate and save quotations.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    history_frame = pd.DataFrame([
        {
            "Quotation ID": quote["quotation_id"],
            "Customer Name": quote["customer_name"] or "-",
            "Company Name": quote["company_name"] or "-",
            "Date": quote["created_at"],
            "Total Amount": format_inr(quote["grand_total"]),
        }
        for quote in quotations
    ])

    table_html = history_frame.to_html(index=False, classes="history-table", border=0)
    st.markdown(
        f"<div class='card' style='padding: 16px;'>{table_html}</div>",
        unsafe_allow_html=True
    )

    for quote in quotations:
        history = fetch_quotation_by_db_id(quote['id'])
        if history is None:
            continue

        payload = json.loads(history['quotation_json'])
        payload_df = pd.DataFrame(payload.get('rows', []))
        meta = payload.get('metadata', {})

        st.markdown("<div class='card' style='padding: 16px; margin-top: 12px;'>", unsafe_allow_html=True)
        cols = st.columns([2, 2, 2, 2, 2, 3])
        cols[0].markdown(f"**{quote['quotation_id']}**")
        cols[1].markdown(quote['customer_name'] or "-")
        cols[2].markdown(quote['company_name'] or "-")
        cols[3].markdown(quote['created_at'])
        cols[4].markdown(f"{format_inr(quote['grand_total'])}")

        with cols[5]:
            if st.button("View", key=f"view_{quote['id']}"):
                st.session_state.history_view_id = quote['id']
                st.session_state["flash_msg"] = f"Quotation {quote['quotation_id']} ready to view."
                st.session_state["flash_type"] = "info"

            if payload.get('type') == 'full_quote':
                excel_data = export_quote_to_excel(payload_df, history['quotation_id'], history['grand_total'])
                csv_data = export_quote_to_csv(payload_df, history['grand_total'])
            else:
                excel_data = export_to_excel(payload_df, meta.get('product', ''), meta.get('flavour', ''), history['quotation_id'])
                csv_data = payload_df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name=f"quotation_{history['quotation_id']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{quote['id']}",
                use_container_width=True
            )
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"quotation_{history['quotation_id']}.csv",
                mime="text/csv",
                key=f"csv_{quote['id']}",
                use_container_width=True
            )
            if st.button("Delete", type="secondary", key=f"delete_{quote['id']}"):
                st.session_state.delete_confirm_id = quote['id']
                st.session_state["flash_msg"] = f"Quotation {quote['quotation_id']} marked for deletion."
                st.session_state["flash_type"] = "warning"

        if st.session_state.get('history_view_id') == quote['id']:
            with st.expander(f"View Quotation: {quote['quotation_id']}", expanded=True):
                st.markdown(f"**Quotation ID:** {quote['quotation_id']}")
                st.markdown(f"**Customer Name:** {quote['customer_name'] or '-'}")
                st.markdown(f"**Company Name:** {quote['company_name'] or '-'}")
                st.markdown(f"**Date:** {quote['created_at']}")
                st.markdown(f"**Grand Total:** {format_inr(quote['grand_total'])}")
                st.markdown("---")
                if not payload_df.empty:
                    st.dataframe(payload_df, use_container_width=True)
                else:
                    st.markdown("No quotation details available.")

        if st.session_state.get('delete_confirm_id') == quote['id']:
            with st.expander("Confirm deletion", expanded=True):
                st.warning("Are you sure you want to delete this quotation?")
                confirm_col, cancel_col = st.columns(2)
                if confirm_col.button("Yes, delete", type="secondary", key=f"confirm_del_{quote['id']}"):
                    delete_quotation_by_id(quote['id'])
                    st.success("Quotation deleted.")
                    st.session_state.delete_confirm_id = None
                    st.rerun()
                if cancel_col.button("Cancel", key=f"cancel_del_{quote['id']}"):
                    st.session_state.delete_confirm_id = None
        st.markdown("</div>", unsafe_allow_html=True)
