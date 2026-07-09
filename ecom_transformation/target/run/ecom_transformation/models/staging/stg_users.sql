

  create or replace view `ecom-data-pipeline-501504`.`silver_layer`.`stg_users`
  OPTIONS()
  as 

WITH source_data AS (
    SELECT * FROM `ecom-data-pipeline-501504`.`bronze_layer`.`raw_users`
)

SELECT
    CAST(id AS STRING) AS user_id,    
    username,
    email,
    CONCAT(name.firstname, ' ', name.lastname) AS full_name,
    address.city AS city
FROM source_data;

