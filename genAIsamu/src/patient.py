from __future__ import annotations
from data_models import PreDiagnosis, PatientRequest
import streamlit as st
import pandas as pd
from services import make_prediagnosis, speech_to_text, add_PatientRequest, add_Prediagnosis, display_table, record_audio
from audiorecorder import audiorecorder
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import os
import sqlite3

st.set_page_config(page_title="Patient Form", layout="centered")

# define session state
def init_state():
    if "requests" not in st.session_state:
        st.session_state["requests"] = []   # list[PatientRequest]


# CSS for form shadow
st.markdown(
    f"""
    <style>
    /* Form container with shadow */
    .stForm {{
        background-color: #FAFAFA;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); /* shadow */
    }}
    """,
    unsafe_allow_html=True
)

# request form 
def patient_request_form():
    st.markdown("## 🏥 Patient Emergency Form")

    with st.form("patient_form"):
        patient_name = st.text_input("Patient Name")
        symptoms = st.text_area("Symptoms", height=100)
        temperature = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, step=0.1)
        tension = st.text_input("Tension (Blood Pressure) e.g. 120/80")
        beat_rate = st.number_input("Beat Rate (BPM)", min_value=20, max_value=250)

        submitted = st.form_submit_button("Submit")

    if submitted:
        if not patient_name.strip():
            st.error("Patient name is required.")
            return
        if not symptoms.strip():
            st.error("Symptoms are required.")
            return

        # Generate prediagnosis
        full_symptoms = (
            symptoms
            + f"\n\nVitals:\nTemperature: {temperature} °C\n"
            f"Tension: {tension}\nHeart rate: {beat_rate} BPM"
        )
        condition, urgency = make_prediagnosis(full_symptoms)

        prediagnosis = PreDiagnosis(condition=condition, urgencyLevel=urgency, symptoms=symptoms)

        prediagnosis_id = add_Prediagnosis(prediagnosis.condition, prediagnosis.urgencyLevel, prediagnosis.symptoms)

        # Store request (Part 2)
        req = PatientRequest(
            name=patient_name,
            symptoms=prediagnosis.symptoms,
            temperature=temperature,
            tension=tension,
            beat_rate=int(beat_rate),
            prediagnosis=prediagnosis,
        )
        st.session_state["requests"].append(req)

        add_PatientRequest(req.name, req.symptoms, req.temperature, req.tension, req.beat_rate, prediagnosis_id)

        # Display confirmation
        with st.container():
            st.markdown("### 🧾 Patient Information")
            st.markdown(f"""
            <div style="
                background-color: #f9f9f9; 
                border-radius: 15px; 
                padding: 20px; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 15px;
            ">
                <p><strong>Patient :</strong> {patient_name}</p>
                <p><strong>Symptoms :</strong> {symptoms}</p>
                <p><strong>Temperature :</strong> {temperature} °C</p>
                <p><strong>Tension :</strong> {tension}</p>
                <p><strong>Beat Rate :</strong> {beat_rate} BPM</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🔎 Pre-Diagnosis Result")
        st.markdown(f"""
        <div style="
            background-color: #f0f0f5; 
            border-radius: 15px; 
            padding: 20px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <p><strong>Condition:</strong> {prediagnosis.condition}.</p>
            <p><strong>Urgency Level:</strong> {prediagnosis.urgencyLevel.upper()}</p>
        </div>
        """, unsafe_allow_html=True)

        display_table("PreDiagnosis")
        display_table("PatientRequest")

# request with live audio 
def patient_request_live_audio():
    st.markdown("## 🔊 Use Voice AI")

    patient_name = st.text_input("Patient Name")

    if patient_name.strip(): 
        if record_audio(patient_name):
            save_path = os.path.join("/Users/familyelkouch/genAIsamu/data", f"audio_{patient_name}.wav")

            symptoms = speech_to_text(save_path)
            st.write(symptoms)
            
            condition, urgency = make_prediagnosis(symptoms)

            prediagnosis = PreDiagnosis(condition=condition, urgencyLevel=urgency, symptoms=symptoms)

            prediag_id = add_Prediagnosis(prediagnosis.condition, prediagnosis.urgencyLevel, prediagnosis.symptoms)

            # Store request (Part 2)
            req = PatientRequest(
                name=patient_name,
                symptoms=prediagnosis.symptoms,
                prediagnosis=prediagnosis,
                temperature=None,
                tension=None,
                beat_rate=None,
            )
            st.session_state["requests"].append(req)

            add_PatientRequest(req.name, req.symptoms, req.temperature, req.tension, req.beat_rate, prediag_id)

            # Display confirmation
            with st.container():
                st.markdown("### 🧾 Patient Information")
                st.markdown(f"""
                <div style="
                    background-color: #f9f9f9; 
                    border-radius: 15px; 
                    padding: 20px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    margin-bottom: 15px;
                ">
                    <p><strong>Patient :</strong> {patient_name}</p>
                    <p><strong>Symptoms :</strong> {symptoms}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### 🔎 Pre-Diagnosis Result")
            st.markdown(f"""
            <div style="
                background-color: #f0f0f5; 
                border-radius: 15px; 
                padding: 20px; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            ">
                <p><strong>Condition:</strong> {prediagnosis.condition}.</p>
                <p><strong>Urgency Level:</strong> {prediagnosis.urgencyLevel.upper()}</p>
            </div>
            """, unsafe_allow_html=True)

            display_table("PreDiagnosis")
            display_table("PatientRequest")


# request with uploading audio
def patient_request_upload_audio():
    st.markdown("## 🔊 Upload Your Request")


    with st.form("patient_upload_request"):
        patient_name = st.text_input("Patient Name")
        audio = st.file_uploader("Upload an audio file", type=[".wav"])

        print(audio)

        if audio is not None:
            save_path = os.path.join("/Users/familyelkouch/genAIsamu/data", audio.name)

            # Sauvegarde du fichier sur le disque
            with open(save_path, "wb") as f:
                f.write(audio.getbuffer())

            st.success(f"Fichier sauvegardé !")

        submitted = st.form_submit_button("Submit")

    if submitted:
        if not patient_name.strip():
            st.error("Patient name is required.")
            return
        if audio is None:
            st.error("Symptoms are required.")
            return

        symptoms = speech_to_text(save_path)
        st.write(symptoms)
        
        condition, urgency = make_prediagnosis(symptoms)

        prediagnosis = PreDiagnosis(condition=condition, urgencyLevel=urgency, symptoms=symptoms)

        prediag_id = add_Prediagnosis(prediagnosis.condition, prediagnosis.urgencyLevel, prediagnosis.symptoms)

        # Store request (Part 2)
        req = PatientRequest(
            name=patient_name,
            symptoms=prediagnosis.symptoms,
            prediagnosis=prediagnosis,
            temperature=None,
            tension=None,
            beat_rate=None,
        )
        st.session_state["requests"].append(req)

        add_PatientRequest(req.name, req.symptoms, req.temperature, req.tension, req.beat_rate, prediag_id)

        # Display confirmation
        with st.container():
            st.markdown("### 🧾 Patient Information")
            st.markdown(f"""
            <div style="
                background-color: #f9f9f9; 
                border-radius: 15px; 
                padding: 20px; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 15px;
            ">
                <p><strong>Patient :</strong> {patient_name}</p>
                <p><strong>Symptoms :</strong> {symptoms}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🔎 Pre-Diagnosis Result")
        st.markdown(f"""
        <div style="
            background-color: #f0f0f5; 
            border-radius: 15px; 
            padding: 20px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <p><strong>Condition:</strong> {prediagnosis.condition}.</p>
            <p><strong>Urgency Level:</strong> {prediagnosis.urgencyLevel.upper()}</p>
        </div>
        """, unsafe_allow_html=True)

        display_table("PreDiagnosis")
        display_table("PatientRequest")


# main for patient page
def main():
    init_state()
    tab1, tab2, tab3 = st.tabs(["Fill Form", "Use Voice AI", "Upload Audio"])

    with tab1:
        patient_request_form()
    
    with tab2:
        patient_request_live_audio()
    
    with tab3:
        patient_request_upload_audio()


if __name__ == "__main__":
    main()