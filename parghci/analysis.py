# analysis.py
"""
Model loading and prediction utilities.
Assumes artifacts are in ./models directory:
- model.joblib (sklearn pipeline)
- explainer.joblib (shap explainer) — optional
- feature_names.joblib — optional
"""

import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import shap
import numpy as np
from io import BytesIO

MODEL_DIR = os.environ.get("MODEL_DIR", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")
EXPLAINER_PATH = os.path.join(MODEL_DIR, "explainer.joblib")
FEATURE_NAMES_PATH = os.path.join(MODEL_DIR, "feature_names.joblib")

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

def load_explainer():
    if os.path.exists(EXPLAINER_PATH):
        return joblib.load(EXPLAINER_PATH)
    return None

def load_feature_names():
    if os.path.exists(FEATURE_NAMES_PATH):
        return joblib.load(FEATURE_NAMES_PATH)
    return None

def predict_proba_and_class(model_pipeline, application_data):
    """Returns (probability_of_approval, class)"""
    df = pd.DataFrame([application_data])
    proba = model_pipeline.predict_proba(df)[0, 1]
    pred = int(model_pipeline.predict(df)[0])
    return float(proba), pred

def shap_bar_plot(explainer, model_pipeline, application_data, feature_names=None, topn=10):
    """
    Returns a matplotlib figure with topn features by absolute SHAP value.
    Uses explainer (already fitted) and pipeline preprocessor.
    """
    df = pd.DataFrame([application_data])
    X_trans = model_pipeline.named_steps['preprocessor'].transform(df)
    shap_values = explainer.shap_values(X_trans)
    # shap_values for linear explainer often returns array-like (1,n_features)
    arr = shap_values if isinstance(shap_values, (list, tuple)) else [shap_values]
    vals = np.array(arr[0]).flatten()
    if feature_names is None:
        feature_names = [f"f{i}" for i in range(len(vals))]
    data = list(zip(feature_names, vals))
    data_sorted = sorted(data, key=lambda x: abs(x[1]), reverse=True)[:topn]
    names, values = zip(*data_sorted) if data_sorted else ([], [])

    fig, ax = plt.subplots(figsize=(6, max(2, len(values) * 0.4)))
    y_pos = range(len(values))
    ax.barh(y_pos, values[::-1])
    ax.set_yticks(y_pos)
    ax.set_yticklabels(list(names)[::-1])
    ax.set_xlabel("SHAP value")
    ax.set_title("Top SHAP feature contributions")
    plt.tight_layout()
    return fig
