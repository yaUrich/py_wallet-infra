variable "aws_region" {
  description = "AWS region for this environment"
  type        = string
  default     = "ap-southeast-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name"
  type        = string
  default     = "pywallet-stage"
}

variable "project" {
  description = "Project tag value"
  type        = string
  default     = "pywallet"
}

variable "environment" {
  description = "Environment tag value"
  type        = string
  default     = "stage"
}

variable "owner" {
  description = "Owner tag value"
  type        = string
  default     = "alex"
}

variable "key_name" {
  description = "Existing AWS EC2 key pair name"
  type        = string
  default     = "pywallet-stage-key"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "my_ip_cidr" {
  description = "Your public IP in /32 CIDR format for SSH access"
  type        = string

  validation {
    condition     = can(cidrhost(var.my_ip_cidr, 0)) && endswith(var.my_ip_cidr, "/32")
    error_message = "my_ip_cidr must be a valid IPv4/IPv6 CIDR and end with /32 (example: 203.0.113.10/32)."
  }
}
