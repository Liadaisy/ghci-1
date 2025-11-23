# model_training.py
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import shap

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# synthetic dataset (same as before)
np.random.seed(42)
n = 1000
data = pd.DataFrame({
    'Gender': np.random.choice(['Male', 'Female'], n),
    'Age': np.random.randint(21,65,n),
    'Region': np.random.choice(['Urban','Rural','Semi-Urban'], n),
    'Employment_Type': np.random.choice(['Salaried','Self-Employed','Freelancer'], n),
    'Annual_Income': np.random.randint(20000,150001,n),
    'Credit_Score': np.random.randint(300,851,n),
    'Loan_Amount': np.random.randint(50000,200001,n),
    'Loan_Tenure_Months': np.random.choice([12,24,36,48,60], n),
    'Existing_Loans': np.random.randint(0,4,n),
    'Monthly_Expenses': np.random.randint(5000,30001,n)
})

# generate label
income_norm = data['Annual_Income'] / data['Annual_Income'].max()
loan_amount_norm = data['Loan_Amount'] / data['Loan_Amount'].max()
credit_score_norm = data['Credit_Score'] / 850
monthly_expenses_norm = data['Monthly_Expenses'] / data['Monthly_Expenses'].max()
existing_loans_norm = data['Existing_Loans'] / 3
loan_tenure_norm = data['Loan_Tenure_Months'] / 60

approval_probability = (
    0.4 * income_norm +
    0.3 * credit_score_norm -
    0.2 * loan_amount_norm -
    0.1 * monthly_expenses_norm -
    0.05 * existing_loans_norm +
    0.05 * loan_tenure_norm
).clip(0,1)

data['Loan_Approved'] = (approval_probability > 0.4).astype(int)

categorical_cols = ['Gender','Region','Employment_Type']
numerical_cols = ['Age','Annual_Income','Credit_Score','Loan_Amount','Loan_Tenure_Months','Existing_Loans','Monthly_Expenses']

X = data.drop(columns=['Loan_Approved'])
y = data['Loan_Approved']

preprocessor = ColumnTransformer(transformers=[
    ('num', StandardScaler(), numerical_cols),
    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
], remainder='drop')

pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', LogisticRegression(max_iter=500))
])

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)
pipeline.fit(X_train, y_train)

# feature names
try:
    cat_enc = pipeline.named_steps['preprocessor'].named_transformers_['cat']
    cat_names = list(cat_enc.get_feature_names_out(categorical_cols))
except Exception:
    cat_names = []
    for c in categorical_cols:
        cat_names += [f"{c}_{v}" for v in sorted(data[c].unique())]
feature_names = numerical_cols + cat_names

# SHAP explainer best-effort
explainer = None
try:
    X_train_trans = pipeline.named_steps['preprocessor'].transform(X_train)
    explainer = shap.LinearExplainer(pipeline.named_steps['classifier'], X_train_trans)
    joblib.dump(explainer, os.path.join(MODEL_DIR, "explainer.joblib"))
except Exception as e:
    print("Could not build explainer:", e)

joblib.dump(pipeline, os.path.join(MODEL_DIR, "model.joblib"))
joblib.dump(feature_names, os.path.join(MODEL_DIR, "feature_names.joblib"))
joblib.dump(categorical_cols, os.path.join(MODEL_DIR, "categorical_cols.joblib"))
joblib.dump(numerical_cols, os.path.join(MODEL_DIR, "numerical_cols.joblib"))

print("Saved model artifacts to", MODEL_DIR)
