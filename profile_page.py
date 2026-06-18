import streamlit as st
from auth import change_password, delete_account

def show_profile():
    user = st.session_state.user

    st.markdown(f"""
    <div class="card">
        <h2 style="margin:0; color:#1B3A6B;">👤 User Profile</h2>
        <p style="color:#64748B;">Manage your account</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div class="section-title">Account Info</div>
        <p><b>Name:</b> {user['full_name']}</p>
        <p><b>Email:</b> {user['email']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🔑 Change Password</div>', unsafe_allow_html=True)
    with st.form("change_pw_form"):
        old_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password", placeholder="Min 8 chars, uppercase, number, symbol")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password", use_container_width=True)

    if submitted:
        if not old_pw or not new_pw or not confirm_pw:
            st.error("Please fill in all fields.")
        elif new_pw != confirm_pw:
            st.error("New passwords do not match.")
        else:
            success, message = change_password(user["id"], old_pw, new_pw)
            if success:
                st.success(message)
            else:
                st.error(message)

    st.markdown("---")
    st.markdown('<div class="section-title" style="color:#991B1B; border-color:#EF4444;">⚠️ Delete Account</div>', unsafe_allow_html=True)
    st.warning("This action is permanent and cannot be undone.")
    with st.form("delete_form"):
        confirm_del_pw = st.text_input("Enter your password to confirm", type="password")
        delete_submitted = st.form_submit_button("🗑️ Delete My Account", use_container_width=True)

    if delete_submitted:
        if not confirm_del_pw:
            st.error("Please enter your password.")
        else:
            success, message = delete_account(user["id"], confirm_del_pw)
            if success:
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = "login"
                st.success("Account deleted. Redirecting...")
                st.rerun()
            else:
                st.error(message)