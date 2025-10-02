resource "aws_iam_user" "this" {
  name = "dandi-test-legal-holds"
}

resource "aws_iam_access_key" "this" {
  user = aws_iam_user.this.name
}

# Based on 
# https://github.com/dandi/dandi-infrastructure/blob/master/terraform/sponsored_bucket.tf
module "dandi_s3_bucket" {
  source = "git::https://github.com/dandi/dandi-infrastructure//terraform/modules/dandiset_bucket?ref=add-s3-public-access-block"

  bucket_name                           = "dandi-test-legal-holds"
  public                                = true
  versioning                            = true
  allow_cross_account_heroku_put_object = true
  heroku_user                           = aws_iam_user.this
  embargo_readers                       = []
  log_bucket_name                       = "dandi-test-legal-holds-logs"
  providers = {
    aws         = aws
    aws.project = aws
  }
}

resource "aws_s3_bucket_object_lock_configuration" "this" {
  bucket = module.dandi_s3_bucket.bucket_name
}
