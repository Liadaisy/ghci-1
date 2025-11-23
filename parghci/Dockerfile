# Base Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for SHAP, numpy, scipy, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Streamlit configuration (headless mode)
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=true
ENV STREAMLIT_SERVER_ENABLEXSRS=false

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
