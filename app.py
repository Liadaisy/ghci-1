# app.py - YOUR ORIGINAL BEAUTIFUL DESIGN - NOW 100% WORKING
import streamlit as st
import os
from fairauth import build_auth_url, exchange_code_for_tokens, decode_id_token, AUTH0_LOGOUT_URL
from models import sessionscope, User, init_db

st.set_page_config(page_title="FairFin", layout="centered", page_icon="⚖️")
init_db()

# GORGEOUS CUSTOM CSS
st.markdown("""
<style>
    .main-header {font-size: 4rem; color: #1e3a8a; text-align: center; font-weight: bold; margin-bottom: 2rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);}
    .role-card {padding: 2rem; border-radius: 20px; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1); transition: all 0.3s; margin: 1rem;}
    .role-card:hover {transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.2);}
    .user-card {background: linear-gradient(135deg, #10b981, #34d399); color: white;}
    .admin-card {background: linear-gradient(135deg, #ef4444, #f87171); color: white;}
    .analyst-card {background: linear-gradient(135deg, #f59e0b, #fbbf24); color: white;}
    .big-button {height: 200px; font-size: 2rem !important; font-weight: bold !important;}
</style>
""", unsafe_allow_html=True)

query_params = st.query_params

# AUTH0 CALLBACK
if "code" in query_params:
    code = query_params["code"][0]
    role_selected = query_params.get("state", ["user"])[0]
    
    try:
        tokens = exchange_code_for_tokens(code)
        user_info = decode_id_token(tokens["id_token"])
        auth0id = user_info["sub"]
        
        with sessionscope() as s:
            user = s.query(User).filter(User.auth0id == auth0id).first()
            if not user:
                user = User(auth0id=auth0id, email=user_info["email"], role="user")
                s.add(user)
            db_role = user.role
            
            if role_selected != db_role and role_selected in ["admin", "analyst"]:
                st.error(f"Access Denied! Your role is {db_role}")
                st.stop()
                
            st.session_state.authenticated = True
            st.session_state.role = db_role
            st.session_state.email = user_info["email"]
            
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Login Failed: {e}")

# MAIN UI
if not st.session_state.get("authenticated"):
    st.markdown('<h1 class="main-header">⚖️ FairFin</h1>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#666;'>Fair Lending Platform</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="role-card user-card"><h2>Customer</h2><p>Apply for loans</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="role-card admin-card"><h2>Admin</h2><p>Manage system</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="role-card analyst-card"><h2>Analyst</h2><p>AI Analysis</p></div>', unsafe_allow_html=True)
    
    st.markdown("### Select Role to Continue")
    role = st.radio("", ["user", "admin", "analyst"], horizontal=True, label_visibility="collapsed")
    
    if st.button("🚀 Login with Auth0", use_container_width=True, type="primary"):
        url = build_auth_url(role)
        st.markdown(f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True)
else:
    st.sidebar.success(f"Logged in as {st.session_state.role.upper()}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
        
    st.markdown(f'<h1 class="main-header">Welcome, {st.session_state.role.capitalize()}!</h1>', unsafe_allow_html=True)
    
    if st.session_state.role == "user":
        st.success("User Dashboard")
    elif st.session_state.role == "admin":
        st.error("Admin Panel")
    elif st.session_state.role == "analyst":
        st.warning("AI Analyst Tools")