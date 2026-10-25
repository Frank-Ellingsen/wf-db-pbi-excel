from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_ROOT = (
    PROJECT_ROOT
    / "src"
    / "project_finance"
)

DB_DIR = PROJECT_ROOT / "db"

REGISTRY_DB = (
    DB_DIR
    / "pipeline_registry.db"
)


# ============================================================
# PIPELINE COMPONENTS
# ============================================================

REGISTRY_SCRIPT = (
    SRC_ROOT
    / "audit"
    / "pipeline_registry.py"
)

PROFILE_SCRIPT = (
    SRC_ROOT
    / "ingestion"
    / "profile_source.py"
)

CLEAN_SCRIPT = (
    SRC_ROOT
    / "cleaning"
    / "clean_source.py"
)

RECONCILE_SCRIPT = (
    SRC_ROOT
    / "reconciliation"
    / "reconcile_staging.py"
)

VALIDATE_SCRIPT = (
    SRC_ROOT
    / "validation"
    / "validate_staging.py"
)

PARQUET_SCRIPT = (
    SRC_ROOT
    / "transformations"
    / "write_parquet.py"
)

SCHEMA_SCRIPT = (
    SRC_ROOT
    / "validation"
    / "validate_parquet_schema.py"
)

HISTORICAL_SILVER_SCRIPT = (
    SRC_ROOT
    / "transformations"
    / "write_historical_silver.py"
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


STAGE_TIMESTAMP_COLUMN = {
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


# ============================================================
# TIME
# ============================================================

def utc_now() -> str:
    """
    Current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# RUN ID
# ============================================================

def generate_run_id() -> str:
    """
    Generate one pipeline-wide run ID.
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
# SHA-256
# ============================================================

def calculate_sha256(
    path: Path,
) -> str:
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
            digest.update(
                chunk
            )

    return digest.hexdigest()


# ============================================================
# REGISTRY DATABASE
# ============================================================

def connect_registry() -> sqlite3.Connection:
    """
    Open pipeline registry.
    """

    if not REGISTRY_DB.exists():

        raise FileNotFoundError(
            "Pipeline registry does not exist: "
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
# PENDING RECORDS
# ============================================================

def get_pending_records(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """
    Return anything that has not completed
    and has not permanently failed.
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
# SILVER READY COUNT
# ============================================================

def get_silver_ready_count(
    connection: sqlite3.Connection,
) -> int:

    cursor = connection.execute(
        """
        SELECT COUNT(*)
        FROM pipeline_file_registry
        WHERE status = ?
        """,
        (
            STATUS_SILVER_READY,
        ),
    )

    row = cursor.fetchone()

    return int(
        row[0]
    )


# ============================================================
# RELOAD REGISTRY RECORD
# ============================================================

def get_record_by_hash(
    connection: sqlite3.Connection,
    source_hash: str,
) -> sqlite3.Row:

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

    record = cursor.fetchone()

    if record is None:

        raise RuntimeError(
            "Registry record not found for SHA-256: "
            + source_hash
        )

    return record


# ============================================================
# STATUS UPDATE
# ============================================================

def update_status(
    connection: sqlite3.Connection,
    source_hash: str,
    status: str,
    run_id: str,
) -> None:

    timestamp = utc_now()

    timestamp_column = (
        STAGE_TIMESTAMP_COLUMN.get(
            status
        )
    )

    assignments = [
        "status = ?",
        "run_id = ?",
        "last_updated_at_utc = ?",
    ]

    parameters = [
        status,
        run_id,
        timestamp,
    ]

    if timestamp_column is not None:

        assignments.append(
            timestamp_column
            + " = ?"
        )

        parameters.append(
            timestamp
        )

    if status == STATUS_VALIDATED:

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
        + ", ".join(
            assignments
        )
        + " WHERE source_sha256 = ?"
    )

    cursor = connection.execute(
        sql,
        tuple(parameters),
    )

    connection.commit()

    if cursor.rowcount == 0:

        raise RuntimeError(
            "Registry record not found for SHA-256: "
            + source_hash
        )


# ============================================================
# MARK FAILED
# ============================================================

def mark_failed(
    connection: sqlite3.Connection,
    source_hash: str,
    run_id: str,
    stage: str,
    message: str,
) -> None:

    connection.execute(
        """
        UPDATE pipeline_file_registry
        SET
            status = ?,
            run_id = ?,
            failed_stage = ?,
            error_message = ?,
            last_updated_at_utc = ?
        WHERE source_sha256 = ?
        """,
        (
            STATUS_FAILED,
            run_id,
            stage,
            message,
            utc_now(),
            source_hash,
        ),
    )

    connection.commit()


# ============================================================
# ADVANCE ALL ACTIVE RECORDS
# ============================================================

def advance_records(
    connection: sqlite3.Connection,
    records: list[sqlite3.Row],
    status: str,
    run_id: str,
) -> None:

    for record in records:

        update_status(
            connection=connection,
            source_hash=record[
                "source_sha256"
            ],
            status=status,
            run_id=run_id,
        )


# ============================================================
# FAIL ACTIVE RECORDS
# ============================================================

def fail_records(
    connection: sqlite3.Connection,
    records: list[sqlite3.Row],
    run_id: str,
    stage: str,
    message: str,
) -> None:

    for record in records:

        mark_failed(
            connection=connection,
            source_hash=record[
                "source_sha256"
            ],
            run_id=run_id,
            stage=stage,
            message=message,
        )


# ============================================================
# RUN CHILD SCRIPT
# ============================================================

def run_script(
    stage_name: str,
    script: Path,
) -> tuple[bool, str]:
    """
    Run one WF1 component with the same Python
    interpreter/environment as this orchestrator.
    """

    if not script.exists():

        return (
            False,
            "Script not found: "
            + str(script),
        )

    print()
    print("=" * 100)
    print(
        "PIPELINE STAGE:",
        stage_name,
    )
    print("=" * 100)

    process = subprocess.run(
        [
            sys.executable,
            str(script),
        ],
        cwd=str(
            script.parent
        ),
        capture_output=True,
        text=True,
        check=False,
    )

    if process.stdout:

        print(
            process.stdout,
            end=(
                ""
                if process.stdout.endswith(
                    "\n"
                )
                else "\n"
            ),
        )

    if process.stderr:

        print(
            process.stderr,
            file=sys.stderr,
            end=(
                ""
                if process.stderr.endswith(
                    "\n"
                )
                else "\n"
            ),
        )

    success = (
        process.returncode == 0
    )

    print(
        "STAGE RESULT:",
        "PASS"
        if success
        else "FAIL",
    )

    error_text = (
        process.stderr.strip()
        or process.stdout.strip()
        or (
            "Process returned exit code "
            + str(
                process.returncode
            )
        )
    )

    return (
        success,
        error_text,
    )


# ============================================================
# VERIFY HISTORICAL SILVER ARTIFACT
# ============================================================

def verify_silver_artifact(
    connection: sqlite3.Connection,
    source_hash: str,
) -> Path:
    """
    Verify that historical Silver exists physically
    and that its SHA-256 matches the registry.

    write_historical_silver.py is responsible for
    writing silver_file and silver_sha256.
    """

    record = get_record_by_hash(
        connection,
        source_hash,
    )

    silver_file = record[
        "silver_file"
    ]

    silver_sha256 = record[
        "silver_sha256"
    ]

    materialized_at = record[
        "silver_materialized_at_utc"
    ]

    if not silver_file:

        raise RuntimeError(
            "Registry has no silver_file for: "
            + source_hash
        )

    if not silver_sha256:

        raise RuntimeError(
            "Registry has no silver_sha256 for: "
            + source_hash
        )

    if not materialized_at:

        raise RuntimeError(
            "Registry has no "
            "silver_materialized_at_utc for: "
            + source_hash
        )

    silver_path = Path(
        silver_file
    )

    if not silver_path.exists():

        raise FileNotFoundError(
            "Historical Silver artifact missing: "
            + str(
                silver_path
            )
        )

    actual_hash = calculate_sha256(
        silver_path
    )

    if actual_hash != silver_sha256:

        raise RuntimeError(
            "Historical Silver SHA-256 mismatch.\n"
            "Registry : "
            + silver_sha256
            + "\n"
            "Physical : "
            + actual_hash
        )

    return silver_path


# ============================================================
# VERIFY ALL HISTORICAL SILVER RECORDS
# ============================================================

def verify_all_silver_artifacts(
    connection: sqlite3.Connection,
    records: list[sqlite3.Row],
) -> None:

    print()
    print("=" * 100)
    print(
        "VERIFY HISTORICAL SILVER ARTIFACTS"
    )
    print("=" * 100)

    for record in records:

        source_hash = record[
            "source_sha256"
        ]

        silver_path = (
            verify_silver_artifact(
                connection=connection,
                source_hash=source_hash,
            )
        )

        print(
            "PASS |",
            record[
                "dataset_name"
            ],
            "|",
            silver_path,
        )


# ============================================================
# PRINT SELECTED RECORDS
# ============================================================

def print_records(
    records: list[sqlite3.Row],
) -> None:

    print()
    print(
        "Records selected for processing:",
        len(records),
    )

    for record in records:

        print(
            "  -",
            record[
                "dataset_name"
            ],
            "|",
            record[
                "source_file"
            ],
            "| status:",
            record[
                "status"
            ],
        )


# ============================================================
# PROCESS NORMAL PIPELINE STAGE
# ============================================================

def execute_stage(
    connection: sqlite3.Connection,
    records: list[sqlite3.Row],
    run_id: str,
    stage_name: str,
    script: Path,
    success_status: str,
) -> bool:
    """
    Execute one stage and update lifecycle
    only after a successful child-process exit.
    """

    success, error = run_script(
        stage_name,
        script,
    )

    if not success:

        fail_records(
            connection=connection,
            records=records,
            run_id=run_id,
            stage=success_status,
            message=error,
        )

        return False

    advance_records(
        connection=connection,
        records=records,
        status=success_status,
        run_id=run_id,
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    print()
    print("=" * 100)
    print(
        "WF1 END-TO-END PIPELINE V2"
    )
    print("=" * 100)

    print(
        "Project root:",
        PROJECT_ROOT,
    )

    print(
        "Python      :",
        sys.executable,
    )

    run_id = generate_run_id()

    print(
        "Run ID      :",
        run_id,
    )

    # ========================================================
    # 0. REGISTRY DISCOVERY / MIGRATION
    # ========================================================

    registry_ok, registry_error = (
        run_script(
            "REGISTRY DISCOVERY",
            REGISTRY_SCRIPT,
        )
    )

    if not registry_ok:

        print()
        print(
            "PIPELINE FAILED DURING "
            "REGISTRY DISCOVERY."
        )

        print(
            registry_error
        )

        return 1

    # ========================================================
    # OPEN REGISTRY
    # ========================================================

    connection = connect_registry()

    try:

        records = get_pending_records(
            connection
        )

        silver_ready_before = (
            get_silver_ready_count(
                connection
            )
        )

        # ----------------------------------------------------
        # NOTHING TO PROCESS
        # ----------------------------------------------------

        if not records:

            print()
            print("=" * 100)
            print("PIPELINE SUMMARY")
            print("=" * 100)

            print(
                "Pending records :",
                0,
            )

            print(
                "Silver ready    :",
                silver_ready_before,
            )

            print(
                "Action          :",
                "Nothing to process.",
            )

            print("=" * 100)

            return 0

        print_records(
            records
        )

        # ====================================================
        # 1. PROFILE
        # ====================================================

        if not execute_stage(
            connection=connection,
            records=records,
            run_id=run_id,
            stage_name="PROFILE",
            script=PROFILE_SCRIPT,
            success_status=STATUS_PROFILED,
        ):
            return 1

        # ====================================================
        # 2. CLEAN
        # ====================================================

        if not execute_stage(
            connection=connection,
            records=records,
            run_id=run_id,
            stage_name="CLEAN",
            script=CLEAN_SCRIPT,
            success_status=STATUS_CLEANED,
        ):
            return 1

        # ====================================================
        # 3. RECONCILE
        # ====================================================

        if not execute_stage(
            connection=connection,
            records=records,
            run_id=run_id,
            stage_name="RECONCILE",
            script=RECONCILE_SCRIPT,
            success_status=STATUS_RECONCILED,
        ):
            return 1

        # ====================================================
        # 4. PYDANTIC VALIDATION
        # ====================================================

        if not execute_stage(
            connection=connection,
            records=records,
            run_id=run_id,
            stage_name=(
                "PYDANTIC VALIDATION"
            ),
            script=VALIDATE_SCRIPT,
            success_status=STATUS_VALIDATED,
        ):
            return 1

        # ====================================================
        # 5. CURATED PARQUET
        # ====================================================

        if not execute_stage(
            connection=connection,
            records=records,
            run_id=run_id,
            stage_name="PARQUET WRITE",
            script=PARQUET_SCRIPT,
            success_status=(
                STATUS_PARQUET_WRITTEN
            ),
        ):
            return 1

        # ====================================================
        # 6. PARQUET SCHEMA VALIDATION
        # ====================================================

        if not execute_stage(
            connection=connection,
            records=records,
            run_id=run_id,
            stage_name=(
                "PARQUET SCHEMA VALIDATION"
            ),
            script=SCHEMA_SCRIPT,
            success_status=(
                STATUS_SCHEMA_VALIDATED
            ),
        ):
            return 1

        # ====================================================
        # 7. HISTORICAL SILVER MATERIALIZATION
        # ====================================================

        success, error = run_script(
            "HISTORICAL SILVER",
            HISTORICAL_SILVER_SCRIPT,
        )

        if not success:

            fail_records(
                connection=connection,
                records=records,
                run_id=run_id,
                stage=(
                    STATUS_SILVER_MATERIALIZED
                ),
                message=error,
            )

            return 1

        # ----------------------------------------------------
        # Artifact verification is mandatory.
        # ----------------------------------------------------

        try:

            verify_all_silver_artifacts(
                connection=connection,
                records=records,
            )

        except Exception as exc:

            fail_records(
                connection=connection,
                records=records,
                run_id=run_id,
                stage=(
                    STATUS_SILVER_MATERIALIZED
                ),
                message=str(
                    exc
                ),
            )

            print()
            print(
                "SILVER ARTIFACT "
                "VERIFICATION FAILED:"
            )

            print(
                exc
            )

            return 1

        # ----------------------------------------------------
        # Physical Silver exists and hash matches.
        # ----------------------------------------------------

        advance_records(
            connection=connection,
            records=records,
            status=(
                STATUS_SILVER_MATERIALIZED
            ),
            run_id=run_id,
        )

        # ====================================================
        # 8. FINAL SILVER READY GATE
        # ====================================================

        try:

            verify_all_silver_artifacts(
                connection=connection,
                records=records,
            )

        except Exception as exc:

            fail_records(
                connection=connection,
                records=records,
                run_id=run_id,
                stage=(
                    STATUS_SILVER_READY
                ),
                message=str(
                    exc
                ),
            )

            print()
            print(
                "FINAL SILVER GATE FAILED:"
            )

            print(
                exc
            )

            return 1

        advance_records(
            connection=connection,
            records=records,
            status=STATUS_SILVER_READY,
            run_id=run_id,
        )

        # ====================================================
        # SUMMARY
        # ====================================================

        silver_ready_after = (
            get_silver_ready_count(
                connection
            )
        )

        print()
        print("=" * 100)
        print("PIPELINE SUMMARY")
        print("=" * 100)

        print(
            "Run ID                :",
            run_id,
        )

        print(
            "Records processed     :",
            len(records),
        )

        print(
            "Silver ready before   :",
            silver_ready_before,
        )

        print(
            "Silver ready after    :",
            silver_ready_after,
        )

        print(
            "Historical Silver gate:",
            "PASS",
        )

        print(
            "Pipeline result       :",
            "PASS",
        )

        print("=" * 100)

        return 0

    except Exception as exc:

        print()
        print("=" * 100)
        print(
            "PIPELINE FATAL ERROR"
        )
        print("=" * 100)

        print(
            exc
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