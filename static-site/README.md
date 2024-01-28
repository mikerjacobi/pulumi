
# pulumi static site

Followed this tutorial:

https://pulumi.awsworkshop.io/25_intro_modern_iac_python/20_getting_started_with_pulumi/1_new_project.html

This creates and configures an S3 bucket to host a static site purely from command line.

# steps to run this

```
pulumi new python -y
source venv/bin/activate
pip3 install -r requirements.txt
pulumi config set aws:region us-west-2
pulumi config set aws:profile default
pulumi config set subdomain my-site
# find this in AWS console for ACM
pulumi config set acm_certificate_arn arn:aws:acm:us-east-1:<acct>:certificate/<cert>
# find this in route 53 zone details
config set route_53_zone_id <zone_id>

pulumi up
```

# deploy new version of site
```
pulumi stack select dev 
./deploy.sh $(pulumi stack output s3_bucket_id) $(pulumi stack output cloudfront_id)
```