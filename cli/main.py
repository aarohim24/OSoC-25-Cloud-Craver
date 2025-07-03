
"""
Cloud Craver CLI Entry Point
"""

import argparse
import sys
from cli import generate, validate, apply, state_switch 

def main():
    parser = argparse.ArgumentParser(description="Cloud Craver CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("generate", help="Generate Terraform templates")
    subparsers.add_parser("validate", help="Validate generated templates")
    subparsers.add_parser("apply", help="Apply templates to cloud provider")
    subparsers.add_parser("state-switch", help="Switch environment state")

    args, unknown = parser.parse_known_args()

    if args.command == "generate":
        sys.argv = [sys.argv[0]] + unknown
        generate.run()

    elif args.command == "validate":
        sys.argv = [sys.argv[0]] + unknown
        validate.run()

    elif args.command == "apply":
        sys.argv = [sys.argv[0]] + unknown
        apply.run()


    elif args.command == "state-switch":
        sys.argv = [sys.argv[0]] + unknown
        state_switch.run()

    else:
        parser.print_help()
