from __future__ import annotations

import hashlib
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CURATED_DIR = (
    PROJECT_ROOT
    / "data"
    / "curated"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
)

REGISTRY_DB = (
    PROJECT_ROOT
    / "db"
    / "pipeline_registry.db"
)


# ============================================================
# SETTINGS
# ============================================================

PARQUET_ENGINE = "pyarrow"
PARQUET_COMPRESSION = "snappy"

STATUS_SILVER_READY = "SILVER_READY"


# ============================================================
# TIME
# ============================================================

def utc_now():
    """
    Return current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(path):
    """
    Calculate SHA-256 checksum for a file.
    """

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


# ============================================================
# REGISTRY CONNECTION
# ============================================================

def connect_registry():
    """
    Connect to pipeline_registry.db.
    """

    if not REGISTRY_DB.exists():

        raise FileNotFoundError(
            "Registry database not found: "
            + str(REGISTRY_DB)
        )

    connection = sqlite3.connect(
        REGISTRY_DB
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


# ============================================================
# REGISTRY COLUMNS
# ============================================================

def get_registry_columns(connection):
    """
    Return current columns in pipeline_file_registry.
    """

    cursor = connection.execute(
        """
        PRAGMA table_info(pipeline_file_registry)
        """
    )

    return {
        row["name"]
        for row in cursor.fetchall()
    }


# ============================================================
# ADD COLUMN IF MISSING
# ============================================================

def add_column_if_missing(
    connection,
    column_name,
    column_type,
):
    """
    Add registry column if missing.
    """

    columns = get_registry_columns(
        connection
    )

    if column_name in columns:
        return

    sql = (
        "ALTER TABLE pipeline_file_registry "
        "ADD COLUMN "
        + column_name
        + " "
        + column_type
    )

    connection.execute(
        sql
    )

    connection.commit()


# ============================================================
# HISTORICAL SILVER REGISTRY MIGRATION
# ============================================================

def ensure_historical_columns(connection):
    """
    Ensure registry contains historical Silver fields.
    """

    add_column_if_missing(
        connection,
        "silver_file",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "silver_sha256",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "silver_materialized_at_utc",
        "TEXT",
    )


# ============================================================
# SILVER READY RECORDS
# ============================================================

def get_silver_ready_records(connection):
    """
    Return all registry records ready for historical Silver materialization.
    """

    cursor = connection.execute(
        """
        SELECT *
        FROM pipeline_file_registry
        WHERE status IN (?, ?, ?)
        ORDER BY registry_id
        """,
        (
            "SCHEMA_VALIDATED",
            "SILVER_MATERIALIZED",
            STATUS_SILVER_READY,
        ),
    )

    return cursor.fetchall()



# ============================================================
# CURATED PARQUET PATH
# ============================================================

def get_curated_path(dataset_name):
    """
    Return validated curated Parquet path.
    """

    path = (
        CURATED_DIR
        / (
            dataset_name
            + ".parquet"
        )
    )

    if not path.exists():

        raise FileNotFoundError(
            "Curated Parquet file not found: "
            + str(path)
        )

    return path


# ============================================================
# HISTORICAL SILVER TARGET
# ============================================================

def build_target_path(
    dataset_name,
    source_hash,
):
    """
    Build immutable historical Silver path.

    Layout:

    data/silver/
        dataset/
            source_sha256.parquet
    """

    dataset_directory = (
        SILVER_DIR
        / dataset_name
    )

    dataset_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        dataset_directory
        / (
            source_hash
            + ".parquet"
        )
    )


# ============================================================
# VALIDATE EXISTING SNAPSHOT
# ============================================================

def validate_existing_snapshot(
    target_path,
    record,
    curated_path,
):
    """
    Validate an already existing historical snapshot.

    This prevents an existing hash-named file from
    silently representing the wrong source.
    """

    historical_df = pd.read_parquet(
        target_path,
        engine=PARQUET_ENGINE,
    )

    curated_hash = (
        record["curated_sha256"]
        if "curated_sha256" in record.keys()
        else None
    )

    if (
        curated_path.exists()
        and curated_hash is not None
        and calculate_sha256(curated_path) == curated_hash
    ):
        curated_df = pd.read_parquet(
            curated_path,
            engine=PARQUET_ENGINE,
        )

        if len(historical_df) != len(curated_df):
            raise ValueError(
                "Existing historical Silver row count "
                "does not match curated source."
            )
    required_metadata = {
        "_silver_source_sha256",
        "_silver_snapshot_date",
        "_silver_registry_id",
        "_silver_materialized_at_utc",
    }

    missing_metadata = required_metadata - set(historical_df.columns)
    if missing_metadata:
        raise ValueError(
            "Historical Silver file is missing technical metadata: "
            + ", ".join(sorted(missing_metadata))
        )

    expected_hash = (
        record[
            "source_sha256"
        ]
    )

    hash_values = (
        historical_df[
            "_silver_source_sha256"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if hash_values != [
        expected_hash
    ]:

        raise ValueError(
            "Historical Silver source hash "
            "does not match registry."
        )

    return {
        "rows": len(
            historical_df
        ),
        "columns": len(
            historical_df.columns
        ),
    }


# ============================================================
# WRITE ONE SNAPSHOT
# ============================================================

def write_snapshot(record):
    """
    Write one immutable historical Silver snapshot.
    """

    dataset_name = (
        record[
            "dataset_name"
        ]
    )

    source_hash = (
        record[
            "source_sha256"
        ]
    )

    registry_id = (
        record[
            "registry_id"
        ]
    )

    snapshot_date = (
        record[
            "snapshot_date"
        ]
    )

    curated_path = get_curated_path(
        dataset_name
    )

    target_path = build_target_path(
        dataset_name,
        source_hash,
    )

    # --------------------------------------------------------
    # Existing immutable snapshot
    # --------------------------------------------------------

    if target_path.exists():

        verification = (
            validate_existing_snapshot(
                target_path=target_path,
                record=record,
                curated_path=curated_path,
            )
        )

        return {
            "dataset": dataset_name,
            "source_hash": source_hash,
            "registry_id": registry_id,
            "snapshot_date": snapshot_date,
            "status": "EXISTS",
            "target": target_path,
            "rows": verification["rows"],
            "columns": verification["columns"],
        }

    # --------------------------------------------------------
    # Read validated curated Parquet
    # --------------------------------------------------------

    df = pd.read_parquet(
        curated_path,
        engine=PARQUET_ENGINE,
    )

    source_rows = len(
        df
    )

    # --------------------------------------------------------
    # Add historical Silver lineage
    # --------------------------------------------------------

    materialized_at = utc_now()

    df[
        "_silver_source_sha256"
    ] = source_hash

    df[
        "_silver_snapshot_date"
    ] = snapshot_date

    df[
        "_silver_registry_id"
    ] = registry_id

    df[
        "_silver_materialized_at_utc"
    ] = materialized_at

    # --------------------------------------------------------
    # Write immutable Parquet
    # --------------------------------------------------------

    df.to_parquet(
        target_path,
        engine=PARQUET_ENGINE,
        compression=PARQUET_COMPRESSION,
        index=False,
    )

    # --------------------------------------------------------
    # Read back
    # --------------------------------------------------------

    written_df = pd.read_parquet(
        target_path,
        engine=PARQUET_ENGINE,
    )

    # --------------------------------------------------------
    # Row-count verification
    # --------------------------------------------------------

    if len(
        written_df
    ) != source_rows:

        raise ValueError(
            "Historical Silver row count mismatch."
        )

    # --------------------------------------------------------
    # Column verification
    # --------------------------------------------------------

    if list(
        written_df.columns
    ) != list(
        df.columns
    ):

        raise ValueError(
            "Historical Silver column structure mismatch."
        )

    # --------------------------------------------------------
    # Source-hash verification
    # --------------------------------------------------------

    hash_values = (
        written_df[
            "_silver_source_sha256"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if hash_values != [
        source_hash
    ]:

        raise ValueError(
            "Historical Silver source hash mismatch."
        )

    return {
        "dataset": dataset_name,
        "source_hash": source_hash,
        "registry_id": registry_id,
        "snapshot_date": snapshot_date,
        "status": "WRITTEN",
        "target": target_path,
        "rows": len(
            written_df
        ),
        "columns": len(
            written_df.columns
        ),
    }


# ============================================================
# UPDATE REGISTRY
# ============================================================

def update_registry(
    connection,
    result,
):
    """
    Store historical Silver artifact information
    in pipeline registry.
    """

    target_path = Path(
        result[
            "target"
        ]
    )

    if not target_path.exists():

        raise FileNotFoundError(
            "Historical Silver file not found: "
            + str(
                target_path
            )
        )

    silver_hash = calculate_sha256(
        target_path
    )

    timestamp = utc_now()

    cursor = connection.execute(
        """
        UPDATE pipeline_file_registry
        SET
            silver_file = ?,
            silver_sha256 = ?,
            silver_materialized_at_utc = ?,
            last_updated_at_utc = ?
        WHERE source_sha256 = ?
        """,
        (
            str(
                target_path.resolve()
            ),
            silver_hash,
            timestamp,
            timestamp,
            result[
                "source_hash"
            ],
        ),
    )

    connection.commit()

    if cursor.rowcount == 0:

        raise ValueError(
            "Registry record not found for source hash: "
            + result[
                "source_hash"
            ]
        )


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(result):
    """
    Print snapshot materialization result.
    """

    print()
    print("=" * 100)

    print(
        "DATASET :",
        result[
            "dataset"
        ],
    )

    print("=" * 100)

    print(
        "Status       :",
        result[
            "status"
        ],
    )

    print(
        "Registry ID  :",
        result[
            "registry_id"
        ],
    )

    print(
        "Rows         :",
        result[
            "rows"
        ],
    )

    print(
        "Columns      :",
        result[
            "columns"
        ],
    )

    print(
        "Snapshot date:",
        result[
            "snapshot_date"
        ],
    )

    print(
        "Source hash  :",
        result[
            "source_hash"
        ],
    )

    print(
        "Silver file  :",
        result[
            "target"
        ],
    )


# ============================================================
# MAIN
# ============================================================

def main():
    """
    Materialize all SILVER_READY registry records
    as immutable historical Parquet snapshots.
    """

    print()
    print("=" * 100)
    print(
        "WF1 HISTORICAL SILVER WRITER V1"
    )
    print("=" * 100)

    print(
        "Curated :",
        CURATED_DIR,
    )

    print(
        "Silver  :",
        SILVER_DIR,
    )

    print(
        "Registry:",
        REGISTRY_DB,
    )

    # --------------------------------------------------------
    # Connect registry
    # --------------------------------------------------------

    try:

        connection = (
            connect_registry()
        )

    except Exception as exc:

        print()
        print(
            "REGISTRY ERROR:"
        )

        print(
            exc
        )

        return 1

    try:

        # ----------------------------------------------------
        # Registry migration
        # ----------------------------------------------------

        ensure_historical_columns(
            connection
        )

        # ----------------------------------------------------
        # Find completed records
        # ----------------------------------------------------

        records = (
            get_silver_ready_records(
                connection
            )
        )

        if not records:

            print()
            print(
                "No SILVER_READY records found."
            )

            return 0

        print()
        print(
            "Silver-ready records:",
            len(
                records
            ),
        )

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        written = 0
        existing = 0
        failed = 0

        # ----------------------------------------------------
        # Materialize
        # ----------------------------------------------------

        for record in records:

            try:

                result = write_snapshot(
                    record
                )

                update_registry(
                    connection,
                    result,
                )

                print_result(
                    result
                )

                if (
                    result[
                        "status"
                    ]
                    == "WRITTEN"
                ):

                    written += 1

                else:

                    existing += 1

            except Exception as exc:

                failed += 1

                print()
                print("=" * 100)

                print(
                    "FAILED:",
                    record[
                        "dataset_name"
                    ],
                )

                print(
                    "Registry ID:",
                    record[
                        "registry_id"
                    ],
                )

                print(
                    "ERROR:",
                    exc,
                )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print(
            "HISTORICAL SILVER SUMMARY"
        )
        print("=" * 100)

        print(
            "Written :",
            written,
        )

        print(
            "Existing:",
            existing,
        )

        print(
            "Failed  :",
            failed,
        )

        print(
            "Total   :",
            len(
                records
            ),
        )

        print("=" * 100)

        if failed:
            return 1

        return 0

    finally:

        connection.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )