from __future__ import annotations

import csv
import fnmatch
import hashlib
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_DIR = PROJECT_ROOT / "db"

REGISTRY_DB = DB_DIR / "pipeline_registry.db"

MAPPING_FILE = (
    PROJECT_ROOT
    / "config"
    / "column_mapping.yaml"
)

CONTRACT_FILE = (
    PROJECT_ROOT
    / "config"
    / "dataset_contracts.yaml"
)


# ============================================================
# PIPELINE STATUS
# ============================================================

STATUS_NEW = "NEW"
STATUS_PROFILED = "PROFILED"
STATUS_CLEANED = "CLEANED"
STATUS_RECONCILED = "RECONCILED"
STATUS_VALIDATED = "VALIDATED"
STATUS_PARQUET_WRITTEN = "PARQUET_WRITTEN"
STATUS_SCHEMA_VALIDATED = "SCHEMA_VALIDATED"
STATUS_SILVER_MATERIALIZED = "SILVER_MATERIALIZED"
STATUS_SILVER_READY = "SILVER_READY"
STATUS_FAILED = "FAILED"

STATUS_ALREADY_REGISTERED = "ALREADY_REGISTERED"


VALID_STATUSES = {
    STATUS_NEW,
    STATUS_PROFILED,
    STATUS_CLEANED,
    STATUS_RECONCILED,
    STATUS_VALIDATED,
    STATUS_PARQUET_WRITTEN,
    STATUS_SCHEMA_VALIDATED,
    STATUS_SILVER_MATERIALIZED,
    STATUS_SILVER_READY,
    STATUS_FAILED,
}


STATUS_ORDER = {
    STATUS_NEW: 10,
    STATUS_PROFILED: 20,
    STATUS_CLEANED: 30,
    STATUS_RECONCILED: 40,
    STATUS_VALIDATED: 50,
    STATUS_PARQUET_WRITTEN: 60,
    STATUS_SCHEMA_VALIDATED: 70,
    STATUS_SILVER_MATERIALIZED: 80,
    STATUS_SILVER_READY: 90,
    STATUS_FAILED: 100,
}


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
# RUN ID
# ============================================================

def generate_run_id():
    """
    Generate unique pipeline run ID.
    """

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    suffix = (
        uuid.uuid4()
        .hex[:8]
        .upper()
    )

    return (
        "WF1-"
        + timestamp
        + "-"
        + suffix
    )


# ============================================================
# YAML
# ============================================================

def load_yaml(path):
    """
    Load YAML configuration.
    """

    if not path.exists():

        raise FileNotFoundError(
            "Missing configuration file: "
            + str(path)
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return yaml.safe_load(file) or {}


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(path):
    """
    Calculate SHA-256 checksum.
    """

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):

            digest.update(chunk)

    return digest.hexdigest()


# ============================================================
# RAW FILE DISCOVERY
# ============================================================

def discover_raw_files():
    """
    Discover RAW CSV files.
    """

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sorted(
        path
        for path in RAW_DIR.glob("*.csv")
        if not path.name.startswith("~$")
    )


# ============================================================
# DATASET IDENTIFICATION
# ============================================================

def identify_dataset(
    path,
    mapping_config,
):
    """
    Identify dataset from filename patterns.
    """

    datasets = mapping_config.get(
        "datasets",
        {},
    )

    matches = []

    for dataset_name, settings in datasets.items():

        patterns = settings.get(
            "file_patterns",
            [],
        )

        for pattern in patterns:

            if fnmatch.fnmatch(
                path.name.lower(),
                pattern.lower(),
            ):

                matches.append(
                    dataset_name
                )

                break

    if len(matches) == 1:

        return matches[0]

    if len(matches) == 0:

        raise ValueError(
            "Unable to identify dataset: "
            + path.name
        )

    raise ValueError(
        "Ambiguous dataset identification: "
        + path.name
        + ". Matches: "
        + str(matches)
    )


# ============================================================
# ENCODING
# ============================================================

def detect_encoding(path):
    """
    Detect source encoding.
    """

    encodings = (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin1",
    )

    for encoding in encodings:

        try:

            with path.open(
                "r",
                encoding=encoding,
            ) as file:

                file.read(8192)

            return encoding

        except UnicodeDecodeError:

            continue

    raise ValueError(
        "Unable to detect encoding: "
        + path.name
    )


# ============================================================
# CSV SEPARATOR
# ============================================================

def detect_separator(
    path,
    encoding,
):
    """
    Detect CSV delimiter.
    """

    with path.open(
        "r",
        encoding=encoding,
        newline="",
    ) as file:

        sample = file.read(8192)

    try:

        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )

        return dialect.delimiter

    except csv.Error:

        candidates = {
            ",": sample.count(","),
            ";": sample.count(";"),
            "\t": sample.count("\t"),
            "|": sample.count("|"),
        }

        separator = max(
            candidates,
            key=candidates.get,
        )

        if candidates[separator] == 0:

            raise ValueError(
                "Unable to detect separator: "
                + path.name
            )

        return separator


# ============================================================
# SOURCE METADATA
# ============================================================

def get_source_metadata(path):
    """
    Read basic RAW source metadata.
    """

    encoding = detect_encoding(
        path
    )

    separator = detect_separator(
        path,
        encoding,
    )

    df = pd.read_csv(
        path,
        sep=separator,
        encoding=encoding,
        low_memory=False,
    )

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "encoding": encoding,
        "separator": separator,
    }


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_registry():
    """
    Connect to pipeline registry.
    """

    DB_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        REGISTRY_DB
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# CREATE BASE TABLE
# ============================================================

def create_registry_table(connection):
    """
    Create registry if it does not exist.
    """

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_file_registry
        (
            registry_id INTEGER PRIMARY KEY AUTOINCREMENT,

            run_id TEXT NOT NULL,

            dataset_name TEXT NOT NULL,

            source_file TEXT NOT NULL,

            source_path TEXT NOT NULL,

            source_sha256 TEXT NOT NULL UNIQUE,

            source_bytes INTEGER NOT NULL,

            row_count INTEGER,

            column_count INTEGER,

            encoding TEXT,

            separator TEXT,

            mapping_version TEXT,

            contract_version TEXT,

            status TEXT NOT NULL,

            discovered_at_utc TEXT NOT NULL,

            processed_at_utc TEXT,

            error_message TEXT
        )
        """
    )

    connection.commit()


# ============================================================
# TABLE COLUMNS
# ============================================================

def get_table_columns(connection):
    """
    Return current registry columns.
    """

    cursor = connection.execute(
        """
        PRAGMA table_info(pipeline_file_registry)
        """
    )

    columns = set()

    for row in cursor.fetchall():

        columns.add(
            row["name"]
        )

    return columns


# ============================================================
# ADD COLUMN IF MISSING
# ============================================================

def add_column_if_missing(
    connection,
    column_name,
    column_type,
):
    """
    Add registry column if it does not exist.
    """

    columns = get_table_columns(
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

    connection.execute(sql)

    connection.commit()


# ============================================================
# REGISTRY MIGRATION
# ============================================================

def migrate_registry(connection):
    """
    Upgrade older registry versions without
    deleting existing records.
    """

    new_columns = {
        "profiled_at_utc": "TEXT",
        "cleaned_at_utc": "TEXT",
        "reconciled_at_utc": "TEXT",
        "validated_at_utc": "TEXT",
        "parquet_written_at_utc": "TEXT",
        "schema_validated_at_utc": "TEXT",
        "silver_materialized_at_utc": "TEXT",
        "silver_ready_at_utc": "TEXT",

        "snapshot_date": "TEXT",

        "validation_run_id": "TEXT",

        "parquet_file": "TEXT",
        "parquet_sha256": "TEXT",

        "silver_file": "TEXT",
        "silver_sha256": "TEXT",

        "last_updated_at_utc": "TEXT",

        "failed_stage": "TEXT",
    }

    for column_name, column_type in new_columns.items():

        add_column_if_missing(
            connection,
            column_name,
            column_type,
        )


# ============================================================
# INDEXES
# ============================================================

def create_indexes(connection):
    """
    Create useful registry indexes.
    """

    statements = [
        """
        CREATE INDEX IF NOT EXISTS
        idx_registry_dataset
        ON pipeline_file_registry(dataset_name)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_registry_status
        ON pipeline_file_registry(status)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_registry_run
        ON pipeline_file_registry(run_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_registry_snapshot
        ON pipeline_file_registry(snapshot_date)
        """,
    ]

    for statement in statements:

        connection.execute(
            statement
        )

    connection.commit()


# ============================================================
# INITIALIZE
# ============================================================

def initialize_registry(connection):
    """
    Initialize or migrate registry.
    """

    create_registry_table(
        connection
    )

    migrate_registry(
        connection
    )

    create_indexes(
        connection
    )


# ============================================================
# FIND BY SHA-256
# ============================================================

def find_by_hash(
    connection,
    source_hash,
):
    """
    Find an existing RAW source by SHA-256.
    """

    cursor = connection.execute(
        """
        SELECT *
        FROM pipeline_file_registry
        WHERE source_sha256 = ?
        LIMIT 1
        """,
        (
            source_hash,
        ),
    )

    return cursor.fetchone()


# ============================================================
# SNAPSHOT DATE
# ============================================================

def infer_snapshot_date(
    dataset_name,
    path,
):
    """
    Placeholder for explicit snapshot-date logic.

    Do not guess financial as-of dates.
    """

    _ = dataset_name
    _ = path

    return None


# ============================================================
# REGISTER NEW FILE
# ============================================================

def register_new_file(
    connection,
    run_id,
    dataset_name,
    path,
    source_hash,
    metadata,
    mapping_version,
    contract_version,
    snapshot_date,
):
    """
    Register a new RAW file.
    """

    timestamp = utc_now()

    connection.execute(
        """
        INSERT INTO pipeline_file_registry
        (
            run_id,
            dataset_name,
            source_file,
            source_path,
            source_sha256,
            source_bytes,
            row_count,
            column_count,
            encoding,
            separator,
            mapping_version,
            contract_version,
            status,
            discovered_at_utc,
            snapshot_date,
            last_updated_at_utc
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        )
        """,
        (
            run_id,
            dataset_name,
            path.name,
            str(path.resolve()),
            source_hash,
            path.stat().st_size,

            metadata["row_count"],
            metadata["column_count"],
            metadata["encoding"],
            metadata["separator"],

            mapping_version,
            contract_version,

            STATUS_NEW,

            timestamp,
            snapshot_date,
            timestamp,
        ),
    )

    connection.commit()


# ============================================================
# REGISTER DISCOVERY FAILURE
# ============================================================

def register_failure(
    connection,
    run_id,
    path,
    source_hash,
    mapping_version,
    contract_version,
    error_message,
):
    """
    Register failure during RAW discovery.
    """

    timestamp = utc_now()

    connection.execute(
        """
        INSERT OR IGNORE INTO pipeline_file_registry
        (
            run_id,
            dataset_name,
            source_file,
            source_path,
            source_sha256,
            source_bytes,
            mapping_version,
            contract_version,
            status,
            discovered_at_utc,
            last_updated_at_utc,
            error_message,
            failed_stage
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            run_id,
            "UNKNOWN",
            path.name,
            str(path.resolve()),
            source_hash,
            path.stat().st_size,

            mapping_version,
            contract_version,

            STATUS_FAILED,

            timestamp,
            timestamp,

            error_message,
            "DISCOVERY",
        ),
    )

    connection.commit()


# ============================================================
# STATUS UPDATE
# ============================================================

def update_status(
    connection,
    source_hash,
    status,
    run_id=None,
    error_message=None,
    failed_stage=None,
    parquet_file=None,
    parquet_sha256=None,
):
    """
    Update lifecycle status for one source.
    """

    if status not in VALID_STATUSES:

        raise ValueError(
            "Invalid pipeline status: "
            + status
        )

    timestamp = utc_now()

    timestamp_columns = {
        STATUS_PROFILED:
            "profiled_at_utc",

        STATUS_CLEANED:
            "cleaned_at_utc",

        STATUS_RECONCILED:
            "reconciled_at_utc",

        STATUS_VALIDATED:
            "validated_at_utc",

        STATUS_PARQUET_WRITTEN:
            "parquet_written_at_utc",

        STATUS_SCHEMA_VALIDATED:
            "schema_validated_at_utc",

        STATUS_SILVER_MATERIALIZED:
            "silver_materialized_at_utc",

        STATUS_SILVER_READY:
            "silver_ready_at_utc",
    }

    timestamp_column = (
        timestamp_columns.get(
            status
        )
    )

    assignments = [
        "status = ?",
        "last_updated_at_utc = ?",
    ]

    parameters = [
        status,
        timestamp,
    ]

    if run_id is not None:

        assignments.append(
            "run_id = ?"
        )

        parameters.append(
            run_id
        )

    if error_message is not None:

        assignments.append(
            "error_message = ?"
        )

        parameters.append(
            error_message
        )

    if failed_stage is not None:

        assignments.append(
            "failed_stage = ?"
        )

        parameters.append(
            failed_stage
        )

    if parquet_file is not None:

        assignments.append(
            "parquet_file = ?"
        )

        parameters.append(
            parquet_file
        )

    if parquet_sha256 is not None:

        assignments.append(
            "parquet_sha256 = ?"
        )

        parameters.append(
            parquet_sha256
        )

    if timestamp_column is not None:

        assignments.append(
            timestamp_column
            + " = ?"
        )

        parameters.append(
            timestamp
        )

    if (
        status == STATUS_VALIDATED
        and run_id is not None
    ):

        assignments.append(
            "validation_run_id = ?"
        )

        parameters.append(
            run_id
        )

    parameters.append(
        source_hash
    )

    sql = (
        "UPDATE pipeline_file_registry "
        "SET "
        + ", ".join(assignments)
        + " WHERE source_sha256 = ?"
    )

    cursor = connection.execute(
        sql,
        tuple(parameters),
    )

    connection.commit()

    if cursor.rowcount == 0:

        raise ValueError(
            "Registry record not found for SHA-256: "
            + source_hash
        )


# ============================================================
# MARK FAILED
# ============================================================

def mark_failed(
    connection,
    source_hash,
    run_id,
    stage,
    message,
):
    """
    Mark registry record as FAILED.
    """

    update_status(
        connection=connection,
        source_hash=source_hash,
        status=STATUS_FAILED,
        run_id=run_id,
        error_message=message,
        failed_stage=stage,
    )


# ============================================================
# SET SNAPSHOT DATE
# ============================================================

def set_snapshot_date(
    connection,
    source_hash,
    snapshot_date,
):
    """
    Set explicit snapshot/as-of date.
    """

    cursor = connection.execute(
        """
        UPDATE pipeline_file_registry
        SET
            snapshot_date = ?,
            last_updated_at_utc = ?
        WHERE source_sha256 = ?
        """,
        (
            snapshot_date,
            utc_now(),
            source_hash,
        ),
    )

    connection.commit()

    if cursor.rowcount == 0:

        raise ValueError(
            "Registry record not found for SHA-256: "
            + source_hash
        )


# ============================================================
# SET CURATED PARQUET ARTIFACT
# ============================================================

def set_parquet_artifact(
    connection,
    source_hash,
    parquet_path,
    run_id=None,
):
    """
    Register validated curated Parquet artifact.
    """

    parquet_path = Path(
        parquet_path
    )

    if not parquet_path.exists():

        raise FileNotFoundError(
            "Parquet file not found: "
            + str(parquet_path)
        )

    parquet_hash = calculate_sha256(
        parquet_path
    )

    update_status(
        connection=connection,
        source_hash=source_hash,
        status=STATUS_PARQUET_WRITTEN,
        run_id=run_id,
        parquet_file=str(
            parquet_path.resolve()
        ),
        parquet_sha256=parquet_hash,
    )


# ============================================================
# SET HISTORICAL SILVER ARTIFACT
# ============================================================

def set_silver_artifact(
    connection,
    source_hash,
    silver_path,
    run_id=None,
):
    """
    Register immutable historical Silver artifact.

    Lifecycle becomes SILVER_MATERIALIZED.
    """

    silver_path = Path(
        silver_path
    )

    if not silver_path.exists():

        raise FileNotFoundError(
            "Historical Silver file not found: "
            + str(silver_path)
        )

    silver_hash = calculate_sha256(
        silver_path
    )

    timestamp = utc_now()

    assignments = [
        "status = ?",
        "silver_file = ?",
        "silver_sha256 = ?",
        "silver_materialized_at_utc = ?",
        "last_updated_at_utc = ?",
    ]

    parameters = [
        STATUS_SILVER_MATERIALIZED,
        str(
            silver_path.resolve()
        ),
        silver_hash,
        timestamp,
        timestamp,
    ]

    if run_id is not None:

        assignments.append(
            "run_id = ?"
        )

        parameters.append(
            run_id
        )

    parameters.append(
        source_hash
    )

    sql = (
        "UPDATE pipeline_file_registry "
        "SET "
        + ", ".join(assignments)
        + " WHERE source_sha256 = ?"
    )

    cursor = connection.execute(
        sql,
        tuple(parameters),
    )

    connection.commit()

    if cursor.rowcount == 0:

        raise ValueError(
            "Registry record not found for SHA-256: "
            + source_hash
        )


# ============================================================
# GET NEW RECORDS
# ============================================================

def get_new_records(connection):
    """
    Return NEW registry records.
    """

    cursor = connection.execute(
        """
        SELECT *
        FROM pipeline_file_registry
        WHERE status = ?
        ORDER BY registry_id
        """,
        (
            STATUS_NEW,
        ),
    )

    return cursor.fetchall()


# ============================================================
# GET PENDING RECORDS
# ============================================================

def get_pending_records(connection):
    """
    Return incomplete non-failed records.
    """

    cursor = connection.execute(
        """
        SELECT *
        FROM pipeline_file_registry
        WHERE status NOT IN (?, ?)
        ORDER BY registry_id
        """,
        (
            STATUS_SILVER_READY,
            STATUS_FAILED,
        ),
    )

    return cursor.fetchall()


# ============================================================
# SILVER MATERIALIZED RECORDS
# ============================================================

def get_silver_materialized_records(
    connection,
):
    """
    Return SILVER_MATERIALIZED records.
    """

    cursor = connection.execute(
        """
        SELECT *
        FROM pipeline_file_registry
        WHERE status = ?
        ORDER BY registry_id
        """,
        (
            STATUS_SILVER_MATERIALIZED,
        ),
    )

    return cursor.fetchall()


# ============================================================
# SILVER READY RECORDS
# ============================================================

def get_silver_ready_records(
    connection,
):
    """
    Return SILVER_READY records.
    """

    cursor = connection.execute(
        """
        SELECT *
        FROM pipeline_file_registry
        WHERE status = ?
        ORDER BY registry_id
        """,
        (
            STATUS_SILVER_READY,
        ),
    )

    return cursor.fetchall()


# ============================================================
# PROCESS RAW FILE
# ============================================================

def process_file(
    connection,
    path,
    mapping_config,
    mapping_version,
    contract_version,
    run_id,
):
    """
    Discover/register one RAW file.
    """

    print()
    print("=" * 100)

    print(
        "FILE:",
        path.name,
    )

    print("=" * 100)

    source_hash = calculate_sha256(
        path
    )

    existing = find_by_hash(
        connection,
        source_hash,
    )

    # --------------------------------------------------------
    # ALREADY REGISTERED
    # --------------------------------------------------------

    if existing is not None:

        print(
            "Dataset :",
            existing["dataset_name"],
        )

        print(
            "Status  :",
            STATUS_ALREADY_REGISTERED,
        )

        print(
            "Lifecycle:",
            existing["status"],
        )

        print(
            "SHA256  :",
            source_hash,
        )

        print(
            "Registry ID:",
            existing["registry_id"],
        )

        print(
            "Run ID:",
            existing["run_id"],
        )

        return STATUS_ALREADY_REGISTERED

    # --------------------------------------------------------
    # NEW RAW FILE
    # --------------------------------------------------------

    try:

        dataset_name = identify_dataset(
            path,
            mapping_config,
        )

        metadata = get_source_metadata(
            path
        )

        snapshot_date = infer_snapshot_date(
            dataset_name,
            path,
        )

        register_new_file(
            connection=connection,
            run_id=run_id,
            dataset_name=dataset_name,
            path=path,
            source_hash=source_hash,
            metadata=metadata,
            mapping_version=mapping_version,
            contract_version=contract_version,
            snapshot_date=snapshot_date,
        )

        print(
            "Dataset :",
            dataset_name,
        )

        print(
            "Status  :",
            STATUS_NEW,
        )

        print(
            "Rows    :",
            metadata["row_count"],
        )

        print(
            "Columns :",
            metadata["column_count"],
        )

        print(
            "SHA256  :",
            source_hash,
        )

        print(
            "Snapshot:",
            snapshot_date,
        )

        return STATUS_NEW

    except Exception as exc:

        register_failure(
            connection=connection,
            run_id=run_id,
            path=path,
            source_hash=source_hash,
            mapping_version=mapping_version,
            contract_version=contract_version,
            error_message=str(exc),
        )

        print(
            "Status  :",
            STATUS_FAILED,
        )

        print(
            "Error   :",
            exc,
        )

        return STATUS_FAILED


# ============================================================
# REGISTRY SUMMARY
# ============================================================

def print_registry_summary(connection):
    """
    Print dataset/status counts.
    """

    cursor = connection.execute(
        """
        SELECT
            dataset_name,
            status,
            COUNT(*) AS file_count
        FROM pipeline_file_registry
        GROUP BY
            dataset_name,
            status
        ORDER BY
            dataset_name,
            status
        """
    )

    rows = cursor.fetchall()

    print()
    print("=" * 100)
    print("REGISTRY CONTENT")
    print("=" * 100)

    if not rows:

        print(
            "Registry is empty."
        )

        return

    for row in rows:

        print(
            row["dataset_name"],
            "|",
            row["status"],
            "| files:",
            row["file_count"],
        )


# ============================================================
# LIFECYCLE SUMMARY
# ============================================================

def print_lifecycle_summary(connection):
    """
    Print lifecycle counts.
    """

    cursor = connection.execute(
        """
        SELECT
            status,
            COUNT(*) AS file_count
        FROM pipeline_file_registry
        GROUP BY status
        """
    )

    rows = cursor.fetchall()

    values = {}

    for row in rows:

        values[
            row["status"]
        ] = row["file_count"]

    print()
    print(
        "Lifecycle totals:"
    )

    ordered_statuses = sorted(
        VALID_STATUSES,
        key=lambda value: (
            STATUS_ORDER.get(
                value,
                999,
            )
        ),
    )

    for status in ordered_statuses:

        print(
            "  {:22} {}".format(
                status,
                values.get(
                    status,
                    0,
                ),
            )
        )


# ============================================================
# MAIN
# ============================================================

def main():
    """
    WF1 Pipeline Registry V2.
    """

    print()
    print("=" * 100)
    print(
        "WF1 PIPELINE REGISTRY V2"
    )
    print("=" * 100)

    print(
        "Raw      :",
        RAW_DIR,
    )

    print(
        "Registry :",
        REGISTRY_DB,
    )

    # --------------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------------

    try:

        mapping_config = load_yaml(
            MAPPING_FILE
        )

        contract_config = load_yaml(
            CONTRACT_FILE
        )

    except Exception as exc:

        print()
        print(
            "CONFIG ERROR"
        )

        print(
            exc
        )

        return 1

    mapping_version = str(
        mapping_config.get(
            "version",
            "unknown",
        )
    )

    contract_version = str(
        contract_config.get(
            "version",
            "unknown",
        )
    )

    run_id = generate_run_id()

    print(
        "Run ID   :",
        run_id,
    )

    print(
        "Mapping  :",
        mapping_version,
    )

    print(
        "Contract :",
        contract_version,
    )

    # --------------------------------------------------------
    # REGISTRY
    # --------------------------------------------------------

    connection = connect_registry()

    try:

        initialize_registry(
            connection
        )

        files = discover_raw_files()

        if not files:

            print()
            print(
                "No RAW CSV files found."
            )

            return 0

        print()
        print(
            "Files detected:",
            len(files),
        )

        for path in files:

            print(
                "  -",
                path.name,
            )

        # ----------------------------------------------------
        # COUNTERS
        # ----------------------------------------------------

        new_count = 0
        registered_count = 0
        failed_count = 0

        # ----------------------------------------------------
        # DISCOVERY
        # ----------------------------------------------------

        for path in files:

            result = process_file(
                connection=connection,
                path=path,
                mapping_config=mapping_config,
                mapping_version=mapping_version,
                contract_version=contract_version,
                run_id=run_id,
            )

            if result == STATUS_NEW:

                new_count += 1

            elif result == STATUS_ALREADY_REGISTERED:

                registered_count += 1

            elif result == STATUS_FAILED:

                failed_count += 1

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print(
            "REGISTRY RUN SUMMARY"
        )
        print("=" * 100)

        print(
            "Run ID             :",
            run_id,
        )

        print(
            "New files          :",
            new_count,
        )

        print(
            "Already registered :",
            registered_count,
        )

        print(
            "Failed             :",
            failed_count,
        )

        print(
            "Total discovered   :",
            len(files),
        )

        print_registry_summary(
            connection
        )

        print_lifecycle_summary(
            connection
        )

        if failed_count:

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