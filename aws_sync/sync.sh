#!/bin/bash

AWS_CLI_PATH="/usr/local/bin/aws"
echo "$(date) Log entry" >> /app/db/cronlog.log
$AWS_CLI_PATH s3 sync --exclude "*" --include "db/label*" /app/db s3://sengital-apas/counter --region ap-east-1