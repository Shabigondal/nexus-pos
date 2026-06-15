"""
Shared PDF export helper.

Builds a simple, professional HTML table report and renders it to PDF using
xhtml2pdf. Orientation (portrait/landscape) is chosen automatically based on
the number of columns, or can be forced.
"""

import datetime


PAGE_CSS_TEMPLATE = """
@page {{
    size: A4 {orientation};
    margin: 1.2cm;
}}
body {{
    font-family: Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    font-size: 9pt;
}}
.report-title {{
    font-size: 16pt;
    font-weight: bold;
    color: #1e3a5f;
    margin-bottom: 2px;
}}
.report-subtitle {{
    font-size: 9pt;
    color: #666666;
    margin-bottom: 12px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
    table-layout: fixed;
}}
th {{
    background-color: #1e3a5f;
    color: #ffffff;
    padding: 6px 6px;
    font-size: 8.5pt;
    text-align: left;
    border: 1px solid #1e3a5f;
    word-wrap: break-word;
    overflow-wrap: break-word;
}}
td {{
    padding: 5px 6px;
    font-size: 8.5pt;
    border: 1px solid #cccccc;
    word-wrap: break-word;
    overflow-wrap: break-word;
}}
tr:nth-child(even) td {{
    background-color: #f2f5f9;
}}
.right {{ text-align: right; }}
.center {{ text-align: center; }}
.bold {{ font-weight: bold; }}
.green {{ color: #1a8a3a; font-weight: bold; }}
.red {{ color: #c0392b; font-weight: bold; }}
.orange {{ color: #d4820a; font-weight: bold; }}
.blue {{ color: #1a5fa8; font-weight: bold; }}
.totals-row td {{
    background-color: #dbe6f3 !important;
    font-weight: bold;
    border-top: 2px solid #1e3a5f;
}}
.section-title {{
    font-size: 12pt;
    font-weight: bold;
    color: #1e3a5f;
    margin-top: 14px;
    margin-bottom: 4px;
}}
.summary-box {{
    margin-bottom: 14px;
}}
.summary-box table {{
    width: auto;
}}
.summary-box td {{
    border: none;
    padding: 3px 14px 3px 0;
    font-size: 9.5pt;
}}
.footer-note {{
    margin-top: 14px;
    font-size: 8pt;
    color: #888888;
}}
"""


def _esc(val):
    """Lightweight HTML-escape for table cell content."""
    if val is None:
        return ""
    return (str(val)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def build_table_html(title, subtitle, headers, rows, col_classes=None,
                      orientation="auto", summary_rows=None, totals_row=None,
                      footer_note=None, col_widths=None):
    """
    Build a printable HTML report.

    headers: list[str] column headers
    rows: list[list] each cell can be a string/number, or a (text, css_class) tuple
    col_classes: optional list of default css classes per column (e.g. ["", "right", "center"])
    orientation: "portrait", "landscape", or "auto" (auto picks landscape if many columns)
    summary_rows: optional list of (label, value) pairs shown above the table
    totals_row: optional list of cells for a totals row appended at the bottom (same length as headers)
    footer_note: optional small text shown below the table
    col_widths: optional list of column widths as percentages (must sum to ~100),
                used with table-layout: fixed so wide text columns don't get squeezed
                into a single-letter-per-line wrap.
    """
    if orientation == "auto":
        orientation = "landscape" if len(headers) >= 6 else "portrait"

    css = PAGE_CSS_TEMPLATE.format(orientation=orientation)

    if col_classes is None:
        col_classes = [""] * len(headers)

    html = [f"<html><head><style>{css}</style></head><body>"]
    html.append(f"<div class='report-title'>{_esc(title)}</div>")
    if subtitle:
        html.append(f"<div class='report-subtitle'>{_esc(subtitle)}</div>")

    if summary_rows:
        html.append("<div class='summary-box'><table>")
        for label, value in summary_rows:
            html.append(f"<tr><td class='bold'>{_esc(label)}</td><td>{_esc(value)}</td></tr>")
        html.append("</table></div>")

    html.append("<table>")

    html.append("<thead><tr>")
    for i, h in enumerate(headers):
        cls = col_classes[i] if i < len(col_classes) else ""
        style = f" style='width:{col_widths[i]}%'" if col_widths and i < len(col_widths) else ""
        html.append(f"<th class='{cls}'{style}>{_esc(h)}</th>")
    html.append("</tr></thead><tbody>")

    for row in rows:
        html.append("<tr>")
        for i, cell in enumerate(row):
            cls = col_classes[i] if i < len(col_classes) else ""
            style = f" style='width:{col_widths[i]}%'" if col_widths and i < len(col_widths) else ""
            if isinstance(cell, tuple):
                text, extra_cls = cell
                cls = f"{cls} {extra_cls}".strip()
            else:
                text = cell
            html.append(f"<td class='{cls}'{style}>{_esc(text)}</td>")
        html.append("</tr>")

    if totals_row:
        html.append("<tr class='totals-row'>")
        for i, cell in enumerate(totals_row):
            cls = col_classes[i] if i < len(col_classes) else ""
            style = f" style='width:{col_widths[i]}%'" if col_widths and i < len(col_widths) else ""
            if isinstance(cell, tuple):
                text, extra_cls = cell
                cls = f"{cls} {extra_cls}".strip()
            else:
                text = cell
            html.append(f"<td class='{cls}'{style}>{_esc(text)}</td>")
        html.append("</tr>")

    html.append("</tbody></table>")

    if footer_note:
        html.append(f"<div class='footer-note'>{_esc(footer_note)}</div>")

    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html.append(f"<div class='footer-note'>Generated on {generated_at}</div>")

    html.append("</body></html>")
    return "".join(html)


def export_html_to_pdf(html_content, save_path):
    """Render the given HTML to a PDF file. Returns (success: bool, message: str)."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return False, (
            "PDF export requires the 'xhtml2pdf' package.\n\n"
            "Please install it:\n"
            "pip install xhtml2pdf"
        )

    try:
        with open(save_path, "wb") as f:
            result = pisa.CreatePDF(html_content, dest=f)
        if result.err:
            return False, "PDF generation encountered errors."
        return True, f"PDF saved to:\n{save_path}"
    except Exception as e:
        return False, f"Could not generate PDF:\n{e}"