from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import spacy

# Deactivate SSL
import requests
from huggingface_hub import configure_http_backend

def backend_factory() -> requests.Session:
    session = requests.Session()
    session.verify = False
    return session

configure_http_backend(backend_factory=backend_factory)

# Models
pipe = pipeline("translation", model="Helsinki-NLP/opus-mt-es-en")
classifier = pipeline("sentiment-analysis", model="michellejieli/emotion_text_classifier")
pipe_aly = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

app = FastAPI()

nlp = spacy.load("es_core_news_sm")

DICT_CONVER = {
    "anger": "enfado",
    "disgust": "disgusto",
    "fear": "miedo",
    "joy": "felicidad",
    "neutral": "neutral",
    "sadness": "tristeza",
    "surprise": "sorpresa",
    "positive": "positivo",
    "negative": "negativa"
}

class TextRequest(BaseModel):
    text: str

@app.post("/analyze/")
async def analyze(request: TextRequest):
    text = request.text
    tr = pipe(text)
    tr_cleaned = tr[0]["translation_text"]
    analyzed = classifier(tr_cleaned)
    aux_tr = analyzed[0]["label"]
    if aux_tr == "neutral":
        aux = pipe_aly(tr_cleaned)
        tr_analyzed = DICT_CONVER[aux[0]["label"]]
    else:
        tr_analyzed = DICT_CONVER[aux_tr]
    return {"analyzed": tr_analyzed}

@app.post("/keywords/")
async def keywords(request: TextRequest):
    text = request.text
    review = nlp(text)
    keywords = [token.text for token in review if token.pos_ == "NOUN"]
    top_keywords = keywords[:3]
    return {"keywords": top_keywords}
