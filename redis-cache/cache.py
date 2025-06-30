from elasticsearch import Elasticsearch
import redis
import json

es = Elasticsearch(['http://es01:9200'])
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

large_text = "x" * 50_000
INDEX_NAME = "processed_data"

def consultar_y_cachear():
    try:
        # 1. Agregación: tipo más frecuente por ciudad
        agg_query = {
            "size": 0,
            "aggs": {
                "cities": {
                    "terms": {"field": "city.keyword", "size": 10},
                    "aggs": {
                        "top_types": {
                            "terms": {"field": "type.keyword", "size": 1}
                        }
                    }
                }
            }
        }

        agg_response = es.search(index=INDEX_NAME, body=agg_query)

        city_type_pairs = []
        for bucket in agg_response['aggregations']['cities']['buckets']:
            city = bucket['key']
            if bucket['top_types']['buckets']:
                top_type = bucket['top_types']['buckets'][0]['key']
                city_type_pairs.append((city, top_type))

        print("🔍 Pares ciudad/tipo más frecuentes:")
        for city, top_type in city_type_pairs:
            print(f"  {city} → {top_type}")

        total = 0

        for city, top_type in city_type_pairs:
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"city.keyword": city}},
                            {"term": {"type.keyword": top_type}}
                        ]
                    }
                },
                "size": 100
            }

            result = es.search(index=INDEX_NAME, body=search_body)

            for hit in result['hits']['hits']:
                doc_id = hit['_id']
                source = hit['_source']
                source['extra_payload'] = large_text

                # 👇 Imprimir solo el primer documento antes de subir al cache
                if total == 0:
                    print(f"\n📦 Subiendo al cache [alert:{doc_id}]:")
                    print(json.dumps(source, indent=2, ensure_ascii=False))  # Imprime con indentación

                redis_client.set(f"alert:{doc_id}", json.dumps(source))
                total += 1

        print(f"\n✅ Total de documentos cacheados: {total}")

    except Exception as e:
        print(f"❌ Error en la consulta o cacheo: {e}")

if __name__ == '__main__':
    consultar_y_cachear()
