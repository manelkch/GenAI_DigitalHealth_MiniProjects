import sqlite3

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

    # verify the connexion with database
    print(connection.total_changes)

    if table_name == "PreDiagnosis":
        # build structure of the database
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    
    if table_name == "PatientRequest":
        # build structure of the database
        cursor = connection.cursor()
        cursor.execute("""
            SELECT PatientRequest.*, PreDiagnosis.condition, PreDiagnosis.urgencyLevel
            FROM PatientRequest
            JOIN PreDiagnosis ON PatientRequest.id_prediagnosis = PreDiagnosis.id_prediagnosis;
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(row)

def add_status():
    # create connexion to the database
    connection = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")

    # verify the connexion with database
    print(connection.total_changes)

    # build structure of the database
    cursor = connection.cursor()
    cursor.execute("ALTER TABLE table_name ADD new_column_name column_definition")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def delete_database(table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect("/Users/familyelkouch/genAIsamu/data/database.db")
    cursor = conn.cursor()

    # DROP the table
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Commit and close
    conn.commit()
    conn.close()

    print(f"Table '{table_name}' deleted.")


