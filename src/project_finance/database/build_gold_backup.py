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
            "DuckDB database not found: "
            + str(DUCKDB_PATH)
        )

    return duckdb.connect(
        str(DUCKDB_PATH)
    )


# ============================================================
# PRECHECK
# ============================================================

def verify_required_silver_objects(
    connection,
):
    """
    Verify that all required Silver objects
    exist before building Gold.
    """

    required_objects = [
        "erp_finance",
        "framsikt_finance",
        "kostra_account_current",
        "kostra_function_current",
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

    existing = {
        row[0]
        for row in cursor.fetchall()
    }

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

def create_gold_schema(
    connection,
):
    """
    Ensure Gold schema exists.
    """

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS gold
        """
    )


# ============================================================
# DIM ACCOUNT
# ============================================================

def create_dim_account(
    connection,
):
    """
    Current KOSTRA account dimension.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW gold.dim_account AS

        SELECT
            account_code,
            account_name,
            account_key,

            kostra_art_4digit,
            kostra_art_3digit,
            kostra_art_name,

            account_class_id,
            account_class_name,

            main_category_code,
            main_category_name,

            main_group_code,
            main_group_name,

            accounting_rule_description,
            active,

            _contract_version,
            _dataset,
            _source_file,
            _run_id,
            _loaded_at_utc,
            _validated_at_utc,

            _silver_source_sha256,
            _silver_snapshot_date,
            _silver_registry_id,
            _silver_materialized_at_utc

        FROM silver.kostra_account_current
        """
    )


# ============================================================
# DIM KOSTRA FUNCTION
# ============================================================

def create_dim_kostra_function(
    connection,
):
    """
    Current KOSTRA function dimension.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.dim_kostra_function AS

        SELECT
            kostra_function_id,
            kostra_function_name,
            function_key,

            active,

            main_function_code,
            main_function_name,
            main_function_key,

            service_area_code,
            service_area_name,

            function_group_code,
            function_group_name,

            accounting_rule_description,

            _contract_version,
            _dataset,
            _source_file,
            _run_id,
            _loaded_at_utc,
            _validated_at_utc,

            _silver_source_sha256,
            _silver_snapshot_date,
            _silver_registry_id,
            _silver_materialized_at_utc

        FROM silver.kostra_function_current
        """
    )


# ============================================================
# ERP FACT
# ============================================================

def create_fact_erp_finance(
    connection,
):
    """
    ERP financial fact view.

    Original ERP values are preserved.

    Function mapping is enriched from the
    KOSTRA dimension where a match exists.

    Unknown IDs remain in the fact table and
    receive mapping status UNMAPPED.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.fact_erp_finance AS

        SELECT
            f.period,
            f.month,
            f.month_number,
            f.tertial,

            f.location,

            f.kostra_function_id,

            d.kostra_function_name,
            d.function_key,

            d.main_function_code,
            d.main_function_name,

            d.service_area_code,
            d.service_area_name,

            d.function_group_code,
            d.function_group_name,

            CASE
                WHEN f.kostra_function_id IS NULL
                    THEN 'NOT_APPLICABLE'

                WHEN d.kostra_function_id IS NULL
                    THEN 'UNMAPPED'

                ELSE 'MATCHED'
            END
            AS function_mapping_status,

            f.kostra_art,

            f.account_code,
            f.account_name,

            a.account_key,

            a.kostra_art_4digit,
            a.kostra_art_3digit,
            a.kostra_art_name,

            a.account_class_id,
            a.account_class_name,

            a.main_category_code,
            a.main_category_name,

            a.main_group_code,
            a.main_group_name,

            CASE
                WHEN f.account_code IS NULL
                    THEN 'NOT_APPLICABLE'

                WHEN a.account_code IS NULL
                    THEN 'UNMAPPED'

                ELSE 'MATCHED'
            END
            AS account_mapping_status,

            f.budget,
            f.actual,

            f.budget - f.actual
                AS variance,

            CASE
                WHEN f.budget IS NULL
                    THEN NULL

                WHEN f.budget = 0
                    THEN NULL

                ELSE
                    (f.budget - f.actual)
                    / ABS(f.budget)
            END
            AS variance_pct,

            f.status,
            f.service_area,
            f.main_group,
            f.sub_group,

            f._contract_version,
            f._dataset,
            f._source_file,
            f._run_id,
            f._loaded_at_utc,
            f._validated_at_utc,

            f._silver_source_sha256,
            f._silver_snapshot_date,
            f._silver_registry_id,
            f._silver_materialized_at_utc

        FROM silver.erp_finance AS f

        LEFT JOIN gold.dim_kostra_function AS d
            ON f.kostra_function_id
             = d.kostra_function_id

        LEFT JOIN gold.dim_account AS a
            ON f.account_code
             = a.account_code
        """
    )


# ============================================================
# FRAMSIKT FACT
# ============================================================

def create_fact_framsikt_finance(
    connection,
):
    """
    Framsikt financial fact view.

    Framsikt remains separate from ERP because
    the datasets currently have different grain
    and financial measures.

    Unknown function IDs are retained.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.fact_framsikt_finance AS

        SELECT
            f.period,
            f.location,
            f.organizational_unit,

            f.kostra_function_id,

            d.kostra_function_name,
            d.function_key,

            d.main_function_code,
            d.main_function_name,

            d.service_area_code,
            d.service_area_name,

            d.function_group_code,
            d.function_group_name,

            CASE
                WHEN f.kostra_function_id IS NULL
                    THEN 'NOT_APPLICABLE'

                WHEN d.kostra_function_id IS NULL
                    THEN 'UNMAPPED'

                ELSE 'MATCHED'
            END
            AS function_mapping_status,

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
                    THEN NULL

                WHEN f.budget_ytd = 0
                    THEN NULL

                ELSE
                    (f.budget_ytd - f.actual_ytd)
                    / ABS(f.budget_ytd)
            END
            AS variance_ytd_pct,

            f.actual_ytd - f.actual_prior_year
                AS change_vs_prior_year,

            CASE
                WHEN f.actual_prior_year IS NULL
                    THEN NULL

                WHEN f.actual_prior_year = 0
                    THEN NULL

                ELSE
                    (f.actual_ytd - f.actual_prior_year)
                    / ABS(f.actual_prior_year)
            END
            AS change_vs_prior_year_pct,

            f._contract_version,
            f._dataset,
            f._source_file,
            f._run_id,
            f._loaded_at_utc,
            f._validated_at_utc,

            f._silver_source_sha256,
            f._silver_snapshot_date,
            f._silver_registry_id,
            f._silver_materialized_at_utc

        FROM silver.framsikt_finance AS f

        LEFT JOIN gold.dim_kostra_function AS d
            ON f.kostra_function_id
             = d.kostra_function_id
        """
    )


# ============================================================
# UNMAPPED FUNCTION VIEW
# ============================================================

def create_unmapped_function_view(
    connection,
):
    """
    Consolidated diagnostic view of source
    function IDs that do not map to the current
    KOSTRA function dimension.

    No automatic correction is performed.
    """

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        gold.v_unmapped_kostra_functions AS

        SELECT
            'ERP' AS source_system,

            kostra_function_id,

            COUNT(*) AS affected_rows,

            SUM(
                COALESCE(actual, 0)
            ) AS actual_value,

            SUM(
                COALESCE(budget, 0)
            ) AS budget_value

        FROM gold.fact_erp_finance

        WHERE function_mapping_status = 'UNMAPPED'

        GROUP BY
            kostra_function_id

        UNION ALL

        SELECT
            'FRAMSIKT' AS source_system,

            kostra_function_id,

            COUNT(*) AS affected_rows,

            SUM(
                COALESCE(actual_ytd, 0)
            ) AS actual_value,

            SUM(
                COALESCE(budget_ytd, 0)
            ) AS budget_value

        FROM gold.fact_framsikt_finance

        WHERE function_mapping_status = 'UNMAPPED'

        GROUP BY
            kostra_function_id
        """
    )


# ============================================================
# GOLD BUILD AUDIT
# ============================================================

def create_gold_audit_view(
    connection,
):
    """
    High-level Gold quality overview.
    """

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
                    WHEN function_mapping_status = 'UNMAPPED'
                    THEN 1
                    ELSE 0
                END
            )
                AS unmapped_function_rows,

            SUM(
                CASE
                    WHEN account_mapping_status = 'UNMAPPED'
                    THEN 1
                    ELSE 0
                END
            )
                AS unmapped_account_rows

        FROM gold.fact_erp_finance

        UNION ALL

        SELECT
            'framsikt_finance'
                AS dataset_name,

            COUNT(*)
                AS row_count,

            SUM(
                CASE
                    WHEN function_mapping_status = 'UNMAPPED'
                    THEN 1
                    ELSE 0
                END
            )
                AS unmapped_function_rows,

            CAST(NULL AS BIGINT)
                AS unmapped_account_rows

        FROM gold.fact_framsikt_finance
        """
    )


# ============================================================
# VERIFY ROW COUNTS
# ============================================================

def verify_row_counts(
    connection,
):
    """
    Fact Gold views must preserve source
    Silver row counts.
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

        silver_count = (
            connection.execute(
                "SELECT COUNT(*) "
                "FROM silver."
                + silver_name
            ).fetchone()[0]
        )

        gold_count = (
            connection.execute(
                "SELECT COUNT(*) "
                "FROM gold."
                + gold_name
            ).fetchone()[0]
        )

        passed = (
            silver_count
            == gold_count
        )

        checks.append(
            {
                "dataset": silver_name,
                "silver_rows": silver_count,
                "gold_rows": gold_count,
                "passed": passed,
            }
        )

    return checks


# ============================================================
# VERIFY DIMENSIONS
# ============================================================

def verify_dimensions(
    connection,
):
    """
    Check current Gold dimension populations.
    """

    account_rows = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM gold.dim_account
            """
        ).fetchone()[0]
    )

    function_rows = (
        connection.execute(
            """
            SELECT COUNT(*)
            FROM gold.dim_kostra_function
            """
        ).fetchone()[0]
    )

    return {
        "account_rows": account_rows,
        "function_rows": function_rows,
        "account_passed": (
            account_rows > 0
        ),
        "function_passed": (
            function_rows > 0
        ),
    }


# ============================================================
# GET UNMAPPED SUMMARY
# ============================================================

def get_unmapped_summary(
    connection,
):

    return connection.execute(
        """
        SELECT
            source_system,
            kostra_function_id,
            affected_rows,
            actual_value,
            budget_value

        FROM gold.v_unmapped_kostra_functions

        ORDER BY
            source_system,
            kostra_function_id
        """
    ).fetchall()


# ============================================================
# PRINT ROW CHECKS
# ============================================================

def print_row_checks(checks):

    print()
    print("=" * 100)
    print("FACT ROW RECONCILIATION")
    print("=" * 100)

    for check in checks:

        if check["passed"]:
            status = "PASS"
        else:
            status = "FAIL"

        print(
            "{} | {:20} | Silver: {:6} | Gold: {:6}".format(
                status,
                check["dataset"],
                check["silver_rows"],
                check["gold_rows"],
            )
        )


# ============================================================
# PRINT DIMENSION CHECKS
# ============================================================

def print_dimension_checks(result):

    print()
    print("=" * 100)
    print("DIMENSION CHECKS")
    print("=" * 100)

    account_status = (
        "PASS"
        if result["account_passed"]
        else "FAIL"
    )

    function_status = (
        "PASS"
        if result["function_passed"]
        else "FAIL"
    )

    print(
        "{} | dim_account          | rows: {}".format(
            account_status,
            result["account_rows"],
        )
    )

    print(
        "{} | dim_kostra_function  | rows: {}".format(
            function_status,
            result["function_rows"],
        )
    )


# ============================================================
# PRINT UNMAPPED
# ============================================================

def print_unmapped(rows):

    print()
    print("=" * 100)
    print("UNMAPPED KOSTRA FUNCTIONS")
    print("=" * 100)

    if not rows:

        print(
            "None"
        )

        return

    for row in rows:

        print(
            "WARNING | {:10} | function {:4} | rows {:4} | actual {:12.2f} | budget {:12.2f}".format(
                row[0],
                row[1],
                row[2],
                float(
                    row[3] or 0
                ),
                float(
                    row[4] or 0
                ),
            )
        )


# ============================================================
# GOLD OBJECTS
# ============================================================

def print_gold_objects():

    print()
    print("=" * 100)
    print("GOLD OBJECTS")
    print("=" * 100)

    objects = [
        "gold.dim_account",
        "gold.dim_kostra_function",
        "gold.fact_erp_finance",
        "gold.fact_framsikt_finance",
        "gold.v_unmapped_kostra_functions",
        "gold.v_data_quality_summary",
    ]

    for name in objects:

        print(
            "  -",
            name,
        )


# ============================================================
# REOPEN TEST
# ============================================================

def verify_reopen():
    """
    Reopen database read-only after build.
    """

    connection = duckdb.connect(
        str(DUCKDB_PATH),
        read_only=True,
    )

    try:

        objects = [
            "gold.dim_account",
            "gold.dim_kostra_function",
            "gold.fact_erp_finance",
            "gold.fact_framsikt_finance",
            "gold.v_unmapped_kostra_functions",
            "gold.v_data_quality_summary",
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
    print("WF1 GOLD BUILDER V1")
    print("=" * 100)

    print(
        "Database:",
        DUCKDB_PATH,
    )

    connection = None

    try:

        connection = connect_database()

        # ----------------------------------------------------
        # PRECHECK
        # ----------------------------------------------------

        verify_required_silver_objects(
            connection
        )

        create_gold_schema(
            connection
        )

        # ----------------------------------------------------
        # DIMENSIONS
        # ----------------------------------------------------

        create_dim_account(
            connection
        )

        create_dim_kostra_function(
            connection
        )

        # ----------------------------------------------------
        # FACTS
        # ----------------------------------------------------

        create_fact_erp_finance(
            connection
        )

        create_fact_framsikt_finance(
            connection
        )

        # ----------------------------------------------------
        # QUALITY / DIAGNOSTIC VIEWS
        # ----------------------------------------------------

        create_unmapped_function_view(
            connection
        )

        create_gold_audit_view(
            connection
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        row_checks = verify_row_counts(
            connection
        )

        dimension_checks = (
            verify_dimensions(
                connection
            )
        )

        unmapped = (
            get_unmapped_summary(
                connection
            )
        )

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        print_dimension_checks(
            dimension_checks
        )

        print_row_checks(
            row_checks
        )

        print_unmapped(
            unmapped
        )

        print_gold_objects()

        # ----------------------------------------------------
        # FAILURE COUNT
        # ----------------------------------------------------

        failures = 0

        for check in row_checks:

            if not check["passed"]:
                failures += 1

        if not dimension_checks[
            "account_passed"
        ]:
            failures += 1

        if not dimension_checks[
            "function_passed"
        ]:
            failures += 1

        warnings = len(
            unmapped
        )

        # ----------------------------------------------------
        # CLOSE BEFORE REOPEN TEST
        # ----------------------------------------------------

        connection.close()
        connection = None

        verify_reopen()

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("GOLD BUILD SUMMARY")
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
            "Reopen   : PASS"
        )

        if failures > 0:

            print(
                "Result   : FAIL"
            )

            print("=" * 100)

            return 1

        if warnings > 0:

            print(
                "Result   : PASS WITH WARNINGS"
            )

            print("=" * 100)

            return 0

        print(
            "Result   : PASS"
        )

        print("=" * 100)

        return 0

    except Exception as exc:

        print()
        print("=" * 100)
        print("GOLD BUILD FAILED")
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