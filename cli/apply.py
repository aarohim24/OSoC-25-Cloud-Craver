print(" Loaded cli/apply.py")

def run():
    import argparse

    parser = argparse.ArgumentParser(description="Apply Terraform configuration to cloud")
    parser.add_argument("--auto-approve", action="store_true", help="Skip approval prompt")
    args = parser.parse_args()

    print("apply.run() was called")

    if args.auto_approve:
        print("Applying Terraform configuration automatically...")
    else:
        input("Press Enter to confirm applying the configuration...")

    print("Terraform apply complete (simulated)")
