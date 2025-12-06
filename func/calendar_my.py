from datetime import timedelta
import datetime
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.colors as mcolors

from trip_inverval import TripInterval

WEEKS_IN_MONTH = 6
DAYS_IN_WEEK = 7
DAY_LABELS = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]
MONTH_LABELS = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]


def create_hlmap(num_intervals: int) -> Dict[int, Tuple[str, str]]:
    """
    Create a color/label map for the given number of intervals.

    Args:
        num_intervals: Number of trip intervals

    Returns:
        Dictionary mapping index to (color, label) tuples
    """
    # Base colors for first few intervals
    base_colors = [
        ("gainsboro", None),
        ("lightblue", "Вариант 1"),
        ("tomato", "Вариант 2"),
        ("lightgreen", "Вариант 3"),
        ("gold", "Вариант 4"),
        ("violet", "Вариант 5"),
        ("lightcoral", "Вариант 6"),
        ("skyblue", "Вариант 7"),
        ("palegreen", "Вариант 8"),
        ("khaki", "Вариант 9"),
    ]

    hlmap = {}

    for i in range(num_intervals + 1):
        if i < len(base_colors):
            # Use predefined colors for first N intervals
            hlmap[i] = base_colors[i]
        else:
            # Generate colors for additional intervals
            # Use a colormap to generate distinct colors
            cmap = plt.colormaps["tab20c"]
            color_idx = i - len(base_colors)

            color = cmap(color_idx % cmap.N)
            hex_color = mcolors.to_hex(color)

            # Create label
            label = f"Вариант {i}"
            hlmap[i] = (hex_color, label)

    return hlmap


def trip_intervals_to_dataframe(
    trips: List[TripInterval],
) -> Tuple[pd.DataFrame, Dict[int, Tuple[str, str]]]:
    """
    Convert a list of TripInterval objects to a DataFrame with Date, Value, and metadata columns.
    Each trip interval gets a unique value based on its index.

    Args:
        trips: List of TripInterval objects (can be any number)

    Returns:
        Tuple of (DataFrame with columns ['Date', 'Value', 'Label', 'Color'], hlmap dictionary)
    """
    # Create hlmap based on number of trips
    hlmap = create_hlmap(len(trips))

    all_dates = []
    all_values = []

    for idx, trip in enumerate(trips):
        # Get the color and label for this trip index
        trip_value = idx + 1  # Unique value for each trip

        # Generate all dates for this trip (inclusive)
        current_date = trip.departure_date
        while current_date <= trip.return_date:
            all_dates.append(current_date)
            all_values.append(trip_value)  # Same value for all days in this trip
            current_date += timedelta(days=1)

    # Create DataFrame with all columns
    df = pd.DataFrame({"Date": all_dates, "Value": all_values})

    return df, hlmap


def split_months(df, year):
    # Empty matrices
    a = np.empty((6, 7))
    a[:] = np.nan

    day_nums = {m: np.copy(a) for m in range(1, 13)}  # matrix for day numbers
    day_vals = {m: np.copy(a) for m in range(1, 13)}  # matrix for day values

    # Logic to shape datetimes to matrices in calendar layout
    date = pd.Timestamp(year=year, month=1, day=1)
    oneday = pd.Timedelta(1, unit="D")
    while date.year == year:
        try:
            value = df[date]
        except KeyError:
            value = 0

        day = date.day
        month = date.month
        col = (date.dayofweek + 1) % 7

        if date.is_month_start:
            row = 0

        day_nums[month][row, col] = day  # day number (0-31)
        day_vals[month][row, col] = value  # day value (the heatmap data)

        if col == 6:
            row += 1

        date = date + oneday

    return day_nums, day_vals


def create_year_calendar(
    df,
    year,
    title=None,
    filename=None,
    cmap="cool",
    hlmap={},
    showcb=False,
    portrait=False,
):
    if title is None:
        title = str(year)
    if filename is None:
        filename = title.replace(" ", "_") + ".png"

    vmin = df.min()
    vmin = vmin if vmin < 0 else 0
    vmax = df.max()
    day_nums, day_vals = split_months(df, year)

    if portrait:
        fig, ax = plt.subplots(4, 3, figsize=(8.5, 11))
    else:
        fig, ax = plt.subplots(3, 4, figsize=(11, 8.5))

    gridcolor = "white"
    fontcolor = "black"

    label_map = {}

    for i, axs in enumerate(ax.flat):
        axs.imshow(day_vals[i + 1], cmap=cmap, vmin=vmin, vmax=vmax)  # heatmap
        axs.set_title(MONTH_LABELS[i])

        # Labels
        axs.set_xticks(np.arange(DAYS_IN_WEEK))
        axs.set_xticklabels(DAY_LABELS, fontsize=10, color=fontcolor)
        axs.set_yticklabels([])

        # Tick marks
        axs.tick_params(axis="both", which="both", length=0)  # remove tick marks
        axs.xaxis.tick_top()

        # Modify tick locations for proper grid placement
        axs.set_xticks(np.arange(-0.5, 6, 1), minor=True)
        axs.set_yticks(np.arange(-0.5, 5, 1), minor=True)
        axs.grid(which="minor", color=gridcolor, linestyle="-", linewidth=2.1)

        # Despine
        for edge in ["left", "right", "bottom", "top"]:
            axs.spines[edge].set_color(gridcolor)

        # Annotate
        for w in range(WEEKS_IN_MONTH):
            for d in range(DAYS_IN_WEEK):
                day_val = day_vals[i + 1][w, d]
                day_num = day_nums[i + 1][w, d]

                # If day number is a valid calendar day, add an annotation
                if not np.isnan(day_num):
                    axs.text(
                        d - 0.43,
                        w - 0.40,
                        f"{int(day_num)}",
                        ha="left",
                        va="top",
                        fontsize=8,
                        color=fontcolor,
                    )
                    # draw a highlight
                    if day_val in hlmap:
                        vcolor, vlabel = hlmap[day_val]
                        patch_coords = (
                            (d - 0.5, w - 0.5),
                            (d - 0.5, w + 0.5),
                            (d + 0.5, w + 0.5),
                            (d + 0.5, w - 0.5),
                        )
                        square = Polygon(patch_coords, fc=vcolor)
                        axs.add_artist(square)
                        if vlabel is not None:
                            label_map[day_val] = (square, vlabel)

    # Figure metadata
    fig.suptitle(title, fontsize=16)
    showlegend = len(label_map) > 0
    if showlegend:
        mapvals = sorted(label_map)
        handles = [label_map[v][0] for v in mapvals]
        labels = [label_map[v][1] for v in mapvals]
        if showcb:
            loc = (0.04, 0.01)
        else:
            loc = "lower center"
        fig.legend(handles, labels, loc=loc, fontsize=10, ncol=len(mapvals))
    if showcb:
        norm = Normalize(vmin=vmin, vmax=vmax)
        mappable = ScalarMappable(norm=norm, cmap=cmap)
        if showlegend:
            coords = (
                [0.68, 0.027, 0.275, 0.01] if portrait else [0.752, 0.033, 0.208, 0.01]
            )
            cax = fig.add_axes(coords)
        else:
            coords = (
                [0.3625, 0.027, 0.275, 0.01]
                if portrait
                else [0.396, 0.033, 0.208, 0.01]
            )
            cax = fig.add_axes(coords)
        fig.colorbar(mappable, cax=cax, orientation="horizontal")

    # Final adjustments
    if portrait:
        plt.subplots_adjust(
            left=0.04, right=0.96, top=0.90, bottom=0.04, wspace=0.12, hspace=0.24
        )
    else:
        plt.subplots_adjust(
            left=0.04, right=0.96, top=0.88, bottom=0.04, wspace=0.14, hspace=0.12
        )

    # Save to file
    plt.savefig(filename)


def select_non_conflicting_intervals(
    intervals: List[TripInterval],
) -> List[TripInterval]:
    """
    Select a set of non-conflicting intervals where no two intervals overlap.
    If intervals overlap, only one of them is selected.

    Algorithm:
    1. Sort intervals by end date (return_date)
    2. Greedily select intervals that don't conflict with already selected ones
    3. This gives maximum number of non-overlapping intervals

    Args:
        intervals: List of TripInterval objects

    Returns:
        List of TripInterval objects with no overlaps
    """
    if not intervals:
        return []

    # Sort intervals by return_date (end time)
    sorted_intervals = sorted(intervals, key=lambda x: x.return_date)

    selected = []
    last_end_date = None

    for interval in sorted_intervals:
        # If this is the first interval or it doesn't overlap with the last selected
        if last_end_date is None or interval.departure_date > last_end_date:
            selected.append(interval)
            last_end_date = interval.return_date

    return selected


if __name__ == "__main__":
    import pandas as pd

    # load the CSV into a DataFrame
    trip_intervals = [
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 1, 0, 0),
            return_date=datetime.datetime(2026, 6, 6, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 1, 0, 0),
            return_date=datetime.datetime(2026, 6, 7, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 2, 0, 0),
            return_date=datetime.datetime(2026, 6, 7, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 2, 0, 0),
            return_date=datetime.datetime(2026, 6, 11, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 3, 0, 0),
            return_date=datetime.datetime(2026, 6, 11, 0, 0),
            duration_days=8,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 3, 0, 0),
            return_date=datetime.datetime(2026, 6, 12, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 7, 0, 0),
            return_date=datetime.datetime(2026, 6, 12, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 7, 0, 0),
            return_date=datetime.datetime(2026, 6, 13, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 7, 0, 0),
            return_date=datetime.datetime(2026, 6, 14, 0, 0),
            duration_days=7,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 8, 0, 0),
            return_date=datetime.datetime(2026, 6, 13, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 8, 0, 0),
            return_date=datetime.datetime(2026, 6, 14, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 9, 0, 0),
            return_date=datetime.datetime(2026, 6, 14, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 9, 0, 0),
            return_date=datetime.datetime(2026, 6, 18, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 10, 0, 0),
            return_date=datetime.datetime(2026, 6, 18, 0, 0),
            duration_days=8,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 10, 0, 0),
            return_date=datetime.datetime(2026, 6, 19, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 14, 0, 0),
            return_date=datetime.datetime(2026, 6, 19, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 14, 0, 0),
            return_date=datetime.datetime(2026, 6, 20, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 14, 0, 0),
            return_date=datetime.datetime(2026, 6, 21, 0, 0),
            duration_days=7,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 15, 0, 0),
            return_date=datetime.datetime(2026, 6, 20, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 15, 0, 0),
            return_date=datetime.datetime(2026, 6, 21, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 16, 0, 0),
            return_date=datetime.datetime(2026, 6, 21, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 16, 0, 0),
            return_date=datetime.datetime(2026, 6, 25, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 17, 0, 0),
            return_date=datetime.datetime(2026, 6, 25, 0, 0),
            duration_days=8,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 17, 0, 0),
            return_date=datetime.datetime(2026, 6, 26, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 21, 0, 0),
            return_date=datetime.datetime(2026, 6, 26, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 21, 0, 0),
            return_date=datetime.datetime(2026, 6, 27, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 21, 0, 0),
            return_date=datetime.datetime(2026, 6, 28, 0, 0),
            duration_days=7,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 22, 0, 0),
            return_date=datetime.datetime(2026, 6, 27, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 22, 0, 0),
            return_date=datetime.datetime(2026, 6, 28, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 23, 0, 0),
            return_date=datetime.datetime(2026, 6, 28, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 23, 0, 0),
            return_date=datetime.datetime(2026, 7, 2, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 24, 0, 0),
            return_date=datetime.datetime(2026, 7, 2, 0, 0),
            duration_days=8,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 24, 0, 0),
            return_date=datetime.datetime(2026, 7, 3, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 28, 0, 0),
            return_date=datetime.datetime(2026, 7, 3, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 28, 0, 0),
            return_date=datetime.datetime(2026, 7, 4, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 28, 0, 0),
            return_date=datetime.datetime(2026, 7, 5, 0, 0),
            duration_days=7,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 29, 0, 0),
            return_date=datetime.datetime(2026, 7, 4, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 29, 0, 0),
            return_date=datetime.datetime(2026, 7, 5, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 30, 0, 0),
            return_date=datetime.datetime(2026, 7, 5, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 6, 30, 0, 0),
            return_date=datetime.datetime(2026, 7, 9, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 1, 0, 0),
            return_date=datetime.datetime(2026, 7, 9, 0, 0),
            duration_days=8,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 1, 0, 0),
            return_date=datetime.datetime(2026, 7, 10, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 5, 0, 0),
            return_date=datetime.datetime(2026, 7, 10, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 5, 0, 0),
            return_date=datetime.datetime(2026, 7, 11, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 5, 0, 0),
            return_date=datetime.datetime(2026, 7, 12, 0, 0),
            duration_days=7,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 6, 0, 0),
            return_date=datetime.datetime(2026, 7, 11, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 6, 0, 0),
            return_date=datetime.datetime(2026, 7, 12, 0, 0),
            duration_days=6,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 7, 0, 0),
            return_date=datetime.datetime(2026, 7, 12, 0, 0),
            duration_days=5,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 7, 0, 0),
            return_date=datetime.datetime(2026, 7, 16, 0, 0),
            duration_days=9,
        ),
        TripInterval(
            departure_date=datetime.datetime(2026, 7, 8, 0, 0),
            return_date=datetime.datetime(2026, 7, 16, 0, 0),
            duration_days=8,
        ),
    ]
    df, hlmap = trip_intervals_to_dataframe(
        select_non_conflicting_intervals(trip_intervals)
    )

    # convert the date strings to timestamps
    df["Date"] = pd.to_datetime(df.Date)
    # set the index to the Date column
    df.set_index("Date", inplace=True)

    # create the calendar using the Value column
    create_year_calendar(
        df["Value"],
        2026,
        "Предполагаемые даты по запросу: ...",
        "example.png",
        hlmap=hlmap,
    )
