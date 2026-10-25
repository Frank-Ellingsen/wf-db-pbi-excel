from __future__ import annotations

import sys
from pathlib import Path

import duckdb


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SOURCE_DB = (
    PROJECT_ROOT
    / "db"
    / "project_finance.duckdb"
)

POWERBI_DB = (
    PROJECT_ROOT
    / "db"
    / "project_finance_powerbi.duckdb"
)


# ============================================================
# SETTINGS
# ============================================================

STORAGE_VERSION = "v1.5.0"


# ============================================================
# PUBLISH OBJECTS
# ============================================================

PUBLISH_OBJECTS = {
    "dim_date":
        "gold.dim_date",

    "dim_account":
        "gold.dim_account",

    "dim_kostra_function":
        "gold.dim_kostra_function",

    "dim_budget_organization":
        "gold.dim_budget_organization_pbi",

    "fact_erp_finance":
        "gold.fact_erp_finance",

    "fact_framsikt_finance":
        "gold.fact_framsikt_finance",

    "finance_quality":
        "gold.v_finance_quality",

    "period_quality":
        "gold.v_period_quality",

    "unmapped_kostra_functions":
        "gold.v_unmapped_kostra_functions",
}


# ============================================================
# SQL PATH
# ============================================================

def sql_path(path):
    """
    Return SQL-safe absolute path.
    """

    return (
        path.resolve()
        .as_posix()
        .replace(
            "'",
            "''",
        )
    )


# ============================================================
# PRECHECK
# ============================================================

def precheck():
    """
    Check source DuckDB.
    """

    if not SOURCE_DB.exists():

        raise FileNotFoundError(
            "Source DuckDB not found: "
            + str(SOURCE_DB)
        )


# ============================================================
# REMOVE OLD PUBLISH DATABASE
# ============================================================

def remove_old_publish_database():
    """
    Remove previous Power BI publish database.

    The authoritative project_finance.duckdb
    is never modified.
    """

    if POWERBI_DB.exists():

        POWERBI_DB.unlink()

        print(
            "Removed old Power BI database:",
            POWERBI_DB,
        )


# ============================================================
# VERIFY SOURCE OBJECTS
# ============================================================

def verify_source_objects(connection):
    """
    Verify every required Gold source object.
    """

    print()
    print("=" * 100)
    print(
        "SOURCE OBJECT CHECK"
    )
    print("=" * 100)

    for publish_name, source_name in (
        PUBLISH_OBJECTS.items()
    ):

        try:

            row_count = (
                connection.execute(
                    "SELECT COUNT(*) FROM "
                    + source_name
                )
                .fetchone()[0]
            )

        except Exception as exc:

            raise RuntimeError(
                "Unable to query "
                + source_name
                + ": "
                + str(exc)
            ) from exc

        print(
            "PASS | {:30} | rows: {}".format(
                source_name,
                row_count,
            )
        )


# ============================================================
# CREATE COMPATIBLE DATABASE
# ============================================================

def create_compatible_database(
    connection,
):
    """
    Create attached DuckDB using v1.5-compatible
    storage format.

    DuckDB storage version 68 corresponds
    to DuckDB v1.5.x.
    """

    target = sql_path(
        POWERBI_DB
    )

    sql = (
        "ATTACH '"
        + target
        + "' AS powerbi "
        + "(STORAGE_VERSION '"
        + STORAGE_VERSION
        + "')"
    )

    connection.execute(
        sql
    )


# ============================================================
# CREATE PUBLISH SCHEMA
# ============================================================

def create_publish_schema(connection):

    connection.execute(
        """
        CREATE SCHEMA powerbi.gold
        """
    )


# ============================================================
# MATERIALIZE OBJECT
# ============================================================

def materialize_object(
    connection,
    target_name,
    source_name,
):
    """
    Materialize Gold view/table into the
    Power BI database as a physical table.
    """

    sql = (
        "CREATE TABLE powerbi.gold."
        + target_name
        + " AS "
        + "SELECT * FROM "
        + source_name
    )

    connection.execute(
        sql
    )


# ============================================================
# MATERIALIZE ALL
# ============================================================

def materialize_all(connection):

    print()
    print("=" * 100)
    print(
        "POWER BI MATERIALIZATION"
    )
    print("=" * 100)

    for target_name, source_name in (
        PUBLISH_OBJECTS.items()
    ):

        materialize_object(
            connection,
            target_name,
            source_name,
        )

        row_count = (
            connection.execute(
                "SELECT COUNT(*) "
                "FROM powerbi.gold."
                + target_name
            )
            .fetchone()[0]
        )

        print(
            "WRITTEN | {:30} | rows: {}".format(
                "gold." + target_name,
                row_count,
            )
        )


# ============================================================
# VERIFY ROW COUNTS
# ============================================================

def verify_row_counts(connection):
    """
    Reconcile source and Power BI database.
    """

    print()
    print("=" * 100)
    print(
        "ROW COUNT RECONCILIATION"
    )
    print("=" * 100)

    failures = 0

    results = []

    for target_name, source_name in (
        PUBLISH_OBJECTS.items()
    ):

        source_count = (
            connection.execute(
                "SELECT COUNT(*) FROM "
                + source_name
            )
            .fetchone()[0]
        )

        target_count = (
            connection.execute(
                "SELECT COUNT(*) "
                "FROM powerbi.gold."
                + target_name
            )
            .fetchone()[0]
        )

        passed = (
            source_count
            == target_count
        )

        if not passed:

            failures += 1

        status = (
            "PASS"
            if passed
            else "FAIL"
        )

        print(
            "{} | {:30} | Source: {:6} | PowerBI: {:6}".format(
                status,
                target_name,
                source_count,
                target_count,
            )
        )

        results.append(
            {
                "object":
                    target_name,
                "source":
                    source_count,
                "target":
                    target_count,
                "passed":
                    passed,
            }
        )

    return failures, results


# ============================================================
# VERIFY BUDGET ORGANIZATION
# ============================================================

def verify_budget_organization(connection):
    """
    Verify the published budget organization dimension.

    The dimension is currently N1/N2 only.
    No fact relationship is assumed here.
    """

    result = connection.execute(
        """
        SELECT
            COUNT(*) AS row_count,

            COUNT(
                DISTINCT budget_organization_key
            ) AS unique_keys,

            SUM(
                CASE
                    WHEN budget_organization_key IS NULL
                        THEN 1
                    ELSE 0
                END
            ) AS null_keys,

            SUM(
                CASE
                    WHEN budget_level_2_code IS NULL
                        THEN 1
                    ELSE 0
                END
            ) AS null_level_2_codes,

            SUM(
                CASE
                    WHEN budget_level_2_name IS NULL
                        THEN 1
                    ELSE 0
                END
            ) AS null_level_2_names

        FROM powerbi.gold.dim_budget_organization
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

    passed = (
        row_count > 0
        and null_keys == 0
        and duplicate_keys == 0
        and null_level_2_codes == 0
        and null_level_2_names == 0
    )

    print()
    print("=" * 100)
    print(
        "BUDGET ORGANIZATION CHECK"
    )
    print("=" * 100)

    print(
        "Rows             :",
        row_count,
    )

    print(
        "Unique keys      :",
        unique_keys,
    )

    print(
        "NULL keys        :",
        null_keys,
    )

    print(
        "Duplicate keys   :",
        duplicate_keys,
    )

    print(
        "NULL Level 2 code:",
        null_level_2_codes,
    )

    print(
        "NULL Level 2 name:",
        null_level_2_names,
    )

    print(
        "Result           :",
        (
            "PASS"
            if passed
            else "FAIL"
        ),
    )

    return {
        "row_count":
            row_count,
        "unique_keys":
            unique_keys,
        "null_keys":
            null_keys,
        "duplicate_keys":
            duplicate_keys,
        "null_level_2_codes":
            null_level_2_codes,
        "null_level_2_names":
            null_level_2_names,
        "passed":
            passed,
    }


# ============================================================
# VERIFY STORAGE VERSION
# ============================================================

def verify_storage_version(connection):
    """
    Read actual storage-version metadata
    from DuckDB.
    """

    row = connection.execute(
        """
        SELECT
            database_name,
            tags['storage_version']
                AS storage_version

        FROM duckdb_databases()

        WHERE database_name = 'powerbi'
        """
    ).fetchone()

    if row is None:

        raise RuntimeError(
            "Power BI database metadata not found."
        )

    database_name = row[0]
    storage_version = row[1]

    print()
    print("=" * 100)
    print(
        "STORAGE VERSION"
    )
    print("=" * 100)

    print(
        "Database        :",
        database_name,
    )

    print(
        "Requested       :",
        STORAGE_VERSION,
    )

    print(
        "Actual storage  :",
        storage_version,
    )

    if storage_version is None:

        raise RuntimeError(
            "Unable to determine storage version."
        )

    if not str(
        storage_version
    ).startswith(
        "v1.5"
    ):

        raise RuntimeError(
            "Unexpected Power BI storage version: "
            + str(storage_version)
        )

    print(
        "Compatibility   : PASS"
    )

    return storage_version


# ============================================================
# DETACH
# ============================================================

def detach_powerbi(connection):

    connection.execute(
        """
        DETACH powerbi
        """
    )


# ============================================================
# REOPEN TEST
# ============================================================

def verify_reopen():
    """
    Reopen publish database with DuckDB and
    verify all published Gold tables.
    """

    connection = duckdb.connect(
        str(POWERBI_DB),
        read_only=True,
    )

    try:

        print()
        print("=" * 100)
        print(
            "REOPEN TEST"
        )
        print("=" * 100)

        for target_name in PUBLISH_OBJECTS:

            row_count = (
                connection.execute(
                    "SELECT COUNT(*) "
                    "FROM gold."
                    + target_name
                )
                .fetchone()[0]
            )

            print(
                "PASS | {:30} | rows: {}".format(
                    "gold." + target_name,
                    row_count,
                )
            )

    finally:

        connection.close()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print(
        "WF1 POWER BI DUCKDB PUBLISHER V1"
    )
    print("=" * 100)

    print(
        "Source :",
        SOURCE_DB,
    )

    print(
        "Target :",
        POWERBI_DB,
    )

    print(
        "Storage:",
        STORAGE_VERSION,
    )

    try:

        precheck()

        remove_old_publish_database()

        # ----------------------------------------------------
        # Open authoritative DuckDB database
        # ----------------------------------------------------

        connection = duckdb.connect(
            str(SOURCE_DB)
        )

        try:

            # ------------------------------------------------
            # Validate source Gold model
            # ------------------------------------------------

            verify_source_objects(
                connection
            )

            # ------------------------------------------------
            # Create compatible attached database
            # ------------------------------------------------

            create_compatible_database(
                connection
            )

            create_publish_schema(
                connection
            )

            # ------------------------------------------------
            # Materialize reporting tables
            # ------------------------------------------------

            materialize_all(
                connection
            )

            # ------------------------------------------------
            # Reconciliation
            # ------------------------------------------------

            failures, _ = (
                verify_row_counts(
                    connection
                )
            )

            # ------------------------------------------------
            # Budget organization validation
            # ------------------------------------------------

            budget_organization_check = (
                verify_budget_organization(
                    connection
                )
            )

            if not budget_organization_check[
                "passed"
            ]:

                failures += 1

            # ------------------------------------------------
            # Storage version check
            # ------------------------------------------------

            storage_version = (
                verify_storage_version(
                    connection
                )
            )

            # ------------------------------------------------
            # Detach cleanly
            # ------------------------------------------------

            detach_powerbi(
                connection
            )

        finally:

            connection.close()

        # ----------------------------------------------------
        # Reopen target
        # ----------------------------------------------------

        verify_reopen()

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print(
            "POWER BI PUBLISH SUMMARY"
        )
        print("=" * 100)

        print(
            "Target database :",
            POWERBI_DB,
        )

        print(
            "Storage version :",
            storage_version,
        )

        print(
            "Objects         :",
            len(
                PUBLISH_OBJECTS
            ),
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

        print(
            "Result          : PASS"
        )

        print("=" * 100)

        return 0

    except Exception as exc:

        print()
        print("=" * 100)
        print(
            "POWER BI PUBLISH FAILED"
        )
        print("=" * 100)

        print(
            type(exc).__name__
            + ": "
            + str(exc)
        )

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )