{{ config(materialized='view') }}

WITH source_data AS (
    SELECT * FROM {{ source('bronze_layer', 'raw_carts') }}
),

flattened_data AS (
    SELECT
        CAST(transaction_id AS STRING) AS cart_id,
        CAST(user_id AS STRING) AS user_id,
        CAST(item.product_id AS STRING) AS product_id,
        
        is_anomalous,
        
        gmt_create AS transaction_date,
        
        PARSE_DATE('%Y%m%d', CAST(dt AS STRING)) AS batch_ingestion_date,
        
        item.quantity AS item_quantity,
        CAST(REPLACE(item.price, ' USD', '') AS FLOAT64) AS item_price
        
    FROM source_data,
    UNNEST(items) AS item 
),

deduplicated AS (
    SELECT
        *,
        -- drop duplicate per transaction
        ROW_NUMBER() OVER(
            PARTITION BY cart_id, product_id 
            ORDER BY batch_ingestion_date DESC
        ) AS row_num
    FROM flattened_data
    WHERE item_quantity > 0
)

SELECT
    cart_id,
    user_id,
    product_id,
    item_price,
    item_quantity,
    transaction_date,
    batch_ingestion_date,
    is_anomalous,
    (item_price * item_quantity) AS total_value
FROM deduplicated
WHERE row_num = 1
