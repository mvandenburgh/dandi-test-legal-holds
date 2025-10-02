output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = module.dandi_s3_bucket.bucket_name
}

output "aws_access_key_id" {
  description = "The AWS access key ID for the user"
  value       = aws_iam_access_key.this.id
}

output "aws_secret_access_key" {
  description = "The AWS secret access key for the user"
  value       = aws_iam_access_key.this.secret
  sensitive   = true
}
