from cloudcraverscript.ai_assistant import analyzer, generator, recommender, security, monitor
import json
import yaml

# ---------- AWS TEMPLATE TEST ----------
print("Analyzer Suggestions (AWS):")
print(analyzer.analyze_template('sample-template.yaml'))
print()

print("Resource Sizing Recommendations:")
print(recommender.recommend_resource_sizes({
    "res1": {"cpu": 82},
    "res2": {"cpu": 45}
}))
print()

print("Cost Optimization Suggestions:")
print(recommender.recommend_cost_saving({
    "res1": {"uptime": 5},
    "res2": {"uptime": 60}
}))
print()

print("Predictive Scaling Suggestion:")
print(recommender.recommend_scaling([10, 30, 45, 90]))
print()

print("Security Vulnerability Scan:")
with open('sample-template.yaml', 'r') as f:
    aws_template_data = f.read()
print(security.detect_vulnerabilities(aws_template_data))
print()

print("Compliance Check:")
compliant, messages = security.check_compliance(aws_template_data)
print("Compliant:", compliant)
print("Messages:", messages)
print()

print("Generated Template from Prompt:")
print(generator.generate_template("Create a secure EC2 instance with S3 bucket"))
print()

print("Monitoring Configuration:")
print(monitor.generate_monitoring_config(["EC2Instance", "S3Bucket"]))
print()


# ---------- AZURE TEMPLATE TEST ----------
print("Analyzer Suggestions (Azure):")
print(analyzer.analyze_template('sample-template-azure.json'))
print()

print("Security Vulnerability Scan (Azure):")
with open('sample-template-azure.json', 'r') as f:
    azure_template_data = f.read()
print(security.detect_vulnerabilities(azure_template_data))
print()

print("Compliance Check (Azure):")
compliant, messages = security.check_compliance(azure_template_data)
print("Compliant:", compliant)
print("Messages:", messages)
print()

print("Monitoring Configuration (Azure):")
print(monitor.generate_monitoring_config(["AzureVM", "AzureStorage"]))
