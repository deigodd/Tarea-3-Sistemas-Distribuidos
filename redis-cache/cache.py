from flask import Flask, request, jsonify
import redis
from pymongo import MongoClient
import os
import json  # Importa json para serialización y deserialización
from bson import ObjectId

app = Flask(__name__)

# Redis config
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# texto para ocupar más espacio en el cache, asi se llena más rapido
large_text = "x" * 50_000


# Mongo config
try:
    mongo_client = MongoClient('mongodb://admin:admin123@mongo:27017/')
    mongo_client.admin.command('ping')
    print("Conexión a MongoDB exitosa.")
except Exception as e:
    print(f"Error al conectar con MongoDB: {e}")
    raise

db = mongo_client['waze_db']
collection = db['alertas']

# endpoint principal para obtener alertas y cachear en redis
@app.route('/alerts', methods=['GET'])
def get_alerts():
    alert_id = request.args.get('id')
    if alert_id:
        key = f"alert:{alert_id}"
        cached = redis_client.get(key)

        if cached:
            return jsonify({"source": "cache", "data": json.loads(cached)})

        try:
            result = collection.find_one({"_id": ObjectId(alert_id)}, {"_id": 0})
            if result:
                result["extra_payload"] = large_text
                redis_client.set(key, json.dumps(result))
                return jsonify({"source": "mongo", "data": result})
            else:
                return jsonify({"error": "No se encontró el ID"}), 404
        except Exception as e:
            print(f"Error al buscar en MongoDB: {e}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Debe proporcionar 'id'"}), 400

# endpoint para obtener todas los ids para luego en el generador de requests elegir aleatoriamente
@app.route('/alerts/ids', methods=['GET'])
def get_all_ids():
    ids = collection.find({}, {"_id": 1}).limit(10000)
    id_list = [str(doc["_id"]) for doc in ids]
    return jsonify({"ids": id_list})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
