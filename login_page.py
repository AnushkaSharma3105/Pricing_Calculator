import streamlit as st
from auth import login_user, get_security_question, reset_password_with_answer

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
        password = st.text_input("🔒 Password", type="password",
                                 placeholder="Your password")
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
    st.markdown("<p style='text-align:center; color:#475569;'>Don't have an account?</p>",
                unsafe_allow_html=True)
    if st.button("Create an Account", use_container_width=True):
        st.session_state.page = "register"
        st.rerun()

    # ─────────────────────────────────────────────
    # FORGOT PASSWORD
    # ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<p style='text-align:center; color:#475569;'>Forgot your password?</p>",
                unsafe_allow_html=True)

    if "show_forgot" not in st.session_state:
        st.session_state.show_forgot = False
    if "forgot_step" not in st.session_state:
        st.session_state.forgot_step = 1
    if "forgot_email" not in st.session_state:
        st.session_state.forgot_email = ""
    if "forgot_question" not in st.session_state:
        st.session_state.forgot_question = ""

    if st.button("🔑 Forgot Password?", use_container_width=True):
        st.session_state.show_forgot = not st.session_state.show_forgot
        st.session_state.forgot_step = 1
        st.session_state.forgot_email = ""
        st.session_state.forgot_question = ""

    if st.session_state.show_forgot:

        # ── STEP 1: Enter email and fetch security question ──
        if st.session_state.forgot_step == 1:
            st.markdown("#### Step 1 — Enter your registered email")
            with st.form("forgot_step1_form"):
                forgot_email = st.text_input(
                    "📧 Email Address",
                    placeholder="you@example.com",
                    key="fp_email_input"
                )
                find_clicked = st.form_submit_button(
                    "Find My Account", use_container_width=True
                )

            if find_clicked:
                if not forgot_email.strip():
                    st.error("Please enter your email address.")
                else:
                    question, error = get_security_question(forgot_email)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.forgot_email = forgot_email.strip()
                        st.session_state.forgot_question = question
                        st.session_state.forgot_step = 2
                        st.rerun()

        # ── STEP 2: Answer security question ──
        elif st.session_state.forgot_step == 2:
            st.markdown("#### Step 2 — Answer your security question")
            st.info(f"🔐 **{st.session_state.forgot_question}**")

            with st.form("forgot_step2_form"):
                answer = st.text_input(
                    "Your Answer",
                    placeholder="Enter your answer",
                    key="fp_answer_input"
                )
                verify_clicked = st.form_submit_button(
                    "Verify Answer", use_container_width=True
                )

            if verify_clicked:
                if not answer.strip():
                    st.error("Please enter your answer.")
                else:
                    # Temporarily verify answer before going to step 3
                    from auth import reset_password_with_answer as rpa
                    # We store the answer temporarily to use in step 3
                    st.session_state.forgot_answer = answer.strip()
                    st.session_state.forgot_step = 3
                    st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True, type="secondary"):
                    st.session_state.forgot_step = 1
                    st.rerun()

        # ── STEP 3: Set new password ──
        elif st.session_state.forgot_step == 3:
            st.markdown("#### Step 3 — Set your new password")

            with st.form("forgot_step3_form"):
                new_password = st.text_input(
                    "🔒 New Password",
                    type="password",
                    placeholder="Min 8 chars, uppercase, number, symbol",
                    key="fp_new_password"
                )
                confirm_new_password = st.text_input(
                    "🔒 Confirm New Password",
                    type="password",
                    placeholder="Repeat new password",
                    key="fp_confirm_password"
                )
                reset_clicked = st.form_submit_button(
                    "Reset Password", use_container_width=True
                )

            if reset_clicked:
                if not new_password or not confirm_new_password:
                    st.error("Please fill in both password fields.")
                elif new_password != confirm_new_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = reset_password_with_answer(
                        st.session_state.forgot_email,
                        st.session_state.forgot_answer,
                        new_password
                    )
                    if success:
                        st.success(message)
                        # Reset all forgot password state
                        st.session_state.show_forgot = False
                        st.session_state.forgot_step = 1
                        st.session_state.forgot_email = ""
                        st.session_state.forgot_question = ""
                        st.session_state.forgot_answer = ""
                        st.rerun()
                    else:
                        st.error(message)
                        # If answer was wrong, go back to step 2
                        if "Incorrect answer" in message:
                            st.session_state.forgot_step = 2
                            st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True, type="secondary"):
                    st.session_state.forgot_step = 2
                    st.rerun()