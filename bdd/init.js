// Init de la base de datos
const fs = require("fs");

const rawData = fs.readFileSync("/data/map-scraper/alertas.json");
const alertas = JSON.parse(rawData);

db = db.getSiblingDB("waze_alertas");
db.alertas.insertMany(alertas);
