import pandas as pd
import numpy as np
import glob
import os


# ============================================================
# 1. LOAD RAW DATA
# ============================================================

# Find all CSV files inside the raw_data folder.
file_paths = glob.glob('./raw_data/*.csv')

# Store each CSV as a DataFrame inside a dictionary.
# Example:
# datasets['orders'] -> orders DataFrame
# datasets['products'] -> products DataFrame
datasets = {}

for file in file_paths:
    # Replace Windows backslashes with forward slashes so that
    # extracting the filename works consistently.
    clean_path = file.replace('\\', '/')

    # Extract the filename and remove the .csv extension.
    # Example: "./raw_data/orders.csv" -> "orders"
    file_name = clean_path.split('/')[-1].replace('.csv', '')

    datasets[file_name] = pd.read_csv(file)


# ============================================================
# 2. BASIC DATA PROFILING
# ============================================================

# Inspect the size, missing values, and complete duplicate rows
# for every table before making any cleaning decisions.
for name, df in datasets.items():

    print(f"\n{'=' * 50}")
    print(f"TABLE: {name}")
    print(f"{'=' * 50}")

    print(f"Shape: {df.shape}")

    print("\nMissing values:")
    print(df.isnull().sum())

    print(f"\nComplete duplicate rows: {df.duplicated().sum()}")


# ============================================================
# 3. DATA TYPES AND CARDINALITY
# ============================================================

# Review the data type of each column and the number of unique
# values. This helps identify incorrect types and suspicious
# categorical or identifier columns.
for name, df in datasets.items():

    print(f"\n{'=' * 50}")
    print(f"TABLE: {name}")
    print(f"{'=' * 50}")

    print("\nData types:")
    print(df.dtypes)

    print("\nUnique values:")
    print(df.nunique())


# ============================================================
# 4. PRIMARY KEY VALIDATION
# ============================================================

# A primary key should uniquely identify each record.
# Check whether any IDs expected to be primary keys are duplicated.
primary_keys = {
    'customers': 'customer_id',
    'orders': 'order_id',
    'products': 'product_id',
    'stores': 'store_id'
}

print(f"\n{'=' * 50}")
print("PRIMARY KEY CHECKS")
print(f"{'=' * 50}")

for table, key in primary_keys.items():

    duplicate_count = datasets[table][key].duplicated().sum()

    print(
        f"{table}.{key}: "
        f"{duplicate_count} duplicate primary-key values"
    )


# ============================================================
# 5. FOREIGN KEY VALIDATION
# ============================================================

# Foreign keys should reference an existing record in the parent table.
#
# Example:
# order_items.product_id should exist in products.product_id.
#
# An ID that appears in the child table but not the parent table
# is treated as an orphan foreign key.
foreign_keys = {
    'inventory_snapshots': {
        'store_id': ('stores', 'store_id'),
        'product_id': ('products', 'product_id')
    },
    'order_items': {
        'order_id': ('orders', 'order_id'),
        'product_id': ('products', 'product_id')
    },
    'orders': {
        'customer_id': ('customers', 'customer_id'),
        'store_id': ('stores', 'store_id')
    }
}

print(f"\n{'=' * 50}")
print("FOREIGN KEY CHECKS")
print(f"{'=' * 50}")

for table, columns in foreign_keys.items():

    for column, reference in columns.items():

        parent_table = reference[0]
        parent_column = reference[1]

        # True for rows whose foreign-key value does not exist
        # in the corresponding parent table.
        orphan_mask = ~datasets[table][column].isin(
            datasets[parent_table][parent_column]
        )

        orphan_count = orphan_mask.sum()

        # Display the actual invalid IDs as well as the number
        # of affected records.
        orphan_ids = datasets[table].loc[
            orphan_mask, column
        ].unique()

        print(
            f"{table}.{column} -> "
            f"{parent_table}.{parent_column}: "
            f"{orphan_count} orphan records | "
            f"Orphan IDs: {list(orphan_ids)}"
        )


# ============================================================
# 6. COMPOSITE KEY VALIDATION
# ============================================================

# Some tables require multiple columns together to uniquely
# identify one record.

# In order_items, one order can contain multiple lines.
# Therefore order_id + line_number should uniquely identify
# each order-item record.
duplicate_order_lines = datasets['order_items'].duplicated(
    subset=['order_id', 'line_number']
).sum()

print(
    "\nDuplicate order_id + line_number combinations:",
    duplicate_order_lines
)


# An inventory snapshot represents one product at one store
# on one specific snapshot date.
# Therefore store_id + product_id + snapshot_date should be unique.
duplicate_inventory_snapshots = datasets[
    'inventory_snapshots'
].duplicated(
    subset=['store_id', 'product_id', 'snapshot_date']
).sum()

print(
    "Duplicate store_id + product_id + snapshot_date combinations:",
    duplicate_inventory_snapshots
)


# ============================================================
# 7. ORDER ITEM BUSINESS-RULE VALIDATION
# ============================================================

# ------------------------------------------------------------
# 7.1 Quantity validation
# ------------------------------------------------------------

# An order-item quantity should be greater than zero.
print("\nORDER ITEM QUANTITY DISTRIBUTION")
print(datasets['order_items']['quantity'].describe())

invalid_quantity = datasets['order_items']['quantity'] <= 0

print(
    "Records with quantity <= 0:",
    invalid_quantity.sum()
)


# ------------------------------------------------------------
# 7.2 Unit-price validation
# ------------------------------------------------------------

# A normal product sale should have a positive unit price.
print("\nORDER ITEM UNIT PRICE DISTRIBUTION")
print(datasets['order_items']['unit_price'].describe())

invalid_price = datasets['order_items']['unit_price'] <= 0

print(
    "Records with unit_price <= 0:",
    invalid_price.sum()
)


# ------------------------------------------------------------
# 7.3 Line-revenue consistency
# ------------------------------------------------------------

# Business rule:
# line_revenue should equal quantity * unit_price.
#
# np.isclose() is used instead of == because floating-point
# calculations can contain tiny precision differences.
expected_revenue = (
    datasets['order_items']['quantity']
    * datasets['order_items']['unit_price']
)

line_revenue = datasets['order_items']['line_revenue']

revenue_mismatch = ~np.isclose(
    expected_revenue,
    line_revenue
)

print(
    "\nLine-revenue mismatches:",
    revenue_mismatch.sum()
)


# Check whether revenue mismatches are related to duplicate
# order-item business keys.
#
# keep=False marks BOTH the original and repeated rows belonging
# to a duplicated order_id + line_number group.
duplicate_lines = datasets['order_items'].duplicated(
    subset=['order_id', 'line_number'],
    keep=False
)

print(
    "Revenue mismatches that are also duplicate order lines:",
    (revenue_mismatch & duplicate_lines).sum()
)


# Inspect revenue-mismatch records and add the revenue that
# should have been produced by quantity * unit_price.
mismatch_df = datasets['order_items'][revenue_mismatch].copy()

mismatch_df['expected_revenue'] = expected_revenue[
    revenue_mismatch
]

print("\nREVENUE MISMATCH RECORDS")
print(mismatch_df)


# Determine whether the revenue inconsistencies are explained
# by records that already contain invalid quantity or price values.
mismatch_explained_by_invalid_inputs = (
    revenue_mismatch
    & (invalid_quantity | invalid_price)
)

print(
    "\nRevenue mismatches explained by invalid quantity/price:",
    mismatch_explained_by_invalid_inputs.sum()
)


# ============================================================
# 8. PRODUCT BUSINESS-RULE VALIDATION
# ============================================================

# Review selling-price and unit-cost distributions.
print("\nPRODUCT PRICE AND COST DISTRIBUTION")

print(
    datasets['products'][
        ['selling_price', 'unit_cost']
    ].describe()
)


# For this project, selling price is expected to be greater
# than unit cost so that the product has a positive gross margin.
price_cost_issue = (
    datasets['products']['selling_price']
    <= datasets['products']['unit_cost']
)

print(
    "Products with selling_price <= unit_cost:",
    price_cost_issue.sum()
)


# ============================================================
# 9. INVENTORY BUSINESS-RULE VALIDATION
# ============================================================

# ------------------------------------------------------------
# 9.1 Stock-on-hand validation
# ------------------------------------------------------------

# Physical stock cannot be negative.
# Zero stock is valid and represents no available inventory.
print("\nSTOCK-ON-HAND DISTRIBUTION")
print(
    datasets['inventory_snapshots']['stock_on_hand'].describe()
)

invalid_inventory_stock = (
    datasets['inventory_snapshots']['stock_on_hand'] < 0
)

print(
    "Records with negative stock_on_hand:",
    invalid_inventory_stock.sum()
)


# ------------------------------------------------------------
# 9.2 Estimated weekly demand validation
# ------------------------------------------------------------

# Demand may legitimately be zero, but it should not be negative.
print("\nESTIMATED WEEKLY DEMAND DISTRIBUTION")

print(
    datasets['inventory_snapshots'][
        'estimated_weekly_demand'
    ].describe()
)

invalid_weekly_demand = (
    datasets['inventory_snapshots'][
        'estimated_weekly_demand'
    ] < 0
)

print(
    "Records with negative estimated_weekly_demand:",
    invalid_weekly_demand.sum()
)


# ------------------------------------------------------------
# 9.3 Stockout-flag validation
# ------------------------------------------------------------

# First inspect the actual categories and their frequencies.
# stockout_flag is expected to contain only 0 and 1.
print("\nSTOCKOUT FLAG DISTRIBUTION")

print(
    datasets['inventory_snapshots'][
        'stockout_flag'
    ].value_counts()
)


# Project business rule:
# stock_on_hand <= 1 -> stockout_flag should be 1
# stock_on_hand > 1  -> stockout_flag should be 0
#
# The Boolean result is converted from True/False into 1/0.
expected_stockout_flag = (
    datasets['inventory_snapshots']['stock_on_hand'] <= 1
).astype(int)

stockout_mismatch = (
    expected_stockout_flag
    != datasets['inventory_snapshots']['stockout_flag']
)

print(
    "Stockout-flag inconsistencies:",
    stockout_mismatch.sum()
)


# Inspect the records where the stored stockout flag does not
# agree with the stock-on-hand business rule.
print("\nSTOCKOUT FLAG MISMATCH RECORDS")

print(
    datasets['inventory_snapshots']
    .loc[
        stockout_mismatch,
        [
            'store_id',
            'product_id',
            'snapshot_date',
            'stock_on_hand',
            'stockout_flag'
        ]
    ]
)


# ------------------------------------------------------------
# 9.4 Units-received validation
# ------------------------------------------------------------

# A store may receive zero units during a period,
# but units_received should never be negative.
print("\nUNITS RECEIVED DISTRIBUTION")

print(
    datasets['inventory_snapshots']['units_received'].describe()
)

invalid_units_received = (
    datasets['inventory_snapshots']['units_received'] < 0
)

print(
    "Records with negative units_received:",
    invalid_units_received.sum()
)


# ============================================================
# 10. DATE AND TEMPORAL VALIDATION
# ============================================================

# ------------------------------------------------------------
# 10.1 Inventory dates
# ------------------------------------------------------------

# Convert string dates into Pandas datetime values so that
# chronological comparisons can be performed.
snapshot_dates = pd.to_datetime(
    datasets['inventory_snapshots']['snapshot_date']
)

restock_dates = pd.to_datetime(
    datasets['inventory_snapshots']['last_restock_date']
)

print(
    "\nUnparseable snapshot dates:",
    snapshot_dates.isna().sum()
)

print(
    "Unparseable restock dates:",
    restock_dates.isna().sum()
)


# Business rule:
# The last restock cannot occur after the inventory snapshot.
restock_after_snapshot = (
    restock_dates > snapshot_dates
)

print(
    "Restocks occurring after snapshot date:",
    restock_after_snapshot.sum()
)


# Inspect the records violating the temporal rule.
print("\nRESTOCK DATE VIOLATIONS")

print(
    datasets['inventory_snapshots']
    .loc[
        restock_after_snapshot,
        [
            'store_id',
            'product_id',
            'snapshot_date',
            'last_restock_date'
        ]
    ]
)


# ------------------------------------------------------------
# 10.2 Order dates and customer signup dates
# ------------------------------------------------------------

# Confirm that order and customer signup dates can be parsed.
order_dates = pd.to_datetime(
    datasets['orders']['order_datetime']
)

signup_dates = pd.to_datetime(
    datasets['customers']['signup_date']
)

print(
    "\nUnparseable order dates:",
    order_dates.isna().sum()
)

print(
    "Unparseable customer signup dates:",
    signup_dates.isna().sum()
)


# Create a customer lookup containing the customer ID
# and converted signup date.
customer_signup = datasets['customers'][
    ['customer_id', 'signup_date']
].copy()

customer_signup['signup_date'] = pd.to_datetime(
    customer_signup['signup_date']
)


# Work on a copy so that the raw orders DataFrame remains unchanged.
orders_check = datasets['orders'].copy()

orders_check['order_datetime'] = pd.to_datetime(
    orders_check['order_datetime']
)


# LEFT JOIN customer signup dates onto orders using customer_id.
#
# A left join preserves every order. Orders whose customer_id
# does not exist in the customers table will receive a missing
# signup_date (NaT).
orders_check = orders_check.merge(
    customer_signup,
    on='customer_id',
    how='left'
)

print(
    "Orders without a matching customer signup date:",
    orders_check['signup_date'].isna().sum()
)


# Business rule:
# A customer should not place an order before their signup date.
#
# .notna() ensures that orphan customer records are not incorrectly
# treated as temporal violations.
orders_before_signup = (
    orders_check['signup_date'].notna()
    & (
        orders_check['order_datetime']
        < orders_check['signup_date']
    )
)

print(
    "Orders occurring before customer signup:",
    orders_before_signup.sum()
)


# Inspect a sample of the temporal violations.
print("\nSAMPLE ORDERS BEFORE CUSTOMER SIGNUP")

print(
    orders_check
    .loc[
        orders_before_signup,
        [
            'order_id',
            'customer_id',
            'order_datetime',
            'signup_date'
        ]
    ]
    .head(20)
)


# Compare the overall date ranges of customer signup dates
# and order dates to understand the temporal coverage.
print(
    "\nCustomer signup-date range:",
    datasets['customers']['signup_date'].min(),
    "to",
    datasets['customers']['signup_date'].max()
)

print(
    "Order-date range:",
    datasets['orders']['order_datetime'].min(),
    "to",
    datasets['orders']['order_datetime'].max()
)


# Inspect the most recent signup dates to determine whether
# late signup dates are concentrated or naturally distributed.
print("\nLATEST CUSTOMER SIGNUP DATES")

print(
    datasets['customers']['signup_date']
    .value_counts()
    .sort_index()
    .tail(20)
)


# ============================================================
# 11. CATEGORICAL VALIDATION
# ============================================================

# Categorical validation checks the actual values present in
# categorical columns and their frequencies.
#
# This helps identify unexpected labels, spelling inconsistencies,
# or categories outside the expected business domain.

print("\nORDER STATUS")
print(
    datasets['orders']['order_status'].value_counts()
)

print("\nPAYMENT METHOD")
print(
    datasets['orders']['payment_method'].value_counts()
)

print("\nDELIVERY TYPE")
print(
    datasets['orders']['delivery_type'].value_counts()
)

print("\nABC CLASS")
print(
    datasets['products']['abc_class'].value_counts()
)

print("\nSTORAGE TYPE")
print(
    datasets['products']['storage_type'].value_counts()
)



# ============================================================
# DATA CLEANING
# ============================================================

# Create a separate dictionary for cleaned datasets.
# The original "datasets" dictionary is preserved so that the
# raw data remains unchanged and can always be compared with
# the cleaned version.
cleaned_datasets = {}

for name, df in datasets.items():
    cleaned_datasets[name] = df.copy()


# ============================================================
# 1. CLEAN ORDER ITEMS
# ============================================================

# ------------------------------------------------------------
# 1.1 Remove complete duplicate records
# ------------------------------------------------------------

# Each order-item record should appear only once.
# Complete duplicate rows would cause the same item to be
# counted multiple times in revenue and product-level analysis.
cleaned_datasets['order_items'] = (
    cleaned_datasets['order_items']
    .drop_duplicates()
)


# ------------------------------------------------------------
# 1.2 Remove invalid quantities
# ------------------------------------------------------------

# A valid sales quantity must be greater than zero.
# Zero or negative quantities do not represent a normal
# completed sales line and cannot be reliably corrected.
invalid_quantity = (
    cleaned_datasets['order_items']['quantity'] <= 0
)

print(
    "Invalid quantity records:",
    invalid_quantity.sum()
)

# Remove only the invalid order-item records.
# The complete order is preserved because other line items
# belonging to the same order may still be valid.
cleaned_datasets['order_items'] = (
    cleaned_datasets['order_items']
    [~invalid_quantity]
)


# ------------------------------------------------------------
# 1.3 Remove invalid unit prices
# ------------------------------------------------------------

# A normal sales transaction must have a positive unit price.
# Negative or zero prices cannot be reliably corrected without
# knowing the intended transaction price.
invalid_price = (
    cleaned_datasets['order_items']['unit_price'] <= 0
)

print(
    "Invalid unit-price records:",
    invalid_price.sum()
)

# Remove only the affected order-item records.
cleaned_datasets['order_items'] = (
    cleaned_datasets['order_items']
    [~invalid_price]
)


# ------------------------------------------------------------
# 1.4 Remove orphan product references
# ------------------------------------------------------------

# Every product_id in order_items should exist in the products
# table. An unknown product cannot be reliably assigned to a
# category, cost, ABC class, or storage type.
orphan_product_mask = ~(
    cleaned_datasets['order_items']['product_id']
    .isin(
        cleaned_datasets['products']['product_id']
    )
)

print(
    "Orphan product records:",
    orphan_product_mask.sum()
)

# Remove the affected order-item records rather than guessing
# which product they represent.
cleaned_datasets['order_items'] = (
    cleaned_datasets['order_items']
    [~orphan_product_mask]
)


# ============================================================
# 2. CLEAN ORDERS
# ============================================================

# ------------------------------------------------------------
# 2.1 Remove orphan customer orders
# ------------------------------------------------------------

# Every customer_id in orders should exist in customers.
# An order referencing a nonexistent customer cannot participate
# correctly in customer-level analysis.
orphan_customer_mask = ~(
    cleaned_datasets['orders']['customer_id']
    .isin(
        cleaned_datasets['customers']['customer_id']
    )
)

print(
    "Orphan customer orders:",
    orphan_customer_mask.sum()
)


# Store the affected order IDs before removing the orders.
# These IDs are needed because order_items depends on orders
# through order_id.
orphan_order_ids = cleaned_datasets['orders'].loc[
    orphan_customer_mask,
    'order_id'
]


# Remove the orphan orders.
cleaned_datasets['orders'] = (
    cleaned_datasets['orders']
    [~orphan_customer_mask]
)


# ------------------------------------------------------------
# 2.2 Remove dependent order items
# ------------------------------------------------------------

# order_items contains a foreign key to orders.
# If an order is removed, its dependent order-item records
# must also be removed to maintain referential integrity.
orphan_order_items_mask = (
    cleaned_datasets['order_items']['order_id']
    .isin(orphan_order_ids)
)

cleaned_datasets['order_items'] = (
    cleaned_datasets['order_items']
    [~orphan_order_items_mask]
)


# ============================================================
# 3. CLEAN CUSTOMER DATA
# ============================================================

# ------------------------------------------------------------
# 3.1 Handle missing city values
# ------------------------------------------------------------

# City is missing for 45 customers.
# These customers still contain valid customer records and
# useful geographic coordinates, so the records should not
# be deleted.
#
# The coordinates cannot reliably distinguish individual cities
# in this synthetic dataset, so we do not invent city values.
# Instead, missing cities are explicitly labelled "Unknown".
cleaned_datasets['customers']['city'] = (
    cleaned_datasets['customers']['city']
    .fillna('Unknown')
)

# ============================================================
# 4. CLEAN INVENTORY SNAPSHOTS
# ============================================================

# ------------------------------------------------------------
# 4.1 Remove complete duplicate records
# ------------------------------------------------------------

# One inventory observation is identified by:
# store_id + product_id + snapshot_date.
#
# The duplicate composite-key records were also complete
# duplicates, so removing complete duplicates resolves both
# issues without discarding distinct inventory observations.
cleaned_datasets['inventory_snapshots'] = (
    cleaned_datasets['inventory_snapshots']
    .drop_duplicates()
)


# ------------------------------------------------------------
# 4.2 Remove negative stock values
# ------------------------------------------------------------

# Physical inventory cannot be negative.
# Negative stock values cannot be reliably corrected because
# the actual stock level is unknown.
invalid_inventory_stock = (
    cleaned_datasets['inventory_snapshots']['stock_on_hand'] < 0
)

print(
    "Negative stock records:",
    invalid_inventory_stock.sum()
)

cleaned_datasets['inventory_snapshots'] = (
    cleaned_datasets['inventory_snapshots']
    [~invalid_inventory_stock]
)


# ------------------------------------------------------------
# 4.3 Remove negative demand values
# ------------------------------------------------------------

# Estimated weekly demand can be zero or positive, but a
# negative demand value is not meaningful for this analysis.
# We therefore exclude the affected observations rather than
# replacing the value with an arbitrary estimate.
invalid_weekly_demand = (
    cleaned_datasets['inventory_snapshots']
    ['estimated_weekly_demand'] < 0
)

print(
    "Negative weekly-demand records:",
    invalid_weekly_demand.sum()
)

cleaned_datasets['inventory_snapshots'] = (
    cleaned_datasets['inventory_snapshots']
    [~invalid_weekly_demand]
)


# ------------------------------------------------------------
# 4.4 Remove invalid restock-date relationships
# ------------------------------------------------------------

# Convert date columns to datetime so that chronological
# comparisons can be performed reliably.
snapshot_dates = pd.to_datetime(
    cleaned_datasets['inventory_snapshots']['snapshot_date']
)

restock_dates = pd.to_datetime(
    cleaned_datasets['inventory_snapshots']['last_restock_date']
)


# A restock cannot occur after the inventory snapshot because
# the snapshot represents inventory as of that date.
restock_after_snapshot = (
    restock_dates > snapshot_dates
)

print(
    "Restock dates after snapshot:",
    restock_after_snapshot.sum()
)


# The correct restock date cannot be determined from the
# available data, so the affected observations are removed
# rather than assigning an arbitrary date.
cleaned_datasets['inventory_snapshots'] = (
    cleaned_datasets['inventory_snapshots']
    [~restock_after_snapshot]
)

# ------------------------------------------------------------
# 4.5 Standardize product category names
# ------------------------------------------------------------

# Check the distinct category values before standardization.
# This helps identify inconsistent capitalization or formatting.
print(
    "\nProduct categories before cleaning:"
)

print(
    cleaned_datasets['products']['category']
    .value_counts()
)

cleaned_datasets['products']['category'] = (
    cleaned_datasets['products']['category']
    .str.title()
)

print(
    "\nProduct categories after cleaning:"
)

print(
    cleaned_datasets['products']['category']
    .value_counts()
)


# ============================================================
# 5. FINAL VALIDATION
# ============================================================

# Final validation confirms that the cleaning operations
# successfully removed the identified data-quality problems
# without creating new relational inconsistencies.


# ------------------------------------------------------------
# 5.1 Final row counts
# ------------------------------------------------------------

print("\nFINAL ROW COUNTS")
print("-" * 40)

for name, df in cleaned_datasets.items():
    print(f"{name}: {len(df):,}")


# ------------------------------------------------------------
# 5.2 Final duplicate check
# ------------------------------------------------------------

print("\nFINAL DUPLICATE CHECK")
print("-" * 40)

for name, df in cleaned_datasets.items():
    print(
        f"{name}: "
        f"{df.duplicated().sum()} complete duplicates"
    )


# ------------------------------------------------------------
# 5.3 Final order-item validation
# ------------------------------------------------------------

print("\nFINAL ORDER ITEM CHECKS")
print("-" * 40)

print(
    "Invalid quantities:",
    (
        cleaned_datasets['order_items']['quantity'] <= 0
    ).sum()
)

print(
    "Invalid unit prices:",
    (
        cleaned_datasets['order_items']['unit_price'] <= 0
    ).sum()
)


# Recalculate expected revenue after cleaning.
expected_revenue = (
    cleaned_datasets['order_items']['quantity']
    * cleaned_datasets['order_items']['unit_price']
)

actual_revenue = (
    cleaned_datasets['order_items']['line_revenue']
)

# np.isclose() prevents tiny floating-point precision differences
# from being incorrectly treated as revenue errors.
revenue_mismatch = ~np.isclose(
    expected_revenue,
    actual_revenue
)

print(
    "Remaining revenue mismatches:",
    revenue_mismatch.sum()
)


# ------------------------------------------------------------
# 5.4 Final foreign-key validation
# ------------------------------------------------------------

print("\nFINAL FOREIGN KEY CHECKS")
print("-" * 40)

for table, columns in foreign_keys.items():

    for column, reference in columns.items():

        parent_table = reference[0]
        parent_column = reference[1]

        # Identify foreign-key values that do not exist
        # in the referenced parent table.
        orphan_mask = ~cleaned_datasets[table][column].isin(
            cleaned_datasets[parent_table][parent_column]
        )

        print(
            f"{table}.{column} -> "
            f"{parent_table}.{parent_column}: "
            f"{orphan_mask.sum()} orphan records"
        )


# ------------------------------------------------------------
# 5.5 Final inventory validation
# ------------------------------------------------------------

print("\nFINAL INVENTORY CHECKS")
print("-" * 40)

print(
    "Negative stock:",
    (
        cleaned_datasets['inventory_snapshots']
        ['stock_on_hand'] < 0
    ).sum()
)

print(
    "Negative weekly demand:",
    (
        cleaned_datasets['inventory_snapshots']
        ['estimated_weekly_demand'] < 0
    ).sum()
)

print(
    "Negative units received:",
    (
        cleaned_datasets['inventory_snapshots']
        ['units_received'] < 0
    ).sum()
)


# Verify that no restock date occurs after its snapshot date.
snapshot_dates = pd.to_datetime(
    cleaned_datasets['inventory_snapshots']['snapshot_date']
)

restock_dates = pd.to_datetime(
    cleaned_datasets['inventory_snapshots']['last_restock_date']
)

print(
    "Restock dates after snapshot:",
    (restock_dates > snapshot_dates).sum()
)


# ------------------------------------------------------------
# 5.6 Final missing-city validation
# ------------------------------------------------------------

print(
    "Missing customer cities:",
    cleaned_datasets['customers']['city'].isna().sum()
)

print(
    "Unknown customer cities:",
    (
        cleaned_datasets['customers']['city']
        == 'Unknown'
    ).sum()
)


# ============================================================
# 6. EXPORT CLEANED DATA
# ============================================================

# Create the clean_data directory if it does not already exist.
os.makedirs('./clean_data', exist_ok=True)


# Export each cleaned DataFrame as a CSV file.
#
# index=False prevents Pandas from writing the DataFrame index
# as an additional column in the CSV files.
for name, df in cleaned_datasets.items():

    output_path = f'./clean_data/{name}.csv'

    df.to_csv(
        output_path,
        index=False
    )

    print(
        f"Saved {name}: "
        f"{len(df):,} rows → {output_path}"
    )