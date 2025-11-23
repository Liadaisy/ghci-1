# admin_views.py
import streamlit as st
from services import session_scope, log_action
from ui_components import page_header
from models import EditRequest, LoanApplication, User, LoanStatus

def admin_dashboard(user):
    page_header("Admin dashboard", "Approve edits / withdrawals and view system logs.")

    with session_scope() as s:
        requests = s.query(EditRequest).filter(EditRequest.status == "pending").order_by(EditRequest.created_at.asc()).all()

    if not requests:
        st.info("No pending requests.")
        return

    for req in requests:
        st.write(f"Request #{req.id} | Loan: {req.loan_application_id} | By user: {req.user_id}")
        if req.withdraw_requested:
            st.write("Withdrawal requested.")
            if st.button(f"Approve withdraw {req.id}"):
                with session_scope() as s:
                    loan = s.query(LoanApplication).get(req.loan_application_id)
                    if loan:
                        loan.status = LoanStatus.withdrawn
                    r = s.query(EditRequest).get(req.id)
                    r.status = "approved"
                    log_action(s, user.id, f"Approved withdraw {req.id} for loan {req.loan_application_id}")
                st.success("Withdrawal approved.")
                st.rerun()
            if st.button(f"Reject withdraw {req.id}"):
                with session_scope() as s:
                    r = s.query(EditRequest).get(req.id)
                    r.status = "rejected"
                    log_action(s, user.id, f"Rejected withdraw {req.id}")
                st.success("Rejected.")
                st.rerun()
        else:
            st.write(f"Edit proposed → Monthly Expenses: {req.new_monthly_expenses} | Existing Loans: {req.new_existing_loans} | Tenure: {req.new_loan_tenure}")
            if st.button(f"Approve edit {req.id}"):
                with session_scope() as s:
                    loan = s.query(LoanApplication).get(req.loan_application_id)
                    if loan:
                        if req.new_monthly_expenses is not None:
                            loan.application_data["Monthly_Expenses"] = float(req.new_monthly_expenses)
                        if req.new_existing_loans is not None:
                            loan.application_data["Existing_Loans"] = int(req.new_existing_loans)
                        if req.new_loan_tenure is not None:
                            loan.application_data["Loan_Tenure_Months"] = int(req.new_loan_tenure)
                    r = s.query(EditRequest).get(req.id)
                    r.status = "approved"
                    log_action(s, user.id, f"Approved edit {req.id}")
                st.success("Edit approved.")
                st.rerun()
            if st.button(f"Reject edit {req.id}"):
                with session_scope() as s:
                    r = s.query(EditRequest).get(req.id)
                    r.status = "rejected"
                    log_action(s, user.id, f"Rejected edit {req.id}")
                st.success("Edit rejected.")
                st.rerun()
