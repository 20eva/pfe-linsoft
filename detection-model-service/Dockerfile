
FROM python:3.11-slim



RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*



WORKDIR /app



COPY requirements.txt .

RUN pip install --no-cache-dir scikit-learn==1.8.0 joblib pyyaml pandas flask gitpython



COPY scan_playbook.py .

COPY detector_model_group_split.joblib .

COPY detector_vectorizer_group_split.joblib .

COPY recommendations.py .

COPY app.py .



EXPOSE 5000

CMD ["python", "app.py"]

