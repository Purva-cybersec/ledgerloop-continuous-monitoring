# LedgerLoop customer data storage (simulated).
# This file describes cloud storage as code. It is scanned, never deployed.

provider "aws" {
  region = "us-east-1"
}

# The bucket that holds customers' expense data.
resource "aws_s3_bucket" "customer_data" {
  bucket = "ledgerloop-customer-expense-data"
}
