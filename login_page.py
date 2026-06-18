import streamlit as st
from auth import login_user

def show_login():
    st.markdown("""
    <div style="max-width:420px; margin:60px auto 0 auto;">
    <div class="card" style="padding:36px;">
        <h2 style="color:#1B3A6B; margin-bottom:4px;">👋 Welcome Back</h2>
        <p style="color:#64748B; margin-bottom:24px;">Sign in to CloudQuote</p>
    </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("📧 Email Address", placeholder="you@example.com")
        password = st.text_input("🔒 Password", type="password", placeholder="Your password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please fill in all fields.")
        else:
            success, message, user = login_user(email, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.page = "dashboard"
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#475569;'>Don't have an account?</p>", unsafe_allow_html=True)
    if st.button("Create an Account", use_container_width=True):
        st.session_state.page = "register"
        st.rerun()