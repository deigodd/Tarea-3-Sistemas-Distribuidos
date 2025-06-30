FROM python:3.9-slim

WORKDIR /usr/src/app

RUN apt update && apt install -y iputils-ping

COPY cache.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "cache.py"]
