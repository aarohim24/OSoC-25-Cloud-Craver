def detect_vulnerabilities(template):
    issues = []
    template_str = str(template)

    if '0.0.0.0/0' in template_str:
        issues.append("Security Group or NSG allows open access (0.0.0.0/0).")
    return issues

def check_compliance(template):
    compliant = True
    messages = []

    if 'Encryption' not in str(template) and 'encryption' not in str(template):
        messages.append("No encryption settings found. Enable encryption for compliance.")
        compliant = False

    return compliant, messages
