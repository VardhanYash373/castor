output "instance_public_ip" {
  description = "Public IP of the Castor EC2 instance"
  value       = aws_instance.castor.public_ip
}

output "app_url" {
  description = "Castor web UI URL"
  value       = "http://${aws_instance.castor.public_ip}:5000"
}

output "ssh_command" {
  description = "SSH into the instance"
  value       = "ssh ubuntu@${aws_instance.castor.public_ip}"
}
