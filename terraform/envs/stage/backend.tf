terraform {
  backend "s3" {
    bucket         = "pywallet-stage-tfstate"
    key            = "envs/stage/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "pywallet-stage-tf-lock"
    encrypt        = true
    profile        = "pywallet-stage"
  }
}
