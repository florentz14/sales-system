"""Formato tabular CLI: líneas | y - con borde superior e inferior (sin + ni = bajo cabecera)."""

from __future__ import annotations

from tabulate import DataRow, Line, TableFormat

CLI_TABLEFMT = TableFormat(
    lineabove=Line("|", "-", "|", "|"),
    linebelowheader=Line("|", "-", "|", "|"),
    linebetweenrows=None,
    linebelow=Line("|", "-", "|", "|"),
    headerrow=DataRow("|", "|", "|"),
    datarow=DataRow("|", "|", "|"),
    padding=1,
    with_header_hide=None,
)
