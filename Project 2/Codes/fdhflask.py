import mysql.connector
import requests
import argparse
import pysolr
from flask import Flask, jsonify, request, render_template
from datetime import datetime

#Enter the databse details below
umls_db = mysql.connector.connect(host='172.16.34.1', port='3307',
                                user='umls', password='umls', database='umls2020')
def GetSynonms(search_text):
    mycursor = umls_db.cursor(buffered=True)

    sql = (f"SELECT CUI FROM MRCONSO Where Sab='CHV' and STR='{search_text}'")
    
    mycursor.execute(sql)
    results = mycursor.fetchall()
    field_names = [ col[0] for col in mycursor.description]
    
    a=(results[0][0])
    sql = (f"SELECT STR FROM MRCONSO Where CUI='{a}' and Sab='CHV' LIMIT 30")

    mycursor.execute(sql)
    results = mycursor.fetchall()
    
    return results

# Connect to Solr
solr = pysolr.Solr('http://localhost:8983/solr/mimic3/', timeout=100)

# Create Flask app
app = Flask(__name__)

# Route to load web page
@app.route('/')
def index():
    print('index function called')
    return render_template('index2.html')

# Route to Search and display results
@app.route('/Search', methods=['POST'])
def Search():
    query=''
    synonms=''
    search_text = request.form.get('query', '')
    hospital_expire_flag_input = request.form.get('hospital_expire_flag')
    start_date = request.form.get('start_date','All')
    end_date = request.form.get('end_date','All')
    icd9_codes = request.form.get('icd9_codes','All')

    #synoynms
    if(search_text !=''):
        synonms= GetSynonms(search_text)  
        print(type(synonms))
        synonms_list=[]
        for s in synonms:
          synonms_list.append((s)[0].replace(' ', '\\ '))
        query = " note_text:".join([r for r in synonms_list]) 
        query = " note_text:"+query

    # Hospital expire flag
    if hospital_expire_flag_input=='Died':
        query= query +" AND hospital_expire_flag: "+ str(1)
    elif hospital_expire_flag_input=='Survived':
        query= query +" AND hospital_expire_flag: "+ str(0)
    else:
        print('hospital_expire_flag_input not set'+ hospital_expire_flag_input)
    

    # ICD9 codes 
    if(icd9_codes!=''):
        icd9_list=""
        icd9_list=((icd9_codes).replace(',', ' AND icd9_codes:'))
        if (query!=""):
            query= query+" AND icd9_codes:"+ str(icd9_list)
        else:
            query= query+" icd9_codes:"+ str(icd9_list)
        print(icd9_codes)
        
     # Start and end data  

    if(start_date!='' and end_date!=''):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        if (query!=""):
            date_str= f' AND chart_date:[{start_date.isoformat()}Z TO {end_date.isoformat()}Z]'
        else:
            date_str= f' chart_date:[{start_date.isoformat()}Z TO {end_date.isoformat()}Z]'
        query=query+date_str
    elif(start_date!=''):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if (query!=""):
                    date_str= f' AND chart_date:[{start_date.isoformat()}Z TO *]'
            else:
                date_str= f' chart_date:[{start_date.isoformat()}Z TO *]'
            query=query+date_str
    elif(end_date!=''):      
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        if (query!=""):
            date_str= f' AND chart_date:[* TO {end_date.isoformat()}Z]'
        else:
            date_str= f' chart_date:[* TO {end_date.isoformat()}Z]'
        query=query+date_str

    params = {
    'hl': 'true',
    'hl.simple.pre': '<strong>',
    'hl.simple.post': '</strong>',
    'hl.fl': 'note_text',
    'hl.snippets': 3,
    'rows': 20
    }
    # SOLR search
    results = solr.search(query, **params)
    id_list=[]
    
     # Result format
    for result in results:
        if len(results)==0:
            results= range(0,10)
            data = [{'id': '','note_text':'','hadm_id': '','hospital_expire_flag': '',
            'icd9_codes': '','chart_date':'','synonyms':  '',
             'Num_results':"No Notes found, enter different query",
             'solr_query': query,
              'id_list': 'NA'
            }]
        else:
            for result in results:
                id_list.append(result['id'])
                #if len(id_list)==10:
                    #break
                data = [{'id': result['id'],'note_text': result['note_text'],
                    'hadm_id': result['hadm_id'],'hospital_expire_flag': result['hospital_expire_flag'],
                    'icd9_codes': result['icd9_codes'],'chart_date':result['chart_date'],'synonyms':  synonms,
                     'Num_results':len(results),'solr_query': query,'id_list': id_list
                }]
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)