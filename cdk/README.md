
# CDK Project!

This exammple contains a cdk project to deploy infrastructure using somewhat generic pipeline
In these examples, we deploy a vpc, an autoscaling group, a fargate cluster with 2 services and a datavase
the asg and the fargate services are behind the same load balancer.


## Important 1
The pipeline works with a codecommit repository.
make sure to update `cdk/cdkapp/config/environment_1.py` and `cdk/cdkapp/config/project.py` files with your own informations.

## Important 2
Make sure that the environments you deploy in are already bootsraped

Enjoy!
