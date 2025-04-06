FROM python:3.12-slim

WORKDIR /app

COPY sentiment_ai.py /app/sentiment_ai.py

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download es_core_news_sm

COPY . .

CMD ["uvicorn", "sentiment_ai:app", "--host", "0.0.0.0", "--port", "8002"]
