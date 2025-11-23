import streamlit as st
import os
from auth import build_auth_url, exchange_code_for_tokens, decode_id_token
from models import init_db, User
from services import session_scope
import user_views, analyst_views, admin_views

# Initialize database
init_db()

st.set_page_config(page_title="FairFin - Loan Portal", layout="wide")
st.title("FairFin — Loan Application Portal")

# Extract query params (new Streamlit API)
query_params = st.query_params

# ------------------------------
# 1. AUTH0 CALLBACK HANDLING
# ------------------------------
if "code" in query_params:
    code = query_params.get("code")
    if isinstance(code, list):
        code = code[0]

    try:
        token_data = exchange_code_for_tokens(code)
        st.session_state["id_token"] = token_data.get("id_token")
        st.session_state["access_token"] = token_data.get("access_token")
    except Exception as e:
        st.error(f"Failed to exchange token: {e}")

    # Clear the URL query params
    st.query_params = {}
    st.rerun()


# ------------------------------
# 2. CHECK IF USER IS LOGGED IN
# ------------------------------
if "id_token" in st.session_state and st.session_state["id_token"]:
    try:
        info = decode_id_token(st.session_state["id_token"])
    except Exception:
        st.error("Invalid ID Token")
        st.stop()

    auth0_sub = info.get("sub")
    email = info.get("email")
    name = info.get("name") or info.get("nickname") or email

    st.sidebar.info(f"Logged in as: {name}")

    # ------------------------------
    # 3. ALWAYS LOAD FRESH USER FROM DATABASE
    # ------------------------------
    with session_scope() as s:
        user = (
            s.query(User)
            .filter(User.auth0_id == auth0_sub)
            .first()
        )

        # First-time user → create new row
        if not user:
            user = User(
                auth0_id=auth0_sub,
                name=name,
                email=email,
                role=None
            )
            s.add(user)
            s.commit()
            s.refresh(user)

    # ------------------------------
    # 4. ROLE SELECTION LOGIC — NEVER SKIPPED NOW
    # ------------------------------
    if not user.role or user.role.strip() == "":
        st.info("Please select your role to continue.")

        selected_role = st.radio(
            "Select role",
            ["user", "analyst", "admin"]
        )

        if st.button("Save Role"):
            with session_scope() as s:
                db_user = (
                    s.query(User)
                    .filter(User.auth0_id == auth0_sub)
                    .first()
                )
                db_user.role = selected_role
                s.commit()

            st.success("Role saved! Reloading...")
            st.rerun()

        st.stop()

    # ------------------------------
    # 5. ROLE-BASED DASHBOARD
    # ------------------------------
    if user.role == "user":
        user_views.user_dashboard(user)

    elif user.role == "analyst":
        analyst_views.analyst_dashboard(user)

    elif user.role == "admin":
        admin_views.admin_dashboard(user)

    else:
        st.error("Invalid role in database.")
        st.stop()

else:
    # ------------------------------
    # 6. LOGIN PAGE (NO USER LOGGED IN)
    # ------------------------------
    st.header("Please log in")
    login_url = build_auth_url()
    st.markdown(f"[**Sign in with Auth0**]({login_url})")
