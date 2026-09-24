"""
Reporting module for generating audit dossiers and detection reports.
"""

from src.engine.reporting.html_report import generate_audit_report_html, generate_dossier_html

__all__ = ["generate_dossier_html", "generate_audit_report_html"]
