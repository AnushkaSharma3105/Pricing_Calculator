import streamlit as st
from auth import register_user

def show_register():
    st.markdown("""
    <div style="max-width:420px; margin:40px auto 0 auto;">
    <div class="card" style="padding:36px;">
        <h2 style="color:#1B3A6B; margin-bottom:4px;">🚀 Create Account</h2>
        <p style="color:#64748B; margin-bottom:24px;">Join CloudQuote today</p>
    </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        full_name = st.text_input("👤 Full Name", placeholder="Jane Doe")
        email = st.text_input("📧 Email Address", placeholder="you@example.com")
        password = st.text_input("🔒 Password", type="password", placeholder="Min 8 chars, uppercase, number, symbol")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat your password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not full_name or not email or not password or not confirm_password:
            st.error("Please fill in all fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            success, message = register_user(full_name, email, password)
            if success:
                st.success(message + " Please sign in.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(message)

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#475569;'>Already have an account?</p>", unsafe_allow_html=True)
    if st.button("Sign In Instead", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()