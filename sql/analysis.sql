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
    p.product_id,
    p.product_name,
    SUM(o.line_revenue) AS total_revenue
FROM order_items o
JOIN products p
    ON o.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name
ORDER BY total_revenue DESC;


WITH revenue_calculation AS	 (
	SELECT SUM(line_revenue) AS total_revenue
	FROM order_items
),
cogs_calculation AS (
	SELECT SUM(o.quantity * p.unit_cost) AS total_cogs
	FROM order_items o
	JOIN products p
	ON o.product_id = p.product_id
)
SELECT
	r.total_revenue,
	c.total_cogs,
	(r.total_revenue - c.total_cogs) as profit
FROM revenue_calculation r
CROSS JOIN cogs_calculation c;


SELECT p.product_id, 
		p.product_name, 
		SUM(oi.line_revenue) as total_revenue, 
		SUM(oi.quantity * p.unit_cost) as total_cogs,
		SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost) as total_profit,
		ROUND(((SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost)) / (SUM(oi.line_revenue))) * 100, 2) as profit_margin
FROM products p
JOIN order_items oi
	ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
ORDER BY profit_margin DESC;

-- staging table for products as we found standardization issue in csv file

CREATE TABLE products_stage (
    product_id VARCHAR(10),
    product_name VARCHAR(100),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    selling_price NUMERIC(10,2),
    unit_cost NUMERIC(10,2),
    abc_class VARCHAR(1),
    storage_type VARCHAR(20)
);

UPDATE products p
SET category = s.category
FROM products_stage s
WHERE p.product_id = s.product_id;

DROP TABLE products_stage; 

SELECT p.category, 
		SUM(oi.line_revenue) as total_revenue, 
		SUM(oi.quantity * p.unit_cost) as total_cogs,
		SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost) as total_profit,
		ROUND(((SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost)) / (SUM(oi.line_revenue))) * 100, 2) as profit_margin
FROM products p
JOIN order_items oi
	ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY profit_margin DESC;



SELECT s.store_id, s.store_name, SUM(oi.line_revenue) as total_revenue
FROM stores s
JOIN orders o
	ON s.store_id = o.store_id
JOIN order_items oi
	ON o.order_id = oi.order_id
GROUP BY s.store_id, s.store_name
ORDER BY total_revenue DESC;



SELECT s.store_id, s.store_name, 
		SUM(oi.line_revenue) as total_revenue, 
		SUM(oi.quantity * p.unit_cost) as total_cogs,
		SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost) as total_profit,
		ROUND(((SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost)) / (SUM(oi.line_revenue))) * 100, 2) as profit_margin
FROM stores s
JOIN orders o
	ON s.store_id = o.store_id
JOIN order_items oi
	ON o.order_id = oi.order_id
JOIN products p
	ON oi.product_id = p.product_id
WHERE o.order_status = 'Completed'
GROUP BY s.store_id, s.store_name
ORDER BY total_profit DESC;


WITH order_counts AS (
    SELECT 
        COUNT(order_id) AS total_orders,
        SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
    FROM orders
)
SELECT 
    total_orders,
    cancelled_orders,
    ROUND(cancelled_orders * 100.0 / total_orders, 2) AS cancellation_rate_percentage
FROM order_counts;


WITH order_counts AS (
    SELECT
		s.store_id,
		s.store_name,
        COUNT(o.order_id) AS total_orders,
        SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
    FROM orders o
		JOIN stores s
			ON o.store_id = s.store_id
	GROUP BY s.store_id, s.store_name
)

SELECT
	store_id,
	store_name,
    total_orders,
    cancelled_orders,
    ROUND(cancelled_orders * 100.0 / total_orders, 2) AS cancellation_rate_percentage
FROM order_counts
ORDER BY cancellation_rate_percentage DESC;




SELECT 
		s.region,
		COUNT(DISTINCT o.order_id) as total_orders,
		SUM(oi.line_revenue) as total_revenue, 
		SUM(oi.quantity * p.unit_cost) as total_cogs,
		SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost) as total_profit,
		ROUND(((SUM(oi.line_revenue) - SUM(oi.quantity * p.unit_cost)) / (SUM(oi.line_revenue))) * 100, 2) as profit_margin
FROM stores s
JOIN orders o
	ON s.store_id = o.store_id
JOIN order_items oi
	ON o.order_id = oi.order_id
JOIN products p
	ON oi.product_id = p.product_id
WHERE o.order_status = 'Completed'
GROUP BY region
ORDER BY total_profit DESC;


SELECT
	DATE_TRUNC('month', o.order_datetime) AS month,
	COUNT(DISTINCT o.order_id) as total_orders,
	SUM(oi.line_revenue) as total_revenue
FROM orders o
JOIN order_items oi
	ON o.order_id = oi.order_id
WHERE o.order_status = 'Completed'
GROUP BY month
ORDER BY month;



WITH monthly_sales AS (
	SELECT 
		DATE_TRUNC('month', o.order_datetime) AS month,
		COUNT(DISTINCT o.order_id) AS total_orders,
		SUM(oi.line_revenue) AS total_revenue	
	FROM orders o
	JOIN order_items oi
		ON o.order_id = oi.order_id
	WHERE o.order_status = 'Completed'
	GROUP BY month
),
previous_month_sales AS (
    SELECT
        month,
        total_orders,
        total_revenue,
        LAG(total_revenue) OVER (ORDER BY month) AS previous_month_revenue,
		LAG(total_orders) OVER (ORDER BY month) AS previous_month_orders
    FROM monthly_sales
)
SELECT
	pms.month,
	pms.total_orders,
	pms.total_revenue,
	pms.previous_month_revenue,
	pms.previous_month_orders,
	ROUND(((pms.total_revenue - pms.previous_month_revenue) * 100) / (pms.previous_month_revenue), 2) AS MoM_growth,
	ROUND((pms.total_revenue / pms.total_orders), 2) AS average_order_value,
	ROUND(((pms.total_orders - pms.previous_month_orders) * 100 / pms.previous_month_orders), 2) AS MoM_order_growth
FROM previous_month_sales pms
ORDER BY pms.month
;


SELECT 
	o.customer_id,
	c.city,
	c.region,
	COUNT(DISTINCT o.order_id) as total_orders, 
	SUM(oi.line_revenue) as total_revenue
FROM order_items oi
JOIN orders o
	ON oi.order_id = o.order_id
JOIN customers c
	ON o.customer_id = c.customer_id
WHERE o.order_status = 'Completed'
GROUP BY o.customer_id, c.city, c.region
ORDER BY total_revenue DESC;




WITH customer_sales AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.line_revenue) AS total_revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY o.customer_id
),
customer_tiers AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,
        CASE
            WHEN total_orders = 1 THEN 'One-time'
            ELSE 'Repeat'
        END AS customer_type
    FROM customer_sales
),
customer_type_summary AS (
    SELECT
        customer_type,
        COUNT(*) AS customer_count,
        SUM(total_revenue) AS total_revenue,
        ROUND(AVG(total_revenue), 2) AS average_revenue_per_customer
    FROM customer_tiers
    GROUP BY customer_type
)
SELECT
    customer_type,
    customer_count,
    total_revenue,
    average_revenue_per_customer,
    ROUND(
        total_revenue * 100.0
        / SUM(total_revenue) OVER (),
        2
    ) AS revenue_contribution_percentage
FROM customer_type_summary
ORDER BY total_revenue DESC;
	
	

WITH customer_sales AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.line_revenue) AS total_revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY o.customer_id
),
customer_tiers AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,
		CASE
		    WHEN total_orders = 1 THEN 'One-time'
		    WHEN total_orders BETWEEN 2 AND 3 THEN 'Low-frequency repeat'
		    WHEN total_orders BETWEEN 4 AND 6 THEN 'Medium-frequency repeat'
		    ELSE 'High-frequency repeat'
		END AS customer_type
    FROM customer_sales
)
SELECT
	customer_type,
	COUNT(*) AS customer_count,
	SUM(total_revenue) AS total_revenue,
    ROUND(AVG(total_revenue), 2) AS average_revenue_per_customer
FROM customer_tiers
GROUP BY customer_type;


WITH customer_sales AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.line_revenue) AS total_revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY o.customer_id
),
customer_ranked AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,
        NTILE(10) OVER (
            ORDER BY total_revenue DESC
        ) AS revenue_decile
    FROM customer_sales
)
SELECT
	customer_id,
	total_orders,
	total_revenue
FROM customer_ranked
WHERE revenue_decile = 1
ORDER BY total_revenue DESC;
