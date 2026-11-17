from pathlib import Path

import pandas as pd

from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import BarChart, Reference

from database import (
    initialize_database,
    load_assets_from_db,
    preview_sync_assets,
    sync_assets,
    calculate_portfolio_financials,
    calculate_warranty_summary,
)


# ============================================================
# GLOBAL VARIABLES AND FOLDERS
# ============================================================

assets = []

BASE_FOLDER = Path(__file__).resolve().parent
INPUT_FOLDER = BASE_FOLDER / "input"
OUTPUT_FOLDER = BASE_FOLDER / "output"


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_value(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def _escape_excel_text(value):
    """Preserve user-entered text as text in exported spreadsheets."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _safe_excel_frame(frame):
    """Copy a DataFrame and neutralise formula-like string cells."""
    safe_frame = frame.copy()
    for column in safe_frame.select_dtypes(include=["object", "string"]).columns:
        safe_frame[column] = safe_frame[column].map(_escape_excel_text)
    return safe_frame


def refresh_assets_from_database():
    initialize_database()

    database_assets = load_assets_from_db()

    assets.clear()
    assets.extend(database_assets)

    return assets


refresh_assets_from_database()


# ============================================================
# IT ASSET CLASSIFICATION
# ============================================================

IT_ASSET_KEYWORDS = {
    "desktop",
    "laptop",
    "computer",
    "workstation",
    "thin client",
    "monitor",
    "screen",
    "printer",
    "scanner",
    "server",
    "router",
    "switch",
    "network",
    "access point",
    "firewall",
    "wifi",
    "tablet",
    "smartphone",
    "mobile phone",
    "ups",
    "projector",
    "docking station",
    "dock",
}


def is_it_asset(asset):
    asset_type = clean_value(
        asset.get("asset_type")
    ).lower()

    category = clean_value(
        asset.get("category")
    ).lower()

    combined_text = (
        asset_type
        + " "
        + category
    )

    return any(
        keyword in combined_text
        for keyword in IT_ASSET_KEYWORDS
    )


# ============================================================
# READ CORPORATE FILES
# ============================================================

def read_corporate_asset_files():
    INPUT_FOLDER.mkdir(exist_ok=True)

    files = [
        file
        for file in INPUT_FOLDER.iterdir()
        if file.suffix.lower() in {".csv", ".xlsx"}
    ]

    if not files:
        return []

    imported_records = []

    for file in files:
        try:
            if file.suffix.lower() == ".csv":
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            df.columns = (
                df.columns
                .astype(str)
                .str.strip()
                .str.lower()
                .str.replace(
                    r"[^a-z0-9]+",
                    "_",
                    regex=True,
                )
                .str.strip("_")
            )

            df["source_file"] = file.name

            imported_records.extend(
                df.to_dict("records")
            )

        except Exception as error:
            print(
                f"Unable to read {file.name}: {error}"
            )

    return imported_records


# ============================================================
# SYNCHRONISATION
# ============================================================

def prepare_sync_review():
    corporate_records = read_corporate_asset_files()

    if not corporate_records:
        return None

    it_assets = [
        asset
        for asset in corporate_records
        if is_it_asset(asset)
    ]

    if not it_assets:
        return {
            "corporate_count": len(corporate_records),
            "it_assets": [],
            "preview": None,
        }

    preview = preview_sync_assets(it_assets)

    return {
        "corporate_count": len(corporate_records),
        "it_assets": it_assets,
        "preview": preview,
    }


def apply_prepared_sync(it_assets):
    result = sync_assets(
        it_assets,
        source_system="Corporate Asset System",
    )

    refresh_assets_from_database()

    return result


# ============================================================
# DUPLICATES
# ============================================================

def get_duplicate_records(data=None):
    if data is None:
        data = assets

    duplicate_records = []
    duplicate_messages = []

    fields = {
        "asset_id": "Asset ID",
        "serial_number": "Serial Number",
        "department_asset_tag": "Department Asset Tag",
    }

    for field, display_name in fields.items():
        groups = {}

        for asset in data:
            value = clean_value(
                asset.get(field)
            )

            if not value:
                continue

            key = value.lower()

            groups.setdefault(
                key,
                {
                    "value": value,
                    "records": [],
                },
            )

            groups[key]["records"].append(
                asset
            )

        for information in groups.values():
            count = len(
                information["records"]
            )

            if count > 1:
                duplicate_messages.append(
                    (
                        f"{display_name}: "
                        f"{information['value']} "
                        f"({count} occurrences)"
                    )
                )

                duplicate_records.extend(
                    information["records"]
                )

    return duplicate_records, duplicate_messages


# ============================================================
# REPORT HELPERS
# ============================================================

def create_duplicate_report(df):
    duplicate_frames = []

    fields_to_check = {
        "asset_id": "Asset ID",
        "serial_number": "Serial Number",
        "department_asset_tag": "Department Asset Tag",
    }

    for field, display_name in fields_to_check.items():
        if field not in df.columns:
            continue

        values = (
            df[field]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        valid_values = values != ""
        normalised_values = values.str.lower()

        counts = (
            normalised_values[
                valid_values
            ]
            .value_counts()
        )

        duplicate_values = counts[
            counts > 1
        ].index

        if len(duplicate_values) > 0:
            duplicate_rows = df[
                valid_values
                & normalised_values.isin(
                    duplicate_values
                )
            ].copy()

            duplicate_rows.insert(
                0,
                "duplicate_field",
                display_name,
            )

            duplicate_rows.insert(
                1,
                "duplicate_value",
                duplicate_rows[field],
            )

            duplicate_frames.append(
                duplicate_rows
            )

    if duplicate_frames:
        return pd.concat(
            duplicate_frames,
            ignore_index=True,
        )

    return pd.DataFrame(
        columns=[
            "duplicate_field",
            "duplicate_value",
        ]
    )


def create_data_quality_report(df):
    issues = []

    required_fields = {
        "asset_id": "Asset ID",
        "asset_type": "Asset Type",
        "serial_number": "Serial Number",
        "facility_site": "Facility / Site",
    }

    for _, row in df.iterrows():
        missing_fields = []

        for field, display_name in required_fields.items():
            if field not in df.columns:
                missing_fields.append(display_name)
                continue

            value = row.get(field)

            if clean_value(value) == "":
                missing_fields.append(display_name)

        if missing_fields:
            issue_record = row.to_dict()
            issue_record[
                "data_quality_issue"
            ] = (
                "Missing: "
                + ", ".join(missing_fields)
            )

            issues.append(issue_record)

    if issues:
        return pd.DataFrame(issues)

    return pd.DataFrame(
        columns=[
            "data_quality_issue"
        ]
    )


def format_worksheet(
    worksheet,
    table_name=None,
):
    worksheet.freeze_panes = "A2"

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    header_font = Font(
        color="FFFFFF",
        bold=True,
    )

    thin_border = Border(
        bottom=Side(
            style="thin",
            color="B7B7B7",
        )
    )

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )
        cell.border = thin_border

    worksheet.row_dimensions[
        1
    ].height = 25

    for column_cells in worksheet.columns:
        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:
            value = (
                ""
                if cell.value is None
                else str(cell.value)
            )

            max_length = max(
                max_length,
                len(value),
            )

        worksheet.column_dimensions[
            column_letter
        ].width = min(
            max_length + 3,
            45,
        )

    if (
        table_name
        and worksheet.max_row >= 2
        and worksheet.max_column >= 1
    ):
        table_reference = (
            f"A1:"
            f"{get_column_letter(worksheet.max_column)}"
            f"{worksheet.max_row}"
        )

        table = Table(
            displayName=table_name,
            ref=table_reference,
        )

        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )

        worksheet.add_table(table)


def create_dashboard(
    workbook,
    total_assets,
    duplicate_count,
    data_quality_count,
    facility_summary,
    asset_type_summary,
    portfolio_financials,
    warranty_summary,
):
    dashboard = workbook.create_sheet(
        "Dashboard",
        0,
    )

    dashboard["A1"] = (
        "IT ASSET MANAGEMENT DASHBOARD"
    )
    dashboard["A1"].font = Font(
        size=18,
        bold=True,
        color="FFFFFF",
    )
    dashboard["A1"].fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )
    dashboard["A1"].alignment = Alignment(
        horizontal="center"
    )
    dashboard.merge_cells(
        "A1:E1"
    )

    metrics = [
        ("Total Assets", total_assets),
        ("Duplicate Records", duplicate_count),
        ("Data Quality Issues", data_quality_count),
        (
            "Facilities",
            (
                len(facility_summary)
                if "asset_count"
                in facility_summary.columns
                else 0
            ),
        ),
        (
            "Asset Types",
            (
                len(asset_type_summary)
                if "asset_count"
                in asset_type_summary.columns
                else 0
            ),
        ),
        (
            "Total Purchase Cost",
            portfolio_financials[
                "total_original_cost_r"
            ],
        ),
        (
            "Accumulated Depreciation",
            portfolio_financials[
                "total_accumulated_depreciation_r"
            ],
        ),
        (
            "Current Asset Value",
            portfolio_financials[
                "total_current_book_value_r"
            ],
        ),
        (
            "Assets Excluded from Valuation",
            portfolio_financials[
                "assets_excluded_from_book_value"
            ],
        ),
        (
            "In Warranty",
            warranty_summary[
                "in_warranty"
            ],
        ),
        (
            "Out of Warranty",
            warranty_summary[
                "out_of_warranty"
            ],
        ),
        (
            "Warranty Date Missing",
            warranty_summary[
                "warranty_date_missing"
            ],
        ),
    ]

    dashboard["A3"] = "Metric"
    dashboard["B3"] = "Value"

    for cell_address in ("A3", "B3"):
        dashboard[
            cell_address
        ].font = Font(
            bold=True,
            color="FFFFFF",
        )
        dashboard[
            cell_address
        ].fill = PatternFill(
            fill_type="solid",
            fgColor="5B9BD5",
        )

    for row_number, (
        label,
        value,
    ) in enumerate(
        metrics,
        start=4,
    ):
        dashboard[
            f"A{row_number}"
        ] = label
        dashboard[
            f"B{row_number}"
        ] = value
        dashboard[
            f"A{row_number}"
        ].font = Font(
            bold=True
        )

        if label in {
            "Total Purchase Cost",
            "Accumulated Depreciation",
            "Current Asset Value",
        }:
            dashboard[
                f"B{row_number}"
            ].number_format = (
                'R #,##0.00'
            )

    dashboard.column_dimensions[
        "A"
    ].width = 28
    dashboard.column_dimensions[
        "B"
    ].width = 18

    if (
        "facility_site"
        in facility_summary.columns
        and "asset_count"
        in facility_summary.columns
    ):
        dashboard["D3"] = "Facility"
        dashboard["E3"] = "Assets"

        chart_data = (
            facility_summary
            .head(10)
            .reset_index(
                drop=True
            )
        )

        start_row = 4

        for index, row in chart_data.iterrows():
            dashboard.cell(
                row=start_row + index,
                column=4,
                value=_escape_excel_text(row["facility_site"]),
            )
            dashboard.cell(
                row=start_row + index,
                column=5,
                value=row["asset_count"],
            )

        if not chart_data.empty:
            chart = BarChart()
            chart.title = "Assets by Facility"
            chart.y_axis.title = "Number of Assets"
            chart.x_axis.title = "Facility"
            chart.height = 8
            chart.width = 14

            data = Reference(
                dashboard,
                min_col=5,
                min_row=3,
                max_row=(
                    start_row
                    + len(chart_data)
                    - 1
                ),
            )

            categories = Reference(
                dashboard,
                min_col=4,
                min_row=4,
                max_row=(
                    start_row
                    + len(chart_data)
                    - 1
                ),
            )

            chart.add_data(
                data,
                titles_from_data=True,
            )
            chart.set_categories(categories)

            dashboard.add_chart(
                chart,
                "A16",
            )


# ============================================================
# EXPORT REPORT
# ============================================================

def export_report():
    if not assets:
        raise ValueError(
            "No assets are loaded."
        )

    OUTPUT_FOLDER.mkdir(exist_ok=True)

    df = pd.DataFrame(assets)

    portfolio_financials = (
        calculate_portfolio_financials(
            assets
        )
    )

    warranty_summary = (
        calculate_warranty_summary(
            assets
        )
    )

    warranty_columns = [
        "asset_id",
        "asset_type",
        "make",
        "model",
        "serial_number",
        "facility_site",
        "assigned_user",
        "warranty_expiry",
        "warranty_status",
        "warranty_days_remaining",
        "warranty_detail",
    ]

    warranty_export_df = (
        df.reindex(
            columns=warranty_columns
        )
        .rename(
            columns={
                "asset_id": "Asset ID",
                "asset_type": "Asset Type",
                "make": "Make",
                "model": "Model",
                "serial_number": "Serial Number",
                "facility_site": "Facility / Site",
                "assigned_user": "Assigned User",
                "warranty_expiry": "Warranty Expiry",
                "warranty_status": "Warranty Status",
                "warranty_days_remaining": "Days Remaining",
                "warranty_detail": "Warranty Detail",
            }
        )
    )

    depreciation_columns = [
        "asset_id",
        "asset_type",
        "make",
        "model",
        "serial_number",
        "facility_site",
        "purchase_date",
        "purchase_cost_numeric_r",
        "useful_life_years",
        "calculated_age_years",
        "remaining_life_years",
        "depreciation_method",
        "annual_depreciation_r",
        "monthly_depreciation_r",
        "accumulated_depreciation_r",
        "current_book_value_r",
        "end_of_useful_life",
        "fully_depreciated",
        "financial_calculation_status",
    ]

    depreciation_export_df = (
        df.reindex(
            columns=depreciation_columns
        )
        .rename(
            columns={
                "asset_id": "Asset ID",
                "asset_type": "Asset Type",
                "make": "Make",
                "model": "Model",
                "serial_number": "Serial Number",
                "facility_site": "Facility / Site",
                "purchase_date": "Purchase Date",
                "purchase_cost_numeric_r": "Purchase Cost (R)",
                "useful_life_years": "Useful Life (Years)",
                "calculated_age_years": "Calculated Age (Years)",
                "remaining_life_years": "Remaining Life (Years)",
                "depreciation_method": "Depreciation Method",
                "annual_depreciation_r": "Annual Depreciation (R)",
                "monthly_depreciation_r": "Monthly Depreciation (R)",
                "accumulated_depreciation_r": "Accumulated Depreciation (R)",
                "current_book_value_r": "Current Book Value (R)",
                "end_of_useful_life": "End of Useful Life",
                "fully_depreciated": "Fully Depreciated",
                "financial_calculation_status": "Calculation Status",
            }
        )
    )

    duplicates_df = create_duplicate_report(
        df
    )

    data_quality_df = create_data_quality_report(
        df
    )

    if data_quality_df.empty:
        data_quality_export_df = pd.DataFrame(
            {
                "data_quality_issue": [
                    (
                        "No data quality "
                        "issues detected."
                    )
                ]
            }
        )
    else:
        data_quality_export_df = data_quality_df

    if "facility_site" in df.columns:
        facility_data = df.copy()

        facility_data[
            "facility_site"
        ] = (
            facility_data[
                "facility_site"
            ]
            .fillna(
                "Not specified"
            )
            .astype(str)
            .str.strip()
        )

        facility_data.loc[
            facility_data[
                "facility_site"
            ] == "",
            "facility_site",
        ] = "Not specified"

        facility_summary = (
            facility_data
            .groupby("facility_site")
            .size()
            .reset_index(
                name="asset_count"
            )
            .sort_values(
                by="asset_count",
                ascending=False,
            )
        )
    else:
        facility_summary = pd.DataFrame(
            {
                "message": [
                    "Facility column not found."
                ]
            }
        )

    if "asset_type" in df.columns:
        type_data = df.copy()

        type_data[
            "asset_type"
        ] = (
            type_data[
                "asset_type"
            ]
            .fillna(
                "Not specified"
            )
            .astype(str)
            .str.strip()
        )

        type_data.loc[
            type_data[
                "asset_type"
            ] == "",
            "asset_type",
        ] = "Not specified"

        asset_type_summary = (
            type_data
            .groupby("asset_type")
            .size()
            .reset_index(
                name="asset_count"
            )
            .sort_values(
                by="asset_count",
                ascending=False,
            )
        )
    else:
        asset_type_summary = pd.DataFrame(
            {
                "message": [
                    "Asset Type column not found."
                ]
            }
        )

    output_file = (
        OUTPUT_FOLDER
        / "IT_Asset_Audit_Report.xlsx"
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl",
    ) as writer:
        _safe_excel_frame(df).to_excel(
            writer,
            sheet_name="Master Asset Register",
            index=False,
        )
        _safe_excel_frame(duplicates_df).to_excel(
            writer,
            sheet_name="Duplicates",
            index=False,
        )
        _safe_excel_frame(facility_summary).to_excel(
            writer,
            sheet_name="Summary by Facility",
            index=False,
        )
        _safe_excel_frame(asset_type_summary).to_excel(
            writer,
            sheet_name="Summary by Asset Type",
            index=False,
        )
        _safe_excel_frame(data_quality_export_df).to_excel(
            writer,
            sheet_name="Data Quality Issues",
            index=False,
        )
        _safe_excel_frame(depreciation_export_df).to_excel(
            writer,
            sheet_name="Depreciation Summary",
            index=False,
        )
        _safe_excel_frame(warranty_export_df).to_excel(
            writer,
            sheet_name="Warranty Summary",
            index=False,
        )

        workbook = writer.book

        format_worksheet(
            workbook[
                "Master Asset Register"
            ],
            "MasterAssetTable",
        )
        format_worksheet(
            workbook["Duplicates"],
            "DuplicateAssetTable",
        )
        format_worksheet(
            workbook[
                "Summary by Facility"
            ],
            "FacilitySummaryTable",
        )
        format_worksheet(
            workbook[
                "Summary by Asset Type"
            ],
            "AssetTypeSummaryTable",
        )
        format_worksheet(
            workbook[
                "Data Quality Issues"
            ],
            "DataQualityTable",
        )
        format_worksheet(
            workbook[
                "Depreciation Summary"
            ],
            "DepreciationSummaryTable",
        )
        format_worksheet(
            workbook[
                "Warranty Summary"
            ],
            "WarrantySummaryTable",
        )

        depreciation_sheet = workbook[
            "Depreciation Summary"
        ]

        depreciation_headers = {
            cell.value: cell.column
            for cell in depreciation_sheet[1]
        }

        for header_name in (
            "Purchase Cost (R)",
            "Annual Depreciation (R)",
            "Monthly Depreciation (R)",
            "Accumulated Depreciation (R)",
            "Current Book Value (R)",
        ):
            column_number = (
                depreciation_headers.get(
                    header_name
                )
            )

            if not column_number:
                continue

            for row_number in range(
                2,
                depreciation_sheet.max_row + 1,
            ):
                depreciation_sheet.cell(
                    row=row_number,
                    column=column_number,
                ).number_format = (
                    'R #,##0.00'
                )

        create_dashboard(
            workbook=workbook,
            total_assets=len(df),
            duplicate_count=len(
                duplicates_df
            ),
            data_quality_count=len(
                data_quality_df
            ),
            facility_summary=(
                facility_summary
            ),
            asset_type_summary=(
                asset_type_summary
            ),
            portfolio_financials=(
                portfolio_financials
            ),
            warranty_summary=(
                warranty_summary
            ),
        )

    return output_file


# ============================================================
# TKINTER APPLICATION ENTRY POINT
# ============================================================

def main():
    """Launch the graphical application, including its login window.

    All interactive operations are performed through gui.py. There is no
    unauthenticated console menu in this portfolio edition.
    """
    import sys

    # Running this file directly loads it as __main__. Register the same
    # module under its import name so gui.py can import the existing asset
    # functions without executing this module a second time.
    sys.modules.setdefault("Real_Test", sys.modules[__name__])

    # gui.py creates the Tkinter window and starts its event loop.
    import gui  # noqa: F401


if __name__ == "__main__":
    main()
