from templates.base import AWSTemplate, AzureTemplate, GCPTemplate, TemplateMetadata
import click
import os
import json
from InquirerPy import prompt
from rich.console import Console
from rich.progress import Progress

# Import validators
from interactive.validator import validate_region, validate_tags, validate_resources

VERSION = "0.1.0"
console = Console()

@click.group(context_settings={"help_option_names": ["--help", "-h"]})
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.option("--config-file", type=click.Path(), help="Path to configuration file.")
@click.option("--dry-run", is_flag=True, help="Simulate actions without making changes.")
@click.version_option(VERSION, "--version", "-v", message="CloudCraver version: %(version)s")
@click.pass_context
def cli(ctx, verbose, config_file, dry_run):
    """CloudCraver: A CLI to generate and validate Terraform templates for multi-cloud infrastructure."""
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["CONFIG_FILE"] = config_file
    ctx.obj["DRY_RUN"] = dry_run

@cli.command()
@click.option("--template", "-t", required=True, help="Name of the Terraform template to generate.")
@click.option("--output", "-o", default=".", type=click.Path(), help="Output directory.")
@click.pass_context
def generate(ctx, template, output):
    """Generate a Terraform template by name."""
    click.echo(f"[GENERATE] Template: {template}")
    click.echo(f"[OUTPUT] Saving to: {output}")
    if ctx.obj["DRY_RUN"]:
        click.echo("[DRY-RUN] No files created.")
    else:
        os.makedirs(output, exist_ok=True)
        file_path = os.path.join(output, f"{template}.tf")
        with open(file_path, "w") as f:
            f.write(f"# Terraform template for {template}\n")
        click.echo(f" Template '{template}' created at {file_path}")

@cli.command(name="list-templates")
@click.pass_context
def list_templates(ctx):
    """List available Terraform templates."""
    templates = ["vpc", "ec2", "s3", "rds"]
    click.echo("Available templates:")
    for tpl in templates:
        click.echo(f" - {tpl}")

@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.pass_context
def validate(ctx, path):
    """Validate the Terraform template directory at the given PATH."""
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

@cli.command(name="interactive-generate")
def interactive_generate():
    """Interactive workflow to generate Terraform templates."""
    console.rule("[bold cyan]Interactive Project Generator[/bold cyan]")

    questions = [
        {
            'type': 'list',
            'name': 'provider',
            'message': 'Choose cloud provider:',
            'choices': ['AWS', 'Azure', 'GCP']
        },
        {
            'type': 'input',
            'name': 'region',
            'message': 'Enter cloud region:',
            'validate': validate_region
        },
        {
            'type': 'checkbox',
            'name': 'resources',
            'message': 'Select resources to generate:',
            'choices': [
                {'name': 'VPC', 'value': 'vpc'},
                {'name': 'EC2', 'value': 'ec2'},
                {'name': 'S3', 'value': 's3'},
                {'name': 'RDS', 'value': 'rds'}
            ],
            'validate': validate_resources
        },
        {
            'type': 'input',
            'name': 'project_name',
            'message': 'Enter project name prefix:',
            'default': 'cloudcraver'
        },
        {
            'type': 'input',
            'name': 'suffix',
            'message': 'Enter project name suffix (optional):',
            'default': ''
        },
        {
            'type': 'input',
            'name': 'tags',
            'message': 'Enter comma-separated tags (key=value format):',
            'validate': validate_tags
        },
        {
            'type': 'input',
            'name': 'description',
            'message': 'Enter project description:'
        },
        {
            'type': 'input',
            'name': 'team',
            'message': 'Enter team name:'
        },
        {
            'type': 'list',
            'name': 'environment',
            'message': 'Select environment:',
            'choices': ['development', 'staging', 'production']
        }
    ]

    answers = prompt(questions)
    if not answers:
        console.print("[red]Aborted.[/red]")
        return

    output_dir = f"./{answers['project_name']}_{answers['suffix']}" if answers['suffix'] else f"./{answers['project_name']}"
    os.makedirs(output_dir, exist_ok=True)

    # Save prompt state for persistence
    with open(".cloudcraver_state.json", "w") as f:
        json.dump(answers, f, indent=2)

    with Progress() as progress:
        task = progress.add_task("[green]Creating templates...", total=100)
        for _ in range(5):
            progress.update(task, advance=20)

    console.print(f"[green]✔ Project '{answers['project_name']}' for {answers['provider']} with {answers['resources']} created at {output_dir}[/green]")

if __name__ == "__main__":
    cli()
