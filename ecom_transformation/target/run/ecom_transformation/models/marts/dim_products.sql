
  
    

    create or replace table `ecom-data-pipeline-501504`.`silver_layer`.`dim_products`
      
    
    

    
    OPTIONS()
    as (
      
SELECT * FROM `ecom-data-pipeline-501504`.`silver_layer`.`stg_products`
    );
  