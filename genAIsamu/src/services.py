import os
from dotenv import load_dotenv
from mistralai import Mistral
import requests
from data_models import PreDiagnosis, PatientRequest
import re
import json
import streamlit as st
import sqlite3
from typing import Any
import httpx
from time import sleep
from audiorecorder import audiorecorder

def make_prediagnosis(symptoms) -> PreDiagnosis:

    load_dotenv()

    s = symptoms

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MODEL = "mistral-tiny" 

    client = Mistral(api_key=MISTRAL_API_KEY)

     # --- CONSTRUCTION DU PROMPT ---
    prompt = f"""
    You are a medical triage assistant. 
    Analyze the following symptoms and return ONLY a JSON object following the schema below.

    ### JSON Schema
    {{
    "type": "object",
    "properties": {{
        "condition": {{
        "type": "string",
        "description": "A short and plausible hypothesis about the medical condition."
        }},
        "urgency_level": {{
        "type": "string",
        "enum": ["low", "medium", "high"],
        "description": "The urgency level based on the symptoms."
        }},
        "symptoms": {{
        "type": "string",
        "description": "Exact copy of the input symptoms."
        }}
    }},
        "required": ["condition", "urgency_level", "symptoms"]
    }}

    ### Instructions
    - Output MUST be valid JSON.
    - DO NOT return markdown.
    - DO NOT use backticks.
    - DO NOT add explanations.
    - DO NOT wrap the answer in a code block.

    Symptoms: {s}
    """

    # LLM Call
    response = client.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = response.choices[0].message.content

    # Parse JSON 
    try:
        result = extract_json_from_model_output(result_text)
    except:
        raise ValueError("Le modèle n'a pas renvoyé un JSON valide :", result_text)

    condition = result["condition"]
    urgency = result["urgency_level"]

    return condition, urgency

# Removes markdown blocks and extracts the first valid JSON object.
def extract_json_from_model_output(text):

    # Remove ```json and ```
    cleaned = re.sub(r"```json|```", "", text).strip()

    # Find JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output:\n" + text)

    json_str = match.group(0)

    # Load JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON extracted: {json_str}") from e

# updated code from https://github.com/gladiaio/gladia-samples/blob/main/python/src/pre_recorded/pre_recorded_file.py
def speech_to_text(save_path):
    file_path = save_path
    config = {
        "language_config": {
            "languages": ["es", "ru", "en", "fr"],
            "code_switching": True,
        },
        "diarization": True,
    }

    _, file_extension = os.path.splitext(
        file_path
    )  # Get your audio file name + extension

    with open(file_path, "rb") as f:  # Open the file
        file_content = f.read()  # Read the content of the file
    
    load_dotenv()

    GLADIA_API_KEY = os.getenv("GLADIA_API_KEY")
    GLADIA_API_URL = os.getenv("GLADIA_API_URL")

    headers = {
        "x-gladia-key": GLADIA_API_KEY,  # Replace with your Gladia Token
        "accept": "application/json",
    }

    files = [("audio", (file_path, file_content, "audio/" + file_extension[1:]))]

    upload_response: dict[str, Any] = httpx.post(
        url=f"{GLADIA_API_URL}/v2/upload/", headers=headers, files=files
    ).json()
    print("Upload response with File ID:", upload_response)
    audio_url = upload_response.get("audio_url")

    data = {
        "audio_url": audio_url,
        **config,
    }

    headers["Content-Type"] = "application/json"

    post_response: dict[str, Any] = httpx.post(
        url=f"{GLADIA_API_URL}/v2/pre-recorded/", headers=headers, json=data
    ).json()

    print("Post response with Transcription ID:", post_response)
    result_url = post_response.get("result_url")

    if not result_url:
        print(f"No result URL found in post response: {post_response}")
        return  

    with st.spinner("Transcription in progress…"):
        while True:
            print("Polling for results...")
            poll_response: dict[str, Any] = httpx.get(
                url=result_url, headers=headers
            ).json()

            if poll_response.get("status") == "done":
                print("- Transcription done: \n")
                print(
                    json.dumps(
                        poll_response.get("result"), indent=2, ensure_ascii=False
                    )
                )
                break
            elif poll_response.get("status") == "error":
                print("- Transcription failed")
                print(poll_response)
            else:
                print("Transcription status:", poll_response.get("status"))
                #st.info(f"Transcription status: {poll_response.get("status")}")
            sleep(1)
        
        print("- End of work")
    st.success("Transcription finished !")

    return poll_response.get("result")["transcription"]["utterances"][0]["text"]

def databsae_creation():
    # create the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")

    # verify the connexion with database
    print(connection.total_changes)

    # build structure of the database
    cursor = connection.cursor()

    # create table PreDiagnosis
    cursor.execute("CREATE TABLE IF NOT EXISTS PreDiagnosis (id_prediagnosis INTEGER PRIMARY KEY, condition TEXT, urgencyLevel TEXT CHECK (urgencyLevel IN ('low', 'medium', 'high')), symptoms TEXT)")

    # create table PreDiagnosis
    cursor.execute("CREATE TABLE IF NOT EXISTS PatientRequest (id_patientrequest INTEGER PRIMARY KEY, name TEXT, symptoms TEXT, temperature REAL, tension TEXT, beat_rate INTEGER, id_prediagnosis INTEGER, FOREIGN KEY (id_prediagnosis) REFERENCES prediagnosis(id_prediagnosis))")

def test_database():
    # create the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")

    # verify the connexion with database
    print(connection.total_changes)

    # build structure of the database
    cursor = connection.cursor()

    #pred = ("Influenza", "medium", "cough, fever, fatigue")
    #cursor.execute("INSERT INTO prediagnosis (condition, urgencyLevel, symptoms) VALUES (?, ?, ?)", pred)

    pred_id = cursor.lastrowid

    print(pred_id)

    req = ("John Doe", "fever, cough", 38.2, "120/80", 90, pred_id)
    cursor.execute("""
        INSERT INTO PatientRequest
        (name, symptoms, temperature, tension, beat_rate, prediagnosis_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, req)

    print(cursor.lastrowid)

def add_Prediagnosis(condition, urgencyLevel, symptoms):
    # create connexion to the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")

    # verify the connexion with database
    print(connection.total_changes)

    # build structure of the database
    cursor = connection.cursor()

    prediagnosis = (condition, urgencyLevel, symptoms)

    cursor.execute("INSERT INTO PreDiagnosis (condition, urgencyLevel, symptoms) VALUES (?, ?, ?)", prediagnosis)

    connection.commit()

    return cursor.lastrowid

def add_PatientRequest(name, symptoms, temperature, tension, beat_rate, id_prediagnosis):
    # create connexion to the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")

    # verify the connexion with database
    print(connection.total_changes)

    # build structure of the database
    cursor = connection.cursor()

    request = (name, symptoms, temperature, tension, beat_rate, id_prediagnosis)

    cursor.execute("""
        INSERT INTO PatientRequest
        (name, symptoms, temperature, tension, beat_rate, id_prediagnosis)
        VALUES (?, ?, ?, ?, ?, ?)
    """, request)

    connection.commit()

def display_table(table_name):
    # create connexion to the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")
    # build structure of the database
    cursor = connection.cursor()

    if table_name == "PreDiagnosis":
        print("PreDiagnosis")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    
    if table_name == "PatientRequest":
        print("PatientRequest")
        cursor.execute("""
            SELECT PatientRequest.*, PreDiagnosis.condition, PreDiagnosis.urgencyLevel
            FROM PatientRequest
            JOIN PreDiagnosis ON PatientRequest.id_prediagnosis = PreDiagnosis.id_prediagnosis;
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(row)

def add_status_column():
    # create connexion to the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")

    # verify the connexion with database
    print(connection.total_changes)

    # build structure of the database
    cursor = connection.cursor()
    cursor.execute("ALTER TABLE PatientRequest ADD status TEXT CHECK (status IN ('waiting', 'processing', 'done'))")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

# adaptation of https://github.com/theevann/streamlit-audiorecorder?tab=readme-ov-file
def record_audio(patient_name):
    audio = audiorecorder("Click to record", "Click to stop recording")

    if len(audio) > 0:
        # To play audio in frontend:
        st.audio(audio.export().read())  

        # To save audio to a file, use pydub export method:
        audio.export(f"/Users/familyelkouch/genAIsamu/data/audio_{patient_name}.wav", format="wav")

        # To get audio properties, use pydub AudioSegment properties:
        st.write(f"Duration: {audio.duration_seconds} seconds")
        
        return True
