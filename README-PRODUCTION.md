# Deployment Environment

The deployment environment is Docker running on an AWS EC2 server serving the DJango application and Redis server.  Amazon RDS SQLServer is used for the database.

# Clean Intialial Install

Following are the steps for a clean initial installaction of the application:

* Launch an AWS EC2 instance
  * Reccomend Ubuntu Server 18.04 LTS (HVM)
  * Reccomend T2 medium
* Login to the instance and install Docker and Docker-Compose
  * See Docker [Installation for Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
  * Dowload docker-compose: `sudo curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
  * Set execution permissions: `sudo chmod +x /usr/local/bin/docker-compose`
```
$ sudo apt update
$ sudo apt install apt-transport-https ca-certificates curl software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
$ sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
$ sudo apt update
$ sudo apt install docker-ce
$ sudo usermod -aG docker ${USER}
$ sudo curl -L "https://github.com/docker/compose/releases/download/1.25.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
$ sudo chmod +x /usr/local/bin/docker-compose
```

# Credits

Based on the [Deploying Django to AWS with Docker and Let's Encrypt blog post](https://testdriven.io/blog/django-docker-https-aws/)

# TODO

* Add environment variables OAUTH_APP_ID and OAUTH_APP_SECRET to the spdx-prod.env to enable license submittal API (see README for instructions)
* Turn off debug in the spdx-prod.env file
* Add SSL - see [Django with LetsEncrypt Blog](https://testdriven.io/blog/django-lets-encrypt/)