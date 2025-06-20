records = LOAD '/output/cleaned_records'
    USING PigStorage(',')
    AS (
        uuid:chararray,
        type:chararray,
        city:chararray,
        street:chararray,
        timestamp:long
    );

-- 2. Métrica: Total de incidentes por comuna
by_city = GROUP records BY city;
city_metrics = FOREACH by_city GENERATE
    group AS city,
    COUNT(records) AS total_incidents;

STORE city_metrics INTO '/output/analysis_by_city' USING PigStorage(',');

-- 3. Métrica: Total de incidentes por tipo
by_type = GROUP records BY type;
type_metrics = FOREACH by_type GENERATE
    group AS type,
    COUNT(records) AS total_incidents;

STORE type_metrics INTO '/output/analysis_by_type' USING PigStorage(',');

-- 4. Métrica: Total por tipo y comuna
by_type_city = GROUP records BY (type, city);
type_city_metrics = FOREACH by_type_city GENERATE
    FLATTEN(group) AS (type, city),
    COUNT(records) AS total_incidents;

STORE type_city_metrics INTO '/output/analysis_by_type_city' USING PigStorage(',');

-- 5. Métrica: Total por calle y comuna
by_street_city = GROUP records BY (street, city);
street_city_metrics = FOREACH by_street_city GENERATE
    FLATTEN(group) AS (street, city),
    COUNT(records) AS total_incidents;

STORE street_city_metrics INTO '/output/analysis_by_street_city' USING PigStorage(',');

-- 6. Métrica: Incidentes por día (dividiendo timestamp en milisegundos por 86.400.000)
by_day = FOREACH records GENERATE
    (long)(timestamp / 86400000) AS day_epoch,
    type,
    city;

group_by_day = GROUP by_day BY day_epoch;
day_metrics = FOREACH group_by_day GENERATE
    group AS day_epoch,
    COUNT(by_day) AS total_incidents;

STORE day_metrics INTO '/output/analysis_by_day' USING PigStorage(',');
