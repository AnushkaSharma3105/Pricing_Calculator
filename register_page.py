import streamlit as st
from auth import register_user

SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What was the name of your first school?",
    "What is the name of the city where you were born?",
    "What was your childhood nickname?",
    "What is the name of your favourite childhood friend?",
    "What street did you grow up on?",
    "What was the make and model of your first car?",
    "What is your oldest sibling's middle name?",
    "What was the name of your favourite teacher?",
]

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
        password = st.text_input("🔒 Password", type="password",
                                 placeholder="Min 8 chars, uppercase, number, symbol")
        confirm_password = st.text_input("🔒 Confirm Password", type="password",
                                         placeholder="Repeat your password")

        st.markdown("---")
        st.markdown("**🔑 Security Question** *(used for Forgot Password)*")
        security_question = st.selectbox(
            "Select a Security Question",
            SECURITY_QUESTIONS,
            key="reg_security_question"
        )
        security_answer = st.text_input(
            "Your Answer",
            placeholder="Enter your answer (case-insensitive)",
            help="Remember this answer — you'll need it to reset your password."
        )

        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not full_name or not email or not password or not confirm_password:
            st.error("Please fill in all fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif not security_answer.strip():
            st.error("Please provide an answer to your security question.")
        else:
            success, message = register_user(
                full_name, email, password,
                security_question, security_answer
            )
            if success:
                st.success(message + " Please sign in.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(message)

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#475569;'>Already have an account?</p>",
                unsafe_allow_html=True)
    if st.button("Sign In Instead", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()