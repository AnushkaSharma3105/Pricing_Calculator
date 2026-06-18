import streamlit as st

def show_cart():
    st.markdown("""
    <div class="card">
        <h2 style="margin:0; color:#1B3A6B;">Quotation History</h2>
        <p style="color:#64748B;">Your saved quotations will appear here</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="text-align:center; padding:60px;">
        <h3 style="color:#94A3B8;">No quotations available yet.</h3>
        <p style="color:#CBD5E1;">Go to the Dashboard to generate and save quotations.</p>
    </div>
    """, unsafe_allow_html=True)