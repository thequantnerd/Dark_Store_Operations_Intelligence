CREATE TABLE products (
    product_id VARCHAR(10) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50) NOT NULL,
    selling_price NUMERIC(10,2) NOT NULL,
    unit_cost NUMERIC(10,2) NOT NULL,
    abc_class VARCHAR(1) NOT NULL,
    storage_type VARCHAR(20) NOT NULL
);

CREATE TABLE stores (
    store_id VARCHAR(10) PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    latitude NUMERIC(10,6) NOT NULL,
    longitude NUMERIC(10,6) NOT NULL,
    store_tier VARCHAR(20) NOT NULL,
    storage_capacity_sqft INTEGER NOT NULL,
    opening_date DATE NOT NULL
);

CREATE TABLE customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    region VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    latitude NUMERIC(10,6) NOT NULL,
    longitude NUMERIC(10,6) NOT NULL,
    signup_date DATE NOT NULL,
    preferred_channel VARCHAR(20) NOT NULL
);

CREATE TABLE orders (
    order_id VARCHAR(10) PRIMARY KEY,
    customer_id VARCHAR(10) NOT NULL,
    store_id VARCHAR(10) NOT NULL,
    order_datetime TIMESTAMP NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    delivery_distance_km NUMERIC(10,2) NOT NULL,
    delivery_type VARCHAR(20) NOT NULL,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_orders_store
        FOREIGN KEY (store_id)
        REFERENCES stores(store_id)
);

CREATE TABLE order_items (
    order_id VARCHAR(10) NOT NULL,
    line_number INTEGER NOT NULL,
    product_id VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    line_revenue NUMERIC(10,2) NOT NULL,

    CONSTRAINT pk_order_items
        PRIMARY KEY (order_id, line_number),

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

CREATE TABLE inventory_snapshots (
    store_id VARCHAR(10) NOT NULL,
    product_id VARCHAR(10) NOT NULL,
    snapshot_date DATE NOT NULL,
    stock_on_hand INTEGER NOT NULL,
    estimated_weekly_demand INTEGER NOT NULL,
    stockout_flag INTEGER NOT NULL,
    last_restock_date DATE NOT NULL,
    units_received INTEGER NOT NULL,

    CONSTRAINT pk_inventory_snapshots
        PRIMARY KEY (store_id, product_id, snapshot_date),

    CONSTRAINT fk_inventory_store
        FOREIGN KEY (store_id)
        REFERENCES stores(store_id),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);


SELECT
    p.product_name, SUM(o.line_revenue) AS total_revenue
FROM order_items o
JOIN products p
	ON o.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_revenue DESC;








