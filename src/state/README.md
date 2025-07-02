# Terraform State Management

This folder contains tools and configuration for remote state management across cloud backends.

## Features

- Multi-backend support: S3, Azure Blob, GCS
- Workspace automation
- State migration and backup tools
- Drift detection and reporting

## Scripts

| Script              | Description                        |
|---------------------|------------------------------------|
| `workspace.sh`      | Create/select workspace            |
| `migrate_state.sh`  | Migrate state to new backend       |
| `detect_drift.sh`   | Detect state drift                 |
| `backup_state.sh`   | Pull and save a backup of state    |

## Setup

```bash
cd state
./workspace.sh dev
terraform init -backend-config=backend/s3.tf
```
