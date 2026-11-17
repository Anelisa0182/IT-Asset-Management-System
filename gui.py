# -*- coding: utf-8 -*-
import calendar
from datetime import date, datetime

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from Real_Test import (
    assets,
    clean_value,
    export_report,
    get_duplicate_records,
    prepare_sync_review,
    apply_prepared_sync,
    refresh_assets_from_database,
)

from database import (
    verify_asset,
    get_asset_history,
    get_asset_record,
    get_asset_transactions,
    assign_asset,
    transfer_asset,
    send_asset_for_repair,
    return_asset_from_repair,
    count_users,
    create_user,
    authenticate_user,
    list_users,
    set_user_active,
    reset_user_password,
    create_manual_asset,
    get_user,
    list_assignable_users,
    get_assets_for_user,
    link_asset_to_user,
    unlink_asset_from_user,
    auto_link_existing_assignments,
    verify_employee_asset,
    update_asset_useful_life,
    calculate_asset_financials,
    calculate_portfolio_financials,
    calculate_warranty_info,
    calculate_warranty_summary,
    format_currency_r,
    DEFAULT_USEFUL_LIFE_YEARS,
    USER_ROLES,
)


# ============================================================
# MODERN COLOUR PALETTE
# ============================================================

APP_BG = "#F3F6F9"
CARD_BG = "#FFFFFF"
SIDEBAR_BG = "#123B5D"
SIDEBAR_HOVER = "#1B4F78"
ACCENT = "#1F6AA5"
ACCENT_DARK = "#15507F"
TEXT = "#1F2937"
MUTED = "#6B7280"
BORDER = "#D7DEE7"
SUCCESS = "#2E7D32"
WARNING = "#C77700"
DANGER = "#B3261E"
LIGHT_BLUE = "#EAF3FA"
LIGHT_GREEN = "#ECF7EE"
LIGHT_ORANGE = "#FFF5E5"
LIGHT_RED = "#FCECEC"


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.title("IT Asset Management System")
root.configure(bg=APP_BG)
root.withdraw()


def set_window_size(
    window,
    desired_width,
    desired_height,
    minimum_width=420,
    minimum_height=320,
):
    """
    Size and centre a window so that it fits comfortably
    on smaller laptop screens as well as larger monitors.
    """

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    maximum_width = int(
        screen_width * 0.91
    )

    maximum_height = int(
        screen_height * 0.84
    )

    actual_width = min(
        desired_width,
        maximum_width,
    )

    actual_height = min(
        desired_height,
        maximum_height,
    )

    actual_width = max(
        min(
            minimum_width,
            maximum_width,
        ),
        actual_width,
    )

    actual_height = max(
        min(
            minimum_height,
            maximum_height,
        ),
        actual_height,
    )

    x_position = max(
        0,
        (
            screen_width
            - actual_width
        )
        // 2,
    )

    y_position = max(
        0,
        (
            screen_height
            - actual_height
        )
        // 2,
    )

    window.geometry(
        (
            f"{actual_width}x{actual_height}"
            f"+{x_position}+{y_position}"
        )
    )

    window.minsize(
        min(
            minimum_width,
            actual_width,
        ),
        min(
            minimum_height,
            actual_height,
        ),
    )


set_window_size(
    root,
    1240,
    700,
    1000,
    600,
)


# ============================================================
# STYLE
# ============================================================

style = ttk.Style()

try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure(
    "Treeview",
    background=CARD_BG,
    fieldbackground=CARD_BG,
    foreground=TEXT,
    rowheight=28,
    borderwidth=0,
    font=("Segoe UI", 9),
)

style.configure(
    "Treeview.Heading",
    background=SIDEBAR_BG,
    foreground="white",
    relief="flat",
    borderwidth=0,
    font=("Segoe UI", 9, "bold"),
    padding=8,
)

style.map(
    "Treeview.Heading",
    background=[("active", ACCENT_DARK)],
)

style.map(
    "Treeview",
    background=[("selected", "#D8EAF7")],
    foreground=[("selected", TEXT)],
)

style.configure(
    "TNotebook",
    background=APP_BG,
    borderwidth=0,
)

style.configure(
    "TNotebook.Tab",
    font=("Segoe UI", 9, "bold"),
    padding=(14, 8),
)

style.map(
    "TNotebook.Tab",
    background=[
        ("selected", ACCENT),
        ("!selected", "#E7EDF3"),
    ],
    foreground=[
        ("selected", "white"),
        ("!selected", TEXT),
    ],
)

style.configure("TEntry", padding=6)
style.configure("TCombobox", padding=6)


# ============================================================
# ZOOM / DISPLAY SCALING
# ============================================================

BASE_TK_SCALING = float(
    root.tk.call(
        "tk",
        "scaling",
    )
)

DEFAULT_ZOOM_LEVEL = 0.90
MIN_ZOOM_LEVEL = 0.70
MAX_ZOOM_LEVEL = 1.30

zoom_level = tk.DoubleVar(
    value=DEFAULT_ZOOM_LEVEL
)

zoom_display = tk.StringVar(
    value="90%"
)

NAV_BUTTONS = []


def apply_zoom(
    new_level,
):
    """
    Scale the application fonts and compact key controls.

    The allowed range is 70% to 130%.
    """

    new_level = max(
        MIN_ZOOM_LEVEL,
        min(
            MAX_ZOOM_LEVEL,
            round(
                float(
                    new_level
                ),
                2,
            ),
        ),
    )

    zoom_level.set(
        new_level
    )

    zoom_display.set(
        f"{int(new_level * 100)}%"
    )

    root.tk.call(
        "tk",
        "scaling",
        BASE_TK_SCALING
        * new_level,
    )

    style.configure(
        "Treeview",
        rowheight=max(
            20,
            int(
                28
                * new_level
            ),
        ),
    )

    style.configure(
        "Treeview.Heading",
        padding=max(
            5,
            int(
                8
                * new_level
            ),
        ),
    )

    style.configure(
        "TNotebook.Tab",
        padding=(
            max(
                9,
                int(
                    14
                    * new_level
                ),
            ),
            max(
                5,
                int(
                    8
                    * new_level
                ),
            ),
        ),
    )

    style.configure(
        "TEntry",
        padding=max(
            4,
            int(
                6
                * new_level
            ),
        ),
    )

    style.configure(
        "TCombobox",
        padding=max(
            4,
            int(
                6
                * new_level
            ),
        ),
    )

    for button in NAV_BUTTONS:
        try:
            button.configure(
                pady=max(
                    4,
                    int(
                        7
                        * new_level
                    ),
                ),
                padx=max(
                    10,
                    int(
                        14
                        * new_level
                    ),
                ),
            )
        except tk.TclError:
            pass

    root.update_idletasks()


def zoom_out():
    apply_zoom(
        zoom_level.get()
        - 0.10
    )


def zoom_in():
    apply_zoom(
        zoom_level.get()
        + 0.10
    )


def zoom_reset():
    apply_zoom(
        1.00
    )


def zoom_fit():
    screen_height = (
        root.winfo_screenheight()
    )

    if screen_height <= 768:
        target = 0.75
    elif screen_height <= 900:
        target = 0.85
    else:
        target = 0.90

    apply_zoom(
        target
    )


apply_zoom(
    DEFAULT_ZOOM_LEVEL
)



# ============================================================
# DATE PICKER
# ============================================================

def _parse_date_for_picker(value):
    """
    Convert an existing date string into a date object.

    Selected dates are stored in ISO format: YYYY-MM-DD.
    """

    text = clean_value(value)

    if not text:
        return date.today()

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
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

    try:
        return datetime.fromisoformat(
            text
        ).date()
    except ValueError:
        return date.today()


def open_date_picker(
    parent,
    variable,
    title="Select Date",
    maximum_date=None,
    minimum_date=None,
):
    """
    Open a calendar and write the selected date to variable.

    maximum_date and minimum_date are optional date objects.
    """

    selected_date = _parse_date_for_picker(
        variable.get()
    )

    current_year = tk.IntVar(
        value=selected_date.year
    )

    current_month = tk.IntVar(
        value=selected_date.month
    )

    picker = tk.Toplevel(parent)
    picker.title(title)
    picker.configure(bg=CARD_BG)
    picker.transient(parent)
    picker.grab_set()

    set_window_size(
        picker,
        390,
        440,
        360,
        410,
    )

    header = tk.Frame(
        picker,
        bg=SIDEBAR_BG,
        height=78,
    )
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text=title,
        bg=SIDEBAR_BG,
        fg="white",
        font=("Segoe UI", 15, "bold"),
    ).pack(
        anchor="w",
        padx=18,
        pady=(13, 0),
    )

    tk.Label(
        header,
        text="Dates are saved as YYYY-MM-DD",
        bg=SIDEBAR_BG,
        fg="#D8E7F3",
        font=("Segoe UI", 8),
    ).pack(
        anchor="w",
        padx=18,
        pady=(2, 0),
    )

    body = tk.Frame(
        picker,
        bg=CARD_BG,
    )
    body.pack(
        fill="both",
        expand=True,
        padx=14,
        pady=14,
    )

    month_bar = tk.Frame(
        body,
        bg=CARD_BG,
    )
    month_bar.pack(
        fill="x",
        pady=(0, 10),
    )

    calendar_frame = tk.Frame(
        body,
        bg=CARD_BG,
    )
    calendar_frame.pack(
        fill="both",
        expand=True,
    )

    month_title = tk.StringVar()

    def is_allowed(candidate):
        if (
            minimum_date is not None
            and candidate < minimum_date
        ):
            return False

        if (
            maximum_date is not None
            and candidate > maximum_date
        ):
            return False

        return True

    def choose_date(
        year,
        month,
        day_number,
    ):
        candidate = date(
            year,
            month,
            day_number,
        )

        if not is_allowed(candidate):
            return

        variable.set(
            candidate.isoformat()
        )
        picker.destroy()

    def rebuild_calendar():
        for child in calendar_frame.winfo_children():
            child.destroy()

        year = current_year.get()
        month = current_month.get()

        month_title.set(
            date(
                year,
                month,
                1,
            ).strftime("%B %Y")
        )

        weekday_names = (
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun",
        )

        for column, weekday in enumerate(
            weekday_names
        ):
            calendar_frame.columnconfigure(
                column,
                weight=1,
                uniform="calendar_day",
            )

            tk.Label(
                calendar_frame,
                text=weekday,
                bg=CARD_BG,
                fg=MUTED,
                font=("Segoe UI", 8, "bold"),
            ).grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=2,
                pady=(0, 5),
            )

        weeks = calendar.Calendar(
            firstweekday=0
        ).monthdayscalendar(
            year,
            month,
        )

        today_value = date.today()
        selected_value = _parse_date_for_picker(
            variable.get()
        )
        has_selected_value = bool(
            clean_value(
                variable.get()
            )
        )

        for row_index, week in enumerate(
            weeks,
            start=1,
        ):
            calendar_frame.rowconfigure(
                row_index,
                weight=1,
            )

            for column, day_number in enumerate(
                week
            ):
                if day_number == 0:
                    tk.Label(
                        calendar_frame,
                        text="",
                        bg=CARD_BG,
                    ).grid(
                        row=row_index,
                        column=column,
                        sticky="nsew",
                        padx=2,
                        pady=2,
                    )
                    continue

                candidate = date(
                    year,
                    month,
                    day_number,
                )

                allowed = is_allowed(
                    candidate
                )

                if (
                    has_selected_value
                    and candidate == selected_value
                ):
                    button_bg = ACCENT
                    button_fg = "white"
                elif candidate == today_value:
                    button_bg = LIGHT_BLUE
                    button_fg = ACCENT_DARK
                else:
                    button_bg = "#F7F9FB"
                    button_fg = TEXT

                day_button = tk.Button(
                    calendar_frame,
                    text=str(day_number),
                    command=(
                        lambda
                        selected_day=day_number,
                        selected_year=year,
                        selected_month=month:
                        choose_date(
                            selected_year,
                            selected_month,
                            selected_day,
                        )
                    ),
                    bg=button_bg,
                    fg=button_fg,
                    activebackground=ACCENT,
                    activeforeground="white",
                    disabledforeground="#A8B0B8",
                    relief="flat",
                    bd=0,
                    cursor=(
                        "hand2"
                        if allowed
                        else "arrow"
                    ),
                    font=(
                        "Segoe UI",
                        9,
                        "bold"
                        if candidate == today_value
                        else "normal",
                    ),
                    state=(
                        "normal"
                        if allowed
                        else "disabled"
                    ),
                )

                day_button.grid(
                    row=row_index,
                    column=column,
                    sticky="nsew",
                    padx=2,
                    pady=2,
                    ipady=4,
                )

    def previous_month():
        month = current_month.get() - 1
        year = current_year.get()

        if month < 1:
            month = 12
            year -= 1

        current_month.set(month)
        current_year.set(year)
        rebuild_calendar()

    def next_month():
        month = current_month.get() + 1
        year = current_year.get()

        if month > 12:
            month = 1
            year += 1

        current_month.set(month)
        current_year.set(year)
        rebuild_calendar()

    tk.Button(
        month_bar,
        text="<",
        command=previous_month,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 11, "bold"),
        width=4,
        pady=5,
    ).pack(side="left")

    tk.Label(
        month_bar,
        textvariable=month_title,
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 12, "bold"),
    ).pack(
        side="left",
        fill="x",
        expand=True,
    )

    tk.Button(
        month_bar,
        text=">",
        command=next_month,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 11, "bold"),
        width=4,
        pady=5,
    ).pack(side="right")

    footer = tk.Frame(
        body,
        bg=CARD_BG,
    )
    footer.pack(
        fill="x",
        pady=(10, 0),
    )

    def choose_today():
        today_value = date.today()

        if not is_allowed(today_value):
            return

        variable.set(
            today_value.isoformat()
        )
        picker.destroy()

    def clear_date():
        variable.set("")
        picker.destroy()

    tk.Button(
        footer,
        text="Clear",
        command=clear_date,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 8, "bold"),
        padx=12,
        pady=6,
    ).pack(side="left")

    tk.Button(
        footer,
        text="Today",
        command=choose_today,
        bg=LIGHT_BLUE,
        fg=ACCENT_DARK,
        activebackground="#D5E8F7",
        activeforeground=ACCENT_DARK,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 8, "bold"),
        padx=12,
        pady=6,
    ).pack(
        side="right",
        padx=(6, 0),
    )

    tk.Button(
        footer,
        text="Cancel",
        command=picker.destroy,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 8, "bold"),
        padx=12,
        pady=6,
    ).pack(side="right")

    rebuild_calendar()


def create_date_picker_field(
    parent,
    variable,
    picker_parent,
    title,
    maximum_date=None,
    minimum_date=None,
):
    """
    Create a read-only date entry with a Select Date button.
    """

    wrapper = tk.Frame(
        parent,
        bg=CARD_BG,
    )

    entry = ttk.Entry(
        wrapper,
        textvariable=variable,
        state="readonly",
    )
    entry.pack(
        side="left",
        fill="x",
        expand=True,
    )

    button = tk.Button(
        wrapper,
        text="Select Date",
        command=lambda: open_date_picker(
            picker_parent,
            variable,
            title=title,
            maximum_date=maximum_date,
            minimum_date=minimum_date,
        ),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_DARK,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 8, "bold"),
        padx=9,
        pady=5,
    )
    button.pack(
        side="left",
        padx=(6, 0),
    )

    entry.bind(
        "<Button-1>",
        lambda event: open_date_picker(
            picker_parent,
            variable,
            title=title,
            maximum_date=maximum_date,
            minimum_date=minimum_date,
        ),
    )

    return wrapper


# ============================================================
# STATE VARIABLES
# ============================================================

status_text = tk.StringVar(value="Ready")
search_text = tk.StringVar()
total_value = tk.StringVar(value="0")
in_use_value = tk.StringVar(value="0")
repair_value = tk.StringVar(value="0")
unverified_value = tk.StringVar(value="0")
current_asset_value_text = tk.StringVar(
    value="R 0.00"
)

in_warranty_value = tk.StringVar(
    value="0"
)

out_warranty_value = tk.StringVar(
    value="0"
)

warranty_missing_value = tk.StringVar(
    value="0"
)

current_user = {
    "id": None,
    "username": "",
    "full_name": "",
    "role": "",
}

logged_in_name = tk.StringVar(value="Not signed in")
logged_in_role = tk.StringVar(value="")


def current_actor():
    return (
        clean_value(current_user.get("full_name"))
        or clean_value(current_user.get("username"))
        or "Unknown User"
    )


def has_role(*roles):
    return bool(current_user.get("id")) and current_user.get("role") in roles


def get_visible_assets():
    """Return only assets visible to the signed-in account."""
    if not current_user.get("id"):
        return []

    if has_role("Employee"):
        user_id = current_user.get("id")

        if not user_id:
            return []

        return get_assets_for_user(
            user_id
        )

    return assets


def employee_can_access_asset(asset_id):
    if not current_user.get("id"):
        return False

    if not has_role("Employee"):
        return True

    asset_id = clean_value(
        asset_id
    ).lower()

    return any(
        clean_value(
            asset.get("asset_id")
        ).lower()
        == asset_id
        for asset in get_visible_assets()
    )


def require_employee_asset_access(asset_id):
    if employee_can_access_asset(
        asset_id
    ):
        return True

    messagebox.showwarning(
        "Access Restricted",
        (
            "You can only view or verify assets "
            "assigned to your account."
        ),
    )

    return False


def require_editor_access():
    if has_role("Administrator", "IT Officer"):
        return True

    messagebox.showwarning(
        "Permission Required",
        (
            "This action is available only to "
            "Administrators and IT Officers."
        ),
    )
    return False


def require_admin_access():
    if has_role("Administrator"):
        return True

    messagebox.showwarning(
        "Administrator Required",
        "This action is restricted to Administrators.",
    )
    return False


def update_dashboard_metrics(data=None):
    if data is None:
        data = get_visible_assets()

    total_value.set(
        str(
            len(data)
        )
    )

    in_use_value.set(
        str(
            sum(
                1
                for asset in data
                if clean_value(
                    asset.get("status")
                ).lower()
                == "in use"
            )
        )
    )

    repair_value.set(
        str(
            sum(
                1
                for asset in data
                if clean_value(
                    asset.get("status")
                ).lower()
                == "under repair"
            )
        )
    )

    unverified_value.set(
        str(
            sum(
                1
                for asset in data
                if not clean_value(
                    asset.get(
                        "verified_on"
                    )
                )
            )
        )
    )

    portfolio = (
        calculate_portfolio_financials(
            data
        )
    )

    current_asset_value_text.set(
        format_currency_r(
            portfolio[
                "total_current_book_value_r"
            ]
        )
    )

    warranty_summary = (
        calculate_warranty_summary(
            data
        )
    )

    in_warranty_value.set(
        str(
            warranty_summary[
                "in_warranty"
            ]
        )
    )

    out_warranty_value.set(
        str(
            warranty_summary[
                "out_of_warranty"
            ]
        )
    )

    warranty_missing_value.set(
        str(
            warranty_summary[
                "warranty_date_missing"
            ]
        )
    )


def clear_table():
    for item in asset_table.get_children():
        asset_table.delete(item)


def populate_table(data=None):
    if data is None:
        data = get_visible_assets()

    clear_table()

    for index, asset in enumerate(
        data
    ):
        operational_facility = (
            clean_value(
                asset.get(
                    "operational_facility"
                )
            )
            or clean_value(
                asset.get(
                    "facility_site"
                )
            )
        )

        status = clean_value(
            asset.get(
                "status"
            )
        )

        attention_required = (
            str(
                asset.get(
                    "attention_required",
                    0,
                )
            )
            in {
                "1",
                "True",
                "true",
            }
        )

        status_lower = status.lower()

        if attention_required:
            row_tag = "alert"
        elif status_lower == "under repair":
            row_tag = "repair"
        elif status_lower in {
            "lost",
            "stolen",
        }:
            row_tag = "alert"
        elif index % 2 == 0:
            row_tag = "even"
        else:
            row_tag = "odd"

        asset_table.insert(
            "",
            "end",
            values=(
                clean_value(
                    asset.get(
                        "asset_id"
                    )
                ),
                clean_value(
                    asset.get(
                        "asset_type"
                    )
                ),
                clean_value(
                    asset.get(
                        "make"
                    )
                ),
                clean_value(
                    asset.get(
                        "model"
                    )
                ),
                clean_value(
                    asset.get(
                        "serial_number"
                    )
                ),
                operational_facility,
                clean_value(
                    asset.get(
                        "assigned_user"
                    )
                ),
                clean_value(
                    asset.get(
                        "condition"
                    )
                ),
                clean_value(
                    asset.get(
                        "warranty_status"
                    )
                ),
                (
                    "Attention Required"
                    if attention_required
                    else status
                ),
            ),
            tags=(
                row_tag,
            ),
        )

    status_text.set(
        f"{len(data)} asset(s) displayed"
    )

    update_dashboard_metrics(
        data
    )

def get_selected_asset_id():
    selected = asset_table.selection()

    if not selected:
        messagebox.showwarning(
            "No Asset Selected",
            "Please select an asset first.",
        )
        return None

    item = asset_table.item(
        selected[0]
    )

    values = item.get(
        "values",
        [],
    )

    if not values:
        return None

    return clean_value(
        values[0]
    )


def reload_assets():
    refresh_assets_from_database()

    populate_table(
        get_visible_assets()
    )

def show_all_assets():
    search_text.set("")

    reload_assets()

def gui_search_asset():
    search_value = (
        search_text
        .get()
        .strip()
        .lower()
    )

    base_assets = (
        get_visible_assets()
    )

    if not search_value:
        populate_table(
            base_assets
        )

        return

    results = []

    for asset in base_assets:
        searchable_values = [
            asset.get(
                "asset_id"
            ),
            asset.get(
                "serial_number"
            ),
            asset.get(
                "department_asset_tag"
            ),
            asset.get(
                "asset_type"
            ),
            asset.get(
                "category"
            ),
            asset.get(
                "make"
            ),
            asset.get(
                "model"
            ),
            asset.get(
                "facility_site"
            ),
            asset.get(
                "operational_facility"
            ),
            asset.get(
                "assigned_user"
            ),
            asset.get(
                "status"
            ),
            asset.get(
                "warranty_status"
            ),
            asset.get(
                "warranty_expiry"
            ),
        ]

        if any(
            search_value
            in clean_value(
                value
            ).lower()
            for value in searchable_values
        ):
            results.append(
                asset
            )

    populate_table(
        results
    )

    if not results:
        messagebox.showinfo(
            "Search",
            "No matching assets were found.",
        )

def gui_import_assets():
    if not require_editor_access():
        return

    try:
        prepared = prepare_sync_review()

        if prepared is None:
            messagebox.showwarning(
                "No Files",
                (
                    "No CSV or Excel files were found "
                    "in the input folder."
                ),
            )
            return

        if not prepared["it_assets"]:
            messagebox.showwarning(
                "No IT Assets",
                (
                    f"{prepared['corporate_count']} corporate "
                    "records were read, but no IT assets "
                    "were identified."
                ),
            )
            return

        open_sync_review(prepared)

    except Exception as error:
        messagebox.showerror(
            "Synchronisation Error",
            str(error),
        )


def open_sync_review(prepared):
    preview = prepared["preview"]
    counts = preview["counts"]

    review_window = tk.Toplevel(root)

    review_window.title(
        "Corporate Asset Synchronisation Review"
    )

    set_window_size(
        review_window,
        1100,
        650,
        900,
        560,
    )

    review_window.transient(root)
    review_window.grab_set()

    ttk.Label(
        review_window,
        text=(
            "CORPORATE ASSET "
            "SYNCHRONISATION REVIEW"
        ),
        style="Title.TLabel",
    ).pack(
        pady=(15, 5)
    )

    ttk.Label(
        review_window,
        text=(
            "Review the changes before updating "
            "the IT asset database."
        ),
    ).pack(
        pady=(0, 10)
    )

    summary_frame = ttk.LabelFrame(
        review_window,
        text="Synchronisation Summary",
        padding=10,
    )

    summary_frame.pack(
        fill="x",
        padx=15,
        pady=5,
    )

    summary_values = [
        (
            "Corporate Records",
            prepared["corporate_count"],
        ),
        (
            "IT Assets",
            len(prepared["it_assets"]),
        ),
        (
            "New",
            counts["new"],
        ),
        (
            "Changed",
            counts["changed"],
        ),
        (
            "Unchanged",
            counts["unchanged"],
        ),
        (
            "Duplicates",
            counts["duplicates"],
        ),
        (
            "Skipped",
            counts["skipped"],
        ),
        (
            "Not in Import",
            counts["not_in_current_import"],
        ),
    ]

    for column, (
        label_text,
        value,
    ) in enumerate(
        summary_values
    ):
        ttk.Label(
            summary_frame,
            text=label_text,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        ).grid(
            row=0,
            column=column,
            padx=8,
            pady=2,
        )

        ttk.Label(
            summary_frame,
            text=str(value),
            font=(
                "Segoe UI",
                12,
                "bold",
            ),
        ).grid(
            row=1,
            column=column,
            padx=8,
            pady=2,
        )

    notebook = ttk.Notebook(
        review_window
    )

    notebook.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10,
    )

    def create_review_tab(
        title_text,
        columns,
        headings,
        rows,
        widths=None,
    ):
        frame = ttk.Frame(
            notebook
        )

        notebook.add(
            frame,
            text=(
                f"{title_text} "
                f"({len(rows)})"
            ),
        )

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
        )

        for index, column in enumerate(
            columns
        ):
            tree.heading(
                column,
                text=headings[index],
            )

            width = (
                widths[index]
                if widths
                else 150
            )

            tree.column(
                column,
                width=width,
                minwidth=80,
            )

        for row in rows:
            tree.insert(
                "",
                "end",
                values=row,
            )

        vertical_scroll = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview,
        )

        horizontal_scroll = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=tree.xview,
        )

        tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )

        tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        vertical_scroll.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        horizontal_scroll.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        frame.rowconfigure(
            0,
            weight=1,
        )

        frame.columnconfigure(
            0,
            weight=1,
        )

    new_rows = [
        (
            clean_value(
                asset.get("asset_id")
            ),
            clean_value(
                asset.get("asset_type")
            ),
            clean_value(
                asset.get("make")
            ),
            clean_value(
                asset.get("model")
            ),
            clean_value(
                asset.get("serial_number")
            ),
            clean_value(
                asset.get("facility_site")
            ),
        )
        for asset in preview["new"]
    ]

    create_review_tab(
        "New",
        (
            "asset_id",
            "asset_type",
            "make",
            "model",
            "serial",
            "facility",
        ),
        (
            "Asset ID",
            "Asset Type",
            "Make",
            "Model",
            "Serial Number",
            "Facility",
        ),
        new_rows,
        (
            130,
            130,
            110,
            150,
            170,
            230,
        ),
    )

    changed_rows = []

    for item in preview["changed"]:
        for change in item["changes"]:
            changed_rows.append(
                (
                    item["asset_id"],
                    change["label"],
                    change["old"],
                    change["new"],
                )
            )

    create_review_tab(
        "Changed",
        (
            "asset_id",
            "field",
            "old",
            "new",
        ),
        (
            "Asset ID",
            "Changed Field",
            "Current Value",
            "New Value",
        ),
        changed_rows,
        (
            140,
            180,
            300,
            300,
        ),
    )

    unchanged_rows = [
        (asset_id,)
        for asset_id in preview["unchanged"]
    ]

    create_review_tab(
        "Unchanged",
        ("asset_id",),
        ("Asset ID",),
        unchanged_rows,
        (250,),
    )

    duplicate_rows = [
        (asset_id,)
        for asset_id in preview["duplicates"]
    ]

    create_review_tab(
        "Duplicates",
        ("asset_id",),
        ("Duplicate Asset ID",),
        duplicate_rows,
        (300,),
    )

    skipped_rows = []

    for item in preview["skipped"]:
        skipped_rows.append(
            (
                clean_value(
                    item["asset"].get(
                        "asset_id"
                    )
                ),
                item["reason"],
            )
        )

    create_review_tab(
        "Skipped",
        (
            "asset_id",
            "reason",
        ),
        (
            "Asset ID",
            "Reason",
        ),
        skipped_rows,
        (
            180,
            400,
        ),
    )

    missing_rows = []

    for asset in preview[
        "not_in_current_import"
    ]:
        missing_rows.append(
            (
                clean_value(
                    asset.get(
                        "corporate_asset_id"
                    )
                ),
                clean_value(
                    asset.get("asset_type")
                ),
                clean_value(
                    asset.get("make")
                ),
                clean_value(
                    asset.get("model")
                ),
                clean_value(
                    asset.get("facility_site")
                ),
            )
        )

    create_review_tab(
        "Not in Current Import",
        (
            "asset_id",
            "asset_type",
            "make",
            "model",
            "facility",
        ),
        (
            "Asset ID",
            "Asset Type",
            "Make",
            "Model",
            "Facility",
        ),
        missing_rows,
        (
            140,
            130,
            110,
            160,
            250,
        ),
    )

    button_frame = ttk.Frame(
        review_window,
        padding=10,
    )

    button_frame.pack(
        fill="x"
    )

    def apply_sync():
        confirmation = messagebox.askyesno(
            "Apply Synchronisation",
            (
                "Apply the reviewed corporate asset "
                "changes to the IT database?"
            ),
            parent=review_window,
        )

        if not confirmation:
            return

        try:
            result = apply_prepared_sync(
                prepared["it_assets"]
            )

            populate_table(assets)

            review_window.destroy()

            status_text.set(
                (
                    "Synchronisation complete: "
                    f"{result['inserted']} new, "
                    f"{result['updated']} updated"
                )
            )

            messagebox.showinfo(
                "Synchronisation Complete",
                (
                    "Synchronisation completed.\n\n"
                    f"New: {result['inserted']}\n"
                    f"Updated: {result['updated']}\n"
                    f"Unchanged: {result['unchanged']}\n"
                    f"Skipped: {result['skipped']}"
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Synchronisation Error",
                str(error),
                parent=review_window,
            )

    ttk.Button(
        button_frame,
        text="Apply Synchronisation",
        command=apply_sync,
    ).pack(
        side="right",
        padx=5,
    )

    ttk.Button(
        button_frame,
        text="Cancel",
        command=review_window.destroy,
    ).pack(
        side="right",
        padx=5,
    )


# ============================================================
# VERIFICATION
# ============================================================

def open_employee_verify_asset(
    asset_id,
):
    if not require_employee_asset_access(
        asset_id
    ):
        return

    asset = get_asset_record(
        asset_id
    )

    if asset is None:
        messagebox.showerror(
            "Asset Error",
            "The selected asset could not be found.",
        )

        return

    window = tk.Toplevel(
        root
    )

    window.title(
        f"Verify My Asset - {asset_id}"
    )

    set_window_size(
        window,
        620,
        580,
        560,
        520,
    )

    window.configure(
        bg=APP_BG
    )

    window.transient(
        root
    )

    window.grab_set()

    header = tk.Frame(
        window,
        bg=SIDEBAR_BG,
        height=100,
    )

    header.pack(
        fill="x"
    )

    header.pack_propagate(
        False
    )

    tk.Label(
        header,
        text="Verify My Asset",
        bg=SIDEBAR_BG,
        fg="white",
        font=(
            "Segoe UI",
            19,
            "bold",
        ),
    ).pack(
        anchor="w",
        padx=24,
        pady=(
            15,
            1,
        ),
    )

    tk.Label(
        header,
        text=(
            f"{asset_id} | "
            f"{clean_value(asset.get('asset_type'))} | "
            f"{clean_value(asset.get('make'))} "
            f"{clean_value(asset.get('model'))}"
        ),
        bg=SIDEBAR_BG,
        fg="#D8E7F3",
        font=(
            "Segoe UI",
            9,
        ),
    ).pack(
        anchor="w",
        padx=24,
    )

    card = tk.Frame(
        window,
        bg=CARD_BG,
    )

    card.pack(
        fill="both",
        expand=True,
        padx=22,
        pady=22,
    )

    condition_var = tk.StringVar(
        value=(
            clean_value(
                asset.get(
                    "condition"
                )
            )
            or "Good"
        )
    )

    location_var = tk.StringVar(
        value=(
            clean_value(
                asset.get(
                    "operational_location"
                )
            )
            or clean_value(
                asset.get(
                    "room_location"
                )
            )
        )
    )

    possession_var = tk.StringVar(
        value="Yes"
    )

    issue_var = tk.StringVar(
        value="No"
    )

    tk.Label(
        card,
        text="Employee Verification",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            15,
            "bold",
        ),
    ).grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="w",
        padx=24,
        pady=(
            22,
            4,
        ),
    )

    tk.Label(
        card,
        text=(
            "Confirm possession, condition and current location. "
            "You can also report a problem directly to IT."
        ),
        bg=CARD_BG,
        fg=MUTED,
        font=(
            "Segoe UI",
            9,
        ),
    ).grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="w",
        padx=24,
        pady=(
            0,
            14,
        ),
    )

    form_labels = [
        (
            "Do you currently have this asset?",
            2,
        ),
        (
            "Condition",
            3,
        ),
        (
            "Current Room / Location",
            4,
        ),
        (
            "Report a problem to IT?",
            5,
        ),
    ]

    for label_text, row_number in form_labels:
        tk.Label(
            card,
            text=label_text,
            bg=CARD_BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        ).grid(
            row=row_number,
            column=0,
            sticky="w",
            padx=(
                24,
                12,
            ),
            pady=9,
        )

    ttk.Combobox(
        card,
        textvariable=possession_var,
        values=(
            "Yes",
            "No",
        ),
        state="readonly",
    ).grid(
        row=2,
        column=1,
        sticky="ew",
        padx=(
            0,
            24,
        ),
        pady=9,
    )

    ttk.Combobox(
        card,
        textvariable=condition_var,
        values=(
            "Excellent",
            "Good",
            "Fair",
            "Poor",
            "Damaged",
            "Unserviceable",
        ),
        state="readonly",
    ).grid(
        row=3,
        column=1,
        sticky="ew",
        padx=(
            0,
            24,
        ),
        pady=9,
    )

    ttk.Entry(
        card,
        textvariable=location_var,
    ).grid(
        row=4,
        column=1,
        sticky="ew",
        padx=(
            0,
            24,
        ),
        pady=9,
    )

    ttk.Combobox(
        card,
        textvariable=issue_var,
        values=(
            "No",
            "Yes",
        ),
        state="readonly",
    ).grid(
        row=5,
        column=1,
        sticky="ew",
        padx=(
            0,
            24,
        ),
        pady=9,
    )

    tk.Label(
        card,
        text="Comments / Problem Description",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
    ).grid(
        row=6,
        column=0,
        sticky="nw",
        padx=(
            24,
            12,
        ),
        pady=9,
    )

    notes_text = tk.Text(
        card,
        height=7,
        wrap="word",
        font=(
            "Segoe UI",
            9,
        ),
        bd=1,
        relief="solid",
    )

    notes_text.grid(
        row=6,
        column=1,
        sticky="nsew",
        padx=(
            0,
            24,
        ),
        pady=9,
    )

    card.columnconfigure(
        1,
        weight=1,
    )

    card.rowconfigure(
        6,
        weight=1,
    )

    footer = tk.Frame(
        card,
        bg=CARD_BG,
    )

    footer.grid(
        row=7,
        column=0,
        columnspan=2,
        sticky="ew",
        padx=24,
        pady=(
            10,
            22,
        ),
    )

    def save_employee_verification():
        try:
            result = verify_employee_asset(
                corporate_asset_id=asset_id,
                user_id=current_user["id"],
                condition=condition_var.get(),
                current_location=location_var.get(),
                possession_confirmed=(
                    possession_var.get()
                    == "Yes"
                ),
                issue_reported=(
                    issue_var.get()
                    == "Yes"
                ),
                notes=(
                    notes_text
                    .get(
                        "1.0",
                        "end",
                    )
                    .strip()
                ),
            )

            reload_assets()

            window.destroy()

            if result[
                "attention_required"
            ]:
                messagebox.showwarning(
                    "Verification Saved",
                    (
                        "Your verification was saved.\n\n"
                        "The asset has been flagged for IT attention."
                    ),
                )
            else:
                messagebox.showinfo(
                    "Verification Saved",
                    (
                        "Your asset verification was "
                        "saved successfully."
                    ),
                )

        except Exception as error:
            messagebox.showerror(
                "Verification Error",
                str(error),
                parent=window,
            )

    save_button = tk.Button(
        footer,
        text="Save Verification",
        command=save_employee_verification,
        bg=SUCCESS,
        fg="white",
        activebackground="#236428",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=18,
        pady=9,
    )

    save_button.pack(
        side="right",
        padx=5,
    )

    cancel_button = tk.Button(
        footer,
        text="Cancel",
        command=window.destroy,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=18,
        pady=9,
    )

    cancel_button.pack(
        side="right",
        padx=5,
    )


def open_verify_asset():
    asset_id = get_selected_asset_id()

    if not asset_id:
        return

    if has_role("Employee"):
        open_employee_verify_asset(
            asset_id
        )
        return

    if not has_role(
        "Administrator",
        "IT Officer",
    ):
        messagebox.showwarning(
            "Permission Required",
            (
                "Your account does not have permission "
                "to verify assets."
            ),
        )
        return

    asset = get_asset_record(
        asset_id
    )

    if asset is None:
        messagebox.showerror(
            "Asset Error",
            "The selected asset could not be found.",
        )
        return

    window = tk.Toplevel(root)

    window.title(
        f"Verify Asset - {asset_id}"
    )

    set_window_size(
        window,
        560,
        500,
        520,
        460,
    )

    window.transient(root)
    window.grab_set()

    ttk.Label(
        window,
        text="ASSET VERIFICATION",
        style="Title.TLabel",
    ).pack(
        pady=(15, 5)
    )

    ttk.Label(
        window,
        text=f"Asset ID: {asset_id}",
        font=(
            "Segoe UI",
            11,
            "bold",
        ),
    ).pack(
        pady=(0, 10)
    )

    form = ttk.Frame(
        window,
        padding=20,
    )

    form.pack(
        fill="both",
        expand=True,
    )

    verified_by_var = tk.StringVar(value=current_actor())

    condition_var = tk.StringVar(
        value=clean_value(
            asset.get("condition")
        )
    )

    status_var = tk.StringVar(
        value=clean_value(
            asset.get("status")
        )
    )

    assigned_user_var = tk.StringVar(
        value=clean_value(
            asset.get("assigned_user")
        )
    )

    ttk.Label(
        form,
        text="Verified By:",
    ).grid(
        row=0,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Entry(
        form,
        textvariable=verified_by_var,
    ).grid(
        row=0,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Condition:",
    ).grid(
        row=1,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Combobox(
        form,
        textvariable=condition_var,
        values=(
            "Excellent",
            "Good",
            "Fair",
            "Poor",
            "Damaged",
            "Unserviceable",
        ),
        state="readonly",
    ).grid(
        row=1,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Status:",
    ).grid(
        row=2,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Combobox(
        form,
        textvariable=status_var,
        values=(
            "In Use",
            "In Storage",
            "Under Repair",
            "Transferred",
            "Lost",
            "Stolen",
            "Disposed",
        ),
        state="readonly",
    ).grid(
        row=2,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Assigned User:",
    ).grid(
        row=3,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Entry(
        form,
        textvariable=assigned_user_var,
    ).grid(
        row=3,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Verification Notes:",
    ).grid(
        row=4,
        column=0,
        sticky="nw",
        pady=8,
    )

    notes_text = tk.Text(
        form,
        height=6,
    )

    notes_text.grid(
        row=4,
        column=1,
        sticky="ew",
        pady=8,
    )

    form.columnconfigure(
        1,
        weight=1,
    )

    def save_verification():
        try:
            verify_asset(
                corporate_asset_id=asset_id,
                verified_by=current_actor(),
                condition=condition_var.get(),
                status=status_var.get(),
                assigned_user=assigned_user_var.get(),
                notes=(
                    notes_text
                    .get(
                        "1.0",
                        "end",
                    )
                    .strip()
                ),
            )

            reload_assets()

            window.destroy()

            status_text.set(
                f"Asset {asset_id} verified"
            )

            messagebox.showinfo(
                "Verification Complete",
                (
                    f"Asset {asset_id} "
                    "was successfully verified."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Verification Error",
                str(error),
                parent=window,
            )

    button_frame = ttk.Frame(
        window
    )

    button_frame.pack(
        pady=15
    )

    ttk.Button(
        button_frame,
        text="Save Verification",
        command=save_verification,
    ).pack(
        side="left",
        padx=5,
    )

    ttk.Button(
        button_frame,
        text="Cancel",
        command=window.destroy,
    ).pack(
        side="left",
        padx=5,
    )


# ============================================================
# HISTORY
# ============================================================

def open_asset_history():
    asset_id = get_selected_asset_id()

    if not asset_id:
        return

    if not require_employee_asset_access(
        asset_id
    ):
        return

    history = get_asset_history(
        asset_id
    )

    window = tk.Toplevel(root)

    window.title(
        f"Asset History - {asset_id}"
    )

    set_window_size(
        window,
        1080,
        560,
        860,
        500,
    )

    ttk.Label(
        window,
        text=(
            f"ASSET HISTORY - {asset_id}"
        ),
        style="Title.TLabel",
    ).pack(
        pady=15
    )

    frame = ttk.Frame(
        window,
        padding=10,
    )

    frame.pack(
        fill="both",
        expand=True,
    )

    columns = (
        "date",
        "event",
        "field",
        "old",
        "new",
        "performed_by",
        "notes",
    )

    tree = ttk.Treeview(
        frame,
        columns=columns,
        show="headings",
    )

    headings = {
        "date": "Date / Time",
        "event": "Event",
        "field": "Field",
        "old": "Previous Value",
        "new": "New Value",
        "performed_by": "Performed By",
        "notes": "Notes",
    }

    widths = {
        "date": 150,
        "event": 150,
        "field": 150,
        "old": 180,
        "new": 180,
        "performed_by": 150,
        "notes": 300,
    }

    for column in columns:
        tree.heading(
            column,
            text=headings[column],
        )
        tree.column(
            column,
            width=widths[column],
        )

    for record in history:
        tree.insert(
            "",
            "end",
            values=(
                record.get("event_at", ""),
                record.get("event_type", ""),
                record.get("field_name", ""),
                record.get("old_value", ""),
                record.get("new_value", ""),
                record.get("performed_by", ""),
                record.get("notes", ""),
            ),
        )

    vertical = ttk.Scrollbar(
        frame,
        orient="vertical",
        command=tree.yview,
    )

    horizontal = ttk.Scrollbar(
        frame,
        orient="horizontal",
        command=tree.xview,
    )

    tree.configure(
        yscrollcommand=vertical.set,
        xscrollcommand=horizontal.set,
    )

    tree.grid(
        row=0,
        column=0,
        sticky="nsew",
    )

    vertical.grid(
        row=0,
        column=1,
        sticky="ns",
    )

    horizontal.grid(
        row=1,
        column=0,
        sticky="ew",
    )

    frame.rowconfigure(
        0,
        weight=1,
    )

    frame.columnconfigure(
        0,
        weight=1,
    )


# ============================================================
# ASSET ACTIONS
# ============================================================

def open_asset_actions():
    if not require_editor_access():
        return

    asset_id = get_selected_asset_id()

    if not asset_id:
        return

    window = tk.Toplevel(root)

    window.title(
        f"Asset Actions - {asset_id}"
    )

    set_window_size(
        window,
        460,
        450,
        420,
        400,
    )

    window.transient(root)
    window.grab_set()

    ttk.Label(
        window,
        text="ASSET ACTIONS",
        style="Title.TLabel",
    ).pack(
        pady=(20, 5)
    )

    ttk.Label(
        window,
        text=f"Asset ID: {asset_id}",
    ).pack(
        pady=(0, 20)
    )

    def launch(function):
        window.destroy()
        function(asset_id)

    ttk.Button(
        window,
        text="Assign / Change User",
        command=lambda: launch(
            open_assign_user
        ),
        width=30,
    ).pack(
        pady=6
    )

    ttk.Button(
        window,
        text="Transfer Asset",
        command=lambda: launch(
            open_transfer_asset
        ),
        width=30,
    ).pack(
        pady=6
    )

    ttk.Button(
        window,
        text="Send for Repair",
        command=lambda: launch(
            open_send_for_repair
        ),
        width=30,
    ).pack(
        pady=6
    )

    ttk.Button(
        window,
        text="Return from Repair",
        command=lambda: launch(
            open_return_from_repair
        ),
        width=30,
    ).pack(
        pady=6
    )

    ttk.Button(
        window,
        text="Useful Life / Depreciation",
        command=lambda: launch(
            open_financial_profile
        ),
        width=30,
    ).pack(
        pady=6
    )

    ttk.Button(
        window,
        text="Cancel",
        command=window.destroy,
        width=30,
    ).pack(
        pady=(15, 5)
    )



def open_financial_profile(
    asset_id,
):
    if not require_editor_access():
        return

    asset = get_asset_record(
        asset_id
    )

    if asset is None:
        messagebox.showerror(
            "Asset Error",
            "The selected asset could not be found.",
        )
        return

    window = tk.Toplevel(root)
    window.title(
        f"Useful Life / Depreciation - {asset_id}"
    )

    set_window_size(
        window,
        600,
        560,
        540,
        500,
    )

    window.configure(
        bg=APP_BG
    )

    window.transient(root)
    window.grab_set()

    header = tk.Frame(
        window,
        bg=SIDEBAR_BG,
        height=90,
    )

    header.pack(
        fill="x"
    )

    header.pack_propagate(
        False
    )

    tk.Label(
        header,
        text="Asset Financial Profile",
        bg=SIDEBAR_BG,
        fg="white",
        font=(
            "Segoe UI",
            18,
            "bold",
        ),
    ).pack(
        anchor="w",
        padx=22,
        pady=(
            14,
            1,
        ),
    )

    tk.Label(
        header,
        text=(
            "Straight-line depreciation with zero residual value. "
            "Useful life can be overridden per asset."
        ),
        bg=SIDEBAR_BG,
        fg="#D8E7F3",
        font=(
            "Segoe UI",
            8,
        ),
    ).pack(
        anchor="w",
        padx=22,
    )

    card = tk.Frame(
        window,
        bg=CARD_BG,
    )

    card.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=18,
    )

    useful_life_var = tk.StringVar(
        value=clean_value(
            asset.get(
                "useful_life_years"
            )
        )
        or str(
            DEFAULT_USEFUL_LIFE_YEARS
        )
    )

    notes_var = tk.StringVar()

    preview_vars = {
        "age": tk.StringVar(),
        "remaining": tk.StringVar(),
        "annual": tk.StringVar(),
        "accumulated": tk.StringVar(),
        "book": tk.StringVar(),
        "end": tk.StringVar(),
        "status": tk.StringVar(),
    }

    labels = [
        (
            "Purchase Date",
            clean_value(
                asset.get(
                    "purchase_date"
                )
            ),
        ),
        (
            "Purchase Cost",
            format_currency_r(
                asset.get(
                    "purchase_cost_numeric_r"
                )
            ),
        ),
    ]

    for row_number, (
        label_text,
        value_text,
    ) in enumerate(
        labels
    ):
        tk.Label(
            card,
            text=label_text,
            bg=CARD_BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        ).grid(
            row=row_number,
            column=0,
            sticky="w",
            padx=20,
            pady=8,
        )

        tk.Label(
            card,
            text=value_text,
            bg=CARD_BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                9,
            ),
        ).grid(
            row=row_number,
            column=1,
            sticky="w",
            padx=20,
            pady=8,
        )

    tk.Label(
        card,
        text="Useful Life (Years)",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=20,
        pady=8,
    )

    useful_life_entry = ttk.Entry(
        card,
        textvariable=(
            useful_life_var
        ),
    )

    useful_life_entry.grid(
        row=2,
        column=1,
        sticky="ew",
        padx=20,
        pady=8,
    )

    preview_frame = tk.Frame(
        card,
        bg=LIGHT_BLUE,
    )

    preview_frame.grid(
        row=3,
        column=0,
        columnspan=2,
        sticky="ew",
        padx=20,
        pady=(
            12,
            8,
        ),
    )

    preview_rows = (
        (
            "Calculated Age",
            "age",
        ),
        (
            "Remaining Useful Life",
            "remaining",
        ),
        (
            "Annual Depreciation",
            "annual",
        ),
        (
            "Accumulated Depreciation",
            "accumulated",
        ),
        (
            "Current Book Value",
            "book",
        ),
        (
            "End of Useful Life",
            "end",
        ),
        (
            "Status",
            "status",
        ),
    )

    for row_number, (
        label_text,
        key,
    ) in enumerate(
        preview_rows
    ):
        tk.Label(
            preview_frame,
            text=label_text,
            bg=LIGHT_BLUE,
            fg=TEXT,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
        ).grid(
            row=row_number,
            column=0,
            sticky="w",
            padx=12,
            pady=4,
        )

        tk.Label(
            preview_frame,
            textvariable=(
                preview_vars[
                    key
                ]
            ),
            bg=LIGHT_BLUE,
            fg=TEXT,
            font=(
                "Segoe UI",
                8,
            ),
        ).grid(
            row=row_number,
            column=1,
            sticky="w",
            padx=12,
            pady=4,
        )

    preview_frame.columnconfigure(
        1,
        weight=1,
    )

    card.columnconfigure(
        1,
        weight=1,
    )

    def refresh_preview(
        *args,
    ):
        preview_asset = dict(
            asset
        )

        preview_asset[
            "useful_life_years"
        ] = useful_life_var.get()

        financials = (
            calculate_asset_financials(
                preview_asset
            )
        )

        age = financials.get(
            "calculated_age_years"
        )

        remaining = financials.get(
            "remaining_life_years"
        )

        preview_vars[
            "age"
        ].set(
            (
                f"{age:.2f} years"
                if age is not None
                else "Not available"
            )
        )

        preview_vars[
            "remaining"
        ].set(
            (
                f"{remaining:.2f} years"
                if remaining is not None
                else "Not available"
            )
        )

        preview_vars[
            "annual"
        ].set(
            format_currency_r(
                financials.get(
                    "annual_depreciation_r"
                )
            )
        )

        preview_vars[
            "accumulated"
        ].set(
            format_currency_r(
                financials.get(
                    "accumulated_depreciation_r"
                )
            )
        )

        preview_vars[
            "book"
        ].set(
            format_currency_r(
                financials.get(
                    "current_book_value_r"
                )
            )
        )

        preview_vars[
            "end"
        ].set(
            clean_value(
                financials.get(
                    "end_of_useful_life"
                )
            )
            or "Not available"
        )

        preview_vars[
            "status"
        ].set(
            clean_value(
                financials.get(
                    "financial_calculation_status"
                )
            )
        )

    useful_life_var.trace_add(
        "write",
        refresh_preview,
    )

    refresh_preview()

    footer = tk.Frame(
        card,
        bg=CARD_BG,
    )

    footer.grid(
        row=4,
        column=0,
        columnspan=2,
        sticky="ew",
        padx=20,
        pady=(
            12,
            18,
        ),
    )

    def save_financial_profile():
        try:
            update_asset_useful_life(
                corporate_asset_id=(
                    asset_id
                ),
                useful_life_years=(
                    useful_life_var
                    .get()
                ),
                performed_by=(
                    current_actor()
                ),
                notes=(
                    "Useful life updated "
                    "for depreciation calculation."
                ),
            )

            reload_assets()

            window.destroy()

            messagebox.showinfo(
                "Financial Profile Updated",
                (
                    f"Useful life for asset {asset_id} "
                    "was updated successfully."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Unable to Update",
                str(error),
                parent=window,
            )

    tk.Button(
        footer,
        text="Save Useful Life",
        command=(
            save_financial_profile
        ),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_DARK,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=14,
        pady=7,
    ).pack(
        side="right",
        padx=5,
    )

    tk.Button(
        footer,
        text="Cancel",
        command=window.destroy,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=14,
        pady=7,
    ).pack(
        side="right",
        padx=5,
    )


def open_assign_user(asset_id):
    if not require_editor_access():
        return

    asset = get_asset_record(
        asset_id
    )

    if asset is None:
        return

    def refresh_warranty_preview(
        *args,
    ):
        warranty_info = (
            calculate_warranty_info(
                {
                    "warranty_expiry": (
                        variables[
                            "warranty_expiry"
                        ].get()
                    )
                }
            )
        )

        variables[
            "warranty_status"
        ].set(
            warranty_info[
                "calculated_warranty_status"
            ]
        )

    variables[
        "warranty_expiry"
    ].trace_add(
        "write",
        refresh_warranty_preview,
    )

    refresh_warranty_preview()

    assignable_users = (
        list_assignable_users()
    )

    if not assignable_users:
        messagebox.showwarning(
            "No Employee Accounts",
            (
                "Create an Employee account first, "
                "then assign the asset to that account."
            ),
        )
        return

    display_to_user = {}

    for user in assignable_users:
        display = (
            f"{user['full_name']} "
            f"({user['username']}) - "
            f"{user['role']}"
        )

        display_to_user[
            display
        ] = user

    selected_display = (
        tk.StringVar()
    )

    current_account_id = (
        asset.get(
            "assigned_user_account_id"
        )
    )

    if current_account_id not in (
        None,
        "",
    ):
        for display, user in (
            display_to_user.items()
        ):
            if (
                int(
                    user["id"]
                )
                == int(
                    current_account_id
                )
            ):
                selected_display.set(
                    display
                )
                break

    window = tk.Toplevel(
        root
    )

    window.title(
        f"Assign Employee - {asset_id}"
    )

    set_window_size(
        window,
        620,
        440,
        560,
        400,
    )

    window.configure(
        bg=APP_BG
    )

    window.transient(
        root
    )

    window.grab_set()

    header = tk.Frame(
        window,
        bg=SIDEBAR_BG,
        height=92,
    )

    header.pack(
        fill="x"
    )

    header.pack_propagate(
        False
    )

    tk.Label(
        header,
        text="Assign Asset to Employee",
        bg=SIDEBAR_BG,
        fg="white",
        font=(
            "Segoe UI",
            18,
            "bold",
        ),
    ).pack(
        anchor="w",
        padx=24,
        pady=(
            15,
            1,
        ),
    )

    tk.Label(
        header,
        text=(
            f"Asset {asset_id} will be linked "
            "to the selected login account."
        ),
        bg=SIDEBAR_BG,
        fg="#D8E7F3",
        font=(
            "Segoe UI",
            9,
        ),
    ).pack(
        anchor="w",
        padx=24,
    )

    card = tk.Frame(
        window,
        bg=CARD_BG,
    )

    card.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20,
    )

    tk.Label(
        card,
        text="Employee Account",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=(
            22,
            12,
        ),
        pady=12,
    )

    account_combo = ttk.Combobox(
        card,
        textvariable=selected_display,
        values=tuple(
            display_to_user.keys()
        ),
        state="readonly",
    )

    account_combo.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(
            0,
            22,
        ),
        pady=12,
    )

    tk.Label(
        card,
        text="Current Assigned User",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=(
            22,
            12,
        ),
        pady=8,
    )

    tk.Label(
        card,
        text=(
            clean_value(
                asset.get(
                    "assigned_user"
                )
            )
            or "Not assigned"
        ),
        bg=CARD_BG,
        fg=MUTED,
        font=(
            "Segoe UI",
            9,
        ),
    ).grid(
        row=1,
        column=1,
        sticky="w",
        padx=(
            0,
            22,
        ),
        pady=8,
    )

    tk.Label(
        card,
        text="Notes",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
    ).grid(
        row=2,
        column=0,
        sticky="nw",
        padx=(
            22,
            12,
        ),
        pady=10,
    )

    notes = tk.Text(
        card,
        height=7,
        wrap="word",
        font=(
            "Segoe UI",
            9,
        ),
        bd=1,
        relief="solid",
    )

    notes.grid(
        row=2,
        column=1,
        sticky="nsew",
        padx=(
            0,
            22,
        ),
        pady=10,
    )

    card.columnconfigure(
        1,
        weight=1,
    )

    card.rowconfigure(
        2,
        weight=1,
    )

    footer = tk.Frame(
        card,
        bg=CARD_BG,
    )

    footer.grid(
        row=3,
        column=0,
        columnspan=2,
        sticky="ew",
        padx=22,
        pady=(
            10,
            20,
        ),
    )

    def save():
        try:
            display = (
                selected_display
                .get()
            )

            if not display:
                raise ValueError(
                    "Please select an employee account."
                )

            user = (
                display_to_user[
                    display
                ]
            )

            assign_asset(
                corporate_asset_id=asset_id,
                assigned_user=(
                    user[
                        "full_name"
                    ]
                ),
                assigned_user_account_id=(
                    user[
                        "id"
                    ]
                ),
                performed_by=(
                    current_actor()
                ),
                notes=(
                    notes
                    .get(
                        "1.0",
                        "end",
                    )
                    .strip()
                ),
            )

            reload_assets()

            window.destroy()

            messagebox.showinfo(
                "Assignment Complete",
                (
                    f"Asset {asset_id} is now assigned to "
                    f"{user['full_name']}.\n\n"
                    "The employee will see it in My Assets "
                    "after refreshing their dashboard."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Assignment Error",
                str(error),
                parent=window,
            )

    save_button = tk.Button(
        footer,
        text="Save Assignment",
        command=save,
        bg=SUCCESS,
        fg="white",
        activebackground="#236428",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=18,
        pady=9,
    )

    save_button.pack(
        side="right",
        padx=5,
    )

    cancel_button = tk.Button(
        footer,
        text="Cancel",
        command=window.destroy,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=18,
        pady=9,
    )

    cancel_button.pack(
        side="right",
        padx=5,
    )

def open_transfer_asset(asset_id):
    if not require_editor_access():
        return

    asset = get_asset_record(
        asset_id
    )

    if asset is None:
        return

    window = tk.Toplevel(root)

    window.title(
        f"Transfer Asset - {asset_id}"
    )

    set_window_size(
        window,
        570,
        470,
        520,
        430,
    )

    window.transient(root)
    window.grab_set()

    form = ttk.Frame(
        window,
        padding=20,
    )

    form.pack(
        fill="both",
        expand=True,
    )

    facility_var = tk.StringVar(
        value=(
            clean_value(
                asset.get(
                    "operational_facility"
                )
            )
            or clean_value(
                asset.get("facility_site")
            )
        )
    )

    department_var = tk.StringVar(
        value=(
            clean_value(
                asset.get(
                    "operational_department"
                )
            )
            or clean_value(
                asset.get(
                    "section_department"
                )
            )
        )
    )

    location_var = tk.StringVar(
        value=(
            clean_value(
                asset.get(
                    "operational_location"
                )
            )
            or clean_value(
                asset.get("room_location")
            )
        )
    )

    performed_by_var = tk.StringVar(value=current_actor())

    fields = [
        (
            "New Facility:",
            facility_var,
        ),
        (
            "New Department:",
            department_var,
        ),
        (
            "New Room / Location:",
            location_var,
        ),
        (
            "Performed By:",
            performed_by_var,
        ),
    ]

    for row_number, (
        label,
        variable,
    ) in enumerate(
        fields
    ):
        ttk.Label(
            form,
            text=label,
        ).grid(
            row=row_number,
            column=0,
            sticky="w",
            pady=8,
        )

        ttk.Entry(
            form,
            textvariable=variable,
        ).grid(
            row=row_number,
            column=1,
            sticky="ew",
            pady=8,
        )

    ttk.Label(
        form,
        text="Transfer Notes:",
    ).grid(
        row=4,
        column=0,
        sticky="nw",
        pady=8,
    )

    notes = tk.Text(
        form,
        height=6,
    )

    notes.grid(
        row=4,
        column=1,
        sticky="ew",
        pady=8,
    )

    form.columnconfigure(
        1,
        weight=1,
    )

    def save():
        try:
            transfer_asset(
                corporate_asset_id=asset_id,
                new_facility=facility_var.get(),
                new_department=department_var.get(),
                new_location=location_var.get(),
                performed_by=current_actor(),
                notes=(
                    notes
                    .get(
                        "1.0",
                        "end",
                    )
                    .strip()
                ),
            )

            reload_assets()
            window.destroy()

            messagebox.showinfo(
                "Transfer Complete",
                (
                    f"Asset {asset_id} "
                    "was transferred successfully."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Transfer Error",
                str(error),
                parent=window,
            )

    ttk.Button(
        form,
        text="Save Transfer",
        command=save,
    ).grid(
        row=5,
        column=1,
        sticky="e",
        pady=15,
    )


def open_send_for_repair(asset_id):
    if not require_editor_access():
        return

    window = tk.Toplevel(root)

    window.title(
        f"Send for Repair - {asset_id}"
    )

    set_window_size(
        window,
        530,
        410,
        500,
        380,
    )

    window.transient(root)
    window.grab_set()

    form = ttk.Frame(
        window,
        padding=20,
    )

    form.pack(
        fill="both",
        expand=True,
    )

    provider_var = tk.StringVar()
    reference_var = tk.StringVar()
    performed_by_var = tk.StringVar(value=current_actor())

    fields = [
        (
            "Repair Provider:",
            provider_var,
        ),
        (
            "Reference Number:",
            reference_var,
        ),
        (
            "Performed By:",
            performed_by_var,
        ),
    ]

    for row_number, (
        label,
        variable,
    ) in enumerate(
        fields
    ):
        ttk.Label(
            form,
            text=label,
        ).grid(
            row=row_number,
            column=0,
            sticky="w",
            pady=8,
        )

        ttk.Entry(
            form,
            textvariable=variable,
        ).grid(
            row=row_number,
            column=1,
            sticky="ew",
            pady=8,
        )

    ttk.Label(
        form,
        text="Repair Notes:",
    ).grid(
        row=3,
        column=0,
        sticky="nw",
        pady=8,
    )

    notes = tk.Text(
        form,
        height=6,
    )

    notes.grid(
        row=3,
        column=1,
        sticky="ew",
        pady=8,
    )

    form.columnconfigure(
        1,
        weight=1,
    )

    def save():
        try:
            send_asset_for_repair(
                corporate_asset_id=asset_id,
                repair_provider=provider_var.get(),
                reference_number=reference_var.get(),
                performed_by=current_actor(),
                notes=(
                    notes
                    .get(
                        "1.0",
                        "end",
                    )
                    .strip()
                ),
            )

            reload_assets()
            window.destroy()

            messagebox.showinfo(
                "Repair Logged",
                (
                    f"Asset {asset_id} "
                    "is now marked Under Repair."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Repair Error",
                str(error),
                parent=window,
            )

    ttk.Button(
        form,
        text="Send for Repair",
        command=save,
    ).grid(
        row=4,
        column=1,
        sticky="e",
        pady=15,
    )


def open_return_from_repair(asset_id):
    if not require_editor_access():
        return

    asset = get_asset_record(
        asset_id
    )

    if asset is None:
        return

    window = tk.Toplevel(root)

    window.title(
        f"Return from Repair - {asset_id}"
    )

    set_window_size(
        window,
        530,
        440,
        500,
        400,
    )

    window.transient(root)
    window.grab_set()

    form = ttk.Frame(
        window,
        padding=20,
    )

    form.pack(
        fill="both",
        expand=True,
    )

    condition_var = tk.StringVar(
        value=clean_value(
            asset.get("condition")
        )
    )

    status_var = tk.StringVar(
        value="In Use"
    )

    reference_var = tk.StringVar()
    performed_by_var = tk.StringVar(value=current_actor())

    ttk.Label(
        form,
        text="Condition:",
    ).grid(
        row=0,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Combobox(
        form,
        textvariable=condition_var,
        values=(
            "Excellent",
            "Good",
            "Fair",
            "Poor",
            "Damaged",
            "Unserviceable",
        ),
        state="readonly",
    ).grid(
        row=0,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Status:",
    ).grid(
        row=1,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Combobox(
        form,
        textvariable=status_var,
        values=(
            "In Use",
            "In Storage",
            "Under Repair",
            "Disposed",
        ),
        state="readonly",
    ).grid(
        row=1,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Repair Reference:",
    ).grid(
        row=2,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Entry(
        form,
        textvariable=reference_var,
    ).grid(
        row=2,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Performed By:",
    ).grid(
        row=3,
        column=0,
        sticky="w",
        pady=8,
    )

    ttk.Entry(
        form,
        textvariable=performed_by_var,
    ).grid(
        row=3,
        column=1,
        sticky="ew",
        pady=8,
    )

    ttk.Label(
        form,
        text="Repair Outcome Notes:",
    ).grid(
        row=4,
        column=0,
        sticky="nw",
        pady=8,
    )

    notes = tk.Text(
        form,
        height=6,
    )

    notes.grid(
        row=4,
        column=1,
        sticky="ew",
        pady=8,
    )

    form.columnconfigure(
        1,
        weight=1,
    )

    def save():
        try:
            return_asset_from_repair(
                corporate_asset_id=asset_id,
                condition=condition_var.get(),
                status=status_var.get(),
                performed_by=current_actor(),
                reference_number=reference_var.get(),
                notes=(
                    notes
                    .get(
                        "1.0",
                        "end",
                    )
                    .strip()
                ),
            )

            reload_assets()
            window.destroy()

            messagebox.showinfo(
                "Repair Completed",
                (
                    f"Asset {asset_id} "
                    "was returned from repair."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Repair Error",
                str(error),
                parent=window,
            )

    ttk.Button(
        form,
        text="Complete Repair",
        command=save,
    ).grid(
        row=5,
        column=1,
        sticky="e",
        pady=15,
    )


# ============================================================
# ASSET DETAILS
# ============================================================

def open_asset_details():
    asset_id = get_selected_asset_id()

    if not asset_id:
        return

    if not require_employee_asset_access(
        asset_id
    ):
        return

    asset = get_asset_record(
        asset_id
    )

    if asset is None:
        messagebox.showerror(
            "Asset Error",
            "The selected asset could not be found.",
        )
        return

    history = get_asset_history(
        asset_id
    )

    transactions = get_asset_transactions(
        asset_id
    )

    window = tk.Toplevel(root)

    window.title(
        f"Asset Details - {asset_id}"
    )

    set_window_size(
        window,
        1140,
        640,
        900,
        540,
    )

    header = ttk.Frame(
        window,
        padding=15,
    )

    header.pack(
        fill="x"
    )

    ttk.Label(
        header,
        text="ASSET DETAILS",
        style="Title.TLabel",
    ).pack(
        anchor="w"
    )

    summary_text = (
        f"Asset ID: {asset_id}    |    "
        f"Type: {clean_value(asset.get('asset_type'))}    |    "
        f"Make: {clean_value(asset.get('make'))}    |    "
        f"Model: {clean_value(asset.get('model'))}"
    )

    ttk.Label(
        header,
        text=summary_text,
    ).pack(
        anchor="w",
        pady=(5, 0),
    )

    notebook = ttk.Notebook(
        window
    )

    notebook.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=(0, 15),
    )

    # --------------------------------------------------------
    # OVERVIEW TAB
    # --------------------------------------------------------

    overview_frame = ttk.Frame(
        notebook,
        padding=10,
    )

    notebook.add(
        overview_frame,
        text="Overview",
    )

    overview_tree = ttk.Treeview(
        overview_frame,
        columns=(
            "field",
            "value",
        ),
        show="headings",
    )

    overview_tree.heading(
        "field",
        text="Field",
    )

    overview_tree.heading(
        "value",
        text="Value",
    )

    overview_tree.column(
        "field",
        width=260,
        anchor="w",
    )

    overview_tree.column(
        "value",
        width=750,
        anchor="w",
    )

    operational_facility = (
        clean_value(
            asset.get(
                "operational_facility"
            )
        )
        or clean_value(
            asset.get("facility_site")
        )
    )

    operational_department = (
        clean_value(
            asset.get(
                "operational_department"
            )
        )
        or clean_value(
            asset.get(
                "section_department"
            )
        )
    )

    operational_location = (
        clean_value(
            asset.get(
                "operational_location"
            )
        )
        or clean_value(
            asset.get("room_location")
        )
    )

    overview_data = [
        ("Asset ID", asset_id),
        (
            "Asset Type",
            clean_value(
                asset.get("asset_type")
            ),
        ),
        (
            "Category",
            clean_value(
                asset.get("category")
            ),
        ),
        (
            "Make",
            clean_value(
                asset.get("make")
            ),
        ),
        (
            "Model",
            clean_value(
                asset.get("model")
            ),
        ),
        (
            "Serial Number",
            clean_value(
                asset.get("serial_number")
            ),
        ),
        (
            "Department Asset Tag",
            clean_value(
                asset.get(
                    "department_asset_tag"
                )
            ),
        ),
        (
            "Specification / OS",
            clean_value(
                asset.get(
                    "specification_os"
                )
            ),
        ),
        (
            "Assigned User",
            clean_value(
                asset.get("assigned_user")
            ),
        ),
        (
            "Condition",
            clean_value(
                asset.get("condition")
            ),
        ),
        (
            "Status",
            clean_value(
                asset.get("status")
            ),
        ),
        (
            "Warranty Status",
            clean_value(
                asset.get(
                    "warranty_status"
                )
            ),
        ),
        (
            "Warranty Detail",
            clean_value(
                asset.get(
                    "warranty_detail"
                )
            ),
        ),
        (
            "Recommendation",
            clean_value(
                asset.get(
                    "recommendation"
                )
            ),
        ),
        (
            "Corporate Facility",
            clean_value(
                asset.get("facility_site")
            ),
        ),
        (
            "Corporate District",
            clean_value(
                asset.get("district")
            ),
        ),
        (
            "Corporate Department",
            clean_value(
                asset.get(
                    "section_department"
                )
            ),
        ),
        (
            "Corporate Room / Location",
            clean_value(
                asset.get("room_location")
            ),
        ),
        (
            "Operational Facility",
            operational_facility,
        ),
        (
            "Operational Department",
            operational_department,
        ),
        (
            "Operational Room / Location",
            operational_location,
        ),
        (
            "Purchase Date",
            clean_value(
                asset.get("purchase_date")
            ),
        ),
        (
            "Purchase Cost",
            clean_value(
                asset.get(
                    "purchase_cost_r"
                )
            ),
        ),
        (
            "Useful Life (Years)",
            clean_value(
                asset.get(
                    "useful_life_years"
                )
            ),
        ),
        (
            "Calculated Asset Age",
            (
                (
                    f"{asset.get('calculated_age_years'):.2f} years"
                )
                if asset.get(
                    "calculated_age_years"
                )
                is not None
                else "Not available"
            ),
        ),
        (
            "Remaining Useful Life",
            (
                (
                    f"{asset.get('remaining_life_years'):.2f} years"
                )
                if asset.get(
                    "remaining_life_years"
                )
                is not None
                else "Not available"
            ),
        ),
        (
            "Depreciation Method",
            clean_value(
                asset.get(
                    "depreciation_method"
                )
            ),
        ),
        (
            "Annual Depreciation",
            format_currency_r(
                asset.get(
                    "annual_depreciation_r"
                )
            ),
        ),
        (
            "Accumulated Depreciation",
            format_currency_r(
                asset.get(
                    "accumulated_depreciation_r"
                )
            ),
        ),
        (
            "Current Book Value",
            format_currency_r(
                asset.get(
                    "current_book_value_r"
                )
            ),
        ),
        (
            "End of Useful Life",
            clean_value(
                asset.get(
                    "end_of_useful_life"
                )
            )
            or "Not available",
        ),
        (
            "Financial Calculation Status",
            clean_value(
                asset.get(
                    "financial_calculation_status"
                )
            ),
        ),
        (
            "Supplier",
            clean_value(
                asset.get("supplier")
            ),
        ),
        (
            "Warranty Expiry",
            clean_value(
                asset.get(
                    "warranty_expiry"
                )
            ),
        ),
        (
            "Asset Age",
            clean_value(
                asset.get("age_yrs")
            ),
        ),
        (
            "Verified On",
            clean_value(
                asset.get("verified_on")
            ),
        ),
        (
            "Verified By",
            clean_value(
                asset.get("verified_by")
            ),
        ),
        (
            "Notes",
            clean_value(
                asset.get("notes")
            ),
        ),
        (
            "Source File",
            clean_value(
                asset.get("source_file")
            ),
        ),
        (
            "Source System",
            clean_value(
                asset.get("source_system")
            ),
        ),
        (
            "Created",
            clean_value(
                asset.get("created_at")
            ),
        ),
        (
            "Last Updated",
            clean_value(
                asset.get("updated_at")
            ),
        ),
        (
            "Last Corporate Sync",
            clean_value(
                asset.get("last_synced_at")
            ),
        ),
    ]

    for field_name, value in overview_data:
        overview_tree.insert(
            "",
            "end",
            values=(
                field_name,
                value,
            ),
        )

    overview_scroll = ttk.Scrollbar(
        overview_frame,
        orient="vertical",
        command=overview_tree.yview,
    )

    overview_tree.configure(
        yscrollcommand=overview_scroll.set
    )

    overview_tree.grid(
        row=0,
        column=0,
        sticky="nsew",
    )

    overview_scroll.grid(
        row=0,
        column=1,
        sticky="ns",
    )

    overview_frame.rowconfigure(
        0,
        weight=1,
    )

    overview_frame.columnconfigure(
        0,
        weight=1,
    )

    # --------------------------------------------------------
    # AUDIT HISTORY TAB
    # --------------------------------------------------------

    history_frame = ttk.Frame(
        notebook,
        padding=10,
    )

    notebook.add(
        history_frame,
        text=(
            f"Audit History "
            f"({len(history)})"
        ),
    )

    history_columns = (
        "date",
        "event",
        "field",
        "old_value",
        "new_value",
        "performed_by",
        "notes",
    )

    history_tree = ttk.Treeview(
        history_frame,
        columns=history_columns,
        show="headings",
    )

    history_headings = {
        "date": "Date / Time",
        "event": "Event",
        "field": "Field",
        "old_value": "Previous Value",
        "new_value": "New Value",
        "performed_by": "Performed By",
        "notes": "Notes",
    }

    history_widths = {
        "date": 150,
        "event": 150,
        "field": 150,
        "old_value": 180,
        "new_value": 180,
        "performed_by": 150,
        "notes": 300,
    }

    for column in history_columns:
        history_tree.heading(
            column,
            text=history_headings[column],
        )

        history_tree.column(
            column,
            width=history_widths[column],
        )

    for record in history:
        history_tree.insert(
            "",
            "end",
            values=(
                clean_value(
                    record.get("event_at")
                ),
                clean_value(
                    record.get("event_type")
                ),
                clean_value(
                    record.get("field_name")
                ),
                clean_value(
                    record.get("old_value")
                ),
                clean_value(
                    record.get("new_value")
                ),
                clean_value(
                    record.get("performed_by")
                ),
                clean_value(
                    record.get("notes")
                ),
            ),
        )

    history_vertical = ttk.Scrollbar(
        history_frame,
        orient="vertical",
        command=history_tree.yview,
    )

    history_horizontal = ttk.Scrollbar(
        history_frame,
        orient="horizontal",
        command=history_tree.xview,
    )

    history_tree.configure(
        yscrollcommand=history_vertical.set,
        xscrollcommand=history_horizontal.set,
    )

    history_tree.grid(
        row=0,
        column=0,
        sticky="nsew",
    )

    history_vertical.grid(
        row=0,
        column=1,
        sticky="ns",
    )

    history_horizontal.grid(
        row=1,
        column=0,
        sticky="ew",
    )

    history_frame.rowconfigure(
        0,
        weight=1,
    )

    history_frame.columnconfigure(
        0,
        weight=1,
    )

    # --------------------------------------------------------
    # TRANSACTIONS TAB
    # --------------------------------------------------------

    transaction_frame = ttk.Frame(
        notebook,
        padding=10,
    )

    notebook.add(
        transaction_frame,
        text=(
            f"Transactions "
            f"({len(transactions)})"
        ),
    )

    transaction_columns = (
        "date",
        "type",
        "from_user",
        "to_user",
        "from_facility",
        "to_facility",
        "provider",
        "reference",
        "status_before",
        "status_after",
        "performed_by",
        "notes",
    )

    transaction_tree = ttk.Treeview(
        transaction_frame,
        columns=transaction_columns,
        show="headings",
    )

    transaction_headings = {
        "date": "Date / Time",
        "type": "Transaction",
        "from_user": "From User",
        "to_user": "To User",
        "from_facility": "From Facility",
        "to_facility": "To Facility",
        "provider": "Repair Provider",
        "reference": "Reference",
        "status_before": "Previous Status",
        "status_after": "New Status",
        "performed_by": "Performed By",
        "notes": "Notes",
    }

    transaction_widths = {
        "date": 150,
        "type": 140,
        "from_user": 150,
        "to_user": 150,
        "from_facility": 180,
        "to_facility": 180,
        "provider": 170,
        "reference": 130,
        "status_before": 130,
        "status_after": 130,
        "performed_by": 150,
        "notes": 250,
    }

    for column in transaction_columns:
        transaction_tree.heading(
            column,
            text=transaction_headings[column],
        )

        transaction_tree.column(
            column,
            width=transaction_widths[column],
        )

    for record in transactions:
        transaction_tree.insert(
            "",
            "end",
            values=(
                clean_value(
                    record.get("event_at")
                ),
                clean_value(
                    record.get(
                        "transaction_type"
                    )
                ),
                clean_value(
                    record.get(
                        "from_assigned_user"
                    )
                ),
                clean_value(
                    record.get(
                        "to_assigned_user"
                    )
                ),
                clean_value(
                    record.get("from_facility")
                ),
                clean_value(
                    record.get("to_facility")
                ),
                clean_value(
                    record.get("repair_provider")
                ),
                clean_value(
                    record.get("reference_number")
                ),
                clean_value(
                    record.get("status_before")
                ),
                clean_value(
                    record.get("status_after")
                ),
                clean_value(
                    record.get("performed_by")
                ),
                clean_value(
                    record.get("notes")
                ),
            ),
        )

    transaction_vertical = ttk.Scrollbar(
        transaction_frame,
        orient="vertical",
        command=transaction_tree.yview,
    )

    transaction_horizontal = ttk.Scrollbar(
        transaction_frame,
        orient="horizontal",
        command=transaction_tree.xview,
    )

    transaction_tree.configure(
        yscrollcommand=transaction_vertical.set,
        xscrollcommand=transaction_horizontal.set,
    )

    transaction_tree.grid(
        row=0,
        column=0,
        sticky="nsew",
    )

    transaction_vertical.grid(
        row=0,
        column=1,
        sticky="ns",
    )

    transaction_horizontal.grid(
        row=1,
        column=0,
        sticky="ew",
    )

    transaction_frame.rowconfigure(
        0,
        weight=1,
    )

    transaction_frame.columnconfigure(
        0,
        weight=1,
    )


# ============================================================
# DUPLICATE CHECK
# ============================================================

def gui_check_duplicates():
    if not has_role("Administrator", "IT Officer", "Viewer"):
        messagebox.showwarning(
            "Permission Required",
            (
                "Employee accounts can only view and "
                "verify their assigned assets."
            ),
        )
        return

    duplicate_records, messages = (
        get_duplicate_records(
            get_visible_assets()
        )
    )

    if not messages:
        messagebox.showinfo(
            "Duplicate Check",
            "No duplicate assets were detected.",
        )
        return

    unique_records = {}

    for asset in duplicate_records:
        key = clean_value(
            asset.get(
                "asset_id"
            )
        )

        unique_records[
            key
        ] = asset

    populate_table(
        list(
            unique_records.values()
        )
    )

    messagebox.showwarning(
        "Duplicates Found",
        "\n".join(
            messages[:20]
        ),
    )

def gui_export_report():
    if not has_role("Administrator", "IT Officer", "Viewer"):
        messagebox.showwarning(
            "Permission Required",
            (
                "Employee accounts can view and verify "
                "their assigned assets, but cannot export "
                "the full asset register."
            ),
        )
        return

    if not assets:
        messagebox.showwarning(
            "No Assets",
            "No assets are currently loaded.",
        )
        return

    try:
        output_file = export_report()

        messagebox.showinfo(
            "Export Complete",
            (
                "The IT Asset Audit Report "
                "was successfully created.\n\n"
                f"{output_file}"
            ),
        )

        status_text.set(
            "Audit report exported successfully"
        )

    except PermissionError:
        messagebox.showerror(
            "Export Error",
            (
                "Please close the existing "
                "IT_Asset_Audit_Report.xlsx "
                "file and try again."
            ),
        )

    except Exception as error:
        messagebox.showerror(
            "Export Error",
            str(error),
        )

def open_add_asset():
    if not require_editor_access():
        return

    window = tk.Toplevel(root)
    window.title("Add New Asset")
    set_window_size(
        window,
        800,
        620,
        700,
        540,
    )
    window.configure(bg=APP_BG)
    window.transient(root)
    window.grab_set()

    header = tk.Frame(
        window,
        bg=SIDEBAR_BG,
        height=92,
    )
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text="Add New IT Asset",
        bg=SIDEBAR_BG,
        fg="white",
        font=("Segoe UI", 19, "bold"),
    ).pack(
        anchor="w",
        padx=24,
        pady=(15, 1),
    )

    tk.Label(
        header,
        text=(
            "Create a local IT asset record. Leave Asset ID blank "
            "to generate a unique IT-LOCAL ID."
        ),
        bg=SIDEBAR_BG,
        fg="#D8E7F3",
        font=("Segoe UI", 9),
    ).pack(
        anchor="w",
        padx=24,
    )

    notebook = ttk.Notebook(window)
    notebook.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=(18, 10),
    )

    identity_tab = tk.Frame(
        notebook,
        bg=CARD_BG,
    )
    location_tab = tk.Frame(
        notebook,
        bg=CARD_BG,
    )
    management_tab = tk.Frame(
        notebook,
        bg=CARD_BG,
    )

    notebook.add(
        identity_tab,
        text="Identification",
    )
    notebook.add(
        location_tab,
        text="Location & Purchase",
    )
    notebook.add(
        management_tab,
        text="IT Management",
    )

    variables = {
        "asset_id": tk.StringVar(),
        "asset_type": tk.StringVar(),
        "category": tk.StringVar(),
        "make": tk.StringVar(),
        "model": tk.StringVar(),
        "serial_number": tk.StringVar(),
        "department_asset_tag": tk.StringVar(),
        "specification_os": tk.StringVar(),
        "facility_site": tk.StringVar(),
        "district": tk.StringVar(),
        "section_department": tk.StringVar(),
        "room_location": tk.StringVar(),
        "purchase_date": tk.StringVar(),
        "purchase_cost_r": tk.StringVar(),
        "supplier": tk.StringVar(),
        "warranty_expiry": tk.StringVar(),
        "useful_life_years": tk.StringVar(
            value=str(
                DEFAULT_USEFUL_LIFE_YEARS
            )
        ),
        "assigned_user": tk.StringVar(),
        "condition": tk.StringVar(value="Good"),
        "status": tk.StringVar(value="In Use"),
        "warranty_status": tk.StringVar(),
        "recommendation": tk.StringVar(),
    }

    assignable_users = (
        list_assignable_users()
    )

    employee_option_var = (
        tk.StringVar()
    )

    employee_option_map = {}

    for user in assignable_users:
        display = (
            f"{user['full_name']} "
            f"({user['username']}) - "
            f"{user['role']}"
        )

        employee_option_map[
            display
        ] = user

    def add_entry(tab, label, variable, row, column_group=0):
        base_column = column_group * 2

        tk.Label(
            tab,
            text=label,
            bg=CARD_BG,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).grid(
            row=row,
            column=base_column,
            sticky="w",
            padx=(20, 10),
            pady=10,
        )

        entry = ttk.Entry(
            tab,
            textvariable=variable,
        )
        entry.grid(
            row=row,
            column=base_column + 1,
            sticky="ew",
            padx=(0, 20),
            pady=10,
        )

        tab.columnconfigure(
            base_column + 1,
            weight=1,
        )

        return entry

    def add_date_entry(
        tab,
        label,
        variable,
        row,
        column_group=0,
        maximum_date=None,
        minimum_date=None,
    ):
        base_column = column_group * 2

        tk.Label(
            tab,
            text=label,
            bg=CARD_BG,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).grid(
            row=row,
            column=base_column,
            sticky="w",
            padx=(20, 10),
            pady=10,
        )

        picker_field = create_date_picker_field(
            parent=tab,
            variable=variable,
            picker_parent=window,
            title=f"Select {label}",
            maximum_date=maximum_date,
            minimum_date=minimum_date,
        )

        picker_field.grid(
            row=row,
            column=base_column + 1,
            sticky="ew",
            padx=(0, 20),
            pady=10,
        )

        tab.columnconfigure(
            base_column + 1,
            weight=1,
        )

        return picker_field

    add_entry(
        identity_tab,
        "Asset ID (optional)",
        variables["asset_id"],
        0,
        0,
    )
    asset_type_entry = add_entry(
        identity_tab,
        "Asset Type *",
        variables["asset_type"],
        0,
        1,
    )
    add_entry(
        identity_tab,
        "Category",
        variables["category"],
        1,
        0,
    )
    add_entry(
        identity_tab,
        "Make",
        variables["make"],
        1,
        1,
    )
    add_entry(
        identity_tab,
        "Model",
        variables["model"],
        2,
        0,
    )
    add_entry(
        identity_tab,
        "Serial Number",
        variables["serial_number"],
        2,
        1,
    )
    add_entry(
        identity_tab,
        "Department Asset Tag",
        variables["department_asset_tag"],
        3,
        0,
    )
    add_entry(
        identity_tab,
        "Specification / OS",
        variables["specification_os"],
        3,
        1,
    )

    add_entry(
        location_tab,
        "Facility / Site",
        variables["facility_site"],
        0,
        0,
    )
    add_entry(
        location_tab,
        "District",
        variables["district"],
        0,
        1,
    )
    add_entry(
        location_tab,
        "Section / Department",
        variables["section_department"],
        1,
        0,
    )
    add_entry(
        location_tab,
        "Room / Location",
        variables["room_location"],
        1,
        1,
    )
    add_date_entry(
        location_tab,
        "Purchase Date",
        variables["purchase_date"],
        2,
        0,
        maximum_date=date.today(),
    )
    add_entry(
        location_tab,
        "Purchase Cost (R)",
        variables["purchase_cost_r"],
        2,
        1,
    )
    add_entry(
        location_tab,
        "Supplier",
        variables["supplier"],
        3,
        0,
    )
    add_date_entry(
        location_tab,
        "Warranty Expiry",
        variables["warranty_expiry"],
        3,
        1,
    )
    add_entry(
        location_tab,
        "Useful Life (Years)",
        variables["useful_life_years"],
        4,
        0,
    )

    tk.Label(
        location_tab,
        text=(
            "Asset age, accumulated depreciation and current book value "
            "are calculated automatically from Purchase Date and Purchase Cost."
        ),
        bg=CARD_BG,
        fg=MUTED,
        font=(
            "Segoe UI",
            8,
        ),
        wraplength=650,
        justify="left",
    ).grid(
        row=5,
        column=0,
        columnspan=4,
        sticky="w",
        padx=20,
        pady=(
            4,
            10,
        ),
    )

    tk.Label(
        management_tab,
        text="Assigned Employee Account",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 9, "bold"),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=(20, 10),
        pady=10,
    )

    employee_combo = ttk.Combobox(
        management_tab,
        textvariable=employee_option_var,
        values=tuple(
            employee_option_map.keys()
        ),
        state="readonly",
    )

    employee_combo.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(0, 20),
        pady=10,
    )

    tk.Label(
        management_tab,
        text="Condition",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 9, "bold"),
    ).grid(
        row=0,
        column=2,
        sticky="w",
        padx=(20, 10),
        pady=10,
    )

    condition_combo = ttk.Combobox(
        management_tab,
        textvariable=variables["condition"],
        values=(
            "Excellent",
            "Good",
            "Fair",
            "Poor",
            "Damaged",
            "Unserviceable",
        ),
        state="readonly",
    )
    condition_combo.grid(
        row=0,
        column=3,
        sticky="ew",
        padx=(0, 20),
        pady=10,
    )

    tk.Label(
        management_tab,
        text="Status",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 9, "bold"),
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=(20, 10),
        pady=10,
    )

    status_combo = ttk.Combobox(
        management_tab,
        textvariable=variables["status"],
        values=(
            "In Use",
            "In Storage",
            "Under Repair",
            "Transferred",
            "Lost",
            "Stolen",
            "Disposed",
        ),
        state="readonly",
    )
    status_combo.grid(
        row=1,
        column=1,
        sticky="ew",
        padx=(0, 20),
        pady=10,
    )

    tk.Label(
        management_tab,
        text="Warranty Status",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
    ).grid(
        row=1,
        column=2,
        sticky="w",
        padx=(
            20,
            10,
        ),
        pady=10,
    )

    warranty_status_label = tk.Label(
        management_tab,
        textvariable=(
            variables[
                "warranty_status"
            ]
        ),
        bg=LIGHT_BLUE,
        fg=ACCENT_DARK,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        anchor="w",
        padx=10,
        pady=6,
    )

    warranty_status_label.grid(
        row=1,
        column=3,
        sticky="ew",
        padx=(
            0,
            20,
        ),
        pady=10,
    )
    add_entry(
        management_tab,
        "Recommendation",
        variables["recommendation"],
        2,
        0,
    )

    tk.Label(
        management_tab,
        text="Notes",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 9, "bold"),
    ).grid(
        row=3,
        column=0,
        sticky="nw",
        padx=(20, 10),
        pady=10,
    )

    notes_text = tk.Text(
        management_tab,
        height=8,
        wrap="word",
        font=("Segoe UI", 9),
        bd=1,
        relief="solid",
    )
    notes_text.grid(
        row=3,
        column=1,
        columnspan=3,
        sticky="nsew",
        padx=(0, 20),
        pady=10,
    )

    management_tab.columnconfigure(1, weight=1)
    management_tab.columnconfigure(3, weight=1)
    management_tab.rowconfigure(3, weight=1)

    footer = tk.Frame(
        window,
        bg=APP_BG,
    )
    footer.pack(
        fill="x",
        padx=20,
        pady=(0, 18),
    )

    def save_new_asset():
        try:
            asset_data = {
                name: variable.get()
                for name, variable
                in variables.items()
            }

            asset_data["notes"] = (
                notes_text
                .get("1.0", "end")
                .strip()
            )

            selected_employee = (
                employee_option_var
                .get()
            )

            if selected_employee:
                linked_user = (
                    employee_option_map[
                        selected_employee
                    ]
                )

                asset_data[
                    "assigned_user"
                ] = linked_user[
                    "full_name"
                ]

                asset_data[
                    "assigned_user_account_id"
                ] = linked_user[
                    "id"
                ]
            else:
                asset_data[
                    "assigned_user"
                ] = ""

                asset_data[
                    "assigned_user_account_id"
                ] = None

            new_asset_id = create_manual_asset(
                asset_data,
                performed_by=current_actor(),
            )

            reload_assets()
            window.destroy()

            status_text.set(
                f"New asset {new_asset_id} created"
            )

            messagebox.showinfo(
                "Asset Created",
                (
                    f"Asset {new_asset_id} was created successfully.\n\n"
                    "The creation has also been recorded in Audit History."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Unable to Create Asset",
                str(error),
                parent=window,
            )

    save_button = tk.Button(
        footer,
        text="Save New Asset",
        command=save_new_asset,
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_DARK,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=9,
    )
    save_button.pack(
        side="right",
        padx=5,
    )

    cancel_button = tk.Button(
        footer,
        text="Cancel",
        command=window.destroy,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 9, "bold"),
        padx=18,
        pady=9,
    )
    cancel_button.pack(
        side="right",
        padx=5,
    )

    asset_type_entry.focus_set()



# ============================================================
# LINK EXISTING ASSIGNMENTS
# ============================================================

def open_link_assignments():
    if not require_editor_access():
        return

    window = tk.Toplevel(
        root
    )

    window.title(
        "Link Existing Asset Assignments"
    )

    set_window_size(
        window,
        1000,
        610,
        820,
        520,
    )

    window.configure(
        bg=APP_BG
    )

    window.transient(
        root
    )

    window.grab_set()

    header = tk.Frame(
        window,
        bg=SIDEBAR_BG,
        height=100,
    )

    header.pack(
        fill="x"
    )

    header.pack_propagate(
        False
    )

    tk.Label(
        header,
        text="Link Existing Assignments",
        bg=SIDEBAR_BG,
        fg="white",
        font=(
            "Segoe UI",
            19,
            "bold",
        ),
    ).pack(
        anchor="w",
        padx=24,
        pady=(
            15,
            1,
        ),
    )

    tk.Label(
        header,
        text=(
            "Connect existing Assigned User names to login accounts "
            "so employees can see their assets in My Assets."
        ),
        bg=SIDEBAR_BG,
        fg="#D8E7F3",
        font=(
            "Segoe UI",
            9,
        ),
    ).pack(
        anchor="w",
        padx=24,
    )

    content = tk.Frame(
        window,
        bg=CARD_BG,
    )

    content.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20,
    )

    top = tk.Frame(
        content,
        bg=CARD_BG,
    )

    top.pack(
        fill="x",
        padx=16,
        pady=(
            16,
            10,
        ),
    )

    tk.Label(
        top,
        text="Employee Account",
        bg=CARD_BG,
        fg=TEXT,
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
    ).pack(
        side="left",
        padx=(
            0,
            10,
        ),
    )

    selected_employee = (
        tk.StringVar()
    )

    user_map = {}

    def refresh_user_options():
        user_map.clear()

        for user in list_assignable_users():
            display = (
                f"{user['full_name']} "
                f"({user['username']}) - "
                f"{user['role']}"
            )

            user_map[
                display
            ] = user

        employee_combo.configure(
            values=tuple(
                user_map.keys()
            )
        )

    employee_combo = ttk.Combobox(
        top,
        textvariable=selected_employee,
        state="readonly",
        width=48,
    )

    employee_combo.pack(
        side="left",
        padx=5,
    )

    table_frame = tk.Frame(
        content,
        bg=CARD_BG,
    )

    table_frame.pack(
        fill="both",
        expand=True,
        padx=16,
        pady=10,
    )

    columns = (
        "asset_id",
        "asset_type",
        "assigned_user",
        "linked_account",
        "facility",
    )

    link_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
    )

    headings = {
        "asset_id": "Asset ID",
        "asset_type": "Asset Type",
        "assigned_user": "Assigned User",
        "linked_account": "Linked Login Account",
        "facility": "Facility",
    }

    widths = {
        "asset_id": 140,
        "asset_type": 140,
        "assigned_user": 190,
        "linked_account": 240,
        "facility": 240,
    }

    for column in columns:
        link_tree.heading(
            column,
            text=headings[
                column
            ],
        )

        link_tree.column(
            column,
            width=widths[
                column
            ],
        )

    vertical = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=link_tree.yview,
    )

    horizontal = ttk.Scrollbar(
        table_frame,
        orient="horizontal",
        command=link_tree.xview,
    )

    link_tree.configure(
        yscrollcommand=vertical.set,
        xscrollcommand=horizontal.set,
    )

    link_tree.grid(
        row=0,
        column=0,
        sticky="nsew",
    )

    vertical.grid(
        row=0,
        column=1,
        sticky="ns",
    )

    horizontal.grid(
        row=1,
        column=0,
        sticky="ew",
    )

    table_frame.rowconfigure(
        0,
        weight=1,
    )

    table_frame.columnconfigure(
        0,
        weight=1,
    )

    def refresh_link_table():
        refresh_assets_from_database()
        refresh_user_options()

        for item in link_tree.get_children():
            link_tree.delete(
                item
            )

        users_by_id = {
            int(user["id"]): user
            for user in list_assignable_users()
        }

        for asset in assets:
            account_id = asset.get(
                "assigned_user_account_id"
            )

            linked_text = "Not linked"

            if account_id not in (
                None,
                "",
            ):
                try:
                    linked_user = (
                        users_by_id.get(
                            int(
                                account_id
                            )
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    linked_user = None

                if linked_user:
                    linked_text = (
                        f"{linked_user['full_name']} "
                        f"({linked_user['username']})"
                    )
                else:
                    linked_text = (
                        f"Account ID {account_id}"
                    )

            facility = (
                clean_value(
                    asset.get(
                        "operational_facility"
                    )
                )
                or clean_value(
                    asset.get(
                        "facility_site"
                    )
                )
            )

            link_tree.insert(
                "",
                "end",
                values=(
                    clean_value(
                        asset.get(
                            "asset_id"
                        )
                    ),
                    clean_value(
                        asset.get(
                            "asset_type"
                        )
                    ),
                    clean_value(
                        asset.get(
                            "assigned_user"
                        )
                    ),
                    linked_text,
                    facility,
                ),
            )

    def selected_asset_id():
        selection = (
            link_tree.selection()
        )

        if not selection:
            messagebox.showwarning(
                "No Asset Selected",
                "Please select an asset first.",
                parent=window,
            )

            return None

        values = link_tree.item(
            selection[0]
        ).get(
            "values",
            [],
        )

        if not values:
            return None

        return clean_value(
            values[0]
        )

    def link_selected():
        asset_id = (
            selected_asset_id()
        )

        if not asset_id:
            return

        display = (
            selected_employee
            .get()
        )

        if not display:
            messagebox.showwarning(
                "No Employee Selected",
                (
                    "Please choose the employee "
                    "login account to link."
                ),
                parent=window,
            )

            return

        try:
            user = user_map[
                display
            ]

            link_asset_to_user(
                corporate_asset_id=(
                    asset_id
                ),
                user_id=user[
                    "id"
                ],
                performed_by=(
                    current_actor()
                ),
                notes=(
                    "Linked from the "
                    "assignment reconciliation screen."
                ),
            )

            reload_assets()
            refresh_link_table()

            messagebox.showinfo(
                "Assignment Linked",
                (
                    f"Asset {asset_id} is now linked to "
                    f"{user['full_name']}."
                ),
                parent=window,
            )

        except Exception as error:
            messagebox.showerror(
                "Link Error",
                str(error),
                parent=window,
            )

    def unlink_selected():
        asset_id = (
            selected_asset_id()
        )

        if not asset_id:
            return

        if not messagebox.askyesno(
            "Remove Account Link",
            (
                f"Remove the login-account link from "
                f"asset {asset_id}?\n\n"
                "The Assigned User text will be retained."
            ),
            parent=window,
        ):
            return

        try:
            unlink_asset_from_user(
                corporate_asset_id=(
                    asset_id
                ),
                performed_by=(
                    current_actor()
                ),
                notes=(
                    "Account link removed from the "
                    "assignment reconciliation screen."
                ),
            )

            reload_assets()
            refresh_link_table()

        except Exception as error:
            messagebox.showerror(
                "Unlink Error",
                str(error),
                parent=window,
            )

    def auto_link():
        if not messagebox.askyesno(
            "Auto-Link Assignments",
            (
                "Automatically link assets where the existing "
                "Assigned User name exactly matches one unique "
                "active user account?"
            ),
            parent=window,
        ):
            return

        try:
            result = (
                auto_link_existing_assignments(
                    current_actor()
                )
            )

            reload_assets()
            refresh_link_table()

            messagebox.showinfo(
                "Auto-Link Complete",
                (
                    f"Linked: {result['linked']}\n"
                    f"Ambiguous: {result['ambiguous']}\n"
                    f"Unmatched: {result['unmatched']}"
                ),
                parent=window,
            )

        except Exception as error:
            messagebox.showerror(
                "Auto-Link Error",
                str(error),
                parent=window,
            )

    footer = tk.Frame(
        content,
        bg=CARD_BG,
    )

    footer.pack(
        fill="x",
        padx=16,
        pady=(
            0,
            16,
        ),
    )

    tk.Button(
        footer,
        text="Link Selected",
        command=link_selected,
        bg=SUCCESS,
        fg="white",
        activebackground="#236428",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=14,
        pady=8,
    ).pack(
        side="left",
        padx=4,
    )

    tk.Button(
        footer,
        text="Auto-Link Exact Name Matches",
        command=auto_link,
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_DARK,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=14,
        pady=8,
    ).pack(
        side="left",
        padx=4,
    )

    tk.Button(
        footer,
        text="Remove Link",
        command=unlink_selected,
        bg=WARNING,
        fg="white",
        activebackground=WARNING,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=14,
        pady=8,
    ).pack(
        side="left",
        padx=4,
    )

    tk.Button(
        footer,
        text="Close",
        command=window.destroy,
        bg="#E7EDF3",
        fg=TEXT,
        activebackground="#D8E1EA",
        activeforeground=TEXT,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(
            "Segoe UI",
            9,
            "bold",
        ),
        padx=14,
        pady=8,
    ).pack(
        side="right",
        padx=4,
    )

    refresh_link_table()


# ============================================================
# USER MANAGEMENT
# ============================================================

def open_manage_users():
    if not require_admin_access():
        return

    window = tk.Toplevel(root)
    window.title("User Management")
    set_window_size(
        window,
        850,
        540,
        760,
        480,
    )
    window.configure(bg=APP_BG)
    window.transient(root)
    window.grab_set()

    header = tk.Frame(
        window,
        bg=SIDEBAR_BG,
        height=88,
    )
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text="User Management",
        bg=SIDEBAR_BG,
        fg="white",
        font=("Segoe UI", 19, "bold"),
    ).pack(
        anchor="w",
        padx=22,
        pady=(15, 1),
    )

    tk.Label(
        header,
        text="Create accounts, reset passwords and control access.",
        bg=SIDEBAR_BG,
        fg="#D8E7F3",
        font=("Segoe UI", 9),
    ).pack(
        anchor="w",
        padx=22,
    )

    table_frame = tk.Frame(
        window,
        bg=CARD_BG,
    )
    table_frame.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=18,
    )

    columns = (
        "id",
        "username",
        "full_name",
        "role",
        "active",
        "last_login",
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
    )

    headings = {
        "id": "ID",
        "username": "Username",
        "full_name": "Full Name",
        "role": "Role",
        "active": "Active",
        "last_login": "Last Login",
    }

    widths = {
        "id": 55,
        "username": 150,
        "full_name": 220,
        "role": 130,
        "active": 80,
        "last_login": 170,
    }

    for column in columns:
        tree.heading(
            column,
            text=headings[column],
        )
        tree.column(
            column,
            width=widths[column],
        )

    vertical = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview,
    )
    tree.configure(
        yscrollcommand=vertical.set
    )

    tree.grid(
        row=0,
        column=0,
        sticky="nsew",
    )
    vertical.grid(
        row=0,
        column=1,
        sticky="ns",
    )

    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    def refresh_users():
        for item in tree.get_children():
            tree.delete(item)

        for user in list_users():
            tree.insert(
                "",
                "end",
                values=(
                    user["id"],
                    user["username"],
                    user["full_name"],
                    user["role"],
                    "Yes" if user["active"] else "No",
                    user["last_login_at"] or "Never",
                ),
            )

    def selected_user():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning(
                "Select User",
                "Please select a user account first.",
                parent=window,
            )
            return None

        values = tree.item(
            selection[0]
        )["values"]

        return {
            "id": int(values[0]),
            "username": str(values[1]),
            "full_name": str(values[2]),
            "role": str(values[3]),
            "active": str(values[4]) == "Yes",
        }

    def add_user_dialog():
        dialog = tk.Toplevel(window)
        dialog.title("Create User")
        set_window_size(
            dialog,
            480,
            400,
            440,
            360,
        )
        dialog.configure(bg=CARD_BG)
        dialog.transient(window)
        dialog.grab_set()

        username_var = tk.StringVar()
        full_name_var = tk.StringVar()
        role_var = tk.StringVar(value="IT Officer")
        password_var = tk.StringVar()
        confirm_var = tk.StringVar()

        fields = [
            ("Username", username_var, False),
            ("Full Name", full_name_var, False),
            ("Password", password_var, True),
            ("Confirm Password", confirm_var, True),
        ]

        tk.Label(
            dialog,
            text="Create User Account",
            bg=CARD_BG,
            fg=TEXT,
            font=("Segoe UI", 16, "bold"),
        ).pack(
            anchor="w",
            padx=24,
            pady=(22, 12),
        )

        form = tk.Frame(
            dialog,
            bg=CARD_BG,
        )
        form.pack(
            fill="both",
            expand=True,
            padx=24,
        )

        for row, (label, variable, password_field) in enumerate(fields):
            tk.Label(
                form,
                text=label,
                bg=CARD_BG,
                fg=TEXT,
                font=("Segoe UI", 9, "bold"),
            ).grid(
                row=row,
                column=0,
                sticky="w",
                pady=8,
            )

            entry = ttk.Entry(
                form,
                textvariable=variable,
                show="*" if password_field else "",
            )
            entry.grid(
                row=row,
                column=1,
                sticky="ew",
                padx=(14, 0),
                pady=8,
            )

        tk.Label(
            form,
            text="Role",
            bg=CARD_BG,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=8,
        )

        ttk.Combobox(
            form,
            textvariable=role_var,
            values=USER_ROLES,
            state="readonly",
        ).grid(
            row=4,
            column=1,
            sticky="ew",
            padx=(14, 0),
            pady=8,
        )

        form.columnconfigure(1, weight=1)

        def save_user():
            if password_var.get() != confirm_var.get():
                messagebox.showerror(
                    "Password Error",
                    "The passwords do not match.",
                    parent=dialog,
                )
                return

            try:
                create_user(
                    username=username_var.get(),
                    password=password_var.get(),
                    full_name=full_name_var.get(),
                    role=role_var.get(),
                    performed_by_user_id=current_user["id"],
                )
                dialog.destroy()
                refresh_users()

                messagebox.showinfo(
                    "User Created",
                    "The user account was created successfully.",
                    parent=window,
                )

            except Exception as error:
                messagebox.showerror(
                    "Unable to Create User",
                    str(error),
                    parent=dialog,
                )

        tk.Button(
            dialog,
            text="Create User",
            command=save_user,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_DARK,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=18,
            pady=9,
        ).pack(
            side="right",
            padx=24,
            pady=18,
        )

    def toggle_active():
        user = selected_user()
        if user is None:
            return

        if user["id"] == current_user["id"] and user["active"]:
            messagebox.showwarning(
                "Current Account",
                "You cannot deactivate the account you are currently using.",
                parent=window,
            )
            return

        try:
            set_user_active(
                user["id"],
                not user["active"],
                performed_by_user_id=current_user["id"],
            )
            refresh_users()
        except Exception as error:
            messagebox.showerror(
                "User Update Error",
                str(error),
                parent=window,
            )

    def reset_password_dialog():
        user = selected_user()
        if user is None:
            return

        dialog = tk.Toplevel(window)
        dialog.title("Reset Password")
        set_window_size(
            dialog,
            430,
            260,
            400,
            240,
        )
        dialog.configure(bg=CARD_BG)
        dialog.transient(window)
        dialog.grab_set()

        new_password = tk.StringVar()
        confirm_password = tk.StringVar()

        tk.Label(
            dialog,
            text=f"Reset Password: {user['username']}",
            bg=CARD_BG,
            fg=TEXT,
            font=("Segoe UI", 14, "bold"),
        ).pack(
            anchor="w",
            padx=24,
            pady=(22, 14),
        )

        form = tk.Frame(
            dialog,
            bg=CARD_BG,
        )
        form.pack(
            fill="x",
            padx=24,
        )

        for row, (label, variable) in enumerate(
            (
                ("New Password", new_password),
                ("Confirm Password", confirm_password),
            )
        ):
            tk.Label(
                form,
                text=label,
                bg=CARD_BG,
                fg=TEXT,
                font=("Segoe UI", 9, "bold"),
            ).grid(
                row=row,
                column=0,
                sticky="w",
                pady=8,
            )

            ttk.Entry(
                form,
                textvariable=variable,
                show="*",
            ).grid(
                row=row,
                column=1,
                sticky="ew",
                padx=(14, 0),
                pady=8,
            )

        form.columnconfigure(1, weight=1)

        def save_password():
            if new_password.get() != confirm_password.get():
                messagebox.showerror(
                    "Password Error",
                    "The passwords do not match.",
                    parent=dialog,
                )
                return

            try:
                reset_user_password(
                    user["id"],
                    new_password.get(),
                    performed_by_user_id=current_user["id"],
                )
                dialog.destroy()
                messagebox.showinfo(
                    "Password Reset",
                    "The password was reset successfully.",
                    parent=window,
                )
            except Exception as error:
                messagebox.showerror(
                    "Password Reset Error",
                    str(error),
                    parent=dialog,
                )

        tk.Button(
            dialog,
            text="Reset Password",
            command=save_password,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_DARK,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=18,
            pady=9,
        ).pack(
            side="right",
            padx=24,
            pady=18,
        )

    footer = tk.Frame(
        window,
        bg=APP_BG,
    )
    footer.pack(
        fill="x",
        padx=18,
        pady=(0, 16),
    )

    for label, command, color in (
        ("Add User", add_user_dialog, ACCENT),
        ("Reset Password", reset_password_dialog, SIDEBAR_HOVER),
        ("Activate / Deactivate", toggle_active, WARNING),
    ):
        tk.Button(
            footer,
            text=label,
            command=command,
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=8,
        ).pack(
            side="left",
            padx=4,
        )

    refresh_users()


# ============================================================
# LOGIN / LOGOUT
# ============================================================

def apply_role_permissions():
    role = current_user.get(
        "role"
    )

    editor_state = (
        "normal"
        if role in {
            "Administrator",
            "IT Officer",
        }
        else "disabled"
    )

    verify_state = (
        "normal"
        if role in {
            "Administrator",
            "IT Officer",
            "Employee",
        }
        else "disabled"
    )

    general_reporting_state = (
        "disabled"
        if role == "Employee"
        else "normal"
    )

    import_nav_button.configure(
        state=editor_state
    )

    add_asset_nav_button.configure(
        state=editor_state
    )

    add_asset_header_button.configure(
        state=editor_state
    )

    actions_nav_button.configure(
        state=editor_state
    )

    link_assignments_nav_button.configure(
        state=editor_state
    )

    verify_nav_button.configure(
        state=verify_state
    )

    duplicate_nav_button.configure(
        state=general_reporting_state
    )

    export_nav_button.configure(
        state=general_reporting_state
    )

    admin_state = (
        "normal"
        if role == "Administrator"
        else "disabled"
    )

    users_nav_button.configure(
        state=admin_state
    )

    all_navigation_buttons = [
        dashboard_nav_button,
        add_asset_nav_button,
        import_nav_button,
        details_nav_button,
        actions_nav_button,
        link_assignments_nav_button,
        verify_nav_button,
        history_nav_button,
        duplicate_nav_button,
        export_nav_button,
        users_nav_button,
    ]

    for navigation_button in all_navigation_buttons:
        navigation_button.pack_forget()

    if role == "Employee":
        dashboard_nav_button.configure(
            text="My Assets"
        )

        verify_nav_button.configure(
            text="Verify My Asset"
        )

        dashboard_title_label.configure(
            text="My IT Assets"
        )

        dashboard_subtitle_label.configure(
            text=(
                "View and verify the IT assets "
                "assigned to your account."
            )
        )

        visible_buttons = [
            dashboard_nav_button,
            details_nav_button,
            verify_nav_button,
            history_nav_button,
        ]

    elif role == "Viewer":
        dashboard_nav_button.configure(
            text="Dashboard / View All"
        )

        verify_nav_button.configure(
            text="Verify Asset"
        )

        dashboard_title_label.configure(
            text="IT Asset Dashboard"
        )

        dashboard_subtitle_label.configure(
            text=(
                "View IT asset information "
                "and audit history."
            )
        )

        visible_buttons = [
            dashboard_nav_button,
            details_nav_button,
            history_nav_button,
            duplicate_nav_button,
            export_nav_button,
        ]

    else:
        dashboard_nav_button.configure(
            text="Dashboard / View All"
        )

        verify_nav_button.configure(
            text="Verify Asset"
        )

        dashboard_title_label.configure(
            text="IT Asset Dashboard"
        )

        dashboard_subtitle_label.configure(
            text=(
                "Manage, verify and audit IT assets "
                "from one workspace."
            )
        )

        visible_buttons = [
            dashboard_nav_button,
            add_asset_nav_button,
            import_nav_button,
            details_nav_button,
            actions_nav_button,
            link_assignments_nav_button,
            verify_nav_button,
            history_nav_button,
            duplicate_nav_button,
            export_nav_button,
        ]

        if role == "Administrator":
            visible_buttons.append(
                users_nav_button
            )

    for navigation_button in visible_buttons:
        navigation_button.pack(
            fill="x",
            pady=1,
        )

def finish_login(user):
    current_user.clear()
    current_user.update(user)

    logged_in_name.set(
        user["full_name"]
    )
    logged_in_role.set(
        user["role"]
    )

    user_name_label.configure(
        text=user["full_name"]
    )
    user_role_label.configure(
        text=user["role"]
    )

    apply_role_permissions()
    reload_assets()

    root.deiconify()
    root.lift()

    status_text.set(
        f"Signed in as {user['full_name']} ({user['role']})"
    )


def show_login_window():
    root.withdraw()

    login = tk.Toplevel(root)
    login.title("Sign In - IT Asset Management System")
    set_window_size(
        login,
        480,
        480,
        460,
        460,
    )
    login.resizable(False, False)
    login.configure(bg=APP_BG)
    login.protocol(
        "WM_DELETE_WINDOW",
        root.destroy,
    )

    card = tk.Frame(
        login,
        bg=CARD_BG,
    )
    card.pack(
        fill="both",
        expand=True,
        padx=35,
        pady=35,
    )

    tk.Label(
        card,
        text="IT",
        bg=SIDEBAR_BG,
        fg="white",
        font=("Segoe UI", 24, "bold"),
        width=4,
        height=2,
    ).pack(
        pady=(28, 12),
    )

    tk.Label(
        card,
        text="Welcome Back",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 20, "bold"),
    ).pack()

    tk.Label(
        card,
        text="Sign in to the IT Asset Management System",
        bg=CARD_BG,
        fg=MUTED,
        font=("Segoe UI", 9),
    ).pack(
        pady=(4, 22),
    )

    username_var = tk.StringVar()
    password_var = tk.StringVar()

    form = tk.Frame(
        card,
        bg=CARD_BG,
    )
    form.pack(
        fill="x",
        padx=32,
    )

    tk.Label(
        form,
        text="Username",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 9, "bold"),
    ).pack(
        anchor="w",
        pady=(0, 5),
    )

    username_entry = ttk.Entry(
        form,
        textvariable=username_var,
    )
    username_entry.pack(
        fill="x",
        pady=(0, 14),
    )

    tk.Label(
        form,
        text="Password",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 9, "bold"),
    ).pack(
        anchor="w",
        pady=(0, 5),
    )

    password_entry = ttk.Entry(
        form,
        textvariable=password_var,
        show="*",
    )
    password_entry.pack(
        fill="x",
        pady=(0, 18),
    )

    def attempt_login():
        user = authenticate_user(
            username_var.get(),
            password_var.get(),
        )

        if user is None:
            messagebox.showerror(
                "Sign In Failed",
                (
                    "The username or password is incorrect, "
                    "or the account is inactive."
                ),
                parent=login,
            )
            password_var.set("")
            password_entry.focus_set()
            return

        login.destroy()
        finish_login(user)

    tk.Button(
        form,
        text="Sign In",
        command=attempt_login,
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_DARK,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        pady=10,
    ).pack(
        fill="x",
    )

    username_entry.bind(
        "<Return>",
        lambda event: password_entry.focus_set(),
    )
    password_entry.bind(
        "<Return>",
        lambda event: attempt_login(),
    )

    login.update_idletasks()
    width = 480
    height = 480
    x = (
        login.winfo_screenwidth()
        - width
    ) // 2
    y = (
        login.winfo_screenheight()
        - height
    ) // 2
    login.geometry(
        f"{width}x{height}+{x}+{y}"
    )

    username_entry.focus_set()


def show_first_run_admin_setup():
    setup = tk.Toplevel(root)
    setup.title("Create Administrator Account")
    set_window_size(
        setup,
        520,
        560,
        500,
        520,
    )
    setup.resizable(False, False)
    setup.configure(bg=APP_BG)
    setup.protocol(
        "WM_DELETE_WINDOW",
        root.destroy,
    )

    card = tk.Frame(
        setup,
        bg=CARD_BG,
    )
    card.pack(
        fill="both",
        expand=True,
        padx=34,
        pady=34,
    )

    tk.Label(
        card,
        text="First-Time Setup",
        bg=CARD_BG,
        fg=TEXT,
        font=("Segoe UI", 20, "bold"),
    ).pack(
        anchor="w",
        padx=30,
        pady=(30, 4),
    )

    tk.Label(
        card,
        text=(
            "Create the first Administrator account. "
            "No default password is stored in the application."
        ),
        bg=CARD_BG,
        fg=MUTED,
        justify="left",
        wraplength=410,
        font=("Segoe UI", 9),
    ).pack(
        anchor="w",
        padx=30,
        pady=(0, 22),
    )

    username_var = tk.StringVar()
    full_name_var = tk.StringVar()
    password_var = tk.StringVar()
    confirm_var = tk.StringVar()

    form = tk.Frame(
        card,
        bg=CARD_BG,
    )
    form.pack(
        fill="x",
        padx=30,
    )

    fields = (
        ("Username", username_var, False),
        ("Full Name", full_name_var, False),
        ("Password", password_var, True),
        ("Confirm Password", confirm_var, True),
    )

    first_entry = None

    for row, (label, variable, is_password) in enumerate(fields):
        tk.Label(
            form,
            text=label,
            bg=CARD_BG,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=9,
        )

        entry = ttk.Entry(
            form,
            textvariable=variable,
            show="*" if is_password else "",
        )
        entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(14, 0),
            pady=9,
        )

        if first_entry is None:
            first_entry = entry

    form.columnconfigure(1, weight=1)

    tk.Label(
        card,
        text=(
            "Password requirement: at least 8 characters."
        ),
        bg=CARD_BG,
        fg=MUTED,
        font=("Segoe UI", 8),
    ).pack(
        anchor="w",
        padx=30,
        pady=(12, 10),
    )

    def create_admin():
        if password_var.get() != confirm_var.get():
            messagebox.showerror(
                "Password Error",
                "The passwords do not match.",
                parent=setup,
            )
            return

        try:
            user = create_user(
                username=username_var.get(),
                password=password_var.get(),
                full_name=full_name_var.get(),
                role="Administrator",
            )

            setup.destroy()
            finish_login(user)

            messagebox.showinfo(
                "Administrator Created",
                (
                    "Your Administrator account has been created.\n\n"
                    "You are now signed in."
                ),
            )

        except Exception as error:
            messagebox.showerror(
                "Setup Error",
                str(error),
                parent=setup,
            )

    tk.Button(
        card,
        text="Create Administrator",
        command=create_admin,
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_DARK,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        pady=10,
    ).pack(
        fill="x",
        padx=30,
        pady=(8, 28),
    )

    setup.update_idletasks()
    width = 520
    height = 560
    x = (
        setup.winfo_screenwidth()
        - width
    ) // 2
    y = (
        setup.winfo_screenheight()
        - height
    ) // 2
    setup.geometry(
        f"{width}x{height}+{x}+{y}"
    )

    if first_entry:
        first_entry.focus_set()


def logout():
    if not messagebox.askyesno(
        "Sign Out",
        "Are you sure you want to sign out?",
    ):
        return

    current_user.update(
        {
            "id": None,
            "username": "",
            "full_name": "",
            "role": "",
        }
    )

    logged_in_name.set(
        "Not signed in"
    )
    logged_in_role.set("")

    # Close any open asset/detail windows and clear the previous session's
    # visible records before presenting the login dialog.
    for child in root.winfo_children():
        if isinstance(child, tk.Toplevel):
            child.destroy()
    search_text.set("")
    populate_table([])
    root.withdraw()
    show_login_window()


def start_authentication():
    if count_users() == 0:
        show_first_run_admin_setup()
    else:
        show_login_window()


# ============================================================
# MODERN LAYOUT - SIDEBAR
# ============================================================

sidebar = tk.Frame(
    root,
    bg=SIDEBAR_BG,
    width=210,
)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

logo_area = tk.Frame(
    sidebar,
    bg=SIDEBAR_BG,
    height=105,
)
logo_area.pack(fill="x")
logo_area.pack_propagate(False)

logo_box = tk.Label(
    logo_area,
    text="IT",
    bg="white",
    fg=SIDEBAR_BG,
    font=("Segoe UI", 18, "bold"),
    width=3,
    height=1,
)
logo_box.pack(pady=(10, 2))

tk.Label(
    logo_area,
    text="ASSET MANAGEMENT",
    bg=SIDEBAR_BG,
    fg="white",
    font=("Segoe UI", 10, "bold"),
).pack()

tk.Label(
    logo_area,
    text="Operational & Audit System",
    bg=SIDEBAR_BG,
    fg="#BED4E6",
    font=("Segoe UI", 8),
).pack(pady=(2, 0))

navigation = tk.Frame(
    sidebar,
    bg=SIDEBAR_BG,
)
navigation.pack(
    fill="both",
    expand=True,
    padx=12,
    pady=6,
)


def add_nav_button(label, command):
    button = tk.Button(
        navigation,
        text=label,
        command=command,
        anchor="w",
        bg=SIDEBAR_BG,
        fg="white",
        activebackground=SIDEBAR_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 9),
        padx=14,
        pady=7,
    )
    button.pack(
        fill="x",
        pady=1,
    )

    NAV_BUTTONS.append(
        button
    )

    return button


dashboard_nav_button = add_nav_button(
    "Dashboard / View All",
    show_all_assets,
)

add_asset_nav_button = add_nav_button(
    "Add New Asset",
    open_add_asset,
)

import_nav_button = add_nav_button(
    "Import & Synchronise",
    gui_import_assets,
)

details_nav_button = add_nav_button(
    "Asset Details",
    open_asset_details,
)

actions_nav_button = add_nav_button(
    "Asset Actions",
    open_asset_actions,
)

link_assignments_nav_button = add_nav_button(
    "Link Assignments",
    open_link_assignments,
)

verify_nav_button = add_nav_button(
    "Verify Asset",
    open_verify_asset,
)

history_nav_button = add_nav_button(
    "Asset History",
    open_asset_history,
)

duplicate_nav_button = add_nav_button(
    "Check Duplicates",
    gui_check_duplicates,
)

export_nav_button = add_nav_button(
    "Export Audit Report",
    gui_export_report,
)

users_nav_button = add_nav_button(
    "Manage Users",
    open_manage_users,
)

exit_frame = tk.Frame(
    sidebar,
    bg=SIDEBAR_BG,
)
exit_frame.pack(
    side="bottom",
    fill="x",
    padx=12,
    pady=14,
)

tk.Frame(
    exit_frame,
    bg="#2B5878",
    height=1,
).pack(
    fill="x",
    pady=(0, 10),
)

tk.Label(
    exit_frame,
    text="SIGNED IN AS",
    bg=SIDEBAR_BG,
    fg="#8FB2CC",
    font=("Segoe UI", 7, "bold"),
).pack(
    anchor="w",
    padx=4,
)

user_name_label = tk.Label(
    exit_frame,
    text="",
    bg=SIDEBAR_BG,
    fg="white",
    font=("Segoe UI", 9, "bold"),
)
user_name_label.pack(
    anchor="w",
    padx=4,
    pady=(2, 0),
)

user_role_label = tk.Label(
    exit_frame,
    text="",
    bg=SIDEBAR_BG,
    fg="#BED4E6",
    font=("Segoe UI", 8),
)
user_role_label.pack(
    anchor="w",
    padx=4,
    pady=(0, 9),
)

logout_button = tk.Button(
    exit_frame,
    text="Sign Out",
    command=logout,
    bg=SIDEBAR_HOVER,
    fg="white",
    activebackground=ACCENT_DARK,
    activeforeground="white",
    relief="flat",
    bd=0,
    cursor="hand2",
    font=("Segoe UI", 9, "bold"),
    padx=12,
    pady=8,
)
logout_button.pack(
    fill="x",
    pady=(0, 6),
)

exit_button = tk.Button(
    exit_frame,
    text="Exit Application",
    command=root.destroy,
    bg=DANGER,
    fg="white",
    activebackground="#8F1D18",
    activeforeground="white",
    relief="flat",
    bd=0,
    cursor="hand2",
    font=("Segoe UI", 9, "bold"),
    padx=12,
    pady=8,
)
exit_button.pack(fill="x")


# Keep the signed-in user area and Sign Out button pinned
# to the bottom of the sidebar, even on shorter screens.
navigation.pack_forget()
exit_frame.pack_forget()

exit_frame.pack(
    side="bottom",
    fill="x",
    padx=12,
    pady=10,
)

navigation.pack(
    fill="both",
    expand=True,
    padx=12,
    pady=6,
)


# ============================================================
# MODERN LAYOUT - MAIN CONTENT
# ============================================================

main = tk.Frame(root, bg=APP_BG)
main.pack(side="left", fill="both", expand=True)

header = tk.Frame(
    main,
    bg=CARD_BG,
    height=88,
)
header.pack(fill="x")
header.pack_propagate(False)

header_left = tk.Frame(header, bg=CARD_BG)
header_left.pack(side="left", padx=24, pady=14)

dashboard_title_label = tk.Label(
    header_left,
    text="IT Asset Dashboard",
    bg=CARD_BG,
    fg=TEXT,
    font=("Segoe UI", 20, "bold"),
)

dashboard_title_label.pack(
    anchor="w"
)

dashboard_subtitle_label = tk.Label(
    header_left,
    text="Manage, verify and audit IT assets from one workspace.",
    bg=CARD_BG,
    fg=MUTED,
    font=("Segoe UI", 9),
)

dashboard_subtitle_label.pack(
    anchor="w",
    pady=(2, 0),
)

header_right = tk.Frame(
    header,
    bg=CARD_BG,
)
header_right.pack(
    side="right",
    padx=18,
)

zoom_frame = tk.Frame(
    header_right,
    bg=CARD_BG,
)

zoom_frame.pack(
    side="left",
    padx=(
        0,
        12,
    ),
)

zoom_out_button = tk.Button(
    zoom_frame,
    text="-",
    command=zoom_out,
    bg="#E7EDF3",
    fg=TEXT,
    activebackground="#D8E1EA",
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    cursor="hand2",
    font=(
        "Segoe UI",
        10,
        "bold",
    ),
    width=3,
    pady=6,
)

zoom_out_button.pack(
    side="left",
)

zoom_percent_label = tk.Label(
    zoom_frame,
    textvariable=zoom_display,
    bg=CARD_BG,
    fg=TEXT,
    font=(
        "Segoe UI",
        9,
        "bold",
    ),
    width=5,
)

zoom_percent_label.pack(
    side="left",
    padx=4,
)

zoom_in_button = tk.Button(
    zoom_frame,
    text="+",
    command=zoom_in,
    bg="#E7EDF3",
    fg=TEXT,
    activebackground="#D8E1EA",
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    cursor="hand2",
    font=(
        "Segoe UI",
        10,
        "bold",
    ),
    width=3,
    pady=6,
)

zoom_in_button.pack(
    side="left",
)

zoom_fit_button = tk.Button(
    zoom_frame,
    text="Fit",
    command=zoom_fit,
    bg="#E7EDF3",
    fg=TEXT,
    activebackground="#D8E1EA",
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    cursor="hand2",
    font=(
        "Segoe UI",
        8,
        "bold",
    ),
    padx=8,
    pady=6,
)

zoom_fit_button.pack(
    side="left",
    padx=(
        5,
        0,
    ),
)

add_asset_header_button = tk.Button(
    header_right,
    text="+ Add Asset",
    command=open_add_asset,
    bg=SUCCESS,
    fg="white",
    activebackground="#236428",
    activeforeground="white",
    relief="flat",
    bd=0,
    cursor="hand2",
    font=("Segoe UI", 9, "bold"),
    padx=16,
    pady=8,
)
add_asset_header_button.pack(
    side="left",
    padx=(0, 8),
)

refresh_button = tk.Button(
    header_right,
    text="Refresh",
    command=reload_assets,
    bg=ACCENT,
    fg="white",
    activebackground=ACCENT_DARK,
    activeforeground="white",
    relief="flat",
    bd=0,
    cursor="hand2",
    font=("Segoe UI", 9, "bold"),
    padx=18,
    pady=8,
)
refresh_button.pack(
    side="left",
)


# ============================================================
# KPI CARDS
# ============================================================

cards_frame = tk.Frame(main, bg=APP_BG)
cards_frame.pack(fill="x", padx=22, pady=(18, 10))

cards = [
    ("Total Assets", total_value, LIGHT_BLUE, ACCENT),
    ("In Use", in_use_value, LIGHT_GREEN, SUCCESS),
    ("Under Repair", repair_value, LIGHT_ORANGE, WARNING),
    ("Not Yet Verified", unverified_value, LIGHT_RED, DANGER),
    (
        "Current Asset Value",
        current_asset_value_text,
        "#EEF2FF",
        "#4338CA",
    ),
    (
        "In Warranty",
        in_warranty_value,
        LIGHT_GREEN,
        SUCCESS,
    ),
    (
        "Out of Warranty",
        out_warranty_value,
        LIGHT_RED,
        DANGER,
    ),
    (
        "Warranty Date Missing",
        warranty_missing_value,
        LIGHT_ORANGE,
        WARNING,
    ),
]

for index, (label_text, variable, bg_color, fg_color) in enumerate(cards):
    row_number = index // 4
    column_number = index % 4

    card = tk.Frame(
        cards_frame,
        bg=bg_color,
        bd=0,
    )

    card.grid(
        row=row_number,
        column=column_number,
        sticky="nsew",
        padx=6,
        pady=5,
    )

    cards_frame.columnconfigure(
        column_number,
        weight=1,
    )

    tk.Label(
        card,
        textvariable=variable,
        bg=bg_color,
        fg=fg_color,
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w", padx=18, pady=(14, 0))

    tk.Label(
        card,
        text=label_text,
        bg=bg_color,
        fg=TEXT,
        font=("Segoe UI", 9, "bold"),
    ).pack(anchor="w", padx=18, pady=(0, 14))


# ============================================================
# SEARCH BAR
# ============================================================

search_card = tk.Frame(main, bg=CARD_BG)
search_card.pack(fill="x", padx=28, pady=(6, 10))

tk.Label(
    search_card,
    text="Search assets",
    bg=CARD_BG,
    fg=TEXT,
    font=("Segoe UI", 9, "bold"),
).pack(side="left", padx=(16, 8), pady=14)

search_entry = ttk.Entry(
    search_card,
    textvariable=search_text,
    width=48,
)
search_entry.pack(side="left", padx=5, pady=12)

search_button = tk.Button(
    search_card,
    text="Search",
    command=gui_search_asset,
    bg=ACCENT,
    fg="white",
    activebackground=ACCENT_DARK,
    activeforeground="white",
    relief="flat",
    bd=0,
    cursor="hand2",
    font=("Segoe UI", 9, "bold"),
    padx=14,
    pady=7,
)
search_button.pack(side="left", padx=5, pady=8)

clear_button = tk.Button(
    search_card,
    text="Clear",
    command=show_all_assets,
    bg="#E7EDF3",
    fg=TEXT,
    activebackground="#D8E1EA",
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    cursor="hand2",
    font=("Segoe UI", 9, "bold"),
    padx=14,
    pady=7,
)
clear_button.pack(side="left", padx=5, pady=8)

tk.Label(
    search_card,
    text="Asset ID | serial | tag | make | model | facility | user | warranty | status",
    bg=CARD_BG,
    fg=MUTED,
    font=("Segoe UI", 8),
).pack(side="right", padx=16)

search_entry.bind(
    "<Return>",
    lambda event: gui_search_asset(),
)


# ============================================================
# ASSET REGISTER TABLE
# ============================================================

table_card = tk.Frame(main, bg=CARD_BG)
table_card.pack(fill="both", expand=True, padx=28, pady=(0, 16))

table_title_bar = tk.Frame(table_card, bg=CARD_BG)
table_title_bar.pack(fill="x")

tk.Label(
    table_title_bar,
    text="Asset Register",
    bg=CARD_BG,
    fg=TEXT,
    font=("Segoe UI", 12, "bold"),
).pack(side="left", padx=16, pady=14)

tk.Label(
    table_title_bar,
    text="Double-click an asset to open details",
    bg=CARD_BG,
    fg=MUTED,
    font=("Segoe UI", 8),
).pack(side="right", padx=16)

table_frame = tk.Frame(table_card, bg=CARD_BG)
table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

columns = (
    "asset_id",
    "asset_type",
    "make",
    "model",
    "serial_number",
    "facility",
    "assigned_user",
    "condition",
    "warranty",
    "status",
)

asset_table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
)

headings = {
    "asset_id": "Asset ID",
    "asset_type": "Asset Type",
    "make": "Make",
    "model": "Model",
    "serial_number": "Serial Number",
    "facility": "Operational Facility / Site",
    "assigned_user": "Assigned User",
    "condition": "Condition",
    "warranty": "Warranty",
    "status": "Status",
}

widths = {
    "asset_id": 115,
    "asset_type": 120,
    "make": 100,
    "model": 140,
    "serial_number": 155,
    "facility": 220,
    "assigned_user": 160,
    "condition": 100,
    "warranty": 135,
    "status": 110,
}

for column in columns:
    asset_table.heading(column, text=headings[column])
    asset_table.column(column, width=widths[column])

asset_table.tag_configure("even", background="#FFFFFF")
asset_table.tag_configure("odd", background="#F8FAFC")
asset_table.tag_configure("repair", background=LIGHT_ORANGE)
asset_table.tag_configure("alert", background=LIGHT_RED)

vertical_scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=asset_table.yview,
)

horizontal_scrollbar = ttk.Scrollbar(
    table_frame,
    orient="horizontal",
    command=asset_table.xview,
)

asset_table.configure(
    yscrollcommand=vertical_scrollbar.set,
    xscrollcommand=horizontal_scrollbar.set,
)

asset_table.grid(row=0, column=0, sticky="nsew")
vertical_scrollbar.grid(row=0, column=1, sticky="ns")
horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

table_frame.rowconfigure(0, weight=1)
table_frame.columnconfigure(0, weight=1)

asset_table.bind(
    "<Double-1>",
    lambda event: open_asset_details(),
)


# ============================================================
# STATUS BAR
# ============================================================

status_bar = tk.Label(
    main,
    textvariable=status_text,
    bg=SIDEBAR_BG,
    fg="white",
    anchor="w",
    font=("Segoe UI", 8),
    padx=12,
    pady=7,
)
status_bar.pack(fill="x", side="bottom")


# ============================================================
# START APPLICATION
# ============================================================

root.bind(
    "<Control-minus>",
    lambda event: zoom_out(),
)

root.bind(
    "<Control-plus>",
    lambda event: zoom_in(),
)

root.bind(
    "<Control-equal>",
    lambda event: zoom_in(),
)

root.bind(
    "<Control-0>",
    lambda event: zoom_reset(),
)

# Do not preload real asset rows into the UI before authentication.
populate_table([])
start_authentication()
root.mainloop()
