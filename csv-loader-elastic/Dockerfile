FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY load_csv.py .

CMD ["python", "-u", "load_csv.py"]
