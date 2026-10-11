# LedgerLoop customer data storage (simulated).
# This file describes cloud storage as code. It is scanned, never deployed.

provider "aws" {
  region = "us-east-1"
}

# The bucket that holds customers' expense data.
resource "aws_s3_bucket" "customer_data" {
  bucket = "ledgerloop-customer-expense-data"
}

# Control 10: customer data is encrypted at rest.
resource "aws_kms_key" "customer_data" {
  description         = "Encryption key for LedgerLoop customer data"
  enable_key_rotation = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "customer_data" {
  bucket = aws_s3_bucket.customer_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.customer_data.arn
    }
  }
}

# Control 18: access to customer financial data is restricted (no public access).
resource "aws_s3_bucket_public_access_block" "customer_data" {
  bucket                  = aws_s3_bucket.customer_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
