#!/bin/bash
terraform init -backend=false >/dev/null
terraform plan -detailed-exitcode

if [ $? -eq 2 ]; then
  echo "❗ Drift detected"
elif [ $? -eq 0 ]; then
  echo "✅ No drift"
else
  echo "⚠️ Error during plan"
fi
