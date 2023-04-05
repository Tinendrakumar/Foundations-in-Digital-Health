import json
import psycopg2
# Connect to the database.
# search_path is set to include mimiciii on the server side.
conn = psycopg2.connect(host="172.16.34.1", port="5432", user="mimic_demo", password="mimic_demo", database="mimic")
cur = conn.cursor()

# Define the query to retrieve the required data
query = """
    SELECT n.row_id, n.hadm_id, n.chartdate, n.text, a.hospital_expire_flag, d.icd9_code
    FROM mimiciii.noteevents n
    INNER JOIN mimiciii.admissions a ON n.hadm_id = a.hadm_id
    LEFT JOIN mimiciii.diagnoses_icd d ON n.hadm_id = d.hadm_id
    WHERE n.category = 'Discharge summary'
    limit 10000
"""

# Execute the query and fetch the results
cur.execute(query)
rows = cur.fetchall()

# Define a dictionary to store the data
data = {'docs': []}

# Iterate over the rows and add them to the dictionary
for row in rows:
    note_id, hadm_id, chart_date, note_text, expire_flag, icd9_code = row

    # Check if the note already exists in the dictionary
    note_doc = next((doc for doc in data['docs'] if doc['id'] == str(note_id)), None)

    if note_doc:
        # Append the ICD9 code to the list of codes for the note
        note_doc['icd9_codes'].append(icd9_code)
    else:
        # Add the note to the dictionary
        note_doc = {
            'id': str(note_id),
            'note_id': str(note_id),
            'hadm_id': str(hadm_id),
            'chart_date': chart_date.isoformat(),
            'note_text': note_text,
            'hospital_expire_flag': expire_flag,
            'icd9_codes': [icd9_code] if icd9_code else []
        }
        data['docs'].append(note_doc)

# Save the data to a JSON file
with open('discharge_summary_notess.json', 'w') as f:
    json.dump(data, f, indent=2)
