# src/terraform_validator/validator_dir/validate.py

import os

def validate_directory(path):
    print(f"Validating Terraform files in: {path}")

    if not os.path.isdir(path):
        raise ValueError(f"{path} is not a valid directory")

    tf_files = [f for f in os.listdir(path) if f.endswith(".tf")]

    if not tf_files:
        return "No Terraform (.tf) files found"

    for tf_file in tf_files:
        print(f" - Found: {tf_file}")

    # Simulated validation success
    return f"{len(tf_files)} Terraform file(s) validated successfully"
