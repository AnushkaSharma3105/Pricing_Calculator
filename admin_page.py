import streamlit as st
from register_page import show_register
from auth import admin_delete_account

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

    st.markdown("---")
    st.markdown("### 🗑️ Delete a User Account")
    st.warning("This permanently deletes the account. This cannot be undone.")

    with st.form("admin_delete_form"):
        target_email = st.text_input("📧 User's Email Address", placeholder="user@example.com")
        target_password = st.text_input("🔒 User's Password", type="password",
                                        placeholder="Their account password")
        confirm = st.checkbox("I understand this will permanently delete this account.")
        delete_clicked = st.form_submit_button("Delete Account", use_container_width=True, type="primary")

    if delete_clicked:
        if not target_email or not target_password:
            st.error("Please fill in both the email and password.")
        elif not confirm:
            st.error("Please confirm you understand this action is permanent.")
        else:
            success, message = admin_delete_account(target_email, target_password)
            if success:
                st.success(message)
            else:
                st.error(message)