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
    Open DuckDB read-only.
    """

    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(
            "DuckDB database not found: "
            + str(DUCKDB_PATH)
        )

    return duckdb.connect(
        str(DUCKDB_PATH),
        read_only=True,
    )


# ============================================================
# HEADER
# ============================================================

def print_header(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


# ============================================================
# QUERY PRINTER
# ============================================================

def print_query(
    connection,
    title,
    sql,
):
    """
    Execute query and print result as DataFrame.
    """

    print_header(title)

    df = connection.execute(
        sql
    ).fetchdf()

    if df.empty:
        print("No rows found.")
        return df

    print(
        df.to_string(
            index=False
        )
    )

    return df


# ============================================================
# ERP ORPHAN FUNCTIONS
# ============================================================

def diagnose_erp_function_orphans(
    connection,
):
    """
    Find ERP KOSTRA function IDs that do not
    exist in current KOSTRA function dimension.
    """

    sql = """
        SELECT
            f.kostra_function_id,

            COUNT(*) AS affected_rows,

            COUNT(
                DISTINCT f.location
            ) AS locations,

            SUM(
                COALESCE(f.budget, 0)
            ) AS budget,

            SUM(
                COALESCE(f.actual, 0)
            ) AS actual

        FROM silver.erp_finance AS f

        LEFT JOIN
            silver.kostra_function_current AS d

            ON f.kostra_function_id
             = d.kostra_function_id

        WHERE
            f.kostra_function_id IS NOT NULL

        AND
            d.kostra_function_id IS NULL

        GROUP BY
            f.kostra_function_id

        ORDER BY
            f.kostra_function_id
    """

    return print_query(
        connection,
        "ERP - MISSING KOSTRA FUNCTION IDS",
        sql,
    )


# ============================================================
# ERP ORPHAN DETAILS
# ============================================================

def diagnose_erp_function_details(
    connection,
):
    """
    Show contextual ERP values for missing
    KOSTRA function IDs.
    """

    sql = """
        SELECT
            f.kostra_function_id,
            f.period,
            f.location,
            f.service_area,
            f.main_group,
            f.sub_group,
            f.account_code,
            f.account_name,
            f.budget,
            f.actual,
            f._silver_source_sha256,
            f._silver_registry_id

        FROM silver.erp_finance AS f

        LEFT JOIN
            silver.kostra_function_current AS d

            ON f.kostra_function_id
             = d.kostra_function_id

        WHERE
            f.kostra_function_id IS NOT NULL

        AND
            d.kostra_function_id IS NULL

        ORDER BY
            f.kostra_function_id,
            f.period,
            f.location,
            f.account_code
    """

    return print_query(
        connection,
        "ERP - ORPHAN FUNCTION DETAILS",
        sql,
    )


# ============================================================
# FRAMSIKT ORPHAN FUNCTIONS
# ============================================================

def diagnose_framsikt_function_orphans(
    connection,
):
    """
    Find Framsikt KOSTRA function IDs that do
    not exist in current function dimension.
    """

    sql = """
        SELECT
            f.kostra_function_id,

            COUNT(*) AS affected_rows,

            COUNT(
                DISTINCT f.location
            ) AS locations,

            COUNT(
                DISTINCT f.organizational_unit
            ) AS organizational_units,

            SUM(
                COALESCE(f.actual_ytd, 0)
            ) AS actual_ytd,

            SUM(
                COALESCE(f.budget_ytd, 0)
            ) AS budget_ytd,

            SUM(
                COALESCE(f.annual_budget, 0)
            ) AS annual_budget,

            SUM(
                COALESCE(f.actual_prior_year, 0)
            ) AS actual_prior_year

        FROM silver.framsikt_finance AS f

        LEFT JOIN
            silver.kostra_function_current AS d

            ON f.kostra_function_id
             = d.kostra_function_id

        WHERE
            f.kostra_function_id IS NOT NULL

        AND
            d.kostra_function_id IS NULL

        GROUP BY
            f.kostra_function_id

        ORDER BY
            f.kostra_function_id
    """

    return print_query(
        connection,
        "FRAMSIKT - MISSING KOSTRA FUNCTION IDS",
        sql,
    )


# ============================================================
# FRAMSIKT ORPHAN DETAILS
# ============================================================

def diagnose_framsikt_function_details(
    connection,
):
    """
    Show contextual Framsikt values for missing
    KOSTRA function IDs.
    """

    sql = """
        SELECT
            f.kostra_function_id,
            f.period,
            f.location,
            f.organizational_unit,
            f.account_type,
            f.account_name,
            f.account_class,
            f.economic_class,
            f.actual_ytd,
            f.budget_ytd,
            f.annual_budget,
            f.actual_prior_year,
            f._silver_source_sha256,
            f._silver_registry_id

        FROM silver.framsikt_finance AS f

        LEFT JOIN
            silver.kostra_function_current AS d

            ON f.kostra_function_id
             = d.kostra_function_id

        WHERE
            f.kostra_function_id IS NOT NULL

        AND
            d.kostra_function_id IS NULL

        ORDER BY
            f.kostra_function_id,
            f.period,
            f.location,
            f.organizational_unit
    """

    return print_query(
        connection,
        "FRAMSIKT - ORPHAN FUNCTION DETAILS",
        sql,
    )


# ============================================================
# FUNCTION DIMENSION
# ============================================================

def show_function_dimension(
    connection,
):
    """
    Print available current KOSTRA function keys.
    """

    sql = """
        SELECT
            kostra_function_id,
            kostra_function_name,
            main_function_code,
            main_function_name,
            service_area_code,
            service_area_name,
            function_group_code,
            function_group_name,
            active

        FROM silver.kostra_function_current

        ORDER BY
            kostra_function_id
    """

    return print_query(
        connection,
        "CURRENT KOSTRA FUNCTION DIMENSION",
        sql,
    )


# ============================================================
# ACCOUNT DIAGNOSTIC
# ============================================================

def diagnose_erp_account_orphans(
    connection,
):
    """
    Confirm ERP account relationship.
    """

    sql = """
        SELECT
            f.account_code,
            f.account_name,

            COUNT(*) AS affected_rows,

            SUM(
                COALESCE(f.budget, 0)
            ) AS budget,

            SUM(
                COALESCE(f.actual, 0)
            ) AS actual

        FROM silver.erp_finance AS f

        LEFT JOIN
            silver.kostra_account_current AS d

            ON f.account_code
             = d.account_code

        WHERE
            f.account_code IS NOT NULL

        AND
            d.account_code IS NULL

        GROUP BY
            f.account_code,
            f.account_name

        ORDER BY
            f.account_code
    """

    return print_query(
        connection,
        "ERP - MISSING ACCOUNT CODES",
        sql,
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    erp_functions,
    framsikt_functions,
    erp_accounts,
):
    print_header(
        "DIAGNOSTIC SUMMARY"
    )

    print(
        "ERP orphan function IDs      :",
        len(erp_functions),
    )

    print(
        "Framsikt orphan function IDs :",
        len(framsikt_functions),
    )

    print(
        "ERP orphan account codes     :",
        len(erp_accounts),
    )

    if (
        len(erp_functions) == 0
        and len(framsikt_functions) == 0
        and len(erp_accounts) == 0
    ):
        print()
        print(
            "Result: No relationship "
            "problems detected."
        )

    else:
        print()
        print(
            "Result: Relationship differences found."
        )

        print(
            "No data has been modified."
        )


# ============================================================
# MAIN
# ============================================================

def main():
    """
    Diagnose Silver relationship failures.

    This program is read-only.
    """

    print()
    print("=" * 100)
    print(
        "WF1 DUCKDB RELATIONSHIP DIAGNOSTICS V1"
    )
    print("=" * 100)

    print(
        "Database:",
        DUCKDB_PATH,
    )

    try:
        connection = connect_database()

    except Exception as exc:

        print()
        print(
            "DATABASE ERROR:"
        )

        print(
            type(exc).__name__
            + ": "
            + str(exc)
        )

        return 1

    try:

        # ----------------------------------------------------
        # ERP KOSTRA FUNCTION
        # ----------------------------------------------------

        erp_functions = (
            diagnose_erp_function_orphans(
                connection
            )
        )

        diagnose_erp_function_details(
            connection
        )

        # ----------------------------------------------------
        # FRAMSIKT KOSTRA FUNCTION
        # ----------------------------------------------------

        framsikt_functions = (
            diagnose_framsikt_function_orphans(
                connection
            )
        )

        diagnose_framsikt_function_details(
            connection
        )

        # ----------------------------------------------------
        # ERP ACCOUNT
        # ----------------------------------------------------

        erp_accounts = (
            diagnose_erp_account_orphans(
                connection
            )
        )

        # ----------------------------------------------------
        # DIMENSION CONTENT
        # ----------------------------------------------------

        show_function_dimension(
            connection
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print_summary(
            erp_functions,
            framsikt_functions,
            erp_accounts,
        )

        return 0

    except Exception as exc:

        print()
        print("=" * 100)
        print(
            "DIAGNOSTIC ERROR"
        )
        print("=" * 100)

        print(
            type(exc).__name__
            + ": "
            + str(exc)
        )

        return 1

    finally:

        connection.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )