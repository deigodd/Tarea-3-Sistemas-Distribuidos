FROM python:3.10-slim

WORKDIR /app

COPY mongo_to_csv.py .

RUN pip install pymongo pandas

CMD ["python", "mongo_to_csv.py"]
