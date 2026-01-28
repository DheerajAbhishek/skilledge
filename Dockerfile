FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including CA certificates and git
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader stopwords punkt wordnet averaged_perceptron_tagger

# Copy application files
COPY . .

# Create directory for uploaded resumes
RUN mkdir -p /app/AI-Resume-Analyzer/App/Uploaded_Resumes

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Set working directory to App folder
WORKDIR /app

# Run the application
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
