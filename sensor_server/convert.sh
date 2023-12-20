#!/bin/bash
echo "$(date) convert entry" >> /home/ec2-user/learning/aws_ec2_sensor/cronlog.log
python3 /home/ec2-user/learning/aws_ec2_sensor/data_convert.py