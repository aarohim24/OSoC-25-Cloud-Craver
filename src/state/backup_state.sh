#!/bin/bash
ENV=$1
DATE=$(date +%F_%H-%M)
FILE="backup_${ENV}_${DATE}.tfstate"

terraform workspace select $ENV
mkdir -p backups
terraform state pull > backups/$FILE
echo "📦 Backup saved to backups/$FILE"
