from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    create_model,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

STAGING_DIR = PROJECT_ROOT / "data" / "staging"
CURATED_DIR = PROJECT_ROOT / "data" / "curated"
QUARANTINE_DIR = PROJECT_ROOT / "data" / "quarantine"
LOG_DIR = PROJECT_ROOT / "logs"

CONTRACT_FILE = (
    PROJECT_ROOT
    / "config"
    / "dataset_contracts.yaml"
)


# ============================================================
# SETTINGS
# ============================================================

TECHNICAL_COLUMNS = {
    "_dataset",
    "_source_file",
    "_loaded_at_utc",
}


# ============================================================
# PYDANTIC BASE MODEL
# ============================================================

class WF1BaseModel(BaseModel):
    """
    Base configuration for dynamically generated
    WF1 validation models.

    extra='forbid' means that any unexpected canonical
    business column causes validation failure.

    Technical lineage fields are excluded before validation.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# ============================================================
# YAML
# ============================================================

def load_yaml(path: Path) -> dict:
    """
    Load YAML configuration.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Missing configuration file:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file) or {}


# ============================================================
# CONTRACT VERSION
# ============================================================

def get_contract_version(
    contracts_config: dict,
) -> str:
    """
    Return contract version as text.
    """

    return str(
        contracts_config.get(
            "version",
            "unknown",
        )
    )


# ============================================================
# TYPE MAPPING
# ============================================================

def python_type(
    contract_type: str,
) -> type:
    """
    Convert YAML contract type to Python/Pydantic type.
    """

    type_map: dict[str, type] = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
    }

    normalized = str(
        contract_type
    ).strip().lower()

    if normalized not in type_map:
        raise ValueError(
            "Unsupported contract datatype: "
            f"{contract_type}"
        )

    return type_map[normalized]


# ============================================================
# DYNAMIC PYDANTIC MODEL
# ============================================================

def build_pydantic_model(
    dataset_name: str,
    contract: dict,
) -> type[BaseModel]:
    """
    Create one dynamic Pydantic model from
    dataset_contracts.yaml.

    Required columns:
        required and non-null unless nullable=true.

    Optional columns:
        may be absent.

    Nullable controls whether None is allowed.
    """

    fields: dict[str, tuple[Any, Any]] = {}

    # --------------------------------------------------------
    # REQUIRED FIELDS
    # --------------------------------------------------------

    required_columns = contract.get(
        "required_columns",
        {},
    )

    for field_name, settings in required_columns.items():

        declared_type = python_type(
            settings.get(
                "type",
                "string",
            )
        )

        nullable = bool(
            settings.get(
                "nullable",
                False,
            )
        )

        if nullable:
            annotation = declared_type | None
        else:
            annotation = declared_type

        # Ellipsis means the field itself is required.
        fields[field_name] = (
            annotation,
            ...,
        )

    # --------------------------------------------------------
    # OPTIONAL FIELDS
    # --------------------------------------------------------

    optional_columns = contract.get(
        "optional_columns",
        {},
    )

    for field_name, settings in optional_columns.items():

        declared_type = python_type(
            settings.get(
                "type",
                "string",
            )
        )

        nullable = bool(
            settings.get(
                "nullable",
                True,
            )
        )

        if nullable:
            annotation = declared_type | None
            default = None
        else:
            annotation = declared_type
            default = None

        fields[field_name] = (
            annotation,
            default,
        )

    model_name = (
        dataset_name
        .replace("_", " ")
        .title()
        .replace(" ", "")
        + "Record"
    )

    model = create_model(
        model_name,
        __base__=WF1BaseModel,
        **fields,
    )

    return model


# ============================================================
# NULL NORMALIZATION
# ============================================================

def normalize_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert pandas/NumPy missing values to None.

    Pydantic should receive normal Python values.
    """

    result: dict[str, Any] = {}

    for key, value in record.items():

        try:
            is_missing = pd.isna(value)
        except Exception:
            is_missing = False

        if isinstance(
            is_missing,
            bool,
        ) and is_missing:

            result[key] = None

        else:
            result[key] = value

    return result


# ============================================================
# STAGING DISCOVERY
# ============================================================

def discover_staging_files() -> list[Path]:
    """
    Find canonical staging CSV files.
    """

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sorted(
        path
        for path in STAGING_DIR.glob("*.csv")
        if not path.name.startswith("~$")
    )


# ============================================================
# DATASET NAME
# ============================================================

def dataset_name_from_file(
    path: Path,
) -> str:
    """
    Staging files use canonical dataset names:

        erp_finance.csv
        framsikt_finance.csv
        kostra_function.csv
        kostra_account.csv
    """

    return path.stem


# ============================================================
# CONTRACT CHECK
# ============================================================

def get_dataset_contract(
    dataset_name: str,
    contracts_config: dict,
) -> dict:
    """
    Retrieve dataset contract.
    """

    datasets = contracts_config.get(
        "datasets",
        {},
    )

    if dataset_name not in datasets:

        raise ValueError(
            "No dataset contract found for "
            f"{dataset_name}"
        )

    return datasets[
        dataset_name
    ]


# ============================================================
# PRE-VALIDATION SCHEMA CHECK
# ============================================================

def validate_dataframe_schema(
    df: pd.DataFrame,
    contract: dict,
) -> None:
    """
    Validate canonical DataFrame structure before
    row-level Pydantic validation.
    """

    required = set(
        contract.get(
            "required_columns",
            {},
        ).keys()
    )

    optional = set(
        contract.get(
            "optional_columns",
            {},
        ).keys()
    )

    business_columns = {
        column
        for column in df.columns
        if column not in TECHNICAL_COLUMNS
    }

    missing_required = sorted(
        required - business_columns
    )

    if missing_required:

        raise ValueError(
            "Missing required canonical columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing_required
            )
        )

    allowed = required | optional

    unexpected = sorted(
        business_columns - allowed
    )

    if unexpected:

        raise ValueError(
            "Unexpected canonical columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in unexpected
            )
        )


# ============================================================
# VALIDATION ERROR SERIALIZATION
# ============================================================

def serialize_error(
    error: ValidationError,
) -> list[dict[str, Any]]:
    """
    Convert Pydantic validation errors into
    JSON-compatible dictionaries.
    """

    output: list[dict[str, Any]] = []

    for item in error.errors():

        location = ".".join(
            str(value)
            for value in item.get(
                "loc",
                [],
            )
        )

        output.append(
            {
                "field": location,
                "error_type": item.get(
                    "type"
                ),
                "message": item.get(
                    "msg"
                ),
                "input": str(
                    item.get(
                        "input"
                    )
                ),
            }
        )

    return output


# ============================================================
# VALIDATE ONE DATASET
# ============================================================

def validate_dataset(
    path: Path,
    dataset_name: str,
    contract: dict,
    contract_version: str,
    run_id: str,
) -> dict[str, Any]:
    """
    Validate every staging record using Pydantic.
    """

    started_at = datetime.now(
        timezone.utc
    )

    df = pd.read_csv(
        path,
        low_memory=False,
    )

    validate_dataframe_schema(
        df=df,
        contract=contract,
    )

    model = build_pydantic_model(
        dataset_name=dataset_name,
        contract=contract,
    )

    valid_indices: list[int] = []
    invalid_indices: list[int] = []
    error_rows: list[dict[str, Any]] = []

    business_columns = [
        column
        for column in df.columns
        if column not in TECHNICAL_COLUMNS
    ]

    # --------------------------------------------------------
    # ROW VALIDATION
    # --------------------------------------------------------

    for row_number, (
        index,
        row,
    ) in enumerate(
        df.iterrows(),
        start=2,
    ):

        raw_record = (
            row[
                business_columns
            ]
            .to_dict()
        )

        record = normalize_record(
            raw_record
        )

        try:

            model.model_validate(
                record
            )

            valid_indices.append(
                index
            )

        except ValidationError as exc:

            invalid_indices.append(
                index
            )

            serialized = serialize_error(
                exc
            )

            for error in serialized:

                error_rows.append(
                    {
                        "run_id": run_id,
                        "dataset": dataset_name,
                        "staging_file": path.name,
                        "source_row_number": row_number,
                        "dataframe_index": int(index),
                        **error,
                    }
                )

    # --------------------------------------------------------
    # SPLIT VALID / INVALID
    # --------------------------------------------------------

    valid_df = (
        df.loc[
            valid_indices
        ]
        .copy()
    )

    invalid_df = (
        df.loc[
            invalid_indices
        ]
        .copy()
    )

    # --------------------------------------------------------
    # ADD VALIDATION METADATA
    # --------------------------------------------------------

    validation_time = datetime.now(
        timezone.utc
    ).isoformat()

    valid_df["_run_id"] = run_id
    valid_df["_contract_version"] = (
        contract_version
    )
    valid_df["_validated_at_utc"] = (
        validation_time
    )

    if not invalid_df.empty:

        invalid_df["_run_id"] = run_id
        invalid_df[
            "_contract_version"
        ] = contract_version

        invalid_df[
            "_validated_at_utc"
        ] = validation_time

    # --------------------------------------------------------
    # WRITE VALID DATA
    # --------------------------------------------------------

    CURATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    curated_path = (
        CURATED_DIR
        / f"{dataset_name}.csv"
    )

    valid_df.to_csv(
        curated_path,
        index=False,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # WRITE QUARANTINE
    # --------------------------------------------------------

    QUARANTINE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    quarantine_path: Path | None = None
    error_path: Path | None = None

    if not invalid_df.empty:

        quarantine_path = (
            QUARANTINE_DIR
            / (
                f"{dataset_name}"
                "_invalid.csv"
            )
        )

        invalid_df.to_csv(
            quarantine_path,
            index=False,
            encoding="utf-8",
        )

        error_path = (
            QUARANTINE_DIR
            / (
                f"{dataset_name}"
                "_validation_errors.csv"
            )
        )

        pd.DataFrame(
            error_rows
        ).to_csv(
            error_path,
            index=False,
            encoding="utf-8",
        )

    # --------------------------------------------------------
    # DATASET RESULT
    # --------------------------------------------------------

    completed_at = datetime.now(
        timezone.utc
    )

    rows_input = len(df)
    rows_valid = len(valid_df)
    rows_invalid = len(invalid_df)

    status = (
        "PASS"
        if rows_invalid == 0
        else "FAIL"
    )

    return {
        "run_id": run_id,
        "dataset": dataset_name,
        "staging_file": path.name,
        "contract_version": contract_version,
        "status": status,
        "rows_input": rows_input,
        "rows_valid": rows_valid,
        "rows_invalid": rows_invalid,
        "validation_errors": len(
            error_rows
        ),
        "started_at_utc": (
            started_at.isoformat()
        ),
        "completed_at_utc": (
            completed_at.isoformat()
        ),
        "curated_file": str(
            curated_path
        ),
        "quarantine_file": (
            str(quarantine_path)
            if quarantine_path
            else None
        ),
        "error_file": (
            str(error_path)
            if error_path
            else None
        ),
    }


# ============================================================
# AUDIT REPORT
# ============================================================

def write_validation_report(
    run_id: str,
    results: list[dict[str, Any]],
    contract_version: str,
) -> Path:
    """
    Write one machine-readable JSON report per run.
    """

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        LOG_DIR
        / f"validation_{run_id}.json"
    )

    report = {
        "run_id": run_id,
        "contract_version": (
            contract_version
        ),
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "datasets": results,
    }

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return report_path


# ============================================================
# PRINT RESULT
# ============================================================

def print_dataset_result(
    result: dict[str, Any],
) -> None:

    print()
    print("=" * 100)

    print(
        f"DATASET : "
        f"{result['dataset']}"
    )

    print("=" * 100)

    print(
        f"Status            : "
        f"{result['status']}"
    )

    print(
        f"Rows input        : "
        f"{result['rows_input']:,}"
    )

    print(
        f"Rows valid        : "
        f"{result['rows_valid']:,}"
    )

    print(
        f"Rows invalid      : "
        f"{result['rows_invalid']:,}"
    )

    print(
        f"Validation errors : "
        f"{result['validation_errors']:,}"
    )

    print(
        f"Contract version  : "
        f"{result['contract_version']}"
    )

    print(
        f"Curated           : "
        f"{result['curated_file']}"
    )

    if result[
        "quarantine_file"
    ]:

        print(
            f"Quarantine        : "
            f"{result['quarantine_file']}"
        )


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    """
    WF1 Pydantic validation pipeline.
    """

    print()
    print("=" * 100)
    print("WF1 STAGING VALIDATION V1")
    print("=" * 100)

    print(
        f"Staging   : {STAGING_DIR}"
    )

    print(
        f"Curated   : {CURATED_DIR}"
    )

    print(
        f"Quarantine: {QUARANTINE_DIR}"
    )

    print(
        f"Contracts : {CONTRACT_FILE}"
    )

    # --------------------------------------------------------
    # Load contracts
    # --------------------------------------------------------

    try:

        contracts_config = load_yaml(
            CONTRACT_FILE
        )

    except Exception as exc:

        print()
        print("CONFIG ERROR")
        print(str(exc))

        return 1

    contract_version = (
        get_contract_version(
            contracts_config
        )
    )

    # --------------------------------------------------------
    # Run ID
    # --------------------------------------------------------

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    short_uuid = (
        uuid.uuid4()
        .hex[:8]
        .upper()
    )

    run_id = (
        f"WF1-{timestamp}-{short_uuid}"
    )

    print(
        f"Run ID    : {run_id}"
    )

    # --------------------------------------------------------
    # Discover staging datasets
    # --------------------------------------------------------

    files = discover_staging_files()

    if not files:

        print()
        print(
            "No staging CSV files found."
        )

        return 1

    print()
    print(
        f"Datasets detected: {len(files)}"
    )

    for path in files:
        print(
            f"  - {path.name}"
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    results: list[
        dict[str, Any]
    ] = []

    failed = 0

    contracts = contracts_config.get(
        "datasets",
        {},
    )

    for path in files:

        dataset_name = (
            dataset_name_from_file(
                path
            )
        )

        try:

            contract = (
                get_dataset_contract(
                    dataset_name,
                    contracts_config,
                )
            )

            result = validate_dataset(
                path=path,
                dataset_name=dataset_name,
                contract=contract,
                contract_version=contract_version,
                run_id=run_id,
            )

        except Exception as exc:

            result = {
                "run_id": run_id,
                "dataset": dataset_name,
                "staging_file": path.name,
                "contract_version": (
                    contract_version
                ),
                "status": "FAIL",
                "rows_input": 0,
                "rows_valid": 0,
                "rows_invalid": 0,
                "validation_errors": 1,
                "started_at_utc": None,
                "completed_at_utc": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                "curated_file": None,
                "quarantine_file": None,
                "error_file": None,
                "fatal_error": str(exc),
            }

        results.append(
            result
        )

        print_dataset_result(
            result
        )

        if result["status"] != "PASS":

            failed += 1

            if "fatal_error" in result:

                print(
                    f"ERROR             : "
                    f"{result['fatal_error']}"
                )

    # --------------------------------------------------------
    # Write audit report
    # --------------------------------------------------------

    report_path = (
        write_validation_report(
            run_id=run_id,
            results=results,
            contract_version=contract_version,
        )
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    passed = len(results) - failed

    print()
    print("=" * 100)
    print("VALIDATION SUMMARY")
    print("=" * 100)

    print(
        f"Run ID : {run_id}"
    )

    print(
        f"Passed : {passed}"
    )

    print(
        f"Failed : {failed}"
    )

    print(
        f"Total  : {len(results)}"
    )

    print(
        f"Report : {report_path}"
    )

    print("=" * 100)

    return 1 if failed else 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )