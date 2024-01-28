#!/bin/bash
set -e

subdomain=$1
cloudfront_id=$2

# Check if subdomain or cloudfront_id is empty
if [ -z "$subdomain" ] || [ -z "$cloudfront_id" ]; then
    echo "Error: subdomain or cloudfront_id is not provided."
    echo "Usage: $0 <subdomain> <cloudfront_id>"
    exit 1
fi

set -x

aws s3 sync www "s3://$subdomain" --delete
aws cloudfront create-invalidation --distribution-id $cloudfront_id --paths "/*"
