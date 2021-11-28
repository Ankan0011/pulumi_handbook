"""A Python Pulumi program"""

from warnings import filters
import pulumi
import pulumi_aws as aws
from pulumi_aws.ec2 import default_vpc, security_group
from pulumi_aws.lb import listener, target_group

#Section 2
#Provision an EC2 instance with ssh access
size = "t2.micro"
user_data = """
#!/bin/bash
echo "Hello, World!" > index.html
nohup python -m SimpleHTTPServer 80 &
"""

#Provision a Amazon Machine Image
ami = aws.ec2.get_ami(most_recent="true", 
                    owners=['137112412989'], 
                    filters=[{"name":"name","values":["amzn-ami-hvm-*-x86_64-ebs"]}])

#Provision a Amazon Security Group
group = aws.ec2.SecurityGroup('webserver-secgrp',
                                description='Enable HTTP access',
                                ingress=[
                                        { 'protocol': 'icmp', 'from_port': 8, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0'] },
                                        { 'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0']},
                                    ],
                                egress=[
                                        { 'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0'] },
                                ])
#Fetch the details of a VPC 
default_vpc = aws.ec2.get_vpc(default="true")
default_vpc_subnets = aws.ec2.get_subnet_ids(vpc_id=default_vpc.id)

#Configura a loadbalancer
lb = aws.lb.LoadBalancer("external-loadbalancer",
                            internal="false",
                            security_groups=[group.id],
                            subnets=default_vpc_subnets.ids,
                            load_balancer_type="application")

#Configure TargetGroup for the load balancer
target_group = aws.lb.TargetGroup("target-group",
                                    port=80,
                                    protocol="HTTP",
                                    target_type="ip",
                                    vpc_id=default_vpc.id)

#Configure listeners for the load balance
listener = aws.lb.Listener("listerner",
                            load_balancer_arn=lb.arn,
                            port=80,
                            default_actions=[
                                {
                                    "type": "forward",
                                    "target_group_arn": target_group.arn
                                }
                            ])
                        

ips = []
hostnames = []

#Provision a EC2 Instance
for az in aws.get_availability_zones().names:
    server = aws.ec2.Instance(f'web-server-{az}',
                                instance_type=size,
                                vpc_security_group_ids=[group.id],
                                user_data=user_data,
                                ami=ami.id,
                                availability_zone=az,
                                tags={
                                        "Name": "web-server",
                                },
                                )
    ips.append(server.public_ip)
    hostnames.append(server.public_dns)
    attachment = aws.lb.TargetGroupAttachment(f'web-server-{az}',
        target_group_arn=target_group.arn,
        target_id=server.private_ip,
        port=80,
    )


pulumi.export('ips', ips)
pulumi.export('hostnames', hostnames)
pulumi.export("url", lb.dns_name)