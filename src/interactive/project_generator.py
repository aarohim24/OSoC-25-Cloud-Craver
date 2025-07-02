from rich.progress import Progress
from pathlib import Path
import shutil

def generate_templates(data):
    provider = data['cloud_provider'].lower()
    project_dir = Path(f"./{data['prefix']}")

    project_dir.mkdir(parents=True, exist_ok=True)

    with Progress() as progress:
        task = progress.add_task("Creating templates", total=len(data['resources']))
        for resource in data['resources']:
            src = Path(f"terraform_templates/{provider}/{resource.lower()}")
            dest = project_dir / resource.lower()
            if src.exists():
                shutil.copytree(src, dest, dirs_exist_ok=True)
            progress.advance(task)

    return project_dir
