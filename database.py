# -*- coding: utf-8 -*-
from pathlib import Path
from contextlib import contextmanager
import math
import sqlite3
import hashlib
import hmac
import secrets
import re
from datetime import datetime, date, timedelta
from uuid import uuid4

BASE_FOLDER = Path(__file__).resolve().parent
DATA_FOLDER = BASE_FOLDER / "data"
DATABASE_FILE = DATA_FOLDER / "it_assets.db"

# Financial calculation policy.
# This is a provisional operational default and can be overridden per asset.
DEFAULT_USEFUL_LIFE_YEARS = 5.0
DEPRECIATION_METHOD = "Straight-line"
DEFAULT_RESIDUAL_VALUE_R = 0.0

SOURCE_FIELDS = [
    "asset_type",
    "category",
    "make",
    "model",
    "serial_number",
    "department_asset_tag",
    "facility_site",
    "district",
    "section_department",
    "room_location",
    "specification_os",
    "purchase_date",
    "purchase_cost_r",
    "supplier",
    "warranty_expiry",
    "age_yrs",
]

SOURCE_FIELD_LABELS = {
    "asset_type": "Asset Type",
    "category": "Category",
    "make": "Make",
    "model": "Model",
    "serial_number": "Serial Number",
    "department_asset_tag": "Department Asset Tag",
    "facility_site": "Facility / Site",
    "district": "District",
    "section_department": "Section / Department",
    "room_location": "Room / Location",
    "specification_os": "Specification / OS",
    "purchase_date": "Purchase Date",
    "purchase_cost_r": "Purchase Cost",
    "supplier": "Supplier",
    "warranty_expiry": "Warranty Expiry",
    "age_yrs": "Age",
}

IT_MANAGED_FIELDS = [
    "assigned_user",
    "condition",
    "status",
    "warranty_status",
    "recommendation",
    "verified_on",
    "verified_by",
    "notes",
]


def clean_text(value):
    if value is None:
        return ""
    if isinstance(value, float):
        try:
            if math.isnan(value):
                return ""
        except Exception:
            pass
    return str(value).strip()



def parse_asset_cost(value):
    """
    Convert common South African Rand / numeric cost formats to float.
    Returns None when the value cannot be interpreted.
    """

    text = clean_text(value)

    if not text:
        return None

    negative = (
        text.startswith("(")
        and text.endswith(")")
    )

    text = (
        text.replace("ZAR", "")
        .replace("zar", "")
        .replace("R", "")
        .replace("r", "")
        .replace(" ", "")
        .replace("\u00a0", "")
    )

    if negative:
        text = text[1:-1]

    # Support both 12,345.67 and 12 345,67 style values.
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        parts = text.split(",")

        if (
            len(parts) == 2
            and len(parts[1]) in (1, 2)
        ):
            text = (
                parts[0]
                + "."
                + parts[1]
            )
        else:
            text = text.replace(",", "")

    text = re.sub(
        r"[^0-9.\-]",
        "",
        text,
    )

    if text in {
        "",
        "-",
        ".",
        "-.",
    }:
        return None

    try:
        amount = float(text)
    except ValueError:
        return None

    if negative:
        amount = -abs(amount)

    return amount


def parse_asset_date(value):
    """
    Parse the date formats commonly found in asset registers.
    Returns a date object or None.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = clean_text(value)

    if not text:
        return None

    # ISO strings, including timestamps from pandas / Excel imports.
    try:
        return datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        ).date()
    except ValueError:
        pass

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%m/%d/%Y",
    )

    for format_string in formats:
        try:
            return datetime.strptime(
                text,
                format_string,
            ).date()
        except ValueError:
            continue

    return None


def _normalise_useful_life(value):
    try:
        useful_life = float(
            clean_text(value)
        )
    except (TypeError, ValueError):
        useful_life = 0.0

    if useful_life <= 0:
        return DEFAULT_USEFUL_LIFE_YEARS

    return useful_life


def calculate_asset_financials(
    asset,
    as_of_date=None,
):
    """
    Calculate age, depreciation and current book value.

    Method:
      - Straight-line depreciation
      - Zero residual value
      - Useful life defaults to DEFAULT_USEFUL_LIFE_YEARS
        unless an asset-specific override exists.

    The calculations are dynamic. Current book value is not permanently
    stored, so it automatically changes as time passes.
    """

    if as_of_date is None:
        as_of_date = date.today()
    elif isinstance(
        as_of_date,
        datetime,
    ):
        as_of_date = as_of_date.date()

    purchase_cost = parse_asset_cost(
        asset.get(
            "purchase_cost_r"
        )
    )

    purchase_date = parse_asset_date(
        asset.get(
            "purchase_date"
        )
    )

    raw_useful_life = asset.get(
        "useful_life_years"
    )

    useful_life = (
        _normalise_useful_life(
            raw_useful_life
        )
    )

    useful_life_source = (
        "Asset override"
        if clean_text(
            raw_useful_life
        )
        else "System default"
    )

    result = {
        "depreciation_method": (
            DEPRECIATION_METHOD
        ),
        "useful_life_years": round(
            useful_life,
            2,
        ),
        "useful_life_source": (
            useful_life_source
        ),
        "residual_value_r": (
            DEFAULT_RESIDUAL_VALUE_R
        ),
        "purchase_cost_numeric_r": (
            purchase_cost
        ),
        "calculated_age_years": None,
        "remaining_life_years": None,
        "annual_depreciation_r": None,
        "monthly_depreciation_r": None,
        "accumulated_depreciation_r": None,
        "current_book_value_r": None,
        "end_of_useful_life": "",
        "fully_depreciated": 0,
        "financial_calculation_valid": 0,
        "financial_calculation_status": "",
    }

    if purchase_cost is None:
        result[
            "financial_calculation_status"
        ] = (
            "Purchase cost is missing or invalid."
        )
        return result

    if purchase_cost < 0:
        result[
            "financial_calculation_status"
        ] = (
            "Purchase cost cannot be negative."
        )
        return result

    if purchase_date is None:
        result[
            "financial_calculation_status"
        ] = (
            "Purchase date is missing or invalid."
        )
        return result

    age_days = (
        as_of_date
        - purchase_date
    ).days

    if age_days < 0:
        age_days = 0
        calculation_status = (
            "Purchase date is in the future; "
            "depreciation has not started."
        )
    else:
        calculation_status = "Calculated"

    age_years = (
        age_days
        / 365.25
    )

    depreciable_amount = max(
        0.0,
        purchase_cost
        - DEFAULT_RESIDUAL_VALUE_R,
    )

    annual_depreciation = (
        depreciable_amount
        / useful_life
    )

    monthly_depreciation = (
        annual_depreciation
        / 12.0
    )

    accumulated_depreciation = min(
        depreciable_amount,
        annual_depreciation
        * age_years,
    )

    current_book_value = max(
        DEFAULT_RESIDUAL_VALUE_R,
        purchase_cost
        - accumulated_depreciation,
    )

    remaining_life = max(
        0.0,
        useful_life
        - age_years,
    )

    end_of_life = (
        purchase_date
        + timedelta(
            days=round(
                useful_life
                * 365.25
            )
        )
    )

    fully_depreciated = (
        age_years
        >= useful_life
    )

    result.update(
        {
            "calculated_age_years": round(
                age_years,
                2,
            ),
            "remaining_life_years": round(
                remaining_life,
                2,
            ),
            "annual_depreciation_r": round(
                annual_depreciation,
                2,
            ),
            "monthly_depreciation_r": round(
                monthly_depreciation,
                2,
            ),
            "accumulated_depreciation_r": round(
                accumulated_depreciation,
                2,
            ),
            "current_book_value_r": round(
                current_book_value,
                2,
            ),
            "end_of_useful_life": (
                end_of_life.isoformat()
            ),
            "fully_depreciated": (
                1
                if fully_depreciated
                else 0
            ),
            "financial_calculation_valid": 1,
            "financial_calculation_status": (
                calculation_status
            ),
        }
    )

    return result



def calculate_warranty_info(
    asset,
    as_of_date=None,
):
    """
    Calculate warranty status dynamically from Warranty Expiry.

    Rules:
      - expiry date >= today: In Warranty
      - expiry date < today: Out of Warranty
      - missing/invalid expiry date: Warranty Date Missing
    """

    if as_of_date is None:
        as_of_date = date.today()
    elif isinstance(
        as_of_date,
        datetime,
    ):
        as_of_date = as_of_date.date()

    expiry_date = parse_asset_date(
        asset.get(
            "warranty_expiry"
        )
    )

    result = {
        "calculated_warranty_status": (
            "Warranty Date Missing"
        ),
        "warranty_days_remaining": None,
        "warranty_detail": (
            "Warranty expiry date is missing or invalid."
        ),
        "warranty_expiry_parsed": "",
    }

    if expiry_date is None:
        return result

    result[
        "warranty_expiry_parsed"
    ] = expiry_date.isoformat()

    days_difference = (
        expiry_date
        - as_of_date
    ).days

    result[
        "warranty_days_remaining"
    ] = days_difference

    if days_difference >= 0:
        result[
            "calculated_warranty_status"
        ] = "In Warranty"

        if days_difference == 0:
            result[
                "warranty_detail"
            ] = "Warranty expires today."
        elif days_difference == 1:
            result[
                "warranty_detail"
            ] = "1 day remaining."
        else:
            result[
                "warranty_detail"
            ] = (
                f"{days_difference} days remaining."
            )

    else:
        result[
            "calculated_warranty_status"
        ] = "Out of Warranty"

        expired_days = abs(
            days_difference
        )

        if expired_days == 1:
            result[
                "warranty_detail"
            ] = "Warranty expired 1 day ago."
        else:
            result[
                "warranty_detail"
            ] = (
                f"Warranty expired {expired_days} days ago."
            )

    return result


def calculate_warranty_summary(
    asset_records,
):
    """
    Count assets by calculated warranty status.
    """

    summary = {
        "in_warranty": 0,
        "out_of_warranty": 0,
        "warranty_date_missing": 0,
    }

    for asset in asset_records:
        warranty_info = (
            calculate_warranty_info(
                asset
            )
        )

        status = warranty_info[
            "calculated_warranty_status"
        ]

        if status == "In Warranty":
            summary[
                "in_warranty"
            ] += 1
        elif status == "Out of Warranty":
            summary[
                "out_of_warranty"
            ] += 1
        else:
            summary[
                "warranty_date_missing"
            ] += 1

    return summary


def calculate_portfolio_financials(
    asset_records,
):
    """
    Summarise original cost, depreciation and book value
    for a collection of assets.
    """

    total_original_cost = 0.0
    total_accumulated_depreciation = 0.0
    total_current_book_value = 0.0
    assets_with_cost = 0
    assets_with_book_value = 0
    excluded_from_book_value = 0

    for asset in asset_records:
        financials = (
            calculate_asset_financials(
                asset
            )
        )

        purchase_cost = financials.get(
            "purchase_cost_numeric_r"
        )

        if purchase_cost is not None:
            total_original_cost += (
                purchase_cost
            )
            assets_with_cost += 1

        if financials.get(
            "financial_calculation_valid"
        ):
            total_accumulated_depreciation += (
                financials.get(
                    "accumulated_depreciation_r"
                )
                or 0.0
            )

            total_current_book_value += (
                financials.get(
                    "current_book_value_r"
                )
                or 0.0
            )

            assets_with_book_value += 1
        else:
            excluded_from_book_value += 1

    return {
        "total_original_cost_r": round(
            total_original_cost,
            2,
        ),
        "total_accumulated_depreciation_r": round(
            total_accumulated_depreciation,
            2,
        ),
        "total_current_book_value_r": round(
            total_current_book_value,
            2,
        ),
        "assets_with_cost": (
            assets_with_cost
        ),
        "assets_with_book_value": (
            assets_with_book_value
        ),
        "assets_excluded_from_book_value": (
            excluded_from_book_value
        ),
    }


def format_currency_r(value):
    if value is None:
        return "Not available"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "Not available"

    return (
        "R "
        + f"{number:,.2f}"
    )


def _enrich_asset_record(record):
    record = dict(record)

    record.update(
        calculate_asset_financials(
            record
        )
    )

    warranty_info = (
        calculate_warranty_info(
            record
        )
    )

    record.update(
        warranty_info
    )

    # Keep the legacy database column for compatibility,
    # but always expose the current calculated warranty status.
    record[
        "warranty_status"
    ] = warranty_info[
        "calculated_warranty_status"
    ]

    return record


@contextmanager
def get_connection():
    """Open, transactionally commit/rollback, and always close SQLite."""
    DATA_FOLDER.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
    finally:
        connection.close()


def _get_table_columns(connection, table_name):
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    return {row["name"] for row in rows}


def _ensure_column(
    connection,
    table_name,
    column_name,
    column_type,
):
    columns = _get_table_columns(connection, table_name)
    if column_name not in columns:
        connection.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
            """
        )


def initialize_database():
    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                corporate_asset_id TEXT NOT NULL COLLATE NOCASE UNIQUE,
                asset_type TEXT,
                category TEXT,
                make TEXT,
                model TEXT,
                serial_number TEXT,
                department_asset_tag TEXT,
                facility_site TEXT,
                district TEXT,
                section_department TEXT,
                room_location TEXT,
                specification_os TEXT,
                purchase_date TEXT,
                purchase_cost_r TEXT,
                supplier TEXT,
                warranty_expiry TEXT,
                age_yrs TEXT,
                assigned_user TEXT,
                condition TEXT,
                status TEXT,
                warranty_status TEXT,
                recommendation TEXT,
                verified_on TEXT,
                verified_by TEXT,
                notes TEXT,
                source_file TEXT,
                source_system TEXT DEFAULT 'Corporate Asset System',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_synced_at TEXT
            )
            """
        )

        _ensure_column(
            connection,
            "assets",
            "operational_facility",
            "TEXT",
        )
        _ensure_column(
            connection,
            "assets",
            "operational_department",
            "TEXT",
        )
        _ensure_column(
            connection,
            "assets",
            "operational_location",
            "TEXT",
        )
        _ensure_column(
            connection,
            "assets",
            "assigned_user_account_id",
            "INTEGER",
        )
        _ensure_column(
            connection,
            "assets",
            "attention_required",
            "INTEGER NOT NULL DEFAULT 0",
        )
        _ensure_column(
            connection,
            "assets",
            "useful_life_years",
            "REAL",
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS asset_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                corporate_asset_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                performed_by TEXT,
                notes TEXT,
                event_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (corporate_asset_id)
                    REFERENCES assets(corporate_asset_id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS asset_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                corporate_asset_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                from_assigned_user TEXT,
                to_assigned_user TEXT,
                from_facility TEXT,
                to_facility TEXT,
                from_department TEXT,
                to_department TEXT,
                from_location TEXT,
                to_location TEXT,
                repair_provider TEXT,
                reference_number TEXT,
                status_before TEXT,
                status_after TEXT,
                condition_before TEXT,
                condition_after TEXT,
                performed_by TEXT NOT NULL,
                notes TEXT,
                event_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (corporate_asset_id)
                    REFERENCES assets(corporate_asset_id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_assets_serial_number
            ON assets(serial_number)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_assets_asset_tag
            ON assets(department_asset_tag)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_assets_facility
            ON assets(facility_site)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_assets_type
            ON assets(asset_type)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_history_asset_id
            ON asset_history(corporate_asset_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_transactions_asset_id
            ON asset_transactions(corporate_asset_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_assets_assigned_user_account
            ON assets(assigned_user_account_id)
            """
        )


def load_assets_from_db():
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                corporate_asset_id AS asset_id,
                asset_type,
                category,
                make,
                model,
                serial_number,
                department_asset_tag,
                facility_site,
                district,
                section_department,
                room_location,
                operational_facility,
                operational_department,
                operational_location,
                specification_os,
                assigned_user,
                assigned_user_account_id,
                attention_required,
                useful_life_years,
                purchase_date,
                purchase_cost_r,
                supplier,
                warranty_expiry,
                condition,
                status,
                age_yrs,
                warranty_status,
                recommendation,
                verified_on,
                verified_by,
                notes,
                source_file,
                source_system,
                created_at,
                updated_at,
                last_synced_at
            FROM assets
            ORDER BY corporate_asset_id
            """
        ).fetchall()
    return [
        _enrich_asset_record(
            row
        )
        for row in rows
    ]


def get_asset_record(corporate_asset_id):
    initialize_database()
    corporate_asset_id = clean_text(corporate_asset_id)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()
    if row is None:
        return None

    return _enrich_asset_record(
        row
    )


def preview_sync_assets(imported_assets):
    initialize_database()

    new_assets = []
    changed_assets = []
    unchanged_assets = []
    duplicate_source_ids = []
    skipped_records = []
    seen_ids = set()
    source_ids = set()

    with get_connection() as connection:
        database_rows = connection.execute(
            "SELECT * FROM assets"
        ).fetchall()

    existing_assets = {
        clean_text(row["corporate_asset_id"]).lower(): row
        for row in database_rows
        if clean_text(row["corporate_asset_id"])
    }

    for asset in imported_assets:
        corporate_asset_id = clean_text(
            asset.get("asset_id")
            or asset.get("corporate_asset_id")
        )

        if not corporate_asset_id:
            skipped_records.append(
                {
                    "reason": "Missing Asset ID",
                    "asset": asset,
                }
            )
            continue

        key = corporate_asset_id.lower()

        if key in seen_ids:
            duplicate_source_ids.append(corporate_asset_id)
            skipped_records.append(
                {
                    "reason": "Duplicate Asset ID in source",
                    "asset": asset,
                }
            )
            continue

        seen_ids.add(key)
        source_ids.add(key)

        current_record = existing_assets.get(key)

        if current_record is None:
            new_assets.append(asset)
            continue

        changes = []

        for field in SOURCE_FIELDS:
            old_value = clean_text(current_record[field])
            new_value = clean_text(asset.get(field))

            if old_value != new_value:
                changes.append(
                    {
                        "field": field,
                        "label": SOURCE_FIELD_LABELS.get(field, field),
                        "old": old_value,
                        "new": new_value,
                    }
                )

        if changes:
            changed_assets.append(
                {
                    "asset_id": corporate_asset_id,
                    "asset": asset,
                    "changes": changes,
                }
            )
        else:
            unchanged_assets.append(corporate_asset_id)

    not_in_current_import = [
        dict(row)
        for key, row in existing_assets.items()
        if key not in source_ids
    ]

    return {
        "new": new_assets,
        "changed": changed_assets,
        "unchanged": unchanged_assets,
        "duplicates": duplicate_source_ids,
        "skipped": skipped_records,
        "not_in_current_import": not_in_current_import,
        "counts": {
            "new": len(new_assets),
            "changed": len(changed_assets),
            "unchanged": len(unchanged_assets),
            "duplicates": len(duplicate_source_ids),
            "skipped": len(skipped_records),
            "not_in_current_import": len(not_in_current_import),
        },
    }


def sync_assets(
    imported_assets,
    source_system="Corporate Asset System",
):
    initialize_database()

    inserted = 0
    updated = 0
    unchanged = 0
    skipped = 0
    duplicate_source_ids = []
    seen_ids = set()

    insert_columns = (
        ["corporate_asset_id"]
        + SOURCE_FIELDS
        + IT_MANAGED_FIELDS
        + ["source_file", "source_system"]
    )

    insert_sql = f"""
        INSERT INTO assets (
            {", ".join(insert_columns)},
            last_synced_at
        )
        VALUES (
            {", ".join(["?"] * len(insert_columns))},
            CURRENT_TIMESTAMP
        )
    """

    update_fields = SOURCE_FIELDS + ["source_file", "source_system"]

    update_sql = f"""
        UPDATE assets
        SET
            {", ".join(f"{field} = ?" for field in update_fields)},
            updated_at = CURRENT_TIMESTAMP,
            last_synced_at = CURRENT_TIMESTAMP
        WHERE corporate_asset_id = ?
    """

    with get_connection() as connection:
        for asset in imported_assets:
            corporate_asset_id = clean_text(
                asset.get("asset_id")
                or asset.get("corporate_asset_id")
            )

            if not corporate_asset_id:
                skipped += 1
                continue

            key = corporate_asset_id.lower()

            if key in seen_ids:
                duplicate_source_ids.append(corporate_asset_id)
                skipped += 1
                continue

            seen_ids.add(key)

            current_record = connection.execute(
                """
                SELECT *
                FROM assets
                WHERE corporate_asset_id = ?
                """,
                (corporate_asset_id,),
            ).fetchone()

            if current_record is None:
                values = [corporate_asset_id]
                values.extend(
                    clean_text(asset.get(field))
                    for field in SOURCE_FIELDS
                )
                values.extend(
                    clean_text(asset.get(field))
                    for field in IT_MANAGED_FIELDS
                )
                values.append(clean_text(asset.get("source_file")))
                values.append(source_system)

                connection.execute(insert_sql, values)
                inserted += 1
                continue

            has_changed = any(
                clean_text(current_record[field])
                != clean_text(asset.get(field))
                for field in SOURCE_FIELDS
            )

            if has_changed:
                update_values = [
                    clean_text(asset.get(field))
                    for field in SOURCE_FIELDS
                ]
                update_values.append(
                    clean_text(asset.get("source_file"))
                )
                update_values.append(source_system)
                update_values.append(corporate_asset_id)

                connection.execute(
                    update_sql,
                    update_values,
                )
                updated += 1
            else:
                connection.execute(
                    """
                    UPDATE assets
                    SET
                        source_file = ?,
                        source_system = ?,
                        last_synced_at = CURRENT_TIMESTAMP
                    WHERE corporate_asset_id = ?
                    """,
                    (
                        clean_text(asset.get("source_file")),
                        source_system,
                        corporate_asset_id,
                    ),
                )
                unchanged += 1

    return {
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "skipped": skipped,
        "duplicate_source_ids": duplicate_source_ids,
    }


def add_asset_history(
    corporate_asset_id,
    event_type,
    field_name="",
    old_value="",
    new_value="",
    performed_by="",
    notes="",
):
    initialize_database()
    corporate_asset_id = clean_text(corporate_asset_id)

    if not corporate_asset_id:
        raise ValueError("Asset ID is required.")

    with get_connection() as connection:
        exists = connection.execute(
            """
            SELECT 1
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if exists is None:
            raise ValueError("Asset could not be found.")

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                clean_text(event_type),
                clean_text(field_name),
                clean_text(old_value),
                clean_text(new_value),
                clean_text(performed_by),
                clean_text(notes),
            ),
        )


def get_asset_history(corporate_asset_id):
    initialize_database()
    corporate_asset_id = clean_text(corporate_asset_id)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes,
                event_at
            FROM asset_history
            WHERE corporate_asset_id = ?
            ORDER BY event_at DESC, id DESC
            """,
            (corporate_asset_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def verify_asset(
    corporate_asset_id,
    verified_by,
    condition,
    status,
    assigned_user,
    notes="",
):
    initialize_database()

    corporate_asset_id = clean_text(corporate_asset_id)
    verified_by = clean_text(verified_by)
    condition = clean_text(condition)
    status = clean_text(status)
    assigned_user = clean_text(assigned_user)
    notes = clean_text(notes)

    if not corporate_asset_id:
        raise ValueError("Asset ID is required.")

    if not verified_by:
        raise ValueError("Verified By is required.")

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if current is None:
            raise ValueError("Asset could not be found.")

        tracked_fields = {
            "condition": condition,
            "status": status,
            "assigned_user": assigned_user,
        }

        for field_name, new_value in tracked_fields.items():
            old_value = clean_text(current[field_name])

            if old_value != new_value:
                connection.execute(
                    """
                    INSERT INTO asset_history (
                        corporate_asset_id,
                        event_type,
                        field_name,
                        old_value,
                        new_value,
                        performed_by,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        corporate_asset_id,
                        "Field Changed",
                        field_name,
                        old_value,
                        new_value,
                        verified_by,
                        notes,
                    ),
                )

        connection.execute(
            """
            UPDATE assets
            SET
                condition = ?,
                status = ?,
                assigned_user = ?,
                verified_on = CURRENT_TIMESTAMP,
                verified_by = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (
                condition,
                status,
                assigned_user,
                verified_by,
                notes,
                corporate_asset_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Asset Verified",
                verified_by,
                notes,
            ),
        )


def get_asset_transactions(corporate_asset_id):
    initialize_database()
    corporate_asset_id = clean_text(corporate_asset_id)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM asset_transactions
            WHERE corporate_asset_id = ?
            ORDER BY event_at DESC, id DESC
            """,
            (corporate_asset_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def assign_asset(
    corporate_asset_id,
    assigned_user,
    performed_by,
    notes="",
    assigned_user_account_id=None,
):
    initialize_user_security()

    corporate_asset_id = clean_text(corporate_asset_id)
    assigned_user = clean_text(assigned_user)
    performed_by = clean_text(performed_by)
    notes = clean_text(notes)

    if not performed_by:
        raise ValueError("Performed By is required.")

    account_id = None

    if assigned_user_account_id not in (None, ""):
        try:
            account_id = int(assigned_user_account_id)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "The selected employee account is invalid."
            ) from error

        linked_user = get_user(account_id)

        if linked_user is None:
            raise ValueError(
                "The selected employee account could not be found."
            )

        if not int(linked_user["active"]):
            raise ValueError(
                "The selected employee account is inactive."
            )

        assigned_user = linked_user["full_name"]

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if current is None:
            raise ValueError("Asset could not be found.")

        old_user = clean_text(current["assigned_user"])
        old_account_id = current["assigned_user_account_id"]

        connection.execute(
            """
            UPDATE assets
            SET
                assigned_user = ?,
                assigned_user_account_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (
                assigned_user,
                account_id,
                corporate_asset_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_transactions (
                corporate_asset_id,
                transaction_type,
                from_assigned_user,
                to_assigned_user,
                status_before,
                status_after,
                condition_before,
                condition_after,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "User Assignment",
                old_user,
                assigned_user,
                clean_text(current["status"]),
                clean_text(current["status"]),
                clean_text(current["condition"]),
                clean_text(current["condition"]),
                performed_by,
                notes,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "User Assignment",
                "assigned_user",
                old_user,
                assigned_user,
                performed_by,
                notes,
            ),
        )

        if old_account_id != account_id:
            connection.execute(
                """
                INSERT INTO asset_history (
                    corporate_asset_id,
                    event_type,
                    field_name,
                    old_value,
                    new_value,
                    performed_by,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    corporate_asset_id,
                    "Account Link Changed",
                    "assigned_user_account_id",
                    clean_text(old_account_id),
                    clean_text(account_id),
                    performed_by,
                    notes,
                ),
            )

    return {
        "old_user": old_user,
        "new_user": assigned_user,
        "assigned_user_account_id": account_id,
    }

def transfer_asset(
    corporate_asset_id,
    new_facility,
    new_department,
    new_location,
    performed_by,
    notes="",
):
    initialize_database()

    corporate_asset_id = clean_text(corporate_asset_id)
    new_facility = clean_text(new_facility)
    new_department = clean_text(new_department)
    new_location = clean_text(new_location)
    performed_by = clean_text(performed_by)
    notes = clean_text(notes)

    if not performed_by:
        raise ValueError("Performed By is required.")

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if current is None:
            raise ValueError("Asset could not be found.")

        old_facility = (
            clean_text(current["operational_facility"])
            or clean_text(current["facility_site"])
        )
        old_department = (
            clean_text(current["operational_department"])
            or clean_text(current["section_department"])
        )
        old_location = (
            clean_text(current["operational_location"])
            or clean_text(current["room_location"])
        )

        connection.execute(
            """
            UPDATE assets
            SET
                operational_facility = ?,
                operational_department = ?,
                operational_location = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (
                new_facility,
                new_department,
                new_location,
                corporate_asset_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_transactions (
                corporate_asset_id,
                transaction_type,
                from_facility,
                to_facility,
                from_department,
                to_department,
                from_location,
                to_location,
                status_before,
                status_after,
                condition_before,
                condition_after,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Asset Transfer",
                old_facility,
                new_facility,
                old_department,
                new_department,
                old_location,
                new_location,
                clean_text(current["status"]),
                clean_text(current["status"]),
                clean_text(current["condition"]),
                clean_text(current["condition"]),
                performed_by,
                notes,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Asset Transfer",
                "Operational Location",
                f"{old_facility} / {old_department} / {old_location}",
                f"{new_facility} / {new_department} / {new_location}",
                performed_by,
                notes,
            ),
        )


def send_asset_for_repair(
    corporate_asset_id,
    repair_provider,
    reference_number,
    performed_by,
    notes="",
):
    initialize_database()

    corporate_asset_id = clean_text(corporate_asset_id)
    repair_provider = clean_text(repair_provider)
    reference_number = clean_text(reference_number)
    performed_by = clean_text(performed_by)
    notes = clean_text(notes)

    if not repair_provider:
        raise ValueError("Repair Provider is required.")

    if not performed_by:
        raise ValueError("Performed By is required.")

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if current is None:
            raise ValueError("Asset could not be found.")

        old_status = clean_text(current["status"])

        connection.execute(
            """
            UPDATE assets
            SET
                status = 'Under Repair',
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        )

        connection.execute(
            """
            INSERT INTO asset_transactions (
                corporate_asset_id,
                transaction_type,
                repair_provider,
                reference_number,
                status_before,
                status_after,
                condition_before,
                condition_after,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Repair Out",
                repair_provider,
                reference_number,
                old_status,
                "Under Repair",
                clean_text(current["condition"]),
                clean_text(current["condition"]),
                performed_by,
                notes,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Repair Out",
                "status",
                old_status,
                "Under Repair",
                performed_by,
                (
                    f"Provider: {repair_provider}; "
                    f"Reference: {reference_number}; "
                    f"{notes}"
                ),
            ),
        )


def return_asset_from_repair(
    corporate_asset_id,
    condition,
    status,
    performed_by,
    reference_number="",
    notes="",
):
    initialize_database()

    corporate_asset_id = clean_text(corporate_asset_id)
    condition = clean_text(condition)
    status = clean_text(status)
    performed_by = clean_text(performed_by)
    reference_number = clean_text(reference_number)
    notes = clean_text(notes)

    if not performed_by:
        raise ValueError("Performed By is required.")

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if current is None:
            raise ValueError("Asset could not be found.")

        old_status = clean_text(current["status"])
        old_condition = clean_text(current["condition"])

        connection.execute(
            """
            UPDATE assets
            SET
                status = ?,
                condition = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (
                status,
                condition,
                corporate_asset_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_transactions (
                corporate_asset_id,
                transaction_type,
                reference_number,
                status_before,
                status_after,
                condition_before,
                condition_after,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Repair Return",
                reference_number,
                old_status,
                status,
                old_condition,
                condition,
                performed_by,
                notes,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Repair Return",
                "status / condition",
                f"{old_status} / {old_condition}",
                f"{status} / {condition}",
                performed_by,
                notes,
            ),
        )

# ============================================================
# USER ACCOUNTS / LOGIN
# ============================================================

USER_ROLES = (
    "Administrator",
    "IT Officer",
    "Employee",
    "Viewer",
)

PASSWORD_ITERATIONS = 310_000


def initialize_user_security():
    """Create the local application user table."""

    initialize_database()

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_users_username
            ON users(username)
            """
        )


def _hash_password(password, salt_bytes=None):
    password = str(password)

    if salt_bytes is None:
        salt_bytes = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PASSWORD_ITERATIONS,
    )

    return (
        salt_bytes.hex(),
        password_hash.hex(),
    )


def _validate_password(password):
    if len(str(password)) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )


def count_users():
    initialize_user_security()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM users"
        ).fetchone()

    return int(row["total"])


def _require_active_administrator(performed_by_user_id):
    """Require an active administrator for user-management changes.

    This is a local desktop app: it does not protect a database file from
    someone who already has unrestricted access to the computer.
    """
    user = get_user(performed_by_user_id)
    if (user is None or not int(user["active"])
            or user["role"] != "Administrator"):
        raise PermissionError("An active Administrator account is required.")
    return user


def create_user(
    username,
    password,
    full_name,
    role="IT Officer",
    performed_by_user_id=None,
):
    initialize_user_security()

    username = clean_text(username)
    full_name = clean_text(full_name)
    role = clean_text(role)

    if not username:
        raise ValueError("Username is required.")

    if not full_name:
        raise ValueError("Full name is required.")

    if role not in USER_ROLES:
        raise ValueError("Please select a valid user role.")

    _validate_password(password)

    # Bootstrap the first account. All later account creation requires
    # an authenticated administrator identity passed by the GUI.
    if count_users() == 0:
        role = "Administrator"
    else:
        _require_active_administrator(performed_by_user_id)

    salt_hex, hash_hex = _hash_password(password)

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username,
                    full_name,
                    role,
                    password_hash,
                    password_salt,
                    active
                )
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (
                    username,
                    full_name,
                    role,
                    hash_hex,
                    salt_hex,
                ),
            )

            user_id = cursor.lastrowid

    except sqlite3.IntegrityError as error:
        raise ValueError(
            "That username already exists."
        ) from error

    return {
        "id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "active": 1,
    }


def authenticate_user(username, password):
    initialize_user_security()

    username = clean_text(username)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if row is None:
            return None

        if not int(row["active"]):
            return None

        salt_bytes = bytes.fromhex(
            row["password_salt"]
        )

        _, candidate_hash = _hash_password(
            password,
            salt_bytes,
        )

        if not hmac.compare_digest(
            candidate_hash,
            row["password_hash"],
        ):
            return None

        connection.execute(
            """
            UPDATE users
            SET last_login_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (row["id"],),
        )

        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "role": row["role"],
            "active": row["active"],
        }


def list_users():
    initialize_user_security()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                username,
                full_name,
                role,
                active,
                created_at,
                last_login_at
            FROM users
            ORDER BY full_name, username
            """
        ).fetchall()

    return [dict(row) for row in rows]


def set_user_active(user_id, active, performed_by_user_id=None):
    initialize_user_security()
    _require_active_administrator(performed_by_user_id)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, role, active
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            raise ValueError("User could not be found.")

        # Do not allow the final active administrator to be disabled.
        if (
            row["role"] == "Administrator"
            and int(row["active"]) == 1
            and not active
        ):
            admin_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM users
                WHERE role = 'Administrator'
                  AND active = 1
                """
            ).fetchone()["total"]

            if int(admin_count) <= 1:
                raise ValueError(
                    "At least one active Administrator account is required."
                )

        connection.execute(
            """
            UPDATE users
            SET active = ?
            WHERE id = ?
            """,
            (
                1 if active else 0,
                user_id,
            ),
        )


def reset_user_password(user_id, new_password, performed_by_user_id=None):
    initialize_user_security()
    _require_active_administrator(performed_by_user_id)
    _validate_password(new_password)

    salt_hex, hash_hex = _hash_password(
        new_password
    )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE users
            SET
                password_hash = ?,
                password_salt = ?
            WHERE id = ?
            """,
            (
                hash_hex,
                salt_hex,
                user_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError("User could not be found.")



# ============================================================
# EMPLOYEE ASSET ACCESS / ACCOUNT LINKING
# ============================================================

def get_user(user_id):
    initialize_user_security()

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                username,
                full_name,
                role,
                active,
                created_at,
                last_login_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return None if row is None else dict(row)


def list_assignable_users():
    """
    Return active accounts that can own an IT asset.

    Employee accounts are the normal choice, but administrators
    and IT officers can also have equipment assigned to them.
    """
    initialize_user_security()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                username,
                full_name,
                role,
                active
            FROM users
            WHERE active = 1
              AND role IN (
                    'Employee',
                    'Administrator',
                    'IT Officer'
              )
            ORDER BY
                CASE role
                    WHEN 'Employee' THEN 0
                    WHEN 'IT Officer' THEN 1
                    ELSE 2
                END,
                full_name,
                username
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_assets_for_user(user_id):
    """
    Return only assets linked to one application account.
    """
    initialize_user_security()

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return []

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                corporate_asset_id AS asset_id,
                asset_type,
                category,
                make,
                model,
                serial_number,
                department_asset_tag,
                facility_site,
                district,
                section_department,
                room_location,
                operational_facility,
                operational_department,
                operational_location,
                specification_os,
                assigned_user,
                assigned_user_account_id,
                attention_required,
                useful_life_years,
                purchase_date,
                purchase_cost_r,
                supplier,
                warranty_expiry,
                condition,
                status,
                age_yrs,
                warranty_status,
                recommendation,
                verified_on,
                verified_by,
                notes,
                source_file,
                source_system,
                created_at,
                updated_at,
                last_synced_at
            FROM assets
            WHERE assigned_user_account_id = ?
            ORDER BY corporate_asset_id
            """,
            (user_id,),
        ).fetchall()

    return [
        _enrich_asset_record(
            row
        )
        for row in rows
    ]


def link_asset_to_user(
    corporate_asset_id,
    user_id,
    performed_by,
    notes="",
):
    """
    Link an existing asset to an application account.

    The human-readable Assigned User field is kept in sync with
    the selected account's full name.
    """
    initialize_user_security()

    corporate_asset_id = clean_text(corporate_asset_id)
    performed_by = clean_text(performed_by)
    notes = clean_text(notes)

    if not performed_by:
        raise ValueError("Performed By is required.")

    user = get_user(user_id)

    if user is None:
        raise ValueError("Employee account could not be found.")

    if not int(user["active"]):
        raise ValueError("Employee account is inactive.")

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT
                corporate_asset_id,
                assigned_user,
                assigned_user_account_id
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if current is None:
            raise ValueError("Asset could not be found.")

        old_name = clean_text(current["assigned_user"])
        old_account_id = current["assigned_user_account_id"]

        connection.execute(
            """
            UPDATE assets
            SET
                assigned_user = ?,
                assigned_user_account_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (
                user["full_name"],
                user["id"],
                corporate_asset_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Employee Account Linked",
                "assigned_user",
                old_name,
                user["full_name"],
                performed_by,
                (
                    notes
                    or (
                        f"Linked to login account "
                        f"{user['username']}."
                    )
                ),
            ),
        )

        if old_account_id != user["id"]:
            connection.execute(
                """
                INSERT INTO asset_history (
                    corporate_asset_id,
                    event_type,
                    field_name,
                    old_value,
                    new_value,
                    performed_by,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    corporate_asset_id,
                    "Account Link Changed",
                    "assigned_user_account_id",
                    clean_text(old_account_id),
                    clean_text(user["id"]),
                    performed_by,
                    notes,
                ),
            )

    return {
        "asset_id": corporate_asset_id,
        "user_id": user["id"],
        "full_name": user["full_name"],
    }


def unlink_asset_from_user(
    corporate_asset_id,
    performed_by,
    notes="",
):
    """
    Remove the application-account link.

    The displayed Assigned User text is intentionally retained,
    because it may still be useful for reconciliation.
    """
    initialize_user_security()

    corporate_asset_id = clean_text(corporate_asset_id)
    performed_by = clean_text(performed_by)
    notes = clean_text(notes)

    if not performed_by:
        raise ValueError("Performed By is required.")

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT
                assigned_user,
                assigned_user_account_id
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        ).fetchone()

        if current is None:
            raise ValueError("Asset could not be found.")

        old_account_id = current["assigned_user_account_id"]

        connection.execute(
            """
            UPDATE assets
            SET
                assigned_user_account_id = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (corporate_asset_id,),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Employee Account Unlinked",
                "assigned_user_account_id",
                clean_text(old_account_id),
                "",
                performed_by,
                notes,
            ),
        )


def auto_link_existing_assignments(performed_by):
    """
    Safely link unlinked assets where Assigned User exactly matches
    one unique active account full name (case-insensitive).
    """
    initialize_user_security()

    performed_by = clean_text(performed_by)

    if not performed_by:
        raise ValueError("Performed By is required.")

    users = list_assignable_users()

    users_by_name = {}

    for user in users:
        key = clean_text(user["full_name"]).lower()

        if not key:
            continue

        users_by_name.setdefault(key, [])
        users_by_name[key].append(user)

    linked = 0
    ambiguous = 0
    unmatched = 0

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                corporate_asset_id,
                assigned_user
            FROM assets
            WHERE assigned_user_account_id IS NULL
              AND TRIM(COALESCE(assigned_user, '')) <> ''
            ORDER BY corporate_asset_id
            """
        ).fetchall()

    for row in rows:
        key = clean_text(row["assigned_user"]).lower()
        candidates = users_by_name.get(key, [])

        if len(candidates) == 1:
            link_asset_to_user(
                row["corporate_asset_id"],
                candidates[0]["id"],
                performed_by,
                notes="Auto-linked by exact employee-name match.",
            )
            linked += 1
        elif len(candidates) > 1:
            ambiguous += 1
        else:
            unmatched += 1

    return {
        "linked": linked,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
    }


def verify_employee_asset(
    corporate_asset_id,
    user_id,
    condition,
    current_location,
    possession_confirmed,
    issue_reported,
    notes="",
):
    """
    Employee self-service verification.

    Security is enforced in the database: the asset must be linked
    to the same account that is performing the verification.
    """
    initialize_user_security()

    corporate_asset_id = clean_text(corporate_asset_id)
    condition = clean_text(condition)
    current_location = clean_text(current_location)
    possession_confirmed = bool(possession_confirmed)
    issue_reported = bool(issue_reported)
    notes = clean_text(notes)

    user = get_user(user_id)

    if user is None or not int(user["active"]):
        raise PermissionError(
            "Your user account is not active."
        )

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE corporate_asset_id = ?
              AND assigned_user_account_id = ?
            """,
            (
                corporate_asset_id,
                int(user_id),
            ),
        ).fetchone()

        if current is None:
            raise PermissionError(
                "You can only verify assets assigned to your account."
            )

        old_condition = clean_text(current["condition"])
        old_location = (
            clean_text(current["operational_location"])
            or clean_text(current["room_location"])
        )

        needs_attention = (
            not possession_confirmed
            or issue_reported
        )

        new_location = (
            current_location
            or old_location
        )

        connection.execute(
            """
            UPDATE assets
            SET
                condition = ?,
                operational_location = ?,
                verified_on = CURRENT_TIMESTAMP,
                verified_by = ?,
                attention_required = CASE
                    WHEN ? = 1 THEN 1
                    ELSE attention_required
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
              AND assigned_user_account_id = ?
            """,
            (
                condition,
                new_location,
                user["full_name"],
                1 if needs_attention else 0,
                corporate_asset_id,
                int(user_id),
            ),
        )

        if old_condition != condition:
            connection.execute(
                """
                INSERT INTO asset_history (
                    corporate_asset_id,
                    event_type,
                    field_name,
                    old_value,
                    new_value,
                    performed_by,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    corporate_asset_id,
                    "Employee Field Confirmed",
                    "condition",
                    old_condition,
                    condition,
                    user["full_name"],
                    notes,
                ),
            )

        if old_location != new_location:
            connection.execute(
                """
                INSERT INTO asset_history (
                    corporate_asset_id,
                    event_type,
                    field_name,
                    old_value,
                    new_value,
                    performed_by,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    corporate_asset_id,
                    "Employee Field Confirmed",
                    "operational_location",
                    old_location,
                    new_location,
                    user["full_name"],
                    notes,
                ),
            )

        verification_notes = (
            f"Possession confirmed: "
            f"{'Yes' if possession_confirmed else 'No'}; "
            f"Issue reported: "
            f"{'Yes' if issue_reported else 'No'}; "
            f"Condition: {condition}; "
            f"Location: {new_location or 'Not supplied'}"
        )

        if notes:
            verification_notes += f"; Employee notes: {notes}"

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Employee Verification",
                "employee_confirmation",
                "",
                (
                    "Confirmed"
                    if possession_confirmed
                    else "Not in possession"
                ),
                user["full_name"],
                verification_notes,
            ),
        )

        if needs_attention:
            connection.execute(
                """
                INSERT INTO asset_history (
                    corporate_asset_id,
                    event_type,
                    field_name,
                    old_value,
                    new_value,
                    performed_by,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    corporate_asset_id,
                    "Attention Required",
                    "attention_required",
                    clean_text(current["attention_required"]),
                    "1",
                    user["full_name"],
                    verification_notes,
                ),
            )

    return {
        "asset_id": corporate_asset_id,
        "verified_by": user["full_name"],
        "attention_required": needs_attention,
    }



# ============================================================
# ASSET FINANCIAL PROFILE
# ============================================================

def update_asset_useful_life(
    corporate_asset_id,
    useful_life_years,
    performed_by,
    notes="",
):
    """
    Set an asset-specific useful-life override.

    Age, accumulated depreciation and book value remain calculated
    dynamically from purchase date and purchase cost.
    """

    initialize_database()

    corporate_asset_id = clean_text(
        corporate_asset_id
    )

    performed_by = clean_text(
        performed_by
    )

    notes = clean_text(
        notes
    )

    if not corporate_asset_id:
        raise ValueError(
            "Asset ID is required."
        )

    if not performed_by:
        raise ValueError(
            "Performed By is required."
        )

    try:
        useful_life = float(
            useful_life_years
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Useful Life must be a number greater than zero."
        ) from error

    if useful_life <= 0:
        raise ValueError(
            "Useful Life must be greater than zero."
        )

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT
                corporate_asset_id,
                useful_life_years
            FROM assets
            WHERE corporate_asset_id = ?
            """,
            (
                corporate_asset_id,
            ),
        ).fetchone()

        if current is None:
            raise ValueError(
                "Asset could not be found."
            )

        old_value = clean_text(
            current[
                "useful_life_years"
            ]
        )

        connection.execute(
            """
            UPDATE assets
            SET
                useful_life_years = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE corporate_asset_id = ?
            """,
            (
                useful_life,
                corporate_asset_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO asset_history (
                corporate_asset_id,
                event_type,
                field_name,
                old_value,
                new_value,
                performed_by,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporate_asset_id,
                "Financial Profile Updated",
                "useful_life_years",
                (
                    old_value
                    or str(
                        DEFAULT_USEFUL_LIFE_YEARS
                    )
                ),
                str(
                    useful_life
                ),
                performed_by,
                notes,
            ),
        )

    return get_asset_record(
        corporate_asset_id
    )


# ============================================================
# MANUAL ASSET CREATION
# ============================================================

def generate_local_asset_id():
    """Generate a unique ID for an asset created in this IT system."""

    return (
        "IT-LOCAL-"
        + datetime.now().strftime("%Y%m%d")
        + "-"
        + uuid4().hex[:6].upper()
    )


def create_manual_asset(asset_data, performed_by):
    """Create a new locally managed IT asset and audit the creation."""

    initialize_database()

    performed_by = clean_text(performed_by)

    if not performed_by:
        raise ValueError("Performed By is required.")

    asset_id = clean_text(
        asset_data.get("asset_id")
    )

    if not asset_id:
        asset_id = generate_local_asset_id()

    asset_type = clean_text(
        asset_data.get("asset_type")
    )

    if not asset_type:
        raise ValueError("Asset Type is required.")

    assigned_user_account_id = asset_data.get(
        "assigned_user_account_id"
    )

    linked_user = None

    if assigned_user_account_id not in (None, ""):
        try:
            assigned_user_account_id = int(
                assigned_user_account_id
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "The selected employee account is invalid."
            ) from error

        linked_user = get_user(
            assigned_user_account_id
        )

        if linked_user is None:
            raise ValueError(
                "The selected employee account could not be found."
            )

        if not int(linked_user["active"]):
            raise ValueError(
                "The selected employee account is inactive."
            )

    columns = [
        "corporate_asset_id",
        "asset_type",
        "category",
        "make",
        "model",
        "serial_number",
        "department_asset_tag",
        "facility_site",
        "district",
        "section_department",
        "room_location",
        "operational_facility",
        "operational_department",
        "operational_location",
        "specification_os",
        "purchase_date",
        "purchase_cost_r",
        "supplier",
        "warranty_expiry",
        "age_yrs",
        "useful_life_years",
        "assigned_user",
        "assigned_user_account_id",
        "condition",
        "status",
        "warranty_status",
        "recommendation",
        "notes",
        "source_file",
        "source_system",
    ]

    values_by_column = {
        "corporate_asset_id": asset_id,
        "asset_type": clean_text(asset_data.get("asset_type")),
        "category": clean_text(asset_data.get("category")),
        "make": clean_text(asset_data.get("make")),
        "model": clean_text(asset_data.get("model")),
        "serial_number": clean_text(asset_data.get("serial_number")),
        "department_asset_tag": clean_text(asset_data.get("department_asset_tag")),
        "facility_site": clean_text(asset_data.get("facility_site")),
        "district": clean_text(asset_data.get("district")),
        "section_department": clean_text(asset_data.get("section_department")),
        "room_location": clean_text(asset_data.get("room_location")),
        "operational_facility": clean_text(
            asset_data.get("operational_facility")
            or asset_data.get("facility_site")
        ),
        "operational_department": clean_text(
            asset_data.get("operational_department")
            or asset_data.get("section_department")
        ),
        "operational_location": clean_text(
            asset_data.get("operational_location")
            or asset_data.get("room_location")
        ),
        "specification_os": clean_text(asset_data.get("specification_os")),
        "purchase_date": clean_text(asset_data.get("purchase_date")),
        "purchase_cost_r": clean_text(asset_data.get("purchase_cost_r")),
        "supplier": clean_text(asset_data.get("supplier")),
        "warranty_expiry": clean_text(asset_data.get("warranty_expiry")),
        "age_yrs": clean_text(asset_data.get("age_yrs")),
        "useful_life_years": _normalise_useful_life(
            asset_data.get(
                "useful_life_years"
            )
        ),
        "assigned_user": (
            linked_user["full_name"]
            if linked_user is not None
            else clean_text(asset_data.get("assigned_user"))
        ),
        "assigned_user_account_id": assigned_user_account_id,
        "condition": clean_text(asset_data.get("condition")) or "Good",
        "status": clean_text(asset_data.get("status")) or "In Use",
        "warranty_status": clean_text(asset_data.get("warranty_status")),
        "recommendation": clean_text(asset_data.get("recommendation")),
        "notes": clean_text(asset_data.get("notes")),
        "source_file": "Manual Entry",
        "source_system": "IT Asset Management System",
    }

    placeholders = ", ".join(
        ["?"] * len(columns)
    )

    try:
        with get_connection() as connection:
            connection.execute(
                f"""
                INSERT INTO assets (
                    {", ".join(columns)}
                )
                VALUES ({placeholders})
                """,
                [
                    values_by_column[column]
                    for column in columns
                ],
            )

            connection.execute(
                """
                INSERT INTO asset_history (
                    corporate_asset_id,
                    event_type,
                    performed_by,
                    notes
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    asset_id,
                    "Asset Created",
                    performed_by,
                    (
                        "Asset manually created in the "
                        "IT Asset Management System."
                    ),
                ),
            )

    except sqlite3.IntegrityError as error:
        raise ValueError(
            f"Asset ID '{asset_id}' already exists."
        ) from error

    return asset_id


initialize_user_security()
