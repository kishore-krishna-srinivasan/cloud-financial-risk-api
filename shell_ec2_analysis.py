# Bootstrap script: Shell script to set up the EC2 instances to run the application for Monte Carlo Simulations

#!/bin/bash
# Updating system packages
sudo yum update -y

# Installing Python 3 and pip
sudo yum install python3 -y
sudo yum install python3-pip -y

# Upgrading pip and install virtualenv
sudo pip3 install --upgrade pip
sudo pip3 install virtualenv

# Creating a virtual environment for the application
mkdir /home/ec2-user/app
cd /home/ec2-user/app
virtualenv venv

# Activating the virtual environment
source venv/bin/activate

# Installing necessary Python packages
pip install numpy pandas matplotlib boto3

# Downloading the analysis script from S3
aws s3 cp s3://analyses3bucket/run_analysis.py /home/ec2-user/app/run_analysis.py

# Setting up environment variables for the application
export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET=analyses3bucket
export S3_INPUT_PATH=input-data
export S3_OUTPUT_PATH=output-data

# Setting up logging
touch /var/log/monte_carlo_analysis.log
chown ec2-user:ec2-user /var/log/monte_carlo_analysis.log

# Improvinh security by disabling ssh (if not required)
sudo systemctl stop sshd
sudo systemctl disable sshd
