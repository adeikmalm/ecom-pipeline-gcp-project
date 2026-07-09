
  
    

    create or replace table `ecom-data-pipeline-501504`.`silver_layer`.`dm_daily_sales_performance`
      
    
    

    
    OPTIONS()
    as (
      

WITH fact_carts AS (
    SELECT * FROM `ecom-data-pipeline-501504`.`silver_layer`.`stg_carts` WHERE is_anomalous = FALSE
),
dim_products AS (
    SELECT * FROM `ecom-data-pipeline-501504`.`silver_layer`.`stg_products`
),
dim_users AS (
    SELECT * FROM `ecom-data-pipeline-501504`.`silver_layer`.`stg_users`
)

SELECT
    EXTRACT(DATE FROM c.transaction_date) AS report_date,
    p.category AS product_category,
    u.city AS user_city,
    
    COUNT(DISTINCT c.cart_id) AS total_orders,
    COUNT(DISTINCT c.user_id) AS total_active_buyers,
    
    SUM(c.total_value) AS total_revenue,
    SUM(c.item_quantity) AS total_items_sold,
    
    ROUND(SAFE_DIVIDE(SUM(c.total_value), COUNT(DISTINCT c.cart_id)), 2) AS average_order_value

FROM fact_carts c
LEFT JOIN dim_products p ON c.product_id = p.product_id
LEFT JOIN dim_users u ON c.user_id = u.user_id
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 6 DESC
    );
  