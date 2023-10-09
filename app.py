import os
from flask import Flask, render_template, request, redirect, url_for
from google.cloud import bigquery
from google.oauth2 import service_account

app = Flask(__name__)

@app.route('/')
def index():
    key_path = "credentials.json"

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    query = """
            select num, datetime, lat, lon
            from `progetto-pcsc.dataset.tabella` t1
            where datetime = (select max(datetime) from `progetto-pcsc.dataset.tabella` t2 where t1.num = t2.num)
            group by num, datetime, lat, lon
        """

    query_job = client.query(query)  # Make an API request.

    geo = []
    for row in query_job:
        geo.append([row[0], row[2], row[3]])

    return render_template('index.html', geo=geo)

@app.route('/track', methods=['GET', 'POST'])
def track():
    key_path = "credentials.json"

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    query = """
        select distinct num
        from `progetto-pcsc.dataset.tabella` t1
    """
    query_job = client.query(query)  # Make an API request.

    taxi_list = []
    for row in query_job:
        taxi_list.append(row[0])

    if request.method == 'POST':
        selected_taxi = request.form['taxi']
        return redirect(url_for('display_taxi', taxi=selected_taxi))
    return render_template('track.html', taxi_list=taxi_list)

@app.route('/display/<taxi>')
def display_taxi(taxi):
    key_path = "credentials.json"

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    job_config = bigquery.QueryJobConfig()
    query = """
            select datetime, lat, lon
            from `progetto-pcsc.dataset.tabella` t1
            where num = @num
            ORDER BY TIMESTAMP(datetime)
        """

    query_parameters = [
        bigquery.ScalarQueryParameter('num', 'INT64', int(taxi))
    ]

    job_config.query_parameters = query_parameters
    query_job = client.query(query, job_config=job_config)

    results = query_job.result()
    geo = []
    for row in results:
        geo.append([row[1], row[2]])
    print(geo)

    return render_template('display_taxi.html', taxi=taxi, geo=geo)

# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')

