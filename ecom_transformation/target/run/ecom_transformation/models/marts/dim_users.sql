
  
    

    create or replace table `ecom-data-pipeline-501504`.`silver_layer`.`dim_users`
      
    
    

    
    OPTIONS()
    as (
      
SELECT * FROM `ecom-data-pipeline-501504`.`silver_layer`.`stg_users`
    );
  