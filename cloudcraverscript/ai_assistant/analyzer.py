import yaml

def analyze_template(template_path):
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)
    
    suggestions = []
    if 'Resources' in template:
        for name, resource in template['Resources'].items():
            if resource.get('Type', '').startswith('AWS::EC2') and 't2.micro' in str(resource):
                suggestions.append(f"Resource {name} uses t2.micro, consider upgrading for production workloads.")
    return suggestions
