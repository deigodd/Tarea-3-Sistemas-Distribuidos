import os
import csv
from pymongo import MongoClient
import json
from datetime import datetime
import time
import logging
import sys

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

mongo_host = os.getenv("MONGO_HOST", "mongo")
mongo_db = os.getenv("MONGO_DB", "waze_db")
mongo_collection = os.getenv("MONGO_COLLECTION", "alertas")
mongo_user = os.getenv("MONGO_USER", "admin")
mongo_pass = os.getenv("MONGO_PASS", "admin123")

MAX_RETRIES = 10  # Número máximo de reintentos
RETRY_DELAY = 30  # Segundos entre reintentos

def connect_to_mongo():
    """Establece conexión con MongoDB con manejo de errores"""
    try:
        mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:27017/?authSource=admin&serverSelectionTimeoutMS=5000"
        client = MongoClient(mongo_uri, connectTimeoutMS=20000, socketTimeoutMS=None)
        client.admin.command('ping')
        logger.info("✅ Conexión a MongoDB establecida correctamente")
        return client
    except Exception as e:
        logger.error(f"⚠️ Error conectando a MongoDB: {str(e)}")
        return None

def normalize_field(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value).replace('"', '""').replace('\n', ' ').replace('\r', '')

def export_to_csv():
    retry_count = 0

    fieldnames = [
        'uuid', 'type', 'city', 'street', 'speed', 'reliability', 'confidence', 'country',
        'reportRating', 'pubMillis', 'additionalInfo', 'fromNodeId', 'id', 'inscale',
        'magvar', 'nComments', 'nThumbsUp', 'nearBy', 'provider', 'providerId', 'reportBy',
        'reportByMunicipalityUser', 'reportDescription', 'reportMood', 'roadType', 'subtype',
        'toNodeId'
    ]

    while retry_count < MAX_RETRIES:
        client = None
        try:
            logger.info(f"🔍 Intento {retry_count + 1}/{MAX_RETRIES}")

            client = connect_to_mongo()
            if client is None:
                raise ConnectionError("No se pudo conectar a MongoDB")

            db = client[mongo_db]
            collection = db[mongo_collection]

            count = collection.count_documents({})
            logger.info(f"📊 Documentos encontrados en MongoDB: {count}")

            if count == 0:
                logger.warning(f"⚠️ No hay datos en MongoDB. Reintentando en {RETRY_DELAY} segundos...")
                time.sleep(RETRY_DELAY)
                retry_count += 1
                continue

            data = list(collection.find({}, {"_id": 0}))

            csv_path = "/data/datos_clean.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                # writer.writerow(fieldnames) acá le saqué el encabezado
                for row in data:
                    try:
                        csv_row = []
                        for field in fieldnames:
                            value = row.get(field)
                            csv_row.append(normalize_field(value))
                        writer.writerow(csv_row)
                    except Exception as e:
                        logger.error(f"⚠️ Error procesando fila: {e}")
                        continue

            logger.info(f"✅ CSV generado exitosamente en {csv_path}")
            logger.info(f"📊 Registros exportados: {len(data)}")

            if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
                logger.info("✔️ Verificación: Archivo CSV creado correctamente")
                return True
            else:
                raise Exception("El archivo CSV no se creó correctamente")

        except Exception as e:
            logger.error(f"⚠️ Error durante la exportación: {str(e)}")
            retry_count += 1
            if retry_count < MAX_RETRIES:
                logger.info(f"🔄 Reintentando en {RETRY_DELAY} segundos...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"❌ Error: No se pudieron obtener datos después de {MAX_RETRIES} intentos")
        finally:
            if client:
                client.close()

    return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando script de exportación MongoDB a CSV")
    if export_to_csv():
        logger.info("🎉 Exportación completada con éxito")
        time.sleep(300)  # 5 minutos para inspección
    else:
        logger.error("💥 Fallo crítico en la exportación")
        time.sleep(600)  # 10 minutos para depuración