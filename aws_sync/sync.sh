#!/bin/bash
echo "$(date) Log entry" >> /app/counter_server/db/cronlog.log
aws s3 sync /app/counter_server/db/ s3://lalamove-apas/counter