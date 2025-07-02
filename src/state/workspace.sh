#!/bin/bash
ENV=$1
terraform workspace list | grep "$ENV" || terraform workspace new "$ENV"
terraform workspace select "$ENV"
