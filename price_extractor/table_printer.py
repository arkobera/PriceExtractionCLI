"""
Pretty-print quantity extraction results as a table with box-drawing characters.
"""

from pathlib import Path
from typing import List, Dict

import click


def print_results_table(results: List[Dict]) -> None:
    """Print quantity extraction results as a formatted table."""

    if not results:
        click.echo("No results to display.")
        return

    headers = ["File", "Item Name", "Quantity", "Unit"]

    # 🔁 Build rows
    rows = [
        [
            Path(r["file_path"]).name,
            str(r.get("item_name", "")),
            str(r.get("quantity", "")),
            str(r.get("unit", "")),
        ]
        for r in results
    ]

    # 🔹 Column widths
    col_widths = [
        max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)
    ]

    def fmt_row(row: List[str]) -> str:
        cells = " │ ".join(v.ljust(w) for v, w in zip(row, col_widths))
        return f"│ {cells} │"

    # 🔹 Borders
    top = "┌─" + "─┬─".join("─" * w for w in col_widths) + "─┐"
    sep = "├─" + "─┼─".join("─" * w for w in col_widths) + "─┤"
    bot = "└─" + "─┴─".join("─" * w for w in col_widths) + "─┘"

    # 🔹 Print table
    click.echo(top)
    click.echo(fmt_row(headers))

    for i, row in enumerate(rows):
        click.echo(sep)
        click.echo(fmt_row(row))

    click.echo(bot)
