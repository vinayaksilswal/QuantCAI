import click
import json
import sys
from quantcai_scanner.scanner import scan_domain

@click.group()
def cli():
    """QuantCAI Post-Quantum Cryptography (PQC) Scanner CLI.

    Identify quantum-vulnerable public keys and protocol suites in your digital infrastructure
    to evaluate your posture against the Y2Q / Q-Day threat.
    """
    pass

@cli.command()
@click.argument('target', required=False)
@click.option('--port', '-p', type=int, help='Override default port 443')
@click.option('--source', '-s', type=click.Path(exists=True), help='[Enterprise/Phase 2] Path to a source directory to scan for cryptographic libraries')
@click.option('--output', '-o', type=click.Path(), help='Save scan report as a JSON file')
def scan(target, port, source, output):
    """Scan a domain or IP for quantum-cryptographic readiness."""
    if source:
        click.secho("\n[i] Source Code AST Scanning is an Enterprise feature.", fg="cyan", bold=True)
        click.echo("This CLI module scans source directories for crypto packages (cryptography, javax.crypto, OpenSSL).")
        click.echo("For repo integration, CI/CD scanning pipelines, or compliance CBOM exports:")
        click.secho("  - Visit: https://quantcai.in")
        click.secho("  - Contact: support@quantcai.in")
        click.echo()
        if not target:
            sys.exit(0)

    if not target:
        click.secho("Error: Missing argument 'TARGET'. Run 'quantcai scan --help' for usage.", fg="red")
        sys.exit(1)

    click.echo(f"Initializing post-quantum cryptography scan for target: {target}...")
    report = scan_domain(target, port)

    if "error" in report:
        click.secho(f"\n[!] Error scanning {target}: {report['error']['message']}", fg='red')
        sys.exit(1)

    # CLI visual presentation
    click.echo(f"\n{'=' * 72}")
    click.secho(f"  QuantCAI PQC Scanner Report -- {target}", bold=True)
    click.echo(f"{'=' * 72}\n")

    risk_color = 'green'
    if report['risk_level'] in ('CRITICAL', 'HIGH'):
        risk_color = 'red'
    elif report['risk_level'] == 'MEDIUM':
        risk_color = 'yellow'
    elif report['risk_level'] == 'LOW':
        risk_color = 'blue'

    click.echo("  Risk Level  : ", nl=False)
    click.secho(f"{report['risk_level']}", fg=risk_color, bold=True, nl=False)
    click.echo(f" (Score: {report['overall_risk_score']}/100)")

    click.echo(f"  TLS Version : {report['tls_version']} ({report['tls_version_risk']})")

    cipher_safe = report['cipher_quantum_safe']
    cipher_text = "PQC-Compliant" if cipher_safe else "Quantum-Vulnerable"
    cipher_color = 'green' if cipher_safe else 'red'
    click.echo("  Cipher Suite: ", nl=False)
    click.echo(f"{report['cipher_suite']} (", nl=False)
    click.secho(cipher_text, fg=cipher_color, bold=True, nl=False)
    click.echo(")")

    click.echo(f"  Certificates: {report['cbom_summary']['total_assets']} total, "
               f"{report['cbom_summary']['vulnerable_assets']} vulnerable")
    click.echo(f"{'-' * 72}")

    click.echo("  Findings:")
    severity_icons = {
        "CRITICAL": "[!!]", "HIGH": "[!]", "MEDIUM": "[~]",
        "WARNING": "[~]", "LOW": "[.]", "COMPLIANT": "[OK]",
    }
    severity_colors = {
        "CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow",
        "WARNING": "yellow", "LOW": "cyan", "COMPLIANT": "green",
    }

    for finding in report["findings"]:
        icon = severity_icons.get(finding["severity"], "[?]")
        color = severity_colors.get(finding["severity"], "white")
        click.echo("  ", nl=False)
        click.secho(f"{icon} [{finding['severity']}] {finding['title']}", fg=color)
        click.echo(f"       Description: {finding['description']}")
        click.echo(f"       Remediation: {finding['remediation']}")
        click.echo()

    click.echo(f"{'-' * 72}")

    if output:
        try:
            with open(output, 'w') as f:
                json.dump(report, f, indent=2)
            click.secho(f"\n[+] Full report saved to {output}", fg='green')
        except Exception as e:
            click.secho(f"\n[!] Failed to save output to {output}: {e}", fg='red')

    # Exit code based on findings
    if report['risk_level'] in ('CRITICAL', 'HIGH'):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    cli()
