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

    if not DUCKDB_PATH.exists():

        raise FileNotFoundError(
            "DuckDB database not found: "
            + str(DUCKDB_PATH)
        )

    return duckdb.connect(
        str(DUCKDB_PATH)
    )


# ============================================================
# PRECHECK
# ============================================================

def verify_gold_objects(connection):

    required = {
        "fact_erp_finance",
        "fact_framsikt_finance",
        "dim_account",
        "dim_kostra_function",
        "dim_budget_organization",
    }

    rows = connection.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'gold'

        UNION

        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'gold'
        """
    ).fetchall()

    existing = {
        row[0]
        for row in rows
    }

    missing = required - existing

    if missing:

        raise RuntimeError(
            "Missing Gold objects: "
            + ", ".join(
                sorted(missing)
            )
        )


# ============================================================
# NORMALIZED ERP PERIOD
# ============================================================

def create_erp_period_view(connection):
    """
    Normalize ERP period YYYY-MM to DATE.

    Original source period is preserved.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_erp_period_normalized AS

        SELECT
            f.*,

            f.period
                AS source_period,

            CAST(
                try_strptime(
                    f.period || '-01',
                    '%Y-%m-%d'
                )
                AS DATE
            )
                AS reporting_date,

            CAST(
                try_strptime(
                    f.period || '-01',
                    '%Y-%m-%d'
                )
                AS DATE
            )
                AS reporting_month_start,

            strftime(
                CAST(
                    try_strptime(
                        f.period || '-01',
                        '%Y-%m-%d'
                    )
                    AS DATE
                ),
                '%Y-%m'
            )
                AS reporting_year_month

        FROM gold.fact_erp_finance AS f
        """
    )


# ============================================================
# NORMALIZED FRAMSIKT PERIOD
# ============================================================

def create_framsikt_period_view(connection):
    """
    Normalize Framsikt period YY-Mon to DATE.

    Example:
        25-Aug -> 2025-08-01

    Original source period is preserved.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_framsikt_period_normalized AS

        SELECT
            f.*,

            f.period
                AS source_period,

            CAST(
                try_strptime(
                    f.period,
                    '%y-%b'
                )
                AS DATE
            )
                AS reporting_date,

            CAST(
                try_strptime(
                    f.period,
                    '%y-%b'
                )
                AS DATE
            )
                AS reporting_month_start,

            strftime(
                CAST(
                    try_strptime(
                        f.period,
                        '%y-%b'
                    )
                    AS DATE
                ),
                '%Y-%m'
            )
                AS reporting_year_month

        FROM gold.fact_framsikt_finance AS f
        """
    )


# ============================================================
# PERIOD VALIDATION
# ============================================================

def validate_period_parsing(connection):

    erp_invalid = connection.execute(
        """
        SELECT COUNT(*)
        FROM gold.v_erp_period_normalized
        WHERE reporting_date IS NULL
        """
    ).fetchone()[0]

    framsikt_invalid = connection.execute(
        """
        SELECT COUNT(*)
        FROM gold.v_framsikt_period_normalized
        WHERE reporting_date IS NULL
        """
    ).fetchone()[0]

    return {
        "erp_invalid": erp_invalid,
        "framsikt_invalid": framsikt_invalid,
    }


# ============================================================
# REPORTING DATE BOUNDARIES
# ============================================================

def create_reporting_date_boundaries(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_reporting_date_boundaries AS

        SELECT
            'ERP'
                AS source_system,

            MIN(reporting_date)
                AS min_reporting_date,

            MAX(reporting_date)
                AS max_reporting_date,

            COUNT(*)
                AS fact_rows,

            COUNT(
                DISTINCT reporting_date
            )
                AS reporting_periods

        FROM gold.v_erp_period_normalized

        WHERE reporting_date IS NOT NULL

        UNION ALL

        SELECT
            'FRAMSIKT'
                AS source_system,

            MIN(reporting_date)
                AS min_reporting_date,

            MAX(reporting_date)
                AS max_reporting_date,

            COUNT(*)
                AS fact_rows,

            COUNT(
                DISTINCT reporting_date
            )
                AS reporting_periods

        FROM gold.v_framsikt_period_normalized

        WHERE reporting_date IS NOT NULL
        """
    )


# ============================================================
# DAILY DATE DIMENSION
# ============================================================

def create_dim_date(connection):
    """
    Create dynamic continuous daily calendar if Gold
    dim_date does not already exist.
    """

    check = connection.execute(
        """
        SELECT table_type
        FROM information_schema.tables
        WHERE table_schema = 'gold'
          AND table_name = 'dim_date'
        """
    ).fetchone()

    if check:
        return

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.dim_date AS

        WITH fact_range AS
        (
            SELECT
                MIN(min_reporting_date)
                    AS min_fact_date,

                MAX(max_reporting_date)
                    AS max_fact_date

            FROM gold.v_reporting_date_boundaries
        ),

        calendar_range AS
        (
            SELECT
                make_date(
                    CAST(
                        date_part(
                            'year',
                            min_fact_date
                        )
                        AS INTEGER
                    ),
                    1,
                    1
                )
                    AS calendar_start,

                make_date(
                    CAST(
                        date_part(
                            'year',
                            max_fact_date
                        )
                        AS INTEGER
                    ),
                    12,
                    31
                )
                    AS calendar_end

            FROM fact_range

            WHERE
                min_fact_date IS NOT NULL

            AND
                max_fact_date IS NOT NULL
        ),

        calendar AS
        (
            SELECT
                CAST(
                    generated_date
                    AS DATE
                )
                    AS date

            FROM calendar_range,

            generate_series(
                CAST(
                    calendar_start
                    AS TIMESTAMP
                ),

                CAST(
                    calendar_end
                    AS TIMESTAMP
                ),

                INTERVAL '1 day'
            )
            AS date_series(
                generated_date
            )
        )

        SELECT

            date,

            CAST(
                strftime(
                    date,
                    '%Y%m%d'
                )
                AS INTEGER
            )
                AS date_key,

            CAST(
                date_part(
                    'year',
                    date
                )
                AS INTEGER
            )
                AS year,

            CAST(
                date_part(
                    'quarter',
                    date
                )
                AS INTEGER
            )
                AS quarter_number,

            'Q'
            || CAST(
                date_part(
                    'quarter',
                    date
                )
                AS INTEGER
            )
                AS quarter,

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
                AS INTEGER
            )
                AS year_quarter,

            CAST(
                date_part(
                    'month',
                    date
                )
                AS INTEGER
            )
                AS month_number,

            strftime(
                date,
                '%B'
            )
                AS month_name,

            strftime(
                date,
                '%b'
            )
                AS month_short_name,

            strftime(
                date,
                '%Y-%m'
            )
                AS year_month,

            CAST(
                strftime(
                    date,
                    '%Y%m'
                )
                AS INTEGER
            )
                AS year_month_key,

            CAST(
                date_trunc(
                    'month',
                    date
                )
                AS DATE
            )
                AS month_start,

            last_day(
                date
            )
                AS month_end,

            CASE
                WHEN date_part(
                    'month',
                    date
                ) BETWEEN 1 AND 4
                    THEN 1

                WHEN date_part(
                    'month',
                    date
                ) BETWEEN 5 AND 8
                    THEN 2

                ELSE 3
            END
                AS tertial_number,

            'T'
            || CAST(
                CASE
                    WHEN date_part(
                        'month',
                        date
                    ) BETWEEN 1 AND 4
                        THEN 1

                    WHEN date_part(
                        'month',
                        date
                    ) BETWEEN 5 AND 8
                        THEN 2

                    ELSE 3
                END
                AS VARCHAR
            )
                AS tertial,

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
                    WHEN date_part(
                        'month',
                        date
                    ) BETWEEN 1 AND 4
                        THEN 1

                    WHEN date_part(
                        'month',
                        date
                    ) BETWEEN 5 AND 8
                        THEN 2

                    ELSE 3
                END
                AS VARCHAR
            )
                AS year_tertial,

            CAST(
                date_part(
                    'week',
                    date
                )
                AS INTEGER
            )
                AS iso_week_number,

            CAST(
                date_part(
                    'isoyear',
                    date
                )
                AS INTEGER
            )
                AS iso_year,

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
            )
                AS iso_year_week,

            CAST(
                date_part(
                    'day',
                    date
                )
                AS INTEGER
            )
                AS day_of_month,

            CAST(
                date_part(
                    'dayofyear',
                    date
                )
                AS INTEGER
            )
                AS day_of_year,

            CAST(
                date_part(
                    'isodow',
                    date
                )
                AS INTEGER
            )
                AS weekday_number,

            dayname(
                date
            )
                AS weekday_name,

            CASE
                WHEN date_part(
                    'isodow',
                    date
                ) IN (6, 7)
                    THEN TRUE

                ELSE FALSE
            END
                AS is_weekend,

            CASE
                WHEN date =
                    CAST(
                        date_trunc(
                            'month',
                            date
                        )
                        AS DATE
                    )
                    THEN TRUE

                ELSE FALSE
            END
                AS is_month_start,

            CASE
                WHEN date = last_day(date)
                    THEN TRUE

                ELSE FALSE
            END
                AS is_month_end,

            CASE
                WHEN date_part(
                    'month',
                    date
                ) IN (3, 6, 9, 12)

                AND
                    date = last_day(date)

                    THEN TRUE

                ELSE FALSE
            END
                AS is_quarter_end,

            CASE
                WHEN date_part(
                    'month',
                    date
                ) IN (4, 8, 12)

                AND
                    date = last_day(date)

                    THEN TRUE

                ELSE FALSE
            END
                AS is_tertial_end,

            CASE
                WHEN date_part(
                    'month',
                    date
                ) = 12

                AND
                    date_part(
                        'day',
                        date
                    ) = 31

                    THEN TRUE

                ELSE FALSE
            END
                AS is_year_end

        FROM calendar

        ORDER BY
            date
        """
    )


# ============================================================
# DATE DIMENSION VALIDATION
# ============================================================

def validate_dim_date(connection):

    result = connection.execute(
        """
        SELECT
            COUNT(*)
                AS row_count,

            COUNT(DISTINCT date)
                AS unique_dates,

            SUM(
                CASE
                    WHEN date IS NULL
                    THEN 1
                    ELSE 0
                END
            )
                AS null_dates,

            MIN(date)
                AS min_date,

            MAX(date)
                AS max_date

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
        "row_count": row_count,
        "unique_dates": unique_dates,
        "null_dates": null_dates,
        "duplicate_dates": duplicate_dates,
        "missing_dates": missing_dates,
        "min_date": min_date,
        "max_date": max_date,
        "passed": (
            row_count > 0
            and null_dates == 0
            and duplicate_dates == 0
            and missing_dates == 0
        ),
    }


# ============================================================
# BUDGET ORGANIZATION POWER BI DIMENSION
# ============================================================

def create_budget_organization_powerbi_view(connection):
    """
    Power BI-ready budget organization dimension.

    Current scope:
    - Level 1: municipality / group
    - Level 2: area / kommunalsjef level

    Level 3 is intentionally not derived from example_unit.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.dim_budget_organization_pbi AS

        SELECT
            budget_organization_key,
            budget_level_1_code,
            budget_level_1_name,
            budget_level_2_code,
            budget_level_2_name,
            responsibility_number_range,
            example_responsibility_number,
            example_unit,
            kostra_functions,
            politically_binding_level,
            description,
            active

        FROM gold.dim_budget_organization
        """
    )


# ============================================================
# BUDGET ORGANIZATION VALIDATION
# ============================================================

def validate_budget_organization(connection):

    result = connection.execute(
        """
        SELECT
            COUNT(*)
                AS row_count,

            COUNT(
                DISTINCT budget_organization_key
            )
                AS unique_keys,

            SUM(
                CASE
                    WHEN budget_organization_key IS NULL
                        THEN 1
                    ELSE 0
                END
            )
                AS null_keys,

            SUM(
                CASE
                    WHEN budget_level_2_code IS NULL
                        THEN 1
                    ELSE 0
                END
            )
                AS null_level_2_codes,

            SUM(
                CASE
                    WHEN budget_level_2_name IS NULL
                        THEN 1
                    ELSE 0
                END
            )
                AS null_level_2_names

        FROM gold.dim_budget_organization_pbi
        """
    ).fetchone()

    row_count = result[0]
    unique_keys = result[1]
    null_keys = result[2]
    null_level_2_codes = result[3]
    null_level_2_names = result[4]

    duplicate_keys = (
        row_count
        - unique_keys
    )

    return {
        "row_count": row_count,
        "unique_keys": unique_keys,
        "null_keys": null_keys,
        "duplicate_keys": duplicate_keys,
        "null_level_2_codes": null_level_2_codes,
        "null_level_2_names": null_level_2_names,
        "passed": (
            row_count > 0
            and null_keys == 0
            and duplicate_keys == 0
            and null_level_2_codes == 0
            and null_level_2_names == 0
        ),
    }


# ============================================================
# ERP ACTUAL HORIZON
# ============================================================

def create_erp_actual_horizon(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_erp_actual_horizon AS

        SELECT
            MAX(reporting_date)
                AS latest_actual_month

        FROM
        (
            SELECT
                reporting_date,

                SUM(
                    ABS(
                        COALESCE(
                            actual,
                            0
                        )
                    )
                )
                    AS actual_activity

            FROM gold.v_erp_period_normalized

            WHERE reporting_date IS NOT NULL

            GROUP BY
                reporting_date
        )
        AS monthly

        WHERE actual_activity > 0
        """
    )


# ============================================================
# ERP POWER BI FACT
# ============================================================

def create_erp_powerbi_fact(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.fact_erp_finance_pbi AS

        SELECT
            f.*,

            h.latest_actual_month,

            CASE
                WHEN f.reporting_date IS NULL
                    THEN 'INVALID_PERIOD'

                WHEN h.latest_actual_month IS NULL
                    THEN 'NO_ACTUAL_HORIZON'

                WHEN f.reporting_date
                     > h.latest_actual_month
                    THEN 'FUTURE_OR_NOT_REPORTED'

                ELSE 'REPORTING_PERIOD'
            END
                AS reporting_status,

            CASE
                WHEN f.reporting_date IS NULL
                    THEN 'NO_DATA'

                WHEN h.latest_actual_month IS NULL
                    THEN 'NO_DATA'

                WHEN f.reporting_date
                     > h.latest_actual_month
                    THEN 'NO_DATA'

                WHEN f.variance IS NULL
                    THEN 'NO_DATA'

                WHEN f.variance > 0
                    THEN 'GREEN'

                WHEN f.variance < 0
                    THEN 'RED'

                ELSE 'YELLOW'
            END
                AS variance_rag,

            CASE
                WHEN f.function_mapping_status =
                    'UNMAPPED'
                    THEN 'WARNING'

                WHEN f.account_mapping_status =
                    'UNMAPPED'
                    THEN 'WARNING'

                ELSE 'PASS'
            END
                AS data_quality_status

        FROM gold.v_erp_period_normalized AS f

        CROSS JOIN
            gold.v_erp_actual_horizon AS h
        """
    )


# ============================================================
# ERP MONTHLY KPI
# ============================================================

def create_erp_monthly_kpi_view(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_erp_kpi_monthly AS

        SELECT
            reporting_date,
            reporting_year_month,
            source_period,

            SUM(actual)
                AS actual,

            SUM(budget)
                AS budget,

            SUM(budget)
            - SUM(actual)
                AS variance,

            CASE
                WHEN SUM(budget) IS NULL
                    THEN NULL

                WHEN SUM(budget) = 0
                    THEN NULL

                ELSE
                    (
                        SUM(budget)
                        - SUM(actual)
                    )
                    / ABS(
                        SUM(budget)
                    )
            END
                AS variance_pct,

            COUNT(*)
                AS source_rows,

            SUM(
                CASE
                    WHEN function_mapping_status =
                        'UNMAPPED'
                        THEN 1

                    ELSE 0
                END
            )
                AS unmapped_function_rows,

            SUM(
                CASE
                    WHEN account_mapping_status =
                        'UNMAPPED'
                        THEN 1

                    ELSE 0
                END
            )
                AS unmapped_account_rows

        FROM gold.fact_erp_finance_pbi

        GROUP BY
            reporting_date,
            reporting_year_month,
            source_period

        ORDER BY
            reporting_date
        """
    )


# ============================================================
# FRAMSIKT POWER BI FACT
# ============================================================

def create_framsikt_powerbi_fact(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.fact_framsikt_finance_pbi AS

        SELECT
            f.*,

            CASE
                WHEN f.reporting_date IS NULL
                    THEN 'INVALID_PERIOD'

                ELSE 'REPORTING_PERIOD'
            END
                AS reporting_status,

            CASE
                WHEN f.reporting_date IS NULL
                    THEN 'NO_DATA'

                WHEN f.variance_ytd IS NULL
                    THEN 'NO_DATA'

                WHEN f.variance_ytd > 0
                    THEN 'GREEN'

                WHEN f.variance_ytd < 0
                    THEN 'RED'

                ELSE 'YELLOW'
            END
                AS variance_ytd_rag,

            CASE
                WHEN f.change_vs_prior_year
                    IS NULL
                    THEN 'NO_DATA'

                WHEN f.change_vs_prior_year < 0
                    THEN 'GREEN'

                WHEN f.change_vs_prior_year > 0
                    THEN 'RED'

                ELSE 'YELLOW'
            END
                AS prior_year_change_rag,

            CASE
                WHEN f.function_mapping_status =
                    'UNMAPPED'
                    THEN 'WARNING'

                ELSE 'PASS'
            END
                AS data_quality_status

        FROM
            gold.v_framsikt_period_normalized AS f
        """
    )


# ============================================================
# FRAMSIKT KPI SUMMARY
# ============================================================

def create_framsikt_summary_view(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_framsikt_kpi_summary AS

        SELECT
            reporting_date,
            reporting_year_month,
            source_period,

            SUM(actual_ytd)
                AS actual_ytd,

            SUM(budget_ytd)
                AS budget_ytd,

            SUM(annual_budget)
                AS annual_budget,

            SUM(actual_prior_year)
                AS actual_prior_year,

            SUM(budget_ytd)
            - SUM(actual_ytd)
                AS variance_ytd,

            CASE
                WHEN SUM(budget_ytd) IS NULL
                    THEN NULL

                WHEN SUM(budget_ytd) = 0
                    THEN NULL

                ELSE
                    (
                        SUM(budget_ytd)
                        - SUM(actual_ytd)
                    )
                    / ABS(
                        SUM(budget_ytd)
                    )
            END
                AS variance_ytd_pct,

            SUM(actual_ytd)
            - SUM(actual_prior_year)
                AS change_vs_prior_year,

            CASE
                WHEN SUM(actual_prior_year)
                    IS NULL
                    THEN NULL

                WHEN SUM(actual_prior_year) = 0
                    THEN NULL

                ELSE
                    (
                        SUM(actual_ytd)
                        - SUM(actual_prior_year)
                    )
                    / ABS(
                        SUM(actual_prior_year)
                    )
            END
                AS change_vs_prior_year_pct,

            COUNT(*)
                AS source_rows,

            SUM(
                CASE
                    WHEN function_mapping_status =
                        'UNMAPPED'
                        THEN 1

                    ELSE 0
                END
            )
                AS unmapped_function_rows

        FROM gold.fact_framsikt_finance_pbi

        GROUP BY
            reporting_date,
            reporting_year_month,
            source_period

        ORDER BY
            reporting_date
        """
    )


# ============================================================
# FINANCE QUALITY
# ============================================================

def create_finance_quality_view(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_finance_quality AS

        SELECT
            'ERP'
                AS source_system,

            COUNT(*)
                AS total_rows,

            SUM(
                CASE
                    WHEN function_mapping_status =
                        'MATCHED'
                        THEN 1
                    ELSE 0
                END
            )
                AS matched_function_rows,

            SUM(
                CASE
                    WHEN function_mapping_status =
                        'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            )
                AS unmapped_function_rows,

            SUM(
                CASE
                    WHEN account_mapping_status =
                        'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            )
                AS unmapped_account_rows

        FROM gold.fact_erp_finance_pbi

        UNION ALL

        SELECT
            'FRAMSIKT'
                AS source_system,

            COUNT(*)
                AS total_rows,

            SUM(
                CASE
                    WHEN function_mapping_status =
                        'MATCHED'
                        THEN 1
                    ELSE 0
                END
            )
                AS matched_function_rows,

            SUM(
                CASE
                    WHEN function_mapping_status =
                        'UNMAPPED'
                        THEN 1
                    ELSE 0
                END
            )
                AS unmapped_function_rows,

            CAST(
                NULL
                AS BIGINT
            )
                AS unmapped_account_rows

        FROM gold.fact_framsikt_finance_pbi
        """
    )


# ============================================================
# PERIOD QUALITY
# ============================================================

def create_period_quality_view(connection):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_period_quality AS

        SELECT
            'ERP'
                AS source_system,

            COUNT(*)
                AS total_rows,

            SUM(
                CASE
                    WHEN reporting_date IS NULL
                        THEN 1
                    ELSE 0
                END
            )
                AS invalid_period_rows

        FROM gold.v_erp_period_normalized

        UNION ALL

        SELECT
            'FRAMSIKT'
                AS source_system,

            COUNT(*)
                AS total_rows,

            SUM(
                CASE
                    WHEN reporting_date IS NULL
                        THEN 1
                    ELSE 0
                END
            )
                AS invalid_period_rows

        FROM gold.v_framsikt_period_normalized
        """
    )


# ============================================================
# COUNTS
# ============================================================

def get_counts(connection):

    objects = [
        "gold.v_erp_period_normalized",
        "gold.v_framsikt_period_normalized",
        "gold.v_reporting_date_boundaries",
        "gold.dim_date",
        "gold.dim_budget_organization_pbi",
        "gold.v_erp_actual_horizon",
        "gold.fact_erp_finance_pbi",
        "gold.v_erp_kpi_monthly",
        "gold.fact_framsikt_finance_pbi",
        "gold.v_framsikt_kpi_summary",
        "gold.v_finance_quality",
        "gold.v_period_quality",
    ]

    results = []

    for object_name in objects:

        rows = connection.execute(
            "SELECT COUNT(*) FROM "
            + object_name
        ).fetchone()[0]

        results.append(
            (
                object_name,
                rows,
            )
        )

    return results


# ============================================================
# PRINT PERIOD VALIDATION
# ============================================================

def print_period_validation(result):

    print()
    print("=" * 100)
    print(
        "PERIOD NORMALIZATION"
    )
    print("=" * 100)

    print(
        "ERP invalid periods      :",
        result["erp_invalid"],
    )

    print(
        "Framsikt invalid periods :",
        result["framsikt_invalid"],
    )


# ============================================================
# PRINT DATE BOUNDARIES
# ============================================================

def print_date_boundaries(connection):

    rows = connection.execute(
        """
        SELECT
            source_system,
            min_reporting_date,
            max_reporting_date,
            fact_rows,
            reporting_periods

        FROM gold.v_reporting_date_boundaries

        ORDER BY source_system
        """
    ).fetchall()

    print()
    print("=" * 100)
    print(
        "REPORTING DATE BOUNDARIES"
    )
    print("=" * 100)

    for row in rows:

        print(
            "{} | min: {} | max: {} | rows: {} | periods: {}".format(
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
            )
        )


# ============================================================
# PRINT DIM DATE VALIDATION
# ============================================================

def print_dim_date_validation(result):

    print()
    print("=" * 100)
    print(
        "DIM_DATE VALIDATION"
    )
    print("=" * 100)

    print(
        "Rows            :",
        result["row_count"],
    )

    print(
        "Unique dates    :",
        result["unique_dates"],
    )

    print(
        "NULL dates      :",
        result["null_dates"],
    )

    print(
        "Duplicate dates :",
        result["duplicate_dates"],
    )

    print(
        "Missing dates   :",
        result["missing_dates"],
    )

    print(
        "Minimum date    :",
        result["min_date"],
    )

    print(
        "Maximum date    :",
        result["max_date"],
    )

    print(
        "Result          :",
        (
            "PASS"
            if result["passed"]
            else "FAIL"
        ),
    )


# ============================================================
# PRINT BUDGET ORGANIZATION VALIDATION
# ============================================================

def print_budget_organization_validation(result):

    print()
    print("=" * 100)
    print(
        "BUDGET ORGANIZATION VALIDATION"
    )
    print("=" * 100)

    print(
        "Rows            :",
        result["row_count"],
    )

    print(
        "Unique keys     :",
        result["unique_keys"],
    )

    print(
        "NULL keys       :",
        result["null_keys"],
    )

    print(
        "Duplicate keys  :",
        result["duplicate_keys"],
    )

    print(
        "NULL level 2 IDs:",
        result["null_level_2_codes"],
    )

    print(
        "NULL level 2 names:",
        result["null_level_2_names"],
    )

    print(
        "Result          :",
        (
            "PASS"
            if result["passed"]
            else "FAIL"
        ),
    )


# ============================================================
# REOPEN TEST
# ============================================================

def verify_reopen():

    connection = duckdb.connect(
        str(DUCKDB_PATH),
        read_only=True,
    )

    try:

        objects = [
            "gold.v_reporting_date_boundaries",
            "gold.dim_date",
            "gold.dim_budget_organization",
            "gold.dim_budget_organization_pbi",
            "gold.fact_erp_finance_pbi",
            "gold.fact_framsikt_finance_pbi",
            "gold.v_finance_quality",
            "gold.v_period_quality",
        ]

        for object_name in objects:

            connection.execute(
                "SELECT COUNT(*) FROM "
                + object_name
            ).fetchone()

    finally:

        connection.close()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)

    print(
        "WF1 GOLD REPORTING BUILDER V3"
    )

    print("=" * 100)

    print(
        "Database:",
        DUCKDB_PATH,
    )

    connection = None

    try:

        connection = connect_database()

        verify_gold_objects(
            connection
        )

        # ----------------------------------------------------
        # NORMALIZED PERIODS
        # ----------------------------------------------------

        create_erp_period_view(
            connection
        )

        create_framsikt_period_view(
            connection
        )

        period_validation = (
            validate_period_parsing(
                connection
            )
        )

        # ----------------------------------------------------
        # REPORTING DATE BOUNDARIES
        # ----------------------------------------------------

        create_reporting_date_boundaries(
            connection
        )

        # ----------------------------------------------------
        # DAILY DATE DIMENSION
        # ----------------------------------------------------

        create_dim_date(
            connection
        )

        dim_date_validation = (
            validate_dim_date(
                connection
            )
        )

        # ----------------------------------------------------
        # BUDGET ORGANIZATION
        # ----------------------------------------------------

        create_budget_organization_powerbi_view(
            connection
        )

        budget_organization_validation = (
            validate_budget_organization(
                connection
            )
        )

        # ----------------------------------------------------
        # ERP
        # ----------------------------------------------------

        create_erp_actual_horizon(
            connection
        )

        create_erp_powerbi_fact(
            connection
        )

        create_erp_monthly_kpi_view(
            connection
        )

        # ----------------------------------------------------
        # FRAMSIKT
        # ----------------------------------------------------

        create_framsikt_powerbi_fact(
            connection
        )

        create_framsikt_summary_view(
            connection
        )

        # ----------------------------------------------------
        # QUALITY
        # ----------------------------------------------------

        create_finance_quality_view(
            connection
        )

        create_period_quality_view(
            connection
        )

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        counts = get_counts(
            connection
        )

        print()
        print("=" * 100)

        print(
            "REPORTING OBJECTS"
        )

        print("=" * 100)

        for object_name, rows in counts:

            print(
                object_name,
                "| rows:",
                rows,
            )

        print_period_validation(
            period_validation
        )

        print_date_boundaries(
            connection
        )

        print_dim_date_validation(
            dim_date_validation
        )

        print_budget_organization_validation(
            budget_organization_validation
        )

        # ----------------------------------------------------
        # FAILURE COUNT
        # ----------------------------------------------------

        invalid_periods = (
            period_validation[
                "erp_invalid"
            ]
            + period_validation[
                "framsikt_invalid"
            ]
        )

        failures = 0

        if not dim_date_validation[
            "passed"
        ]:
            failures += 1

        if not budget_organization_validation[
            "passed"
        ]:
            failures += 1

        # ----------------------------------------------------
        # CLOSE / REOPEN
        # ----------------------------------------------------

        connection.close()
        connection = None

        verify_reopen()

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print()
        print("=" * 100)

        print(
            "GOLD REPORTING BUILD SUMMARY"
        )

        print("=" * 100)

        print(
            "Objects         :",
            len(counts),
        )

        print(
            "Invalid periods :",
            invalid_periods,
        )

        print(
            "Failures        :",
            failures,
        )

        print(
            "Reopen          : PASS"
        )

        if failures > 0:

            print(
                "Result          : FAIL"
            )

            print("=" * 100)

            return 1

        if invalid_periods > 0:

            print(
                "Result          : PASS WITH WARNINGS"
            )

            print("=" * 100)

            return 0

        print(
            "Result          : PASS"
        )

        print("=" * 100)

        return 0

    except Exception as exc:

        print()
        print("=" * 100)

        print(
            "GOLD REPORTING BUILD FAILED"
        )

        print("=" * 100)

        print(
            type(exc).__name__
            + ": "
            + str(exc)
        )

        return 1

    finally:

        if connection is not None:

            connection.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )