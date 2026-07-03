import streamlit as st
from register_page import show_register

def show_admin_panel():
    st.markdown("""
    <div class="card">
        <h2 style="color:#1B3A6B; margin:0;">🔐 Admin Panel</h2>
        <p style="color:#64748B; margin:4px 0 0 0;">
            Only you can create accounts. Users must come to you directly.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ➕ Create New User Account")
    show_register()