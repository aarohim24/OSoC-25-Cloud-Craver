def detect_vulnerabilities(template):
    issues = []
    if '0.0.0.0/0' in str(template):
        issues.append("Security Group allows open access (0.0.0.0/0).")
    return issues

def check_compliance(template):
    compliant = True
    messages = []
    if 'Encryption' not in str(template):
        messages.append("No encryption settings found. Enable encryption for compliance.")
        compliant = False
    return compliant, messages
