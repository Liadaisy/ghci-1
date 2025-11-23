# analyst_views.py
import streamlit as st
from services import session_scope, list_pending_loans, log_action
from ui_components import page_header
from analysis import load_model, load_explainer, load_feature_names, predict_proba_and_class, shap_bar_plot
import matplotlib.pyplot as plt

def analyst_dashboard(user):
    page_header("Analyst dashboard", "Review pending applications and run model analysis.")

    model = load_model()
    explainer = load_explainer()
    feature_names = load_feature_names()

    with session_scope() as s:
        pending = list_pending_loans(s)

    if not pending:
        st.info("No pending applications.")
        return

    for loan in pending:
        st.markdown(f"### Application {loan.id} — submitted {loan.created_at}")
        st.json(loan.application_data)

        cols = st.columns([1,1,1])
        with cols[0]:
            if model is not None:
                try:
                    proba, pred = predict_proba_and_class(model, loan.application_data)
                    st.metric("Approval probability", f"{proba:.3f}", delta=None)
                    st.write("Predicted:", "Approved" if pred==1 else "Denied")
                except Exception as e:
                    st.warning(f"Prediction failed: {e}")
            else:
                st.info("Model not available. Train and place model.joblib in ./models")

        with cols[1]:
            if explainer is not None and model is not None:
                try:
                    fig = shap_bar_plot(explainer, model, loan.application_data, feature_names=feature_names, topn=8)
                    st.pyplot(fig)
                except Exception as e:
                    st.warning(f"SHAP plot failed: {e}")
            else:
                st.info("SHAP explainer not available.")

        with cols[2]:
            decision = st.selectbox(f"Decision for {loan.id}", ["leave pending","approve","deny"], key=f"dec_{loan.id}")
            explanation = st.text_area("Explanation", key=f"exp_{loan.id}")
            if st.button(f"Apply decision for {loan.id}"):
                with session_scope() as s:
                    l = s.query(type(loan)).get(loan.id)
                    if decision == "approve":
                        l.status = getattr(l.status.__class__, "approved") if hasattr(l.status.__class__, "approved") else type(l.status)( "approved")
                        l.decision = "approved"
                        l.explanation = explanation
                    elif decision == "deny":
                        l.status = getattr(l.status.__class__, "denied") if hasattr(l.status.__class__, "denied") else type(l.status)("denied")
                        l.decision = "denied"
                        l.explanation = explanation
                    # else leave pending
                    log_action(s, user.id, f"Analyst decision {decision} for loan {loan.id}")
                st.success("Decision applied.")
                st.rerun()
