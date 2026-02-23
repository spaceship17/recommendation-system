# Streamlit UI image. Build from repo root: docker build -f ui/Dockerfile .
# Needs models/trained/ and root requirements.txt (pandas, streamlit, requests).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY ui /app/ui
RUN mkdir -p models/trained
COPY models/trained/ /app/models/trained/

EXPOSE 8501

CMD ["streamlit", "run", "ui/app.py", "--server.address=0.0.0.0"]
