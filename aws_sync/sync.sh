#!/bin/bash

AWS_CLI_PATH="/usr/local/bin/aws"
echo "$(date) Log entry" >> /app/db/cronlog.log
$AWS_CLI_PATH s3 sync /app/db s3://sengital-apas/counter --region ap-east-1 --exclude "*" --include "label*"