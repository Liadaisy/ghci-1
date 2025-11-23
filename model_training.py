# model_training.py
"""
Train a simple logistic regression on synthetic data and save:
- models/model.joblib (pipeline)
- models/explainer.joblib (SHAP explainer) if possible
- models/feature_names.joblib (transformed feature names)
- models/categorical_cols.joblib and numerical_cols.joblib
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import shap
import joblib

# Directory to save artifacts
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

np.random.seed(42)
num_samples = 1000

data = pd.DataFrame({
    'Gender': np.random.choice(['Male', 'Female'], num_samples),
    'Age': np.random.randint(21, 65, num_samples),
    'Region': np.random.choice(['Urban', 'Rural', 'Semi-Urban'], num_samples),
    'Employment_Type': np.random.choice(['Salaried', 'Self-Employed', 'Freelancer'], num_samples),
    'Annual_Income': np.random.randint(20000, 150001, num_samples),
    'Credit_Score': np.random.randint(300, 851, num_samples),
    'Loan_Amount': np.random.randint(50000, 200001, num_samples),
    'Loan_Tenure_Months': np.random.choice([12, 24, 36, 48, 60], num_samples),
    'Existing_Loans': np.random.randint(0, 4, num_samples),
    'Monthly_Expenses': np.random.randint(5000, 30001, num_samples)
})

# --- Approval probability generation ---
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
).clip(0, 1)

data['Loan_Approved'] = (approval_probability > 0.4).astype(int)

categorical_cols = ['Gender', 'Region', 'Employment_Type']
numerical_cols = ['Age', 'Annual_Income', 'Credit_Score', 'Loan_Amount',
                  'Loan_Tenure_Months', 'Existing_Loans', 'Monthly_Expenses']

X = data.drop(columns=['Loan_Approved'])
y = data['Loan_Approved']

# Preprocessor
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        # Use sparse=False for compatibility with many sklearn versions
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
    ],
    remainder='drop'
)

model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', LogisticRegression(max_iter=500))
])

# Train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model.fit(X_train, y_train)

# Create feature names after preprocessing for SHAP
# Get transformed column names
try:
    # for OneHotEncoder with get_feature_names_out
    cat_encoder = model.named_steps['preprocessor'].named_transformers_['cat']
    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_cols))
except Exception:
    # fallback: generate simple names
    cat_feature_names = []
    for c in categorical_cols:
        vals = sorted(data[c].unique())
        cat_feature_names += [f"{c}_{v}" for v in vals]

feature_names = numerical_cols + cat_feature_names

# SHAP explainer (LinearExplainer for linear models)
try:
    X_train_transformed = model.named_steps['preprocessor'].transform(X_train)
    explainer = shap.LinearExplainer(model.named_steps['classifier'], X_train_transformed, feature_perturbation="interventional")
    joblib.dump(explainer, os.path.join(MODEL_DIR, 'explainer.joblib'))
except Exception as e:
    print("Warning: could not create SHAP explainer. Reason:", e)
    explainer = None

# Save model and metadata
joblib.dump(model, os.path.join(MODEL_DIR, 'model.joblib'))
joblib.dump(feature_names, os.path.join(MODEL_DIR, 'feature_names.joblib'))
joblib.dump(categorical_cols, os.path.join(MODEL_DIR, 'categorical_cols.joblib'))
joblib.dump(numerical_cols, os.path.join(MODEL_DIR, 'numerical_cols.joblib'))

print("Model & artifacts saved to", MODEL_DIR)
