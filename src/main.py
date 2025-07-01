from templates.base import AWSTemplate, AzureTemplate, GCPTemplate, TemplateMetadata
import click
import os

VERSION = "0.1.0"

@click.group(context_settings={"help_option_names": ["--help", "-h"]})
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.option("--config-file", type=click.Path(), help="Path to configuration file.")
@click.option("--dry-run", is_flag=True, help="Simulate actions without making changes.")
@click.version_option(VERSION, "--version", "-v", message="CloudCraver version: %(version)s")
@click.pass_context
def cli(ctx, verbose, config_file, dry_run):
    """
    CloudCraver: A CLI to generate and validate Terraform templates for multi-cloud infrastructure.
    """
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["CONFIG_FILE"] = config_file
    ctx.obj["DRY_RUN"] = dry_run

@cli.command()
@click.option("--template", "-t", required=True, help="Name of the Terraform template to generate.")
@click.option("--output", "-o", default=".", type=click.Path(), help="Output directory.")
@click.pass_context
def generate(ctx, template, output):
    """
    🛠️ Generate a Terraform template by name.
    """
    click.echo(f"[GENERATE] Template: {template}")
    click.echo(f"[OUTPUT] Saving to: {output}")
    if ctx.obj["DRY_RUN"]:
        click.echo("[DRY-RUN] No files created.")
    else:
        # Simulate creation
        os.makedirs(output, exist_ok=True)
        file_path = os.path.join(output, f"{template}.tf")
        with open(file_path, "w") as f:
            f.write(f"# Terraform template for {template}\n")
        click.echo(f" Template '{template}' created at {file_path}")

@cli.command(name="list-templates")
@click.pass_context
def list_templates(ctx):
    """
    📚 List available Terraform templates.
    """
    templates = ["vpc", "ec2", "s3", "rds"]
    click.echo("Available templates:")
    for tpl in templates:
        click.echo(f" - {tpl}")

@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.pass_context
def validate(ctx, path):
    """
     Validate the Terraform template directory at the given PATH.
    """
    if not os.path.isdir(path):
        raise click.ClickException(f"{path} is not a directory.")

    tf_files = [f for f in os.listdir(path) if f.endswith(".tf")]
    if tf_files:
        click.echo(f" Found {len(tf_files)} Terraform file(s) at {path}:")
        for f in tf_files:
            click.echo(f"  - {f}")
    else:
        click.echo(" No Terraform files found.")

    if ctx.obj["DRY_RUN"]:
        click.echo("[DRY-RUN] Validation simulated.")

if __name__ == "__main__":
    cli()

#I built the foundation of a CLI tool called that can generate pre-defined Terraform templates for different cloud providers (AWS, Azure, GCP),  Validate existing Terraform files in a directory,Support future enhancements like cost estimation, template rendering, and cloud deployment automation