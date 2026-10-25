from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SILVER_DIR = PROJECT_ROOT / "data" / "silver"
DB_DIR = PROJECT_ROOT / "db"

DUCKDB_PATH = DB_DIR / "project_finance.duckdb"


# ============================================================
# DATASETS
# ============================================================

DATASETS = {
    "erp_finance": {
        "type": "fact",
        "primary_key": None,
    },
    "framsikt_finance": {
        "type": "fact",
        "primary_key": None,
    },
    "kostra_account": {
        "type": "dimension",
        "primary_key": "account_code",
    },
    "kostra_function": {
        "type": "dimension",
        "primary_key": "kostra_function_id",
    },
    "budget_organization": {
        "type": "dimension",
        "primary_key": "budget_level_2_code",
    },
}


# ============================================================
# TIME
# ============================================================

def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# SQL PATH
# ============================================================

def sql_path(path):

    return (
        path.resolve()
        .as_posix()
        .replace(
            "'",
            "''",
        )
    )


# ============================================================
# DISCOVER SILVER
# ============================================================

def discover_silver():

    discovered = {}

    for dataset_name in DATASETS:

        dataset_dir = (
            SILVER_DIR
            / dataset_name
        )

        if dataset_dir.exists():

            files = sorted(
                dataset_dir.glob(
                    "*.parquet"
                )
            )

        else:

            files = []

        discovered[
            dataset_name
        ] = files

    return discovered


# ============================================================
# SILVER PRECHECK
# ============================================================

def precheck_silver(discovered):

    errors = []

    for dataset_name, files in discovered.items():

        if len(files) == 0:

            errors.append(
                "No Silver files found for "
                + dataset_name
            )

    if errors:

        raise RuntimeError(
            "\n".join(
                errors
            )
        )


# ============================================================
# DATABASE
# ============================================================

def connect_database():

    DB_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return duckdb.connect(
        str(
            DUCKDB_PATH
        )
    )


# ============================================================
# SCHEMAS
# ============================================================

def create_schemas(connection):

    connection.execute(
        "CREATE SCHEMA IF NOT EXISTS silver"
    )

    connection.execute(
        "CREATE SCHEMA IF NOT EXISTS gold"
    )

    connection.execute(
        "CREATE SCHEMA IF NOT EXISTS audit"
    )


# ============================================================
# SILVER VIEWS
# ============================================================

def create_silver_view(
    connection,
    dataset_name,
):

    parquet_glob = (
        SILVER_DIR
        / dataset_name
        / "*.parquet"
    )

    path = sql_path(
        parquet_glob
    )

    sql = (
        "CREATE OR REPLACE VIEW silver."
        + dataset_name
        + " AS "
        + "SELECT * "
        + "FROM read_parquet('"
        + path
        + "', union_by_name = true)"
    )

    connection.execute(
        sql
    )


def create_silver_views(connection):

    for dataset_name in DATASETS:

        create_silver_view(
            connection,
            dataset_name,
        )


# ============================================================
# CURRENT DIMENSION VIEWS
# ============================================================

def create_current_dimension_views(
    connection,
):

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        silver.kostra_account_current
        AS

        SELECT *
        FROM silver.kostra_account

        WHERE _silver_registry_id =
        (
            SELECT MAX(_silver_registry_id)
            FROM silver.kostra_account
        )
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        silver.kostra_function_current
        AS

        SELECT *
        FROM silver.kostra_function

        WHERE _silver_registry_id =
        (
            SELECT MAX(_silver_registry_id)
            FROM silver.kostra_function
        )
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW
        silver.budget_organization_current
        AS

        SELECT *
        FROM silver.budget_organization

        WHERE _silver_registry_id =
        (
            SELECT MAX(_silver_registry_id)
            FROM silver.budget_organization
        )
        """
    )


# ============================================================
# ROW COUNT
# ============================================================

def get_row_count(
    connection,
    dataset_name,
):

    sql = (
        "SELECT COUNT(*) "
        "FROM silver."
        + dataset_name
    )

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# SNAPSHOT COUNT
# ============================================================

def get_snapshot_count(
    connection,
    dataset_name,
):

    sql = (
        "SELECT COUNT(DISTINCT "
        "_silver_source_sha256) "
        "FROM silver."
        + dataset_name
    )

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# NULL SOURCE HASH
# ============================================================

def get_null_source_hash_count(
    connection,
    dataset_name,
):

    sql = (
        "SELECT COUNT(*) "
        "FROM silver."
        + dataset_name
        + " WHERE "
        "_silver_source_sha256 IS NULL"
    )

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# NULL REGISTRY ID
# ============================================================

def get_null_registry_id_count(
    connection,
    dataset_name,
):

    sql = (
        "SELECT COUNT(*) "
        "FROM silver."
        + dataset_name
        + " WHERE "
        "_silver_registry_id IS NULL"
    )

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# DIMENSION PRIMARY KEY
# ============================================================

def get_primary_key_null_count(
    connection,
    dataset_name,
    primary_key,
):

    sql = (
        "SELECT COUNT(*) "
        "FROM silver."
        + dataset_name
        + " WHERE "
        + primary_key
        + " IS NULL"
    )

    return connection.execute(
        sql
    ).fetchone()[0]


def get_primary_key_duplicate_count(
    connection,
    dataset_name,
    primary_key,
):

    sql = (
        "SELECT COUNT(*) "
        "FROM ("
        "SELECT "
        "_silver_source_sha256, "
        + primary_key
        + ", COUNT(*) AS n "
        "FROM silver."
        + dataset_name
        + " "
        "GROUP BY "
        "_silver_source_sha256, "
        + primary_key
        + " "
        "HAVING COUNT(*) > 1"
        ") AS duplicate_keys"
    )

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# ERP FUNCTION ORPHANS
# ============================================================

def get_erp_function_orphans(
    connection,
):

    sql = """
        SELECT COUNT(*)
        FROM
        (
            SELECT DISTINCT
                fact.kostra_function_id

            FROM silver.erp_finance AS fact

            LEFT JOIN
                silver.kostra_function_current AS dim

            ON
                fact.kostra_function_id
                =
                dim.kostra_function_id

            WHERE
                fact.kostra_function_id IS NOT NULL

            AND
                dim.kostra_function_id IS NULL
        ) AS orphan_keys
    """

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# FRAMSIKT FUNCTION ORPHANS
# ============================================================

def get_framsikt_function_orphans(
    connection,
):

    sql = """
        SELECT COUNT(*)
        FROM
        (
            SELECT DISTINCT
                fact.kostra_function_id

            FROM silver.framsikt_finance AS fact

            LEFT JOIN
                silver.kostra_function_current AS dim

            ON
                fact.kostra_function_id
                =
                dim.kostra_function_id

            WHERE
                fact.kostra_function_id IS NOT NULL

            AND
                dim.kostra_function_id IS NULL
        ) AS orphan_keys
    """

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# ERP ACCOUNT ORPHANS
# ============================================================

def get_erp_account_orphans(
    connection,
):

    sql = """
        SELECT COUNT(*)
        FROM
        (
            SELECT DISTINCT
                fact.account_code

            FROM silver.erp_finance AS fact

            LEFT JOIN
                silver.kostra_account_current AS dim

            ON
                fact.account_code
                =
                dim.account_code

            WHERE
                fact.account_code IS NOT NULL

            AND
                dim.account_code IS NULL
        ) AS orphan_keys
    """

    return connection.execute(
        sql
    ).fetchone()[0]


# ============================================================
# AUDIT TABLE
# ============================================================

def create_audit_table(connection):

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
        audit.silver_integrity
        (
            check_time_utc VARCHAR,
            dataset_name VARCHAR,
            check_name VARCHAR,
            check_value BIGINT,
            status VARCHAR
        )
        """
    )


def clear_audit_table(connection):

    connection.execute(
        """
        DELETE FROM audit.silver_integrity
        """
    )


# ============================================================
# STORE CHECK
# ============================================================

def store_check(
    connection,
    dataset_name,
    check_name,
    value,
    severity,
):

    connection.execute(
        """
        INSERT INTO audit.silver_integrity
        (
            check_time_utc,
            dataset_name,
            check_name,
            check_value,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            utc_now(),
            dataset_name,
            check_name,
            int(value),
            severity,
        ],
    )


# ============================================================
# STRUCTURAL CHECKS
# ============================================================

def run_dataset_checks(
    connection,
    discovered,
):

    results = []

    for dataset_name, settings in DATASETS.items():

        files = discovered[
            dataset_name
        ]

        rows = get_row_count(
            connection,
            dataset_name,
        )

        snapshots = get_snapshot_count(
            connection,
            dataset_name,
        )

        null_hashes = (
            get_null_source_hash_count(
                connection,
                dataset_name,
            )
        )

        null_registry_ids = (
            get_null_registry_id_count(
                connection,
                dataset_name,
            )
        )

        checks = []

        checks.append(
            {
                "name":
                    "row_count_gt_zero",
                "value":
                    rows,
                "severity":
                    (
                        "PASS"
                        if rows > 0
                        else "FAIL"
                    ),
            }
        )

        checks.append(
            {
                "name":
                    "snapshot_count",
                "value":
                    snapshots,
                "severity":
                    (
                        "PASS"
                        if snapshots == len(files)
                        else "FAIL"
                    ),
            }
        )

        checks.append(
            {
                "name":
                    "null_source_hash",
                "value":
                    null_hashes,
                "severity":
                    (
                        "PASS"
                        if null_hashes == 0
                        else "FAIL"
                    ),
            }
        )

        checks.append(
            {
                "name":
                    "null_registry_id",
                "value":
                    null_registry_ids,
                "severity":
                    (
                        "PASS"
                        if null_registry_ids == 0
                        else "FAIL"
                    ),
            }
        )

        primary_key = settings[
            "primary_key"
        ]

        if primary_key is not None:

            null_pk = (
                get_primary_key_null_count(
                    connection,
                    dataset_name,
                    primary_key,
                )
            )

            duplicate_pk = (
                get_primary_key_duplicate_count(
                    connection,
                    dataset_name,
                    primary_key,
                )
            )

            checks.append(
                {
                    "name":
                        "primary_key_null",
                    "value":
                        null_pk,
                    "severity":
                        (
                            "PASS"
                            if null_pk == 0
                            else "FAIL"
                        ),
                }
            )

            checks.append(
                {
                    "name":
                        "primary_key_duplicate",
                    "value":
                        duplicate_pk,
                    "severity":
                        (
                            "PASS"
                            if duplicate_pk == 0
                            else "FAIL"
                        ),
                }
            )

        for check in checks:

            store_check(
                connection,
                dataset_name,
                check["name"],
                check["value"],
                check["severity"],
            )

        results.append(
            {
                "dataset":
                    dataset_name,
                "files":
                    len(files),
                "rows":
                    rows,
                "snapshots":
                    snapshots,
                "checks":
                    checks,
            }
        )

    return results


# ============================================================
# RELATIONSHIP CHECKS
# ============================================================

def run_relationship_checks(connection):
    """
    Referential-integrity differences are WARNINGs.

    A missing reference may represent:
    - manual coding error
    - incomplete master data
    - source-system coding difference
    - reference-data version difference
    - legitimate unmapped source value
    """

    checks = []

    # ERP -> KOSTRA FUNCTION

    value = get_erp_function_orphans(
        connection
    )

    checks.append(
        {
            "dataset":
                "erp_finance",
            "name":
                "orphan_kostra_function",
            "value":
                value,
            "severity":
                (
                    "PASS"
                    if value == 0
                    else "WARNING"
                ),
        }
    )

    # FRAMSIKT -> KOSTRA FUNCTION

    value = (
        get_framsikt_function_orphans(
            connection
        )
    )

    checks.append(
        {
            "dataset":
                "framsikt_finance",
            "name":
                "orphan_kostra_function",
            "value":
                value,
            "severity":
                (
                    "PASS"
                    if value == 0
                    else "WARNING"
                ),
        }
    )

    # ERP -> ACCOUNT

    value = get_erp_account_orphans(
        connection
    )

    checks.append(
        {
            "dataset":
                "erp_finance",
            "name":
                "orphan_account_code",
            "value":
                value,
            "severity":
                (
                    "PASS"
                    if value == 0
                    else "WARNING"
                ),
        }
    )

    # STORE

    for check in checks:

        store_check(
            connection,
            check["dataset"],
            check["name"],
            check["value"],
            check["severity"],
        )

    return checks


# ============================================================
# PRINT DATASET RESULTS
# ============================================================

def print_dataset_result(result):

    print()
    print("=" * 100)

    print(
        "DATASET :",
        result["dataset"],
    )

    print("=" * 100)

    print(
        "Files     :",
        result["files"],
    )

    print(
        "Rows      :",
        result["rows"],
    )

    print(
        "Snapshots :",
        result["snapshots"],
    )

    print()

    for check in result["checks"]:

        print(
            "{} | {:30} | {}".format(
                check["severity"],
                check["name"],
                check["value"],
            )
        )


# ============================================================
# PRINT RELATIONSHIP RESULTS
# ============================================================

def print_relationship_results(checks):

    print()
    print("=" * 100)

    print(
        "RELATIONSHIP CHECKS"
    )

    print("=" * 100)

    for check in checks:

        print(
            "{} | {:20} | {:30} | {}".format(
                check["severity"],
                check["dataset"],
                check["name"],
                check["value"],
            )
        )


# ============================================================
# COUNT FAILURES
# ============================================================

def count_failures(
    dataset_results,
    relationship_results,
):

    failures = 0

    for result in dataset_results:

        for check in result["checks"]:

            if check["severity"] == "FAIL":

                failures += 1

    for check in relationship_results:

        if check["severity"] == "FAIL":

            failures += 1

    return failures


# ============================================================
# COUNT WARNINGS
# ============================================================

def count_warnings(
    dataset_results,
    relationship_results,
):

    warnings = 0

    for result in dataset_results:

        for check in result["checks"]:

            if check["severity"] == "WARNING":

                warnings += 1

    for check in relationship_results:

        if check["severity"] == "WARNING":

            warnings += 1

    return warnings


# ============================================================
# REOPEN TEST
# ============================================================

def verify_database():

    connection = duckdb.connect(
        str(
            DUCKDB_PATH
        ),
        read_only=True,
    )

    try:

        for dataset_name in DATASETS:

            sql = (
                "SELECT COUNT(*) "
                "FROM silver."
                + dataset_name
            )

            connection.execute(
                sql
            ).fetchone()

        # Verify current dimension views as well.
        for view_name in (
            "kostra_account_current",
            "kostra_function_current",
            "budget_organization_current",
        ):

            connection.execute(
                "SELECT COUNT(*) "
                "FROM silver."
                + view_name
            ).fetchone()

        connection.execute(
            """
            SELECT COUNT(*)
            FROM audit.silver_integrity
            """
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
        "WF1 DUCKDB BUILDER V2"
    )

    print("=" * 100)

    print(
        "Project root:",
        PROJECT_ROOT,
    )

    print(
        "Silver      :",
        SILVER_DIR,
    )

    print(
        "DuckDB      :",
        DUCKDB_PATH,
    )

    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    discovered = discover_silver()

    try:

        precheck_silver(
            discovered
        )

    except Exception as exc:

        print()
        print(
            "SILVER PRECHECK FAILED"
        )

        print(
            exc
        )

        return 1

    print()
    print(
        "Silver datasets:"
    )

    for dataset_name, files in discovered.items():

        print(
            "  -",
            dataset_name,
            "| files:",
            len(files),
        )

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    connection = None

    try:

        connection = connect_database()

        create_schemas(
            connection
        )

        create_silver_views(
            connection
        )

        create_current_dimension_views(
            connection
        )

        create_audit_table(
            connection
        )

        clear_audit_table(
            connection
        )

        # ----------------------------------------------------
        # CHECKS
        # ----------------------------------------------------

        dataset_results = (
            run_dataset_checks(
                connection,
                discovered,
            )
        )

        relationship_results = (
            run_relationship_checks(
                connection
            )
        )

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        for result in dataset_results:

            print_dataset_result(
                result
            )

        print_relationship_results(
            relationship_results
        )

        failures = count_failures(
            dataset_results,
            relationship_results,
        )

        warnings = count_warnings(
            dataset_results,
            relationship_results,
        )

        # ----------------------------------------------------
        # CLOSE AND REOPEN
        # ----------------------------------------------------

        connection.close()
        connection = None

        verify_database()

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print()
        print("=" * 100)

        print(
            "DUCKDB BUILD SUMMARY"
        )

        print("=" * 100)

        print(
            "Database :",
            DUCKDB_PATH,
        )

        print(
            "Datasets :",
            len(DATASETS),
        )

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

        print(
            "DUCKDB BUILD FAILED"
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