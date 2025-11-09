# Flask-SQLAlchemy Database Optimization Report

This repository documents a comprehensive analysis and optimization of a Flask-SQLAlchemy database schema for a Python-based annotation platform. The goal was to identify and fix performance bottlenecks, improve data integrity, and ensure the long-term scalability and security of the application.

## Summary of Optimizations

Five key optimizations were implemented at the schema level:

1.  **Added Strategic Indexes:** Applied `index=True` to all foreign keys and common search columns to accelerate queries and `JOIN` operations.
2.  **Used Native PostgreSQL Enums:** Replaced `db.String` fields (for `status`, `role`, etc.) with `db.Enum` to ensure data integrity and improve storage efficiency.
3.  **Normalized Redundant Data:** Removed redundant `segment_id` columns from child tables (like `LexicalInfo`) to create a single source of truth and prevent data inconsistency (achieving 3NF).
4.  **Used a GIN Index:** Implemented a specialized `GIN` (Generalized Inverted Index) on the `User.languages` `ARRAY` column to enable fast, "contains" style lookups.
5.  **Fixed `password_hash` Length:** Increased the `password_hash` column length from `String(200)` to `String(256)` to prevent a critical bug where modern, secure hashes would be truncated, locking users out.

## Repository Structure

* `/report/`
    * `db_optimization_report.pdf`: **The final, compiled PDF report** detailing the problem, solution, and benefit of each optimization.
* `/code/`
    * `original_models.py`: The original Python models file **before** any optimizations were applied.
    * `optimized_models.py`: The final, optimized Python models file **after** all schema-level changes were implemented.

## How to View the Results

The best place to start is by reading the full report:
[**View the Final Report](./report/db_optimization_report.pdf)**

To see the code changes directly, you can compare the two files in the `/code/` directory:

* [View "Before" Code](./code/original_models.py)
* [View "After" Code](./code/optimized_models.py)