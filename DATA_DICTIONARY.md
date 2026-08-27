# Project 2 Data Dictionary

## stores.csv
store_id, store_name, region, city, latitude, longitude, store_tier, storage_capacity_sqft, opening_date

## customers.csv
customer_id, region, city, latitude, longitude, signup_date, preferred_channel

## products.csv
product_id, product_name, category, subcategory, selling_price, unit_cost, abc_class, storage_type

## orders.csv
order_id, customer_id, store_id, order_datetime, order_status, payment_method, delivery_distance_km, delivery_type

## order_items.csv
order_id, line_number, product_id, quantity, unit_price, line_revenue

## inventory_snapshots.csv
store_id, product_id, snapshot_date, stock_on_hand, estimated_weekly_demand, stockout_flag, last_restock_date, units_received
