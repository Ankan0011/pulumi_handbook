"""A Python Pulumi program"""

from warnings import filters
import pulumi
import pulumi_aws as aws
import os

#Section 1
#Creates a bucket object
bucket = aws.s3.Bucket(
    "my-bucket",
    website= aws.s3.BucketWebsiteArgs(
        index_document="index.html"
    )
)
filepath = os.path.join('site','index.html')

#Bucket object pointing to the S3 assest.
obj = aws.s3.BucketObject("index.html", 
                        bucket = bucket.bucket, 
                        source=pulumi.FileAsset(filepath),
                        acl='public-read',
                        content_type='text/html')

pulumi.export('bucket_name', bucket.bucket)
pulumi.export('bucket_endpoint', pulumi.Output.concat('http://', bucket.website_endpoint))
