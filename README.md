# Tarea-3-Sistemas-Distribuidos

## Aaron Pozas Oyarce - Diego Pérez Carrasco

Este proyecto está organizado en carpetas principales:

1. **map-scraper**: Contiene un script que realiza scraping de datos desde Waze. Este script extrae información relevante y manda las alertas hacia la base de datos.

2. **bdd**: Incluye un servidor que consume los datos del scraper y lo utiliza para procesar o mostrar los datos.

3. **mongo-exporter**: Carpeta que tiene todo lo relacionado al exportador de mongo. Su función principal es tomar los datos de MongoDB y transformarlos a un CSV legible para Pig.

4. **hadoop-pig**: Carpeta contenedora del grueso de la entrega, contiene archivos de configuración, Dockerfile, entrypoint.sh y dos script que en su conjunto levantan el servicio, consumen el CSV generado y posteriormente el filtrado y procesamiento de los datos.

5. **redis-cache**: En este apartado se encuentra el código relacionado al cache, para lograr poblar el cache se hace una consulta al indice de Elastic llamado process_data el cual ya tiene la data procesada por Pig, las consultas más frecuentes se suben al cache. Para poder visualizar el cache se invita a observar redisinsight en el localhost:5540 -> es aquí en donde se pueden observar las consultas que están en cache.

6. **csv-loader-elastic**: Acá se suben los CSV correspondites a la data bruta (datos_clean.csv) que vienen directo desde MongoDB y luego al inicializar los contenedores se generará otro output llamado processed_data proveniente de Hadoop-Pig, ambos CSV se suben en indices distintos a Elastic.

7. **Elastic y Kibana**: Si bien no hay carpetas relacionado a este contenedor, las imagenes están en docker-compose. Se siguío al pie de la letra la documentación misma de elastic (https://www.elastic.co/blog/getting-started-with-the-elastic-stack-and-docker-compose). Para poder observar los indices entrar a localhost:5601.

8. **data**: Este volumen compartido es parte de todos los contenedores, principalmente fue usado para la creación del pipeline para poder exportar/importar cada archivo a su respectivo contenedor.

Además, el proyecto incluye un archivo `docker-compose.yml` que configura y levanta los contenedores de todos estos modulos. Solo es necesario el comando de más abajo para levantar el proyecto.

Dentro del docker-compose.yml se encuentran todos los contenedores y asociaciones a los dockerfile correspondientes.

## Instrucciones para inicializar el proyecto

1. Para levantar los contenedores definidos en el archivo `docker-compose.yml`:

   ```bash
   docker-compose up --build
   ```

2. Una vez arriba los contenedores todo comenzará de forma automática, se inicializará MongoDB asi como tambien mongo-express (**waze_db** en http://localhost:8081 - admin:pass). Si es primera vez que se inicia y no hay datos en MongoDB ni tampoco el archivo creado el contenedor de mongo-exporter y hadoop-pig esperarán hasta que primero hayan datos en la base de datos y segundo esté disponible el archivo (el tiempo de scrapeo puede variar según PC y recursos) para esta implementación se dejo un archivo en el volumen compartido data un CSV con datos de muestra. Luego de eso se generará el CSV y se subirá a Hadoop, con ello comenzará el primer script de filtrado y normalización, posterior a eso el segundo script de procesamiento de los datos. Al final de la consola se podrán ver los datos procesados.

3. Para ingresar y ver el estado de Hadoop puede utilizar http://localhost:50070 y para observar el estado, rendimiento, métricas y demás de Hadoop y YARN utilizar http://localhost:8088.
