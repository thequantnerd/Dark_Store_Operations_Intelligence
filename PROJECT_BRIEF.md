# Project 2 — Dark Store Operations & Location Intelligence

## Business Scenario
You are a Data Analyst at a quick-commerce company operating a network of dark stores.

Management wants to understand store performance, demand patterns, inventory efficiency,
and potential locations for future expansion.

## Core Business Questions
1. Which dark stores generate the most revenue and orders?
2. Which stores are underperforming relative to the network?
3. How does store performance change over time?
4. What are the busiest days and hours for each store?
5. Which products/categories drive demand at each location?
6. Which locations have consistently high demand?
7. Which stores have the highest stockout rates?
8. Which products are slow-moving or aging at particular stores?
9. Which stores have the strongest and weakest inventory efficiency?
10. Which geographic areas appear underserved relative to customer demand?
11. Are existing stores potentially cannibalizing nearby demand?
12. Which locations represent the strongest candidates for expansion?

## Rules
- Treat the CSVs as RAW DATA.
- Do not assume the data is clean.
- Profile and validate the data before analysis.
- Document cleaning decisions.
- Do not change the raw_data files.
- Use Python/Pandas for profiling and cleaning.
- Use PostgreSQL as the primary analytical database.
- Use SQL for the business analysis.
- Build the final dashboard in Tableau.
- Do not fabricate fields or business results that cannot be supported by the data.

## Suggested Workflow
Raw CSV → Python profiling → cleaned CSV → PostgreSQL → SQL analysis/views → Tableau → findings/recommendations
