{{ config(materialized='view') }}

WITH source_data AS (
    SELECT * FROM {{ source('bronze_layer', 'raw_users') }}
)

SELECT
    CAST(id AS STRING) AS user_id,    
    username,
    email,
    CONCAT(name.firstname, ' ', name.lastname) AS full_name,
    address.city AS city
FROM source_data