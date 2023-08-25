#!/bin/bash
echo "$(date) Sync entry" >> /home/ec2-user/learning/aws_ec2_sensor/cronlog.log
aws s3 sync /home/ec2-user/learning/aws_ec2_sensor/data_csv/ s3://lalamove-apas/sensor_logger