"""A Python Pulumi program"""

import pulumi
import pulumi_aws as aws

"""
these configs can be set by doing
pulumi config set key val.

the subdomain is used for the cloudfront subdomain and the S3 bucket name
"""
config = pulumi.Config()
subdomain = config.get("subdomain")
acm_certificate_arn = config.get("acm_certificate_arn")  # should be for *.domain.com
route_53_zone_id = config.get("route_53_zone_id")

hosted_zone = aws.route53.get_zone(zone_id=route_53_zone_id)
fqdn = f"{subdomain}.{hosted_zone.name}"
bucket = aws.s3.Bucket(
    subdomain,  # the name of the bucket matches the subdomain
    aws.s3.BucketArgs(website=aws.s3.BucketWebsiteArgs(index_document="index.html")),
)

# this is an aws managed policy
# https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html#managed-cache-caching-optimized
cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"

public_access_block = aws.s3.BucketPublicAccessBlock(
    "public-access-block",
    bucket=bucket.bucket,
    block_public_policy=False,
)

aws.s3.BucketPolicy(
    "bucket-policy",
    bucket=bucket.bucket,
    policy=pulumi.Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [
                        pulumi.Output.concat(bucket.arn, "/*"),
                    ],
                }
            ],
        }
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[public_access_block],
    ),
)

aws.s3.BucketObject(
    "index.html",
    bucket=bucket.bucket,
    source=pulumi.FileAsset("www/index.html"),
    content_type="text/html",
)


distribution = aws.cloudfront.Distribution(
    "s3-distribution",
    origins=[
        aws.cloudfront.DistributionOriginArgs(
            domain_name=bucket.bucket_regional_domain_name,
            origin_id=subdomain,
        )
    ],
    aliases=[fqdn],
    enabled=True,
    is_ipv6_enabled=True,
    default_root_object="index.html",
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        acm_certificate_arn=acm_certificate_arn,
        ssl_support_method="sni-only",
        minimum_protocol_version="TLSv1.2_2021",  # latest
    ),
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        allowed_methods=["GET", "HEAD"],
        cached_methods=["GET", "HEAD"],
        target_origin_id=subdomain,
        viewer_protocol_policy="redirect-to-https",
        cache_policy_id=cache_policy_id,
    ),
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
        ),
    ),
)

# Create a Route53 CNAME record
dns_record = aws.route53.Record(
    "dns-record",
    zone_id=route_53_zone_id,
    name=subdomain,
    type="CNAME",
    ttl=300,
    records=[distribution.domain_name],
)

pulumi.export("s3_bucket_id", bucket.id)
pulumi.export("cloudfront_id", distribution.id)
pulumi.export("url", dns_record.fqdn)
