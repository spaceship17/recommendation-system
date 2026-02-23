# Model + API image (build from repo root).
# Use for: 1) Serving FastAPI (default CMD), 2) Running pipeline: docker run ... python run_pipeline.py --config configs/model_config.yaml
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY configs /app/configs
COPY run_pipeline.py /app/

RUN mkdir -p models/trained
COPY models/trained/ /app/models/trained/
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
