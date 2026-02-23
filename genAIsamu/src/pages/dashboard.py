import streamlit as st
import pandas as pd
import sqlite3
from services import display_table

st.set_page_config(page_title="Medical Staff Dashboard", layout="wide")

# medical staff page - v1 - not used
def staff_page():
    st.title("🏥 Medical Staff Dashboard")
    st.subheader("Incoming patient requests")

    requests = st.session_state.get("requests", [])

    if not requests:
        st.info("No patient requests yet.")
        return

    data = []
    for r in requests:
        data.append({
            "Patient": r.name,
            "Condition": r.prediagnosis.condition,
            "Urgency": r.prediagnosis.urgencyLevel,
            "Symptoms": r.prediagnosis.symptoms,
            "Temperature (°C)": r.temperature,
            "Tension": r.tension,
            "Beat Rate (BPM)": r.beat_rate,
        })


    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    urgency_filter = st.selectbox("Filter by urgency level", ["All", "low", "medium", "high"])
    if urgency_filter != "All":
        df_filtered = df[df["Urgency"] == urgency_filter]
        st.dataframe(df_filtered, use_container_width=True)


def medical_staff_dashboard():
    st.markdown(
    "<h1 style='text-align: center;'>🏥 Medical Staff Dashboard</h1>",
    unsafe_allow_html=True
    )
    st.title("Incoming patient requests")

    # create connexion to the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")
    # to retrieve dict values from select
    connection.row_factory = sqlite3.Row
    # build structure of the database
    cursor = connection.cursor()

    requests = cursor.execute("""
        SELECT PatientRequest.*, PreDiagnosis.condition, PreDiagnosis.urgencyLevel
        FROM PatientRequest
        JOIN PreDiagnosis ON PatientRequest.id_prediagnosis = PreDiagnosis.id_prediagnosis;
    """)

    if not requests:
        st.info("No patient requests yet.")
        return
    else:
        rows = cursor.fetchall()

        data = []

        for row in rows:
            # convert row in a dict
            row = dict(row)
            # structure data
            data.append({
                "ID" : row['id_patientrequest'],
                "Patient": row['name'],
                "Condition": row['condition'],
                "Symptoms": row['symptoms'],
                "Temperature (°C)": row['temperature'],
                "Tension": row['tension'],
                "Beat Rate (BPM)": row['beat_rate'],
                "Urgency": row['urgencyLevel'],
                "Status": row["status"]
            })
        # create dataframe for streamlit dashboard
        df = pd.DataFrame(data)
        #st.dataframe(df)

        st.subheader("📊 Table View")

        options = ["waiting", "processing", "done"]
        edited_df = st.data_editor(
            df,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=options
                )
            },
            disabled=["ID", "Patient", "Condition", "Symptoms", "Temperature (°C)", "Tension", "Beat Rate (BPM)", "Urgency"],
            use_container_width=True,
            hide_index=True
        )
        
        for i, row in edited_df.iterrows():
            cursor.execute(
                "UPDATE PatientRequest SET status = ? WHERE id_patientrequest = ?",
                (row["Status"], row["ID"])
            )

        connection.commit()

        changes = edited_df.compare(df) 
        for i in list(changes.index.unique()):
            id = edited_df["ID"][i]  

            cursor.execute(f"SELECT id_patientrequest, status FROM PatientRequest WHERE id_patientrequest = {id}")
            rows2 = cursor.fetchall()

            for row in rows2:
                print(f"\nUpdated PatientRequest {dict(row)}\n")


        # Verify update in sqlite Table
        #display_table("PatientRequest")

        # Filter table by urgency level
        #urgency_filter = st.selectbox("Filter by urgency level", ["All", "low", "medium", "high"])
        #if urgency_filter != "All":
            #df_filtered = edited_df[edited_df["Urgency"] == urgency_filter]
            #st.dataframe(df_filtered, use_container_width=True)

        #st.dataframe(edited_df)

        st.subheader("🩺 List View")

        # Get unique values from the edited dataframe
        urgency_levels = edited_df["Urgency"].unique().tolist()
        status_levels = edited_df["Status"].unique().tolist()

        # Filters
        selected_urgency = st.selectbox("Filter by Urgency", options=["All"] + urgency_levels)
        selected_status = st.selectbox("Filter by Status", options=["All"] + status_levels)

        # Filter the dataframe
        filtered_df = edited_df.copy()

        if selected_urgency != "All":
            filtered_df = filtered_df[filtered_df["Urgency"] == selected_urgency]

        if selected_status != "All":
            filtered_df = filtered_df[filtered_df["Status"] == selected_status]

        # Display filtered patients in cards
        if filtered_df.empty:
            st.info("No patients match the selected filters.")
        else:
            for i, row in filtered_df.iterrows():
                # Cards for list view
                with st.container():
                    st.markdown(f"""
                        <div style="
                            background: #f9f9f9;
                            border-radius: 15px;
                            padding: 20px;
                            margin-bottom: 15px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        ">
                            <h3 style="margin-bottom:5px;">{row['Patient']} (ID: {row['ID']})</h3>
                            <p><strong>Condition:</strong> {row['Condition']}</p>
                            <p><strong>Symptoms:</strong> {row['Symptoms']}</p>
                            <p><strong>Temperature:</strong> {row['Temperature (°C)']} °C</p>
                            <p><strong>Tension:</strong> {row['Tension']}</p>
                            <p><strong>Beat Rate:</strong> {row['Beat Rate (BPM)']} BPM</p>
                            <p><strong>Urgency:</strong> {row['Urgency'].upper()}</p>
                            <p><strong>Status:</strong> {row['Status']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                

# main for medical staff page
def main():
   #staff_page()
   medical_staff_dashboard()
    

if __name__ == "__main__":
    main()