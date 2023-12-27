#!/bin/bash

AWS_CLI_PATH="/usr/local/bin/aws"
echo "$(date) Log entry" >> /app/counter_server/db/cronlog.log
$AWS_CLI_PATH s3 sync /app/counter_server/db/ s3://lalamove-apas/counter/test_counter --region ap-east-1