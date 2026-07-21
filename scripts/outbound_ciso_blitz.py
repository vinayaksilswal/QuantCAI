"""
=============================================================================
QuantCAI — B2B Outbound CISO Blitz
=============================================================================
A command-line script to automate the B2B outbound pipeline.
Takes a list of prospective companies, target GitHub repos, and CISO emails.
1. Runs the PQC Repo Scanner
2. Generates the HTML Audit Report
3. Sends the personalized cold email via Resend with the report linked/attached.

Usage:
  python scripts/outbound_ciso_blitz.py --target-csv prospects.csv
=============================================================================
"""

import sys
import os
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path so we can import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from backend.repo_scanner_engine import scan_repository

# In a real scenario, this would use the configured Resend client
# from python_admin.services.email_service import send_email_blast
# For the script, we mock it to avoid sending live emails during testing unless forced.

TEMPLATES_DIR = Path(__file__).parent.parent / "backend" / "report_templates"
REPORTS_OUT_DIR = Path(__file__).parent.parent / "data" / "generated_reports"

def generate_report_html(report_data: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("pqc_audit_report.html")
    
    return template.render(
        repo_url=report_data["repo_url"],
        scan_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        risk_level=report_data["risk_level"],
        total_findings=report_data["total_findings"],
        files_scanned=report_data["files_scanned"],
        findings=report_data["findings"]
    )

def generate_email_html(prospect: dict, report_data: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("outbound_email.html")
    
    primary_file = "N/A"
    primary_type = "N/A"
    if report_data["findings"]:
        primary_file = report_data["findings"][0]["file"]
        primary_type = report_data["findings"][0]["type"]
    
    return template.render(
        first_name=prospect.get("first_name", "Security Leader"),
        company_name=prospect.get("company", "your organization"),
        repo_name=prospect.get("repo_url", "").split("/")[-1],
        total_findings=report_data["total_findings"],
        primary_finding_file=primary_file,
        primary_finding_type=primary_type
    )

def main():
    parser = argparse.ArgumentParser(description="QuantCAI B2B Outbound Engine")
    parser.add_argument("--repo", type=str, help="Single GitHub repo URL to scan")
    parser.add_argument("--email", type=str, help="Target CISO email (for single run)")
    parser.add_argument("--first-name", type=str, default="Security Leader", help="CISO First Name")
    parser.add_argument("--company", type=str, default="Organization", help="Company Name")
    parser.add_argument("--dry-run", action="store_true", help="Generate reports without sending email")
    
    args = parser.parse_args()
    
    REPORTS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.repo and args.email:
        logger.info(f"Starting targeted outreach for {args.company} ({args.email}) on repo {args.repo}")
        
        # 1. Scan
        logger.info("Running PQC scan...")
        report_data = scan_repository(args.repo)
        
        # 2. Generate Audit Report
        audit_html = generate_report_html(report_data)
        report_path = REPORTS_OUT_DIR / f"audit_{args.company.replace(' ', '_').lower()}.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(audit_html)
        logger.info(f"Audit report generated: {report_path}")
        
        # 3. Generate Email Body
        email_html = generate_email_html(
            {
                "first_name": args.first_name,
                "company": args.company,
                "repo_url": args.repo
            },
            report_data
        )
        email_path = REPORTS_OUT_DIR / f"email_{args.company.replace(' ', '_').lower()}.html"
        with open(email_path, "w", encoding="utf-8") as f:
            f.write(email_html)
        logger.info(f"Email template generated: {email_path}")
        
        # 4. Dispatch Email
        if not args.dry_run:
            logger.warning("Email dispatching via Resend would occur here.")
            # await send_email_blast(...)
        else:
            logger.info("DRY RUN mode. Emails not sent.")
            
    else:
        logger.error("Please provide --repo and --email for a single run, or use a CSV mode (not implemented in this demo).")

if __name__ == "__main__":
    main()
