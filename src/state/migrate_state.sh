#!/bin/bash
OLD_BACKEND=$1
NEW_BACKEND=$2

terraform init -backend-config=$OLD_BACKEND
terraform state pull > state.tfstate.backup

echo "Switching backend..."
mv $NEW_BACKEND backend.tf

terraform init -migrate-state
terraform state push state.tfstate.backup
