FROM mongo:latest

COPY init.js /docker-entrypoint-initdb.d/
COPY mongod.conf /etc/mongod.conf

CMD ["mongod", "--config", "/etc/mongod.conf"]