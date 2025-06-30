from elasticsearch import Elasticsearch, helpers
import csv
import os
import sys
import time

# vairbales de entorno
es_host = os.getenv("ES_HOST", "es01")
es_port = int(os.getenv("ES_PORT", "9200"))
es_scheme = os.getenv("ES_SCHEME", "http")

# primero se consume  el raw_data y luego el processed_data
datasets = [
    {
        "csv_path": os.getenv("CSV_PATH_1", "datos_clean.csv"),
        "index_name": os.getenv("ES_INDEX_1", "raw_data")
    },
    {
       "csv_path": os.getenv("CSV_PATH_2", "data/processed_data.csv/part-r-00000"), # el part-r-00000 es el archivo generado por pig
        "index_name": os.getenv("ES_INDEX_2", "processed_data")
    }
]

fieldnames = [
    "uuid", "type", "city", "street", "speed", "reliability", "confidence", "country",
    "reportRating", "pubMillis", "additionalInfo", "fromNodeId", "id", "inscale",
    "magvar", "nComments", "nThumbsUp", "nearBy", "provider", "providerId",
    "reportBy", "reportByMunicipalityUser", "reportDescription", "reportMood",
    "roadType", "subtype", "toNodeId"
]

# conexión al elastic
es = Elasticsearch([{"host": es_host, "port": es_port, "scheme": es_scheme}], verify_certs=False)

try:
    resp = es.info()
    print(f"✅ Conectado con éxito al alestic")
except Exception as e:
    print(f"❌ Error conectando: {e}")
    sys.exit(1)

# verificación simple para saber si estan los archivos en la carpeta data
wait_time = 10
max_retries = 30

for dataset in datasets:
    retries = 0
    while not os.path.exists(dataset["csv_path"]):
        if retries >= max_retries:
            print(f"---- No se encontró el archivo después de esperar: {dataset['csv_path']}")
            sys.exit(1)
        print(f"---- Esperando archivo: {dataset['csv_path']}...")
        time.sleep(wait_time)
        retries += 1
    print(f"---- Archivo encontrado: {dataset['csv_path']}")

for dataset in datasets:
    csv_path = dataset["csv_path"]
    index_name = dataset["index_name"]

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
        print(f"indice '{index_name}' creado")
    else:
        print(f"El indice '{index_name}' ya existe")

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=fieldnames)
            actions = []
            for row in reader:
                clean_row = {k: v for k, v in row.items() if k.strip() != ""}
                actions.append({
                    "_index": index_name,
                    "_source": clean_row
                })

        success, failed = helpers.bulk(es, actions, raise_on_error=False)
        print(f"{success} documentos indexados correctamente en '{index_name}'.")
        if failed:
            print(f"{len(failed)} documentos fallaron en '{index_name}'. Ejemplo:")
            print(failed[:5])
    except Exception as e:
        print(f"Error durante la carga en '{index_name}': {e}")
        sys.exit(1)

    # esto igual se puede hacer manual pero así ta automatizado todo redi
    es.indices.refresh(index=index_name)
    print(f"Indice refrescado '{index_name}'")
