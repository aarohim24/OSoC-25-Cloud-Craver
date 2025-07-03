import yaml
import json
from pathlib import Path

def detect_provider(template):
    if isinstance(template, dict) and 'AWSTemplateFormatVersion' in template:
        return 'aws'
    if isinstance(template, list) or 'resources' in template or any("Microsoft." in str(x) for x in str(template)):
        return 'azure'
    return 'unknown'

def analyze_template(template_path):
    with open(template_path, 'r') as f:
        ext = Path(template_path).suffix
        if ext == '.json':
            template = json.load(f)
        else:
            template = yaml.safe_load(f)

    provider = detect_provider(template)
    suggestions = []

    if provider == 'aws':
        for name, resource in template.get('Resources', {}).items():
            if resource.get('Type', '').startswith('AWS::EC2') and 't2.micro' in str(resource):
                suggestions.append(f"Resource {name} uses t2.micro, consider upgrading for production workloads.")
    elif provider == 'azure':
        for res in template.get('resources', []):
            if res.get('type', '') == 'Microsoft.Compute/virtualMachines':
                vm_size = res.get('properties', {}).get('hardwareProfile', {}).get('vmSize', '')
                if 'Standard_B1s' in vm_size:
                    suggestions.append(f"VM {res.get('name')} uses low-tier size ({vm_size}), consider scaling for production.")
    else:
        suggestions.append("Could not detect template provider (AWS or Azure).")

    return suggestions
