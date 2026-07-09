{{ config(materialized='view') }}

WITH source_data AS (
    SELECT * FROM {{ source('bronze_layer', 'raw_products') }}
)

SELECT
    CAST(id AS STRING) AS product_id,  
    title AS product_name,
    CAST(price AS FLOAT64) AS standard_price,
    category
FROM source_data