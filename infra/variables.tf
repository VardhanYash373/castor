variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "instance_type" {
  description = "EC2 instance type — t3.micro is free tier eligible"
  type        = string
  default     = "t3.micro"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key (e.g. ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "repo_url" {
  description = "Git repo URL to clone on the instance"
  type        = string
}

variable "flask_secret_key" {
  description = "Flask secret key for session signing"
  type        = string
  sensitive   = true
}
