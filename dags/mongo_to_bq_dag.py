from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from datetime import datetime
import json

# Daftar collection yang akan ditarik
COLLECTIONS = ["carts", "users", "products"]
PROJECT_ID = "ecom-data-pipeline-501504" # Sesuaikan dengan Project ID GCP Anda
DATASET_ID = "bronze_layer"

def extract_mongo_data(collection_name, **context):
    print(f"Ekstraksi MongoDB untuk collection: {collection_name}")
    hook = MongoHook(mongo_conn_id='mongo_conn')
    client = hook.get_conn()
    db = client.oltp_ecommerce
    collection = db[collection_name]
    
    cursor = collection.find({}, {'_id': False})
    
    temp_path = f"/opt/airflow/dags/temp_{collection_name}.json"
    with open(temp_path, 'w') as f:
        for doc in cursor:
            f.write(json.dumps(doc) + '\n')
            
    return temp_path

def load_to_bq(collection_name, **context):
    from google.cloud import bigquery
    import os

    temp_path = f"/opt/airflow/dags/temp_{collection_name}.json"
    table_id = f"{PROJECT_ID}.{DATASET_ID}.raw_{collection_name}"
    
    # Membaca file gcp-key.json yang ada di dalam folder dags Docker
    key_path = "/opt/airflow/dags/gcp-key.json" 
    
    print(f"🚀 Memulai upload data dari {temp_path} ke {table_id}...")

    # Inisialisasi koneksi langsung ke BigQuery menggunakan file JSON rahasiamu
    client = bigquery.Client.from_service_account_json(key_path)

    # Konfigurasi upload data
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True, # Biarkan BQ menebak tipe datanya
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE, # Timpa data lama setiap kali narik baru
    )

    # Mengeksekusi pengiriman data
    with open(temp_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)

    job.result()  # Menunggu sampai proses upload BQ selesai 100%
    print(f"✅ Sukses! Sebanyak {job.output_rows} baris berhasil dimuat ke {table_id}")


default_args = {
    'owner': 'data_engineer',
    'start_date': datetime(2026, 1, 1),
}

with DAG('mongo_to_bq_dag', default_args=default_args, schedule_interval='@daily', catchup=False) as dag:
    
    for coll in COLLECTIONS:
        extract_task = PythonOperator(
            task_id=f'extract_{coll}',
            python_callable=extract_mongo_data,
            op_kwargs={'collection_name': coll}
        )
        
        load_task = PythonOperator(
            task_id=f'load_{coll}',
            python_callable=load_to_bq,
            op_kwargs={'collection_name': coll}
        )
        
        extract_task >> load_task