#!/bin/bash

# Configuración de las env
HADOOP_HOME=/opt/hadoop
PIG_HOME=/opt/pig
DATA_DIR=/data
HDFS_INPUT=/input
HDFS_OUTPUT=/output
PIG_SCRIPT=/scripts/process_waze_alerts.pig
PIG_SCRIPT2=/scripts/processing.pig
CSV_FILE=datos_clean.csv
HDFS_FILE=waze_data.csv

# Iniciar servicios SSH y Hadoop
echo "⚙️ Iniciando servicios..."
echo "Iniciando SSH..."
sudo service ssh start

# (no tiene mucho sentido este paso porque por ahora no se guarda en volumen persistente)
echo "Verificando si es necesario formatear NameNode "
if [ ! -d "$HADOOP_HOME/data/namenode/current" ]; then
    $HADOOP_HOME/bin/hdfs namenode -format -force
fi

ssh-keyscan -H localhost >> ~/.ssh/known_hosts 2>/dev/null
ssh-keyscan -H 0.0.0.0 >> ~/.ssh/known_hosts 2>/dev/null

# iniciar servicios de Hadoop - importante -> ver logs en caso de falla
echo "Iniciando HDFS (start-dfs.sh)..."
$HADOOP_HOME/sbin/start-dfs.sh

echo "Iniciando YARN (start-yarn.sh)..."
$HADOOP_HOME/sbin/start-yarn.sh

echo "⏳ Esperando inicialización de HDFS..."
sleep 10

# Configurar estructura HDFS - básicamente se crean los directorios de entrada y salida para los datos
echo "📚 Configurando estructura HDFS..."
$HADOOP_HOME/bin/hdfs dfs -mkdir -p $HDFS_INPUT
$HADOOP_HOME/bin/hdfs dfs -mkdir -p $HDFS_OUTPUT
$HADOOP_HOME/bin/hdfs dfs -chmod -R 755 $HDFS_INPUT
$HADOOP_HOME/bin/hdfs dfs -chmod -R 755 $HDFS_OUTPUT

# Esperar y verificar archivo CSV
echo "🔍 Esperando archivo CSV..."
while [ ! -f "$DATA_DIR/$CSV_FILE" ]; do
    echo "⏳ Esperando que $CSV_FILE esté disponible..."
    sleep 15
done

# Subir archivo a HDFS con reintentos
MAX_RETRIES=3
RETRY_COUNT=0
UPLOAD_SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$UPLOAD_SUCCESS" = false ]; do
    echo "⬆️ Subiendo archivo a HDFS (Intento $((RETRY_COUNT+1))/$MAX_RETRIES)..."

    $HADOOP_HOME/bin/hdfs dfs -put -f $DATA_DIR/$CSV_FILE $HDFS_INPUT/$HDFS_FILE

    if [ $? -eq 0 ]; then
        HDFS_SIZE=$($HADOOP_HOME/bin/hdfs dfs -du -s $HDFS_INPUT/$HDFS_FILE | awk '{print $1}')
        LOCAL_SIZE=$(du -b $DATA_DIR/$CSV_FILE | awk '{print $1}')

        if [ "$HDFS_SIZE" -eq "$LOCAL_SIZE" ]; then
            echo "✓ Archivo subido correctamente ($HDFS_SIZE bytes)"
            UPLOAD_SUCCESS=true
        else
            echo "✗ Los tamaños no coinciden (HDFS: $HDFS_SIZE vs Local: $LOCAL_SIZE)"
        fi
    else
        echo "✗ Falló el intento $((RETRY_COUNT+1))"
    fi

    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 5
done

if [ "$UPLOAD_SUCCESS" = false ]; then
    echo "✗ Error: No se pudo subir el archivo después de $MAX_RETRIES intentos"
    exit 1
fi

# Configurar entorno Pig y rutas para este
export PIG_CLASSPATH=$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/yarn/*

# Esperar que YARN esté listo
echo "⏳ Esperando que YARN esté listo..."
until $HADOOP_HOME/bin/yarn node -list 2>/dev/null | grep -q "RUNNING"; do
    sleep 5
done

echo "📄 Listado del archivo en HDFS:"
$HADOOP_HOME/bin/hdfs dfs -ls $HDFS_INPUT/$HDFS_FILE

echo "Iniciando JobHistory Server..."
$HADOOP_HOME/sbin/mr-jobhistory-daemon.sh start historyserver

# Ejecutar script Pig - este es el procesamiento de los datos
echo "🐷 Ejecutando script Pig para la filtración y homogeneización de los datos"
$PIG_HOME/bin/pig -f $PIG_SCRIPT


echo "Subiendo cleaned_records al HDFS..."

$HADOOP_HOME/bin/hdfs dfs -rm -r /input/cleaned_records

$HADOOP_HOME/bin/hdfs dfs -put /output/cleaned_records /input/

$HADOOP_HOME/bin/hdfs dfs -ls /input/cleaned_records

# Ejecutar segundo script Pig - acá es el análisis de los datos
echo "🐷 Ejecutando el segundo script Pig para el procesamiento de los datos"
sleep 5
$PIG_HOME/bin/pig -f $PIG_SCRIPT2

# acá se hace cat de los outputs de Pig
echo "Se inicia el cat de los outputs de Pig"

echo "Resultados del primer script Pig (filtrado y homogeneización):"
cat /output/cleaned_records/part-r-00000
sleep 5

echo "Resultados del segundo script Pig (análisis de datos):"
echo "Primero el analisis por comuna"
cat /output/analysis_by_city/part-r-00000
sleep 5

echo "Ahora el analisis por hora (los dias estan en epoch)"
cat /output/analysis_by_day/part-r-00000
sleep 5

echo "Ahora el analisis por calle y comuna"
cat /output/analysis_by_street_city/part-r-00000
sleep 5

echo "Ahora el analisis por tipo de alerta"
cat /output/analysis_by_type/part-r-00000
sleep 5

echo "Ahora el analisis por tipo de alerta y comuna"
cat /output/analysis_by_type_city/part-r-00000
sleep 5

# Mantener contenedor activo - esto para poder ver el output mas que nada
# echo "✓ Procesamiento completado. Contenedor activo..."
# tail -f /dev/null ----> esto para mantener el contenedor activo

# Finalizar el contenedor
echo "✓ Procesamiento completado. Contenedor finalizado."