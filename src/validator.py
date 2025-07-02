import subprocess
import json
import os

class TerraformValidator:
    def __init__(self, terraform_path):
        self.terraform_path = terraform_path
        self.reports = []

    def _run_command(self, command, cwd=None):
        try:
            process = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return process.stdout, process.stderr
        except subprocess.CalledProcessError as e:
            return e.stdout, e.stderr
        except FileNotFoundError:
            return "", f"Error: Command not found. Please ensure '{command[0]}' is installed and in your PATH."

    def validate_terraform_syntax(self):
        print(f"Running terraform validate in {self.terraform_path}...")
        stdout, stderr = self._run_command(["terraform", "validate"], cwd=self.terraform_path)
        
        report_entry = {
            "tool": "terraform validate",
            "severity": "INFO",
            "message": "Terraform syntax validation completed.",
            "details": stdout if stdout else "No output from terraform validate.",
            "errors": stderr if stderr else "No errors."
        }

        if "Error" in stderr or "Error" in stdout:
            report_entry["severity"] = "ERROR"
            report_entry["message"] = "Terraform syntax validation failed."
        elif "Warning" in stderr or "Warning" in stdout:
            report_entry["severity"] = "WARNING"
            report_entry["message"] = "Terraform syntax validation completed with warnings."
        
        self.reports.append(report_entry)
        return report_entry["severity"] != "ERROR"

    def run_tfsec(self):
        print(f"Running tfsec in {self.terraform_path}...")
        stdout, stderr = self._run_command(["tfsec", "--format=json", self.terraform_path])
        
        report_entry = {
            "tool": "tfsec",
            "severity": "INFO",
            "message": "tfsec scan completed.",
            "details": "",
            "errors": stderr if stderr else "No errors."
        }

        if stderr and "Error" in stderr:
            report_entry["severity"] = "ERROR"
            report_entry["message"] = "tfsec scan failed."
            report_entry["details"] = stderr
        else:
            try:
                tfsec_output = json.loads(stdout)
                report_entry["details"] = tfsec_output
                if tfsec_output.get("results"):
                    report_entry["severity"] = "CRITICAL" if any(r.get("severity") == "CRITICAL" for r in tfsec_output["results"]) else \
                                               "HIGH" if any(r.get("severity") == "HIGH" for r in tfsec_output["results"]) else \
                                               "MEDIUM" if any(r.get("severity") == "MEDIUM" for r in tfsec_output["results"]) else \
                                               "LOW" if any(r.get("severity") == "LOW" for r in tfsec_output["results"]) else \
                                               "UNKNOWN"
                    report_entry["message"] = f"tfsec found {len(tfsec_output['results'])} issues."
            except json.JSONDecodeError:
                report_entry["severity"] = "ERROR"
                report_entry["message"] = "tfsec output is not valid JSON."
                report_entry["details"] = stdout
        
        self.reports.append(report_entry)
        return report_entry["severity"] not in ["ERROR", "CRITICAL", "HIGH"]

    def run_checkov(self):
        print(f"Running checkov in {self.terraform_path}...")
        stdout, stderr = self._run_command(["checkov", "-d", self.terraform_path, "-o", "json"])
        
        report_entry = {
            "tool": "checkov",
            "severity": "INFO",
            "message": "checkov scan completed.",
            "details": "",
            "errors": stderr if stderr else "No errors."
        }

        if stderr and "Error" in stderr:
            report_entry["severity"] = "ERROR"
            report_entry["message"] = "checkov scan failed."
            report_entry["details"] = stderr
        else:
            try:
                checkov_output = json.loads(stdout)
                report_entry["details"] = checkov_output
                summary = checkov_output[0].get("summary", {}) if checkov_output else {}
                
                if summary.get("failed", 0) > 0:
                    report_entry["severity"] = "HIGH" # Checkov doesn't have explicit severity levels in summary, so we'll use HIGH for failures
                    report_entry["message"] = f"checkov found {summary.get('failed', 0)} failed checks."
                elif summary.get("passed", 0) > 0:
                    report_entry["message"] = f"checkov passed {summary.get('passed', 0)} checks."
            except json.JSONDecodeError:
                report_entry["severity"] = "ERROR"
                report_entry["message"] = "checkov output is not valid JSON."
                report_entry["details"] = stdout
        
        self.reports.append(report_entry)
        return report_entry["severity"] != "ERROR" and report_entry["severity"] != "HIGH"

    def validate_naming_conventions(self):
        # Placeholder for naming convention validation
        # This would involve parsing .tf files and checking resource names against defined patterns
        print("Running naming convention validation (placeholder)...")
        report_entry = {
            "tool": "Custom Naming Conventions",
            "severity": "INFO",
            "message": "Naming convention validation completed (placeholder).",
            "details": "Implement actual naming convention checks here.",
            "errors": ""
        }
        self.reports.append(report_entry)
        return True

    def validate_tagging_standards(self):
        # Placeholder for tagging standards validation
        # This would involve parsing .tf files and checking for required tags and their values
        print("Running tagging standards validation (placeholder)...")
        report_entry = {
            "tool": "Custom Tagging Standards",
            "severity": "INFO",
            "message": "Tagging standards validation completed (placeholder).",
            "details": "Implement actual tagging standards checks here.",
            "errors": ""
        }
        self.reports.append(report_entry)
        return True

    def validate_dependencies(self):
        # Placeholder for dependency validation and circular dependency detection
        print("Running dependency validation (placeholder)...")
        report_entry = {
            "tool": "Custom Dependency Validation",
            "severity": "INFO",
            "message": "Dependency validation completed (placeholder).",
            "details": "Implement actual dependency and circular dependency checks here.",
            "errors": ""
        }
        self.reports.append(report_entry)
        return True

    def provide_performance_recommendations(self):
        # Placeholder for performance recommendations
        print("Providing performance recommendations (placeholder)...")
        report_entry = {
            "tool": "Custom Performance Recommendations",
            "severity": "INFO",
            "message": "Performance recommendations provided (placeholder).",
            "details": "Implement actual performance recommendations here (e.g., resource sizing, networking best practices).",
            "errors": ""
        }
        self.reports.append(report_entry)
        return True

    def generate_report(self):
        print("\n--- Validation Report ---")
        for entry in self.reports:
            print(f"Tool: {entry['tool']}")
            print(f"Severity: {entry['severity']}")
            print(f"Message: {entry['message']}")
            if entry['details']:
                print(f"Details: {json.dumps(entry['details'], indent=2)}")
            if entry['errors']:
                print(f"Errors: {entry['errors']}")
            print("-" * 20)
        print("--- Report End ---")

    def validate_all(self):
        print("Starting comprehensive Terraform validation...")
        self.reports = [] # Clear previous reports
        
        # Run all validation checks
        self.validate_terraform_syntax()
        self.run_tfsec()
        self.run_checkov()
        self.validate_naming_conventions()
        self.validate_tagging_standards()
        self.validate_dependencies()
        self.provide_performance_recommendations()
        
        self.generate_report()
        print("Comprehensive Terraform validation completed.")

if __name__ == "__main__":
    # Example usage: Replace with the actual path to your Terraform code
    # For testing, you might create a dummy directory with some .tf files
    dummy_terraform_path = "./dummy_terraform_code"
    os.makedirs(dummy_terraform_path, exist_ok=True)
    with open(os.path.join(dummy_terraform_path, "main.tf"), "w") as f:
        f.write('''
resource "aws_s3_bucket" "my_bucket" {
  bucket = "my-unique-bucket-name-12345"
  acl    = "private"

  tags = {
    Environment = "dev"
    Project     = "CloudCraver"
  }
}

resource "aws_instance" "web" {
  ami           = "ami-0abcdef1234567890" 
  instance_type = "t2.micro"
}
''')
    
    validator = TerraformValidator(dummy_terraform_path)
    validator.validate_all()

    # Clean up dummy directory
    import shutil
    shutil.rmtree(dummy_terraform_path)
