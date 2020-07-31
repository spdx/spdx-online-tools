# Deployment Architecture
The SPDX Online Tools is deployed on Amazon Web Services.

The tools use the following components:
* Docker image for the Python / DJango application
* Docker image for the Redis server
* Amazon RDS PostgreSQL server for the database
* S3 bucket for the media folder
* Kubernetes for the deployment orchestration

# Initial Deployment

## Prerequisites

The following must be implemented on your local machine:

* Amazon EKS CTL and Kubectl - see [Getting Started with eksctl](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl.html)
* Configure eksctl with credentials to access AWS EKS cluster (described in the documentation above)

## Deployment steps

* Setup a cluster as described in the [Getting Started with eksctl](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl.html)
 * Be sure to choose Managed Nodes - Linux for the compute engine
* Setup the driver for the AWS EBS driver - see the [EKS Persistent Storage documentation](https://aws.amazon.com/premiumsupport/knowledge-center/eks-persistent-storage/)
* Create a volume in EBS for the redis data volume
 * See the [Creating an Amazon EBS volume user guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-creating-volume.html)
* Change to the spec directory
* Update the data-volume-static.yml file with the created volume name
* Create the PV in Kubernetes
 * run `kubectl apply -f data-volume-static.yml`
* Verify the volume was created
 * run `kubectl get pv` to verify the volume was created successfully
* Create the persistent volume claim for Redis
 * run `kubectl apply -f data-volume-persistentvolumeclaim.yaml`
* Create the redis service
 * run `kubectl apply -f redis-service.yaml`
* Create the SPDX service
 * run `kubectl apply -f spdx-service.yaml`
* Deploy redis
 * run `kubectl apply -f redis-deployment.yaml`
* Deploy SPDX online tools
 * run `kubectl apply -f spdx-deployment.yaml`

# TODO
* Add a load balancer front end for public access
* Add SSL support
* Create RDS PostgreSQL server

# Notes
We can not use AWS Fargate since we use persistent volumes for RDS and the application

