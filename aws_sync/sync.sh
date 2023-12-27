#!/bin/bash

AWS_CLI_PATH="/usr/local/bin/aws"
echo "$(date) Log entry" >> /app/db/cronlog.log
$AWS_CLI_PATH s3 sync /app/db/ s3://lalamove-apas/counter/test_counter --region ap-east-1