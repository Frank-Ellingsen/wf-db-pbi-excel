from __future__ import annotations

import sys
from pathlib import Path

import duckdb


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DUCKDB_PATH = (
    PROJECT_ROOT
    / "db"
    / "project_finance.duckdb"
)


# ============================================================
# CONNECTION
# ============================================================

def connect_database():
    """
    Open persistent WF1 DuckDB database.
    """
    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(
            "DuckDB database not found: " + str(DUCKDB_PATH)
        )

    return duckdb.connect(str(DUCKDB_PATH))


# ============================================================
# PRECHECK
# ============================================================

def verify_required_silver_objects(connection):
    """
    Verify that all required Silver objects exist before building Gold.
    """
    required_objects = [
        "erp_finance",
        "framsikt_finance",
        "kostra_account_current",
        "kostra_function_current",
        "budget_organization_current",
    ]

    cursor = connection.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'silver'

        UNION

        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'silver'
        """
    )

    existing = {row[0] for row in cursor.fetchall()}

    missing = [
        name
        for name in required_objects
        if name not in existing
    ]

    if missing:
        raise RuntimeError(
            "Missing required Silver objects: "
            + ", ".join(missing)
        )


# ============================================================
# GOLD SCHEMA
# ============================================================

def create_gold_schema(connection):
    """
    Ensure Gold schema exists.
    """
    connection.execute(
        "CREATE SCHEMA IF NOT EXISTS gold"
    )


def drop_gold_relation(connection, name):
    """
    Safely drop table or view if exists without Catalog Error.
    """
    try:
        connection.execute(
            f"DROP VIEW IF EXISTS gold.{name} CASCADE"
        )
    except Exception:
        pass

    try:
        connection.execute(
            f"DROP TABLE IF EXISTS gold.{name} CASCADE"
        )
    except Exception:
        pass


# ============================================================
# DIM DATE
# ============================================================

def create_dim_date(connection):
    """
    Create conformed continuous calendar dimension
    covering all fact dates.
    """

    drop_gold_relation(
        connection,
        "dim_date",
    )

    connection.execute(
        """
        CREATE TABLE gold.dim_date AS

        WITH fact_dates AS (
            SELECT
                CAST(
                    try_strptime(
                        period || '-01',
                        '%Y-%m-%d'
                    )
                    AS DATE
                ) AS fact_date
            FROM silver.erp_finance
            WHERE period IS NOT NULL

            UNION ALL

            SELECT
                CAST(
                    try_strptime(
                        period,
                        '%y-%b'
                    )
                    AS DATE
                ) AS fact_date
            FROM silver.framsikt_finance
            WHERE period IS NOT NULL
        ),

        date_bounds AS (
            SELECT
                COALESCE(
                    MIN(fact_date),
                    CURRENT_DATE
                ) AS min_d,

                COALESCE(
                    MAX(fact_date),
                    CURRENT_DATE
                ) AS max_d

            FROM fact_dates
        ),

        calendar_bounds AS (
            SELECT
                make_date(
                    CAST(
                        date_part(
                            'year',
                            min_d
                        )
                        AS INTEGER
                    ),
                    1,
                    1
                ) AS start_date,

                make_date(
                    CAST(
                        date_part(
                            'year',
                            max_d
                        )
                        AS INTEGER
                    ),
                    12,
                    31
                ) AS end_date

            FROM date_bounds
        ),

        raw_calendar AS (
            SELECT
                CAST(d AS DATE) AS date

            FROM calendar_bounds,

            generate_series(
                CAST(start_date AS TIMESTAMP),
                CAST(end_date AS TIMESTAMP),
                INTERVAL '1 day'
            ) AS t(d)
        )

        SELECT
            date,

            CAST(
                strftime(
                    date,
                    '%Y%m%d'
                )
                AS INTEGER
            ) AS date_key,

            CAST(
                date_part(
                    'year',
                    date
                )
                AS INTEGER
            ) AS year,

            CAST(
                date_part(
                    'quarter',
                    date
                )
                AS INTEGER
            ) AS quarter_number,

            'Q'
            || CAST(
                date_part(
                    'quarter',
                    date
                )
                AS VARCHAR
            ) AS quarter,

            'Q'
            || CAST(
                date_part(
                    'quarter',
                    date
                )
                AS VARCHAR
            ) AS quarter_label,

            CAST(
                date_part(
                    'year',
                    date
                )
                AS VARCHAR
            )
            || '-Q'
            || CAST(
                date_part(
                    'quarter',
                    date
                )
                AS VARCHAR
            ) AS year_quarter,

            CASE
                WHEN date_part('month', date)
                     BETWEEN 1 AND 4
                    THEN 1
                WHEN date_part('month', date)
                     BETWEEN 5 AND 8
                    THEN 2
                ELSE 3
            END AS tertial_number,

            'T'
            || CAST(
                CASE
                    WHEN date_part('month', date)
                         BETWEEN 1 AND 4
                        THEN 1
                    WHEN date_part('month', date)
                         BETWEEN 5 AND 8
                        THEN 2
                    ELSE 3
                END
                AS VARCHAR
            ) AS tertial,

            'T'
            || CAST(
                CASE
                    WHEN date_part('month', date)
                         BETWEEN 1 AND 4
                        THEN 1
                    WHEN date_part('month', date)
                         BETWEEN 5 AND 8
                        THEN 2
                    ELSE 3
                END
                AS VARCHAR
            ) AS tertial_label,

            CAST(
                date_part(
                    'year',
                    date
                )
                AS VARCHAR
            )
            || '-T'
            || CAST(
                CASE
                    WHEN date_part('month', date)
                         BETWEEN 1 AND 4
                        THEN 1
                    WHEN date_part('month', date)
                         BETWEEN 5 AND 8
                        THEN 2
                    ELSE 3
                END
                AS VARCHAR
            ) AS year_tertial,

            CAST(
                date_part(
                    'month',
                    date
                )
                AS INTEGER
            ) AS month_number,

            strftime(
                date,
                '%b'
            ) AS month_label,

            strftime(
                date,
                '%b'
            ) AS month_short_name,

            monthname(
                date
            ) AS month_name,

            strftime(
                date,
                '%Y-%m'
            ) AS year_month,

            CAST(
                strftime(
                    date,
                    '%Y%m'
                )
                AS INTEGER
            ) AS year_month_key,

            CAST(
                date_trunc(
                    'month',
                    date
                )
                AS DATE
            ) AS month_start,

            last_day(
                date
            ) AS month_end,

            CAST(
                date_part(
                    'week',
                    date
                )
                AS INTEGER
            ) AS iso_week_number,

            CAST(
                date_part(
                    'isoyear',
                    date
                )
                AS INTEGER
            ) AS iso_year,

            CAST(
                date_part(
                    'isoyear',
                    date
                )
                AS VARCHAR
            )
            || '-W'
            || LPAD(
                CAST(
                    date_part(
                        'week',
                        date
                    )
                    AS VARCHAR
                ),
                2,
                '0'
            ) AS iso_year_week,

            CAST(
                date_part(
                    'day',
                    date
                )
                AS INTEGER
            ) AS day_of_month,

            CAST(
                date_part(
                    'dayofyear',
                    date
                )
                AS INTEGER
            ) AS day_of_year,

            CAST(
                date_part(
                    'isodow',
                    date
                )
                AS INTEGER
            ) AS weekday_number,

            dayname(
                date
            ) AS weekday_name,

            CASE
                WHEN date_part(
                    'isodow',
                    date
                ) IN (6, 7)
                    THEN 'True'
                ELSE 'False'
            END AS is_weekend,

            CASE
                WHEN date = date_trunc(
                    'month',
                    date
                )
                    THEN 'True'
                ELSE 'False'
            END AS is_month_start,

            CASE
                WHEN date = last_day(date)
                    THEN 'True'
                ELSE 'False'
            END AS is_month_end,

            CASE
                WHEN date = last_day(date)
                 AND date_part(
                     'month',
                     date
                 ) IN (3, 6, 9, 12)
                    THEN 'True'
                ELSE 'False'
            END AS is_quarter_end,

            CASE
                WHEN date = last_day(date)
                 AND date_part(
                     'month',
                     date
                 ) IN (4, 8, 12)
                    THEN 'True'
                ELSE 'False'
            END AS is_tertial_end,

            CASE
                WHEN date_part(
                    'month',
                    date
                ) = 12
                 AND date_part(
                     'day',
                     date
                 ) = 31
                    THEN 'True'
                ELSE 'False'
            END AS is_year_end

        FROM raw_calendar

        ORDER BY date
        """
    )


# ============================================================
# DIM ACCOUNT
# ============================================================

def create_dim_account(connection):
    """
    Conformed account dimension:
    - Standard 6-digit accounts from KOSTRA kontoplan
    - Summary art lines from Framsikt not present in 6-digit plan
    - Standard fallback UNKNOWN row
    - Formatted string IDs and zero technical ETL columns.
    """

    drop_gold_relation(
        connection,
        "dim_account",
    )

    connection.execute(
        """
        CREATE TABLE gold.dim_account AS

        SELECT
            CAST(account_code AS VARCHAR)
                AS account_code,

            account_name,
            account_key,

            CAST(kostra_art_4digit AS VARCHAR)
                AS kostra_art_4digit,

            CAST(kostra_art_3digit AS VARCHAR)
                AS kostra_art_3digit,

            kostra_art_name,

            CAST(account_class_id AS VARCHAR)
                AS account_class_id,

            account_class_name,

            CAST(main_category_code AS VARCHAR)
                AS main_category_code,

            main_category_name,

            CAST(main_group_code AS VARCHAR)
                AS main_group_code,

            main_group_name,
            accounting_rule_description,
            active

        FROM silver.kostra_account_current

        UNION ALL

        SELECT
            'FS_' || md5(f.account_name)
                AS account_code,

            f.account_name,

            'FS_' || f.account_name
                AS account_key,

            NULL AS kostra_art_4digit,
            NULL AS kostra_art_3digit,

            f.account_name
                AS kostra_art_name,

            NULL AS account_class_id,

            f.account_class
                AS account_class_name,

            NULL AS main_category_code,

            f.account_type
                AS main_category_name,

            NULL AS main_group_code,

            f.economic_class
                AS main_group_name,

            'Framsikt aggregert post'
                AS accounting_rule_description,

            TRUE AS active

        FROM (
            SELECT DISTINCT
                account_name,
                account_type,
                account_class,
                economic_class

            FROM silver.framsikt_finance

            WHERE account_name IS NOT NULL
        ) f

        WHERE f.account_name NOT IN (
            SELECT account_name
            FROM silver.kostra_account_current
        )

        UNION ALL

        SELECT
            'UNKNOWN' AS account_code,
            'Ukjent konto' AS account_name,
            'UNKNOWN' AS account_key,
            'UNKNOWN' AS kostra_art_4digit,
            'UNKNOWN' AS kostra_art_3digit,
            'Ukjent art' AS kostra_art_name,
            'UNKNOWN' AS account_class_id,
            'Ukjent klasse' AS account_class_name,
            'UNKNOWN' AS main_category_code,
            'Ukjent kategori' AS main_category_name,
            'UNKNOWN' AS main_group_code,
            'Ukjent gruppe' AS main_group_name,
            'Fallback for uparrede poster'
                AS accounting_rule_description,
            FALSE AS active
        """
    )


# ============================================================
# DIM KOSTRA FUNCTION
# ============================================================

def create_dim_kostra_function(connection):
    """
    Conformed KOSTRA function dimension.
    """

    drop_gold_relation(
        connection,
        "dim_kostra_function",
    )

    connection.execute(
        """
        CREATE TABLE gold.dim_kostra_function AS

        SELECT
            CAST(kostra_function_id AS VARCHAR)
                AS kostra_function_id,

            kostra_function_name,
            function_key,
            active,
            main_function_code,
            main_function_name,
            main_function_key,

            CAST(service_area_code AS VARCHAR)
                AS service_area_code,

            service_area_name,

            CAST(function_group_code AS VARCHAR)
                AS function_group_code,

            function_group_name,
            accounting_rule_description

        FROM silver.kostra_function_current

        UNION ALL

        SELECT
            'UNKNOWN' AS kostra_function_id,
            'Ukjent funksjon' AS kostra_function_name,
            'UNKNOWN' AS function_key,
            FALSE AS active,
            'UNKNOWN' AS main_function_code,
            'Ukjent hovedfunksjon' AS main_function_name,
            'UNKNOWN' AS main_function_key,
            'UNKNOWN' AS service_area_code,
            'Ukjent tjenesteomrade' AS service_area_name,
            'UNKNOWN' AS function_group_code,
            'Ukjent funksjonsgruppe' AS function_group_name,
            'Fallback for uparrede funksjoner'
                AS accounting_rule_description
        """
    )


# ============================================================
# DIM BUDGET ORGANIZATION
# ============================================================

def create_dim_budget_organization(connection):
    """
    Budget organization dimension for Kristiansand municipality.

    Current scope:
    - Level 1: municipality / group
    - Level 2: area / kommunalsjef level
    - Responsibility-number range
    - Supporting descriptive attributes
    - UNKNOWN fallback

    example_unit is retained as descriptive source information.
    It is not modeled as budget level 3 because the current
    source contains examples rather than a complete unique
    level-3 organizational structure.
    """

    drop_gold_relation(
        connection,
        "dim_budget_organization",
    )

    connection.execute(
        """
        CREATE TABLE gold.dim_budget_organization AS

        SELECT
            CAST(budget_level_2_code AS VARCHAR)
                AS budget_organization_key,

            CAST(budget_level_1_code AS VARCHAR)
                AS budget_level_1_code,

            budget_level_1_name,

            CAST(budget_level_2_code AS VARCHAR)
                AS budget_level_2_code,

            budget_level_2_name,

            responsibility_number_range,

            CAST(example_responsibility_number AS VARCHAR)
                AS example_responsibility_number,

            example_unit,
            kostra_functions,
            politically_binding_level,
            description,

            TRUE AS active

        FROM silver.budget_organization_current

        UNION ALL

        SELECT
            'UNKNOWN'
                AS budget_organization_key,

            'UNKNOWN'
                AS budget_level_1_code,

            'Ukjent budsjettnivaa 1'
                AS budget_level_1_name,

            'UNKNOWN'
                AS budget_level_2_code,

            'Ukjent budsjettomrade'
                AS budget_level_2_name,

            NULL
                AS responsibility_number_range,

            NULL
                AS example_responsibility_number,

            NULL
                AS example_unit,

            NULL
                AS kostra_functions,

            NULL
                AS politically_binding_level,

            'Fallback for uparret budsjettorganisasjon'
                AS description,

            FALSE
                AS active
        """
    )


# ============================================================
# FACT ERP FINANCE
# ============================================================

def create_fact_erp_finance(connection):
    """
    Business-ready ERP financial fact table.

    WF1 test organization mapping:
    - Kommunal Boenhet -> Område 3 -> Helse og mestring
    - Other locations -> UNKNOWN

    The mapping is intentionally explicit for the current
    BoMiljø test dataset. It can later be replaced by a
    responsibility-number based master-data mapping.
    """

    drop_gold_relation(
        connection,
        "fact_erp_finance",
    )

    connection.execute(
        """
        CREATE TABLE gold.fact_erp_finance AS

        SELECT
            CAST(
                try_strptime(
                    f.period || '-01',
                    '%Y-%m-%d'
                )
                AS DATE
            ) AS date,

            f.period AS year_month,
            f.period,
            f.month,
            f.month_number,
            f.tertial,
            f.location,

            -- =================================================
            -- BUDGET ORGANIZATION
            -- Current explicit WF1 test mapping
            -- =================================================

            CASE
                WHEN f.location = 'Kommunal Boenhet'
                    THEN 'Område 3'
                ELSE 'UNKNOWN'
            END AS budget_organization_key,

            CAST(f.kostra_function_id AS VARCHAR)
                AS kostra_function_id,

            COALESCE(
                d.kostra_function_name,
                'Ukjent funksjon'
            ) AS kostra_function_name,

            COALESCE(
                d.function_key,
                'UNKNOWN'
            ) AS function_key,

            d.main_function_code,
            d.main_function_name,

            CAST(
                COALESCE(
                    d.service_area_code,
                    CAST(
                        f.service_area
                        AS VARCHAR
                    )
                )
                AS VARCHAR
            ) AS service_area_code,

            d.service_area_name,

            CAST(
                d.function_group_code
                AS VARCHAR
            ) AS function_group_code,

            d.function_group_name,

            CASE
                WHEN f.kostra_function_id IS NULL
                    THEN 'NOT_APPLICABLE'
                WHEN d.kostra_function_id IS NULL
                    THEN 'UNMAPPED'
                ELSE 'MATCHED'
            END AS function_mapping_status,

            CAST(f.kostra_art AS VARCHAR)
                AS kostra_art,

            CAST(f.account_code AS VARCHAR)
                AS account_code,

            f.account_name,

            COALESCE(
                a.account_key,
                'UNKNOWN'
            ) AS account_key,

            CAST(
                a.kostra_art_4digit
                AS VARCHAR
            ) AS kostra_art_4digit,

            CAST(
                a.kostra_art_3digit
                AS VARCHAR
            ) AS kostra_art_3digit,

            a.kostra_art_name,

            CAST(
                a.account_class_id
                AS VARCHAR
            ) AS account_class_id,

            a.account_class_name,

            CAST(
                a.main_category_code
                AS VARCHAR
            ) AS main_category_code,

            a.main_category_name,

            CAST(
                a.main_group_code
                AS VARCHAR
            ) AS main_group_code,

            a.main_group_name,

            CASE
                WHEN f.account_code IS NULL
                    THEN 'NOT_APPLICABLE'
                WHEN a.account_code IS NULL
                    THEN 'UNMAPPED'
                ELSE 'MATCHED'
            END AS account_mapping_status,

            f.budget,
            f.actual,

            f.budget - f.actual
                AS variance,

            CASE
                WHEN f.budget IS NULL
                  OR f.budget = 0
                    THEN NULL
                ELSE
                    (f.budget - f.actual)
                    / ABS(f.budget)
            END AS variance_pct,

            f.status,
            f.service_area,
            f.main_group,
            f.sub_group,

            CASE
                WHEN (f.budget - f.actual) > 0
                    THEN 'GREEN'
                WHEN (f.budget - f.actual) < 0
                    THEN 'RED'
                ELSE 'YELLOW'
            END AS variance_rag,

            CASE
                WHEN d.kostra_function_id IS NULL
                  OR a.account_code IS NULL
                    THEN 'WARNING'
                ELSE 'PASS'
            END AS data_quality_status,

            'REPORTING_PERIOD'
                AS reporting_status

        FROM silver.erp_finance AS f

        LEFT JOIN gold.dim_kostra_function AS d
            ON CAST(
                f.kostra_function_id
                AS VARCHAR
            ) = d.kostra_function_id

        LEFT JOIN gold.dim_account AS a
            ON CAST(
                f.account_code
                AS VARCHAR
            ) = a.account_code
        """
    )


# ============================================================
# FACT FRAMSIKT FINANCE
# ============================================================

def create_fact_framsikt_finance(connection):
    """
    Business-ready Framsikt financial fact table.

    Budget organization is not mapped yet because current
    Framsikt organization fields represent activity/service
    structure rather than a documented budget responsibility key.
    """

    drop_gold_relation(
        connection,
        "fact_framsikt_finance",
    )

    connection.execute(
        """
        CREATE TABLE gold.fact_framsikt_finance AS

        SELECT
            CAST(
                try_strptime(
                    f.period,
                    '%y-%b'
                )
                AS DATE
            ) AS date,

            strftime(
                CAST(
                    try_strptime(
                        f.period,
                        '%y-%b'
                    )
                    AS DATE
                ),
                '%Y-%m'
            ) AS year_month,

            f.period,
            f.location,
            f.organizational_unit,

            CAST(
                f.kostra_function_id
                AS VARCHAR
            ) AS kostra_function_id,

            COALESCE(
                d.kostra_function_name,
                'Ukjent funksjon'
            ) AS kostra_function_name,

            COALESCE(
                d.function_key,
                'UNKNOWN'
            ) AS function_key,

            d.main_function_code,
            d.main_function_name,

            CAST(
                d.service_area_code
                AS VARCHAR
            ) AS service_area_code,

            d.service_area_name,

            CAST(
                d.function_group_code
                AS VARCHAR
            ) AS function_group_code,

            d.function_group_name,

            CASE
                WHEN f.kostra_function_id IS NULL
                    THEN 'NOT_APPLICABLE'
                WHEN d.kostra_function_id IS NULL
                    THEN 'UNMAPPED'
                ELSE 'MATCHED'
            END AS function_mapping_status,

            f.account_type,
            f.account_name,
            f.account_class,
            f.economic_class,

            f.actual_ytd,
            f.budget_ytd,
            f.annual_budget,
            f.actual_prior_year,

            f.budget_ytd - f.actual_ytd
                AS variance_ytd,

            CASE
                WHEN f.budget_ytd IS NULL
                  OR f.budget_ytd = 0
                    THEN NULL
                ELSE
                    (f.budget_ytd - f.actual_ytd)
                    / ABS(f.budget_ytd)
            END AS variance_ytd_pct,

            f.actual_ytd - f.actual_prior_year
                AS change_vs_prior_year,

            CASE
                WHEN f.actual_prior_year IS NULL
                  OR f.actual_prior_year = 0
                    THEN NULL
                ELSE
                    (
                        f.actual_ytd
                        - f.actual_prior_year
                    )
                    / ABS(f.actual_prior_year)
            END AS change_vs_prior_year_pct,

            CASE
                WHEN (
                    f.budget_ytd
                    - f.actual_ytd
                ) > 0
                    THEN 'GREEN'

                WHEN (
                    f.budget_ytd
                    - f.actual_ytd
                ) < 0
                    THEN 'RED'

                ELSE 'YELLOW'
            END AS variance_rag,

            'REPORTING_PERIOD'
                AS reporting_status

        FROM silver.framsikt_finance AS f

        LEFT JOIN gold.dim_kostra_function AS d
            ON CAST(
                f.kostra_function_id
                AS VARCHAR
            ) = d.kostra_function_id
        """
    )


# ============================================================
# AUDIT & QUALITY VIEWS
# ============================================================

def create_quality_views(connection):
    """
    Create diagnostic and reconciliation views.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_unmapped_kostra_functions AS

        SELECT
            'ERP' AS source_system,
            kostra_function_id,
            COUNT(*) AS affected_rows,
            SUM(COALESCE(actual, 0))
                AS actual_value,
            SUM(COALESCE(budget, 0))
                AS budget_value

        FROM gold.fact_erp_finance

        WHERE function_mapping_status = 'UNMAPPED'

        GROUP BY kostra_function_id

        UNION ALL

        SELECT
            'FRAMSIKT' AS source_system,
            kostra_function_id,
            COUNT(*) AS affected_rows,
            SUM(COALESCE(actual_ytd, 0))
                AS actual_value,
            SUM(COALESCE(budget_ytd, 0))
                AS budget_value

        FROM gold.fact_framsikt_finance

        WHERE function_mapping_status = 'UNMAPPED'

        GROUP BY kostra_function_id
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_finance_quality AS

        SELECT
            'fact_erp_finance'
                AS table_name,

            COUNT(*)
                AS total_rows,

            SUM(
                CASE
                    WHEN function_mapping_status
                         = 'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            ) AS unmapped_functions,

            SUM(
                CASE
                    WHEN account_mapping_status
                         = 'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            ) AS unmapped_accounts,

            SUM(
                CASE
                    WHEN date IS NULL
                        THEN 1
                    ELSE 0
                END
            ) AS null_dates

        FROM gold.fact_erp_finance

        UNION ALL

        SELECT
            'fact_framsikt_finance'
                AS table_name,

            COUNT(*)
                AS total_rows,

            SUM(
                CASE
                    WHEN function_mapping_status
                         = 'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            ) AS unmapped_functions,

            0 AS unmapped_accounts,

            SUM(
                CASE
                    WHEN date IS NULL
                        THEN 1
                    ELSE 0
                END
            ) AS null_dates

        FROM gold.fact_framsikt_finance
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_period_quality AS

        SELECT
            'ERP' AS source_system,
            year_month,
            date,
            COUNT(*) AS row_count,
            SUM(actual) AS total_actual,
            SUM(budget) AS total_budget

        FROM gold.fact_erp_finance

        GROUP BY
            year_month,
            date

        UNION ALL

        SELECT
            'FRAMSIKT' AS source_system,
            year_month,
            date,
            COUNT(*) AS row_count,
            SUM(actual_ytd) AS total_actual,
            SUM(budget_ytd) AS total_budget

        FROM gold.fact_framsikt_finance

        GROUP BY
            year_month,
            date

        ORDER BY date
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_data_quality_summary AS

        SELECT
            'erp_finance'
                AS dataset_name,

            COUNT(*)
                AS row_count,

            SUM(
                CASE
                    WHEN function_mapping_status
                         = 'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            ) AS unmapped_function_rows,

            SUM(
                CASE
                    WHEN account_mapping_status
                         = 'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            ) AS unmapped_account_rows

        FROM gold.fact_erp_finance

        UNION ALL

        SELECT
            'framsikt_finance'
                AS dataset_name,

            COUNT(*)
                AS row_count,

            SUM(
                CASE
                    WHEN function_mapping_status
                         = 'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            ) AS unmapped_function_rows,

            0 AS unmapped_account_rows

        FROM gold.fact_framsikt_finance
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.fact_erp_finance_pbi AS

        SELECT *
        FROM gold.fact_erp_finance
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.fact_framsikt_finance_pbi AS

        SELECT *
        FROM gold.fact_framsikt_finance
        """
    )


# ============================================================
# VERIFICATION CHECKS
# ============================================================

def verify_row_counts(connection):
    """
    Fact Gold views must preserve source Silver row counts.
    """

    checks = []

    pairs = [
        (
            "erp_finance",
            "fact_erp_finance",
        ),
        (
            "framsikt_finance",
            "fact_framsikt_finance",
        ),
    ]

    for silver_name, gold_name in pairs:

        silver_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM silver.{silver_name}
            """
        ).fetchone()[0]

        gold_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM gold.{gold_name}
            """
        ).fetchone()[0]

        checks.append(
            {
                "dataset":
                    silver_name,

                "silver_rows":
                    silver_count,

                "gold_rows":
                    gold_count,

                "passed":
                    silver_count
                    == gold_count,
            }
        )

    return checks


def verify_dimensions(connection):
    """
    Check current Gold dimension populations.
    """

    account_rows = connection.execute(
        """
        SELECT COUNT(*)
        FROM gold.dim_account
        """
    ).fetchone()[0]

    function_rows = connection.execute(
        """
        SELECT COUNT(*)
        FROM gold.dim_kostra_function
        """
    ).fetchone()[0]

    budget_organization_rows = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM gold.dim_budget_organization
            """
        ).fetchone()[0]
    )

    date_rows = connection.execute(
        """
        SELECT COUNT(*)
        FROM gold.dim_date
        """
    ).fetchone()[0]

    return {
        "account_rows":
            account_rows,

        "function_rows":
            function_rows,

        "budget_organization_rows":
            budget_organization_rows,

        "date_rows":
            date_rows,

        "account_passed":
            account_rows > 0,

        "function_passed":
            function_rows > 0,

        "budget_organization_passed":
            budget_organization_rows > 0,

        "date_passed":
            date_rows > 0,
    }


def verify_relationships(connection):
    """
    Verify 0 orphans across implemented
    conformed star-schema relationships.

    ERP budget organization currently uses the explicit
    WF1 test mapping:

        Kommunal Boenhet -> Område 3

    Framsikt budget organization mapping is not
    implemented yet.
    """

    relationships = [
        (
            "fact_erp_finance",
            "dim_budget_organization",
            "budget_organization_key",
            "budget_organization_key",
        ),
        (
            "fact_erp_finance",
            "dim_account",
            "account_code",
            "account_code",
        ),
        (
            "fact_erp_finance",
            "dim_kostra_function",
            "kostra_function_id",
            "kostra_function_id",
        ),
        (
            "fact_erp_finance",
            "dim_date",
            "date",
            "date",
        ),
        (
            "fact_framsikt_finance",
            "dim_account",
            "account_name",
            "account_name",
        ),
        (
            "fact_framsikt_finance",
            "dim_kostra_function",
            "kostra_function_id",
            "kostra_function_id",
        ),
        (
            "fact_framsikt_finance",
            "dim_date",
            "date",
            "date",
        ),
    ]

    results = []

    for (
        from_tbl,
        to_tbl,
        from_col,
        to_col,
    ) in relationships:

        orphan_count = (
            connection.execute(
                f"""
                SELECT COUNT(*)

                FROM gold.{from_tbl} f

                LEFT JOIN gold.{to_tbl} d
                    ON f.{from_col}
                       = d.{to_col}

                WHERE d.{to_col} IS NULL
                """
            ).fetchone()[0]
        )

        results.append(
            {
                "from_table":
                    from_tbl,

                "to_table":
                    to_tbl,

                "from_column":
                    from_col,

                "to_column":
                    to_col,

                "orphan_count":
                    orphan_count,

                "passed":
                    orphan_count == 0,
            }
        )

    return results


def verify_erp_budget_organization_mapping(connection):
    """
    Validate the explicit ERP test organization mapping.

    Current expected WF1 test behavior:
    - Kommunal Boenhet -> Område 3
    - All mapped keys must exist in dim_budget_organization.
    """

    result = connection.execute(
        """
        SELECT
            COUNT(*) AS total_rows,

            SUM(
                CASE
                    WHEN location = 'Kommunal Boenhet'
                     AND budget_organization_key = 'Område 3'
                        THEN 1
                    ELSE 0
                END
            ) AS expected_mapping_rows,

            SUM(
                CASE
                    WHEN budget_organization_key = 'UNKNOWN'
                        THEN 1
                    ELSE 0
                END
            ) AS unknown_mapping_rows

        FROM gold.fact_erp_finance
        """
    ).fetchone()

    total_rows = result[0]
    expected_mapping_rows = result[1]
    unknown_mapping_rows = result[2]

    passed = (
        total_rows > 0
        and expected_mapping_rows == total_rows
        and unknown_mapping_rows == 0
    )

    return {
        "total_rows":
            total_rows,

        "expected_mapping_rows":
            expected_mapping_rows,

        "unknown_mapping_rows":
            unknown_mapping_rows,

        "passed":
            passed,
    }


def verify_date_continuity(connection):
    """
    Verify continuous date dimension integrity.
    """

    result = connection.execute(
        """
        SELECT
            COUNT(*),
            COUNT(DISTINCT date),

            SUM(
                CASE
                    WHEN date IS NULL
                        THEN 1
                    ELSE 0
                END
            ),

            MIN(date),
            MAX(date)

        FROM gold.dim_date
        """
    ).fetchone()

    row_count = result[0]
    unique_dates = result[1]
    null_dates = result[2]
    min_date = result[3]
    max_date = result[4]

    expected_days = connection.execute(
        """
        SELECT
            date_diff(
                'day',
                MIN(date),
                MAX(date)
            ) + 1

        FROM gold.dim_date
        """
    ).fetchone()[0]

    duplicate_dates = (
        row_count
        - unique_dates
    )

    missing_dates = (
        expected_days
        - unique_dates
    )

    return {
        "row_count":
            row_count,

        "unique_dates":
            unique_dates,

        "null_dates":
            null_dates,

        "duplicate_dates":
            duplicate_dates,

        "missing_dates":
            missing_dates,

        "min_date":
            min_date,

        "max_date":
            max_date,

        "passed":
            (
                row_count > 0
                and null_dates == 0
                and duplicate_dates == 0
                and missing_dates == 0
            ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 100)

    print(
        "WF1 BUSINESS-READY GOLD LAYER BUILDER"
    )

    print("=" * 100)

    print(
        "DuckDB :",
        DUCKDB_PATH,
    )

    connection = None
    failures = 0
    warnings = 0

    try:

        connection = connect_database()

        print(
            "\nVerifying Silver prerequisite objects..."
        )

        verify_required_silver_objects(
            connection
        )

        print(
            "Silver prerequisites: PASS"
        )

        print(
            "\nBuilding Gold objects..."
        )

        create_gold_schema(
            connection
        )

        create_dim_date(
            connection
        )

        print(
            "  - gold.dim_date built."
        )

        create_dim_account(
            connection
        )

        print(
            "  - gold.dim_account built."
        )

        create_dim_kostra_function(
            connection
        )

        print(
            "  - gold.dim_kostra_function built."
        )

        create_dim_budget_organization(
            connection
        )

        print(
            "  - gold.dim_budget_organization built."
        )

        create_fact_erp_finance(
            connection
        )

        print(
            "  - gold.fact_erp_finance built."
        )

        create_fact_framsikt_finance(
            connection
        )

        print(
            "  - gold.fact_framsikt_finance built."
        )

        create_quality_views(
            connection
        )

        print(
            "  - diagnostic & quality views built."
        )

        print(
            "\n"
            + "=" * 100
        )

        print(
            "VALIDATION & AUDIT CHECKS"
        )

        print("=" * 100)

        # ----------------------------------------------------
        # Row count checks
        # ----------------------------------------------------

        row_checks = verify_row_counts(
            connection
        )

        for check in row_checks:

            status = (
                "PASS"
                if check["passed"]
                else "FAIL"
            )

            print(
                f"[{status}] "
                f"Row count: "
                f"{check['dataset']} "
                f"(Silver={check['silver_rows']}, "
                f"Gold={check['gold_rows']})"
            )

            if not check["passed"]:
                failures += 1

        # ----------------------------------------------------
        # Dimension checks
        # ----------------------------------------------------

        dim_checks = verify_dimensions(
            connection
        )

        print(
            f"[{'PASS' if dim_checks['account_passed'] else 'FAIL'}] "
            f"dim_account rows: "
            f"{dim_checks['account_rows']}"
        )

        print(
            f"[{'PASS' if dim_checks['function_passed'] else 'FAIL'}] "
            f"dim_kostra_function rows: "
            f"{dim_checks['function_rows']}"
        )

        print(
            f"[{'PASS' if dim_checks['budget_organization_passed'] else 'FAIL'}] "
            f"dim_budget_organization rows: "
            f"{dim_checks['budget_organization_rows']}"
        )

        print(
            f"[{'PASS' if dim_checks['date_passed'] else 'FAIL'}] "
            f"dim_date rows: "
            f"{dim_checks['date_rows']}"
        )

        if not (
            dim_checks["account_passed"]
            and dim_checks["function_passed"]
            and dim_checks[
                "budget_organization_passed"
            ]
            and dim_checks["date_passed"]
        ):
            failures += 1

        # ----------------------------------------------------
        # ERP budget organization mapping
        # ----------------------------------------------------

        organization_check = (
            verify_erp_budget_organization_mapping(
                connection
            )
        )

        print(
            f"[{'PASS' if organization_check['passed'] else 'FAIL'}] "
            f"ERP organization mapping: "
            f"{organization_check['expected_mapping_rows']} / "
            f"{organization_check['total_rows']} rows "
            f"mapped Kommunal Boenhet -> Område 3 "
            f"(UNKNOWN: "
            f"{organization_check['unknown_mapping_rows']})"
        )

        if not organization_check[
            "passed"
        ]:
            failures += 1

        # ----------------------------------------------------
        # Date continuity
        # ----------------------------------------------------

        date_check = (
            verify_date_continuity(
                connection
            )
        )

        print(
            f"[{'PASS' if date_check['passed'] else 'FAIL'}] "
            f"dim_date continuity: "
            f"{date_check['min_date']} "
            f"to {date_check['max_date']} "
            f"({date_check['row_count']} days, "
            f"{date_check['missing_dates']} missing)"
        )

        if not date_check["passed"]:
            failures += 1

        # ----------------------------------------------------
        # Star schema
        # ----------------------------------------------------

        print(
            "\nStar-Schema Referential Integrity:"
        )

        rel_checks = verify_relationships(
            connection
        )

        for rel in rel_checks:

            status = (
                "PASS"
                if rel["passed"]
                else "FAIL"
            )

            print(
                f"[{status}] "
                f"{rel['from_table']}."
                f"{rel['from_column']} "
                f"-> "
                f"{rel['to_table']}."
                f"{rel['to_column']} "
                f"(Orphans: "
                f"{rel['orphan_count']})"
            )

            if not rel["passed"]:
                failures += 1

        print(
            "\n"
            + "=" * 100
        )

        print(
            "GOLD BUILD SUMMARY"
        )

        print("=" * 100)

        print(
            "Failures :",
            failures,
        )

        print(
            "Warnings :",
            warnings,
        )

        print(
            "Result   :",
            (
                "PASS"
                if failures == 0
                else "FAIL"
            ),
        )

        print("=" * 100)

        return (
            0
            if failures == 0
            else 1
        )

    except Exception as exc:

        print(
            "\n"
            + "=" * 100
        )

        print(
            "GOLD BUILD FAILED:",
            exc,
        )

        print("=" * 100)

        return 1

    finally:

        if connection is not None:
            connection.close()


if __name__ == "__main__":

    sys.exit(
        main()
    )