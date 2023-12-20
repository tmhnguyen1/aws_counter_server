#!/bin/bash
echo "$(date) Log entry" >> /home/ec2-user/learning/aws_ec2/cronlog.log
aws s3 sync /home/ec2-user/learning/aws_ec2/db/ s3://lalamove-apas/counter