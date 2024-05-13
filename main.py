from typing import Union
from pydantic import UUID4, BaseModel
from fastapi import FastAPI, File, UploadFile, Body
import requests
import time
import assemblyai as aai
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from mykeys import *
MEANING_CLOUD_SUM_URL = "https://api.meaningcloud.com/summarization-1.0"
base_url = "https://api.assemblyai.com/v2"

headers = {
    "authorization": ASSEM_AI_KEY
}

app = FastAPI()
LVLS = [15, 25, 35]
vertexai.init(project='modified-math-423110-b4', location='europe-west8')
model = GenerativeModel(model_name="gemini-1.0-pro-vision-001")

@app.post("/summarize")
def summ(text: str = Body(..., embed=True), level: int = Body(..., embed=True))  :
    payload = {
        'key':  MC_KEY,
        'txt': text,
        'limit': LVLS[level]
    }
    r = requests.post(MEANING_CLOUD_SUM_URL, data=payload)
    print(r.json())
    return {'summary': r.json()['summary']}

@app.post("/transcribe")
def transcribe(audio_file: UploadFile):

    if audio_file.content_type is None or 'audio' not in audio_file.content_type:
        return {"error": "File must be audio"}
    if audio_file.file is None == "":
        return {"error": "File not found"}

    with open("./my-audio.mp3" , "rb") as f:
        response = requests.post(base_url + "/upload",
                          headers=headers,
                          data=f)

    upload_url = response.json()["upload_url"]

    data = {
        "audio_url": upload_url # You can also use a URL to an audio or video file on the web
    }
    url = base_url + "/transcript" 
    response = requests.post(url, json=data, headers=headers)
    
    transcript_id = response.json()['id']
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    tries: int = 0
    while tries < 4:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()

        if transcription_result['status'] == 'completed':
            return summ(transcription_result['text'], 0)
        elif transcription_result['status'] == 'error':
            return {"error": "Something went wrong"}
        else:
            tries = tries + 1
            time.sleep(2)

@app.post('/improve')
def improveText(text: str = Body(..., embed=True)):
    IMPROVE_PROMPT = "Migliora il seguente testo, correggendo gli errori grammaticali e rendendolo formale, chiaro e coerente. TESTO DA MIGLIORARE: "
    response = model.generate_content(Part.from_text(IMPROVE_PROMPT + text))   
    print(vars(response))
    return response.candidates[0].text

@app.post("/createReply")
def createReply(text: str = Body(..., embed=True)):
    REPLY_PROMPT = "Creare una risposta adeguata e dello stesso registro del seguente testo. TESTO DA CUI CREARE LA RISPOSTA: "
    response = model.generate_content(REPLY_PROMPT + text)
    return response.candidates[0].text


