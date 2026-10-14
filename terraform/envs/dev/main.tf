locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
  }
}


module "network" {
  source = "../../modules/network"

  name_prefix = local.name_prefix
  vpc_cidr    = "10.20.0.0/16"
  azs         = ["ap-southeast-1a", "ap-southeast-1b"]

  public_subnet_cidrs  = ["10.20.0.0/24", "10.20.1.0/24"]
  private_subnet_cidrs = ["10.20.10.0/24", "10.20.11.0/24"]


  tags = local.common_tags
}


data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


resource "aws_security_group" "ec2_ssh" {
  name        = "${var.project}-${var.environment}-ec2-ssh"
  description = "Allow SSH access from my IP"
  vpc_id      = module.network.vpc_id

  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-ec2-ssh"
    }
  )
}


module "ec2" {
  source = "../../modules/ec2"

  name                = "${var.project}-${var.environment}-ec2"
  ami_id              = data.aws_ami.ubuntu.id
  instance_type       = var.instance_type
  subnet_id           = module.network.public_subnet_ids[0]
  security_group_ids  = [aws_security_group.ec2_ssh.id]
  key_name            = var.key_name
  associate_public_ip = true

  tags = local.common_tags
}

module "rds" {
  source = "../../modules/rds"

  name_prefix               = "${var.project}-${var.environment}"
  vpc_id                    = module.network.vpc_id
  subnet_ids                = module.network.private_subnet_ids
  allowed_security_group_id = aws_security_group.ec2_ssh.id
  db_name                   = "pywallet"
  username                  = "pywallet"
  backup_retention_period   = 0
  deletion_protection       = false
  skip_final_snapshot       = true

  tags = local.common_tags
}
