import customtkinter as ctk
import tkinterweb
import os
import base64

from database.db_manager import get_setting


def build_invoice_html(invoice_no, customer_name, date, subtotal, tax, total, cart_items,
                        discount_amount=0.0, discount_note=""):
    """
    Builds the invoice HTML receipt. Shared by the print-preview window
    and the PDF export function so both stay in sync.
    """
    shop_name = get_setting("shop_name", "Afzal Petrol Agency")
    logo_path = get_setting("logo_path", "")
    footer_note = get_setting("footer_note", "System generated invoice. Thank you for your business!")

    discount_amount = float(discount_amount or 0)
    taxable_amount = max(subtotal - discount_amount, 0)

    header_html = _build_header_html(shop_name, logo_path)

    cart_rows_html = ""
    for item in cart_items:
        _, name, qty, price, total_p, _ = item
        qty_f = float(qty)
        qty_display = str(int(qty_f)) if qty_f == int(qty_f) else f"{round(qty_f, 3):g}"
        cart_rows_html += f"""
        <tr>
            <td style='padding: 6px; border-bottom: 1px solid #eeeeee;'>{name}</td>
            <td style='padding: 6px; border-bottom: 1px solid #eeeeee; text-align: center;'>{qty_display}</td>
            <td style='padding: 6px; border-bottom: 1px solid #eeeeee; text-align: right;'>Rs.{price:.2f}</td>
            <td style='padding: 6px; border-bottom: 1px solid #eeeeee; text-align: right;'>Rs.{total_p:.2f}</td>
        </tr>
        """

    discount_row_html = ""
    if discount_amount > 0:
        note_suffix = f" ({discount_note})" if discount_note else ""
        discount_row_html = f"""
            <tr>
                <td style='padding: 5px; color: #c0392b;'>Discount{note_suffix}:</td>
                <td style='padding: 5px; text-align: right; color: #c0392b;'>-Rs.{discount_amount:.2f}</td>
            </tr>
        """

    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 18px; color: #333333; background-color: #ffffff; font-size: 12px; }}
            .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 18px; }}
            .brand-title {{ font-size: 22px; font-weight: bold; color: #1f293d; vertical-align: middle; }}
            .invoice-tag {{ font-size: 18px; font-weight: bold; text-align: right; color: #4a90e2; vertical-align: middle; }}
            .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 18px; background: #f8f9fa; padding: 10px; border-radius: 4px; }}
            .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 18px; }}
            .th-style {{ background-color: #1f293d; color: white; padding: 8px; font-size: 12px; font-weight: bold; text-align: left; }}
            .totals-table {{ width: 40%; margin-left: auto; border-collapse: collapse; font-size: 13px; }}
            .grand-total {{ font-size: 16px; font-weight: bold; color: #ff4a4a; border-top: 2px solid #1f293d; }}
            .logo-img {{ width: 70px; height: 70px; }}
        </style>
    </head>
    <body>
        <table class='header-table'>
            <tr>
                <td class='brand-title'>{header_html}</td>
                <td class='invoice-tag'>INVOICE<br><span style='font-size:12px; color:gray;'>#INV-{invoice_no}</span></td>
            </tr>
        </table>

        <table class='meta-table'>
            <tr>
                <td style='padding: 8px; font-size: 12px;'><strong>Customer ID:</strong> {customer_name}</td>
                <td style='padding: 8px; font-size: 12px; text-align: right;'><strong>Timestamp:</strong> {date}</td>
            </tr>
        </table>

        <table class='items-table'>
            <thead>
                <tr>
                    <th class='th-style'>Item Specifications</th>
                    <th class='th-style' style='text-align: center;'>Qty</th>
                    <th class='th-style' style='text-align: right;'>Unit Valuation</th>
                    <th class='th-style' style='text-align: right;'>Total Price</th>
                </tr>
            </thead>
            <tbody>
                {cart_rows_html}
            </tbody>
        </table>

        <table class='totals-table'>
            <tr>
                <td style='padding: 5px;'>Subtotal:</td>
                <td style='padding: 5px; text-align: right;'>Rs.{subtotal:.2f}</td>
            </tr>
            {discount_row_html}
            <tr>
                <td style='padding: 5px;'>Tax Surcharge ({tax}%):</td>
                <td style='padding: 5px; text-align: right;'>Rs.{(taxable_amount * tax / 100):.2f}</td>
            </tr>
            <tr class='grand-total'>
                <td style='padding: 8px;'>Net Amount:</td>
                <td style='padding: 8px; text-align: right;'>Rs.{total:.2f}</td>
            </tr>
        </table>

        <p style='text-align: center; margin-top: 20px; font-size: 11px; color: gray;'>{footer_note}</p>
    </body>
    </html>
    """
    return html_template


def _build_header_html(shop_name, logo_path):
    """If a shop logo exists, embed it as a base64 image; otherwise fall back to the shop name text."""
    if logo_path and os.path.exists(logo_path):
        try:
            ext = os.path.splitext(logo_path)[1].lower().replace(".", "")
            if ext == "jpg":
                ext = "jpeg"
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"<img class='logo-img' src='data:image/{ext};base64,{encoded}' />"
        except Exception:
            pass
    return shop_name.upper()


def export_invoice_pdf(save_path, invoice_no, customer_name, date, subtotal, tax, total, cart_items,
                        discount_amount=0.0, discount_note=""):
    """
    Renders the invoice HTML and saves it as a PDF file at save_path
    using xhtml2pdf. Returns (success: bool, message: str).
    """
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return False, (
            "PDF export requires the 'xhtml2pdf' package.\n\n"
            "Please install it:\n"
            "pip install xhtml2pdf"
        )

    html_content = build_invoice_html(invoice_no, customer_name, date, subtotal, tax, total, cart_items,
                                       discount_amount=discount_amount, discount_note=discount_note)

    try:
        with open(save_path, "wb") as f:
            result = pisa.CreatePDF(html_content, dest=f)
        if result.err:
            return False, "PDF generation encountered errors."
        return True, f"Invoice PDF saved to:\n{save_path}"
    except Exception as e:
        return False, f"Could not generate PDF:\n{e}"


class InvoicePrintWindow(ctk.CTkToplevel):
    def __init__(self, parent, invoice_no, customer_name, date, subtotal, tax, total, cart_items,
                 discount_amount=0.0, discount_note=""):
        super().__init__(parent)

        self.title(f"Nexus Transaction Print Engine - #INV-{invoice_no}")
        self.geometry("600x750")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        # Primary container setup
        self.configure(fg_color="#121214")

        html_template = build_invoice_html(invoice_no, customer_name, date, subtotal, tax, total, cart_items,
                                            discount_amount=discount_amount, discount_note=discount_note)

        # Embedded HTML Frame Renderer Component
        self.frame = tkinterweb.HtmlFrame(self)
        self.frame.load_html(html_template)
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)
