

  create or replace view `ecom-data-pipeline-501504`.`silver_layer`.`stg_products`
  OPTIONS()
  as 

WITH source_data AS (
    SELECT * FROM `ecom-data-pipeline-501504`.`bronze_layer`.`raw_products`
)

SELECT
    CAST(id AS STRING) AS product_id,  
    title AS product_name,
    CAST(price AS FLOAT64) AS standard_price,
    category
FROM source_data;

