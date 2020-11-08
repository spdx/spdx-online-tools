# Deployment Environment

The deployment environment is Docker running on an AWS EC2 server serving the DJango application and Redis server.  Amazon RDS SQLServer is used for the database.

Docker images are stored in Amazon ECR

# Updating the image

Following are the steps for updating the images:

* If the license matcher version has changed, update the requirements.txt file with the correct git tag
* On you local machine, update the docker-compose.prod.yml - these can be copied from the ECR repositories information in AWS
  * replace `<aws-account-id>` with the AWS account ID
  * replace `<aws-region>` with the AWS region
  * replace `<version>` with the specific version of the spdx-online-tools-build to be deployed
* Build the image by running `docker-compose -f docker-compose.prod.yml build`
* Push the image to AWS ECR
  * Login to ECR using the AWS CLI by running `aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com` replacing the region and account ID
  * Push the images by running `docker-compose -f docker-compose.prod.yml push`
  
* Deploy the images on EC2
  * Clone this repo on the EC2 instance - a convenient way to copy of the docker-compose files
  * Login to ECR using the AWS CLI by running `aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com` replacing the region and account ID
  * Pull the online-tools image by running `docker pull <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/spdx/online-tools:<version>` replacing the <aws-account-id>, <aws-region>, and <version>
  * Launch the containers with the command `docker-compose -f docker-compose.prod.yml up -d`
  * If needed upgrade the database:
    * Stop the current Python service with the command `docker exec spdx_prod supervisorctl stop spdx`
	* Make migrations by running the command `docker exec spdx_prod python src/manage.py makemigrations`
	* Upgrade the database with the command `docker exec spdx_prod python src/manage.py migrate`
	* Start the spdx_prod service with the command `docker exec spdx_prod supervisorctl start spdx`
	
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
  * Add the logged in user to the docker group following the [fixing docker permissions documentation](https://www.digitalocean.com/community/questions/how-to-fix-docker-got-permission-denied-while-trying-to-connect-to-the-docker-daemon-socket)
  * Configure the AWS CLI for access to AWS with permissions to use ECR
* Setup an IAM role to enable EC2 access to Amazon ECR
  * Create an IAM role using the EC2 use case with the policy AmazonEC2ContainerRegistryPowerUser
  * Attach the role to the EC2 instance
* Create a repository in the Amazon ECR spdx/online-tools
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
  * replace `<version>` with the specific version of the spdx-online-tools-build to be deployed
* Build the image by running `docker-compose -f docker-compose.prod.yml build`
* Push the image to AWS ECR
  * Login to ECR using the AWS CLI by running `aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com` replacing the region and account ID
  * Push the images by running `docker-compose -f docker-compose.prod.yml push`
* Setup the SSL Certificates
  * Edit the file scripts/init-letsencrypt.sh replacing the email address and setting staging to 1 if testing, 0 if in production
  * Execut the scriptrun `chmod +x init-letsencrypt.sh` and `sudo ./init-letsencrypt.sh`.
* Deploy the images on EC2
  * Clone this repo on the EC2 instance - a convenient way to copy of the docker-compose files
  * Login to ECR using the AWS CLI by running `aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com` replacing the region and account ID
  * Pull the online-tools image by running `docker pull <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/spdx/online-tools:<version>` replacing the <aws-account-id>, <aws-region>, and <version>
  * Create the spdx-prod.env file

```
DEBUG=0
ONLINE_TOOL_GITHUB_KEY=[Github key - see README.md for more information]
ONLINE_TOOL_GITHUB_SECRET=[Github secret - see README.md for more information]
DJANGO_SECRET_KEY=[Django secret key - see README.md for more information]
DIFF_REPO_WITH_OWNER=spdx/licenseRequestImages
DIFF_REPO_GIT_TOKEN=[Github token for a github user with commit access to the DIFF_REPO_WITH_OWNER]
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=spdx_db
SQL_USER=postgres
SQL_PASSWORD=[SQL database password set while creating the RDS database]
SQL_HOST=[RDS Endpoint]
SQL_PORT=5432
```

  * Launch the containers with the command `docker-compose -f docker-compose.prod.yml up -d`
* Initialize the database
  * Find the container ID for the spdx-online-tools by executing `docker ps`
  * Open a shell in the spdx-online-tools container by executing `docker exec -it [spdx-online-tools-container-id] /bin/shell`
  * Initialize the database using DJango by running `python manage.py migrate`
  * Populate the license list database by running `python src/populate.py`
* Restart the spdx
  * run supervisorctl `supervisorctl`
  * restart spdx `restart spdx`
  * exit supervisorctl `exit`
  
  

# Credits

Based on the [Deploying Django to AWS with Docker and Let's Encrypt blog post](https://testdriven.io/blog/django-docker-https-aws/) and [Nginx and Let’s Encrypt with Docker in Less Than 5 Minutes](https://medium.com/@pentacent/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71)

# TODO

* Add environment variables OAUTH_APP_ID and OAUTH_APP_SECRET to the spdx-prod.env to enable license submittal API (see README for instructions)
* Turn off debug in the spdx-prod.env file
