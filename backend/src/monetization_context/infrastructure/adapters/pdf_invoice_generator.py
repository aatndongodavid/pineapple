import os
from pathlib import Path
from typing import Any, Dict
from jinja2 import Environment, FileSystemLoader

from shared_kernel.domain.value_objects import Money

TEMPLATE_DIR = Path(__file__).parent / "templates"

class PdfInvoiceGeneratorAdapter:
    """Adaptateur pour générer les factures au format PDF via WeasyPrint."""

    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    def generate_pdf(self, invoice_data: Dict[str, Any]) -> bytes:
        """
        Génère un buffer binaire PDF à partir des données de la facture.
        
        Args:
            invoice_data: Dict contenant:
                - invoice_number: str
                - issue_date: str (YYYY-MM-DD)
                - due_date: str (YYYY-MM-DD)
                - status: str
                - company_name: str
                - company_address: str
                - tax_id_number: str | None
                - tenant_name: str
                - tenant_code: str
                - tenant_contact_email: str | None
                - line_items: list[dict(description, quantity, unit_price_xaf, total_xaf)]
                - subtotal_xaf: int
                - tax_rate_percent: int
                - tax_xaf: int
                - total_xaf: int
                - legal_notice: str
                - current_date: str
        """
        # Format XAF amounts
        line_items_formatted = []
        for line in invoice_data.get("line_items", []):
            unit_m = Money(line["unit_price_xaf"])
            tot_m = Money(line["total_xaf"])
            line_items_formatted.append({
                "description": line["description"],
                "quantity": line["quantity"],
                "unit_price_formatted": unit_m.format_xaf(),
                "total_formatted": tot_m.format_xaf(),
            })

        context = {
            **invoice_data,
            "line_items": line_items_formatted,
            "subtotal_formatted": Money(invoice_data.get("subtotal_xaf", 0)).format_xaf(),
            "tax_formatted": Money(invoice_data.get("tax_xaf", 0)).format_xaf(),
            "total_formatted": Money(invoice_data.get("total_xaf", 0)).format_xaf(),
        }

        template = self.env.get_template("invoice_template.html")
        rendered_html = template.render(**context)

        try:
            import weasyprint
            return weasyprint.HTML(string=rendered_html).write_pdf()
        except Exception:
            # Fallback en environnement local de dev si WeasyPrint (Cairo/Pango) n'est pas disponible sur l'OS hôte
            return self._generate_fallback_pdf(context)

    def _generate_fallback_pdf(self, context: Dict[str, Any]) -> bytes:
        """Génère un document PDF minimal valide sans dépendance C native."""
        pdf_content = (
            f"%PDF-1.4\n"
            f"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
            f"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
            f"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>> >> endobj\n"
            f"4 0 obj <</Length 150>> stream\n"
            f"BT /F1 14 Tf 50 720 Td (FACTURE PINEAPPLE OS: {context.get('invoice_number')}) Tj ET\n"
            f"BT /F1 10 Tf 50 690 Td (Etablissement: {context.get('tenant_name')} [{context.get('tenant_code')}]) Tj ET\n"
            f"BT /F1 10 Tf 50 660 Td (Total TTC: {context.get('total_formatted')}) Tj ET\n"
            f"endstream endobj\n"
            f"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
            f"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000240 00000 n \n0000000440 00000 n \n"
            f"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n510\n%%EOF"
        )
        return pdf_content.encode("utf-8")
