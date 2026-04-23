terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Latest Ubuntu 24.04 LTS AMI ───────────────────────────────────────────────

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── IAM Role for EC2 to access SSM ───────────────────────────────────────────

resource "aws_iam_role" "castor_ec2" {
  name = "castor-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = { Project = "castor" }
}

resource "aws_iam_role_policy" "castor_ssm" {
  name = "castor-ssm-policy"
  role = aws_iam_role.castor_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:PutParameter",
        "kms:Decrypt"
      ]
      Resource = [
        "arn:aws:ssm:${var.aws_region}:*:parameter/castor/*",
        "arn:aws:kms:${var.aws_region}:*:key/*"
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "castor" {
  name = "castor-instance-profile"
  role = aws_iam_role.castor_ec2.name
}

# ── Security Group ────────────────────────────────────────────────────────────

resource "aws_security_group" "castor" {
  name        = "castor-sg"
  description = "Castor app security group"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH"
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Castor web UI"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "castor-sg", Project = "castor" }
}

# ── SSH Key Pair ──────────────────────────────────────────────────────────────

resource "aws_key_pair" "castor" {
  key_name   = "castor-key"
  public_key = file(var.ssh_public_key_path)
}

# ── EC2 Instance ──────────────────────────────────────────────────────────────

resource "aws_instance" "castor" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.castor.key_name
  vpc_security_group_ids = [aws_security_group.castor.id]
  iam_instance_profile   = aws_iam_instance_profile.castor.name

  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    repo_url     = var.repo_url
    flask_secret = var.flask_secret_key
    aws_region   = var.aws_region
  })

  tags = { Name = "castor", Project = "castor" }
}
