# Deployment Environment

The deployment environment is Docker running on an AWS EC2 server serving the DJango application and Redis server.  Amazon RDS SQLServer is used for the database.

Docker images are stored in Amazon ECR

# Clean Intialial Install

Following are the steps for a clean initial installaction of the application:

* Launch an AWS EC2 instance
  * Reccomend Ubuntu Server 18.04 LTS (HVM)
  * Reccomend T2 medium
* Login to the instance and install Docker, Docker-Compose, and AWS CLI
  * See Docker [Installation for Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
  * Dowload docker-compose: `sudo curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
  * Set execution permissions for docker-compose: `sudo chmod +x /usr/local/bin/docker-compose`
  * Install AWS CLI - see the [Installing AWS CLI on Linux documentation](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html)
* Setup an IAM role to enable EC2 access to Amazon ECR
  * Create an IAM role using the EC2 use case with the policy AmazonEC2ContainerRegistryPowerUser
  * Attach the role to the EC2 instance
* Create a repository in the Amazon ECR spdx/online-tools
* Create a repository in the Amazon ECR spdx/nginx
* Create an RDS database
  * Instance name spdx-online-tools-db-production
  * Username spdx
  * Set a password which will be used later in setting some of the environment variables in docker
  * Under connectivity drop down, add VPC security group spdx-online-tools-ec2
  * Change initial database name to spdx_db (under additional config)
* Add an inbound rule to for PostgreSQL access
  * Edit the security group inbound rules for spdx-online-tools-ec2
  * Add PostgreSQL with a source of the EC2 instance (search for spdx-)
* On you local machine, update the docker-compose.prod.yml - these can be copied from the ECR repositories information in AWS
  * replace `<aws-account-id>` with the AWS account ID
  * replace `<aws-region>` with the AWS region
  * replace `<version>` with the specific version of the nginx and spdx-online-tools-build to be deployed
* Update the spdx-prod.env file

```
DEBUG=0
ONLINE_TOOL_GITHUB_KEY=[Github key - see README.md for more information]
ONLINE_TOOL_GITHUB_SECRET=[Github secret - see README.md for more information]
DJANGO_SECRET_KEY=[Django secret key - see README.md for more information]
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=spdx_db
SQL_USER=spdx
SQL_PASSWORD=[SQL database password set while creating the RDS database]
SQL_HOST=[RDS Endpoint]
SQL_PORT=5432
```

* Build the image by running `docker-compose -f docker-compose.prod.yml build`
* Push the image to AWS ECR
  * Login to ECR using the AWS CLI by running `aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com` replacing the region and account ID
  * Push the images by running `docker-compose -f docker-compose.prod.yml push`
  
* Deploy the images on EC2
  * Clone this repo on the EC2 instance - a convenient way to copy of the docker-compose files
  * Login to ECR using the AWS CLI by running `aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com` replacing the region and account ID
  * Pull the nginx image by running `docker pull <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/spdx/nginx:<version>` replacing the <aws-account-id>, <aws-region>, and <version>
  * Pull the online-tools image by running `docker pull <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/spdx/online-tools:<version>` replacing the <aws-account-id>, <aws-region>, and <version>
  

# Credits

Based on the [Deploying Django to AWS with Docker and Let's Encrypt blog post](https://testdriven.io/blog/django-docker-https-aws/)

# TODO

* Add environment variables OAUTH_APP_ID and OAUTH_APP_SECRET to the spdx-prod.env to enable license submittal API (see README for instructions)
* Turn off debug in the spdx-prod.env file
* Add SSL - see [Django with LetsEncrypt Blog](https://testdriven.io/blog/django-lets-encrypt/)