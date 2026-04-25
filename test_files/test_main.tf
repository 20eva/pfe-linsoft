resource "aws_security_group" "open" {
  name = "open-to-world"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "main" {
  identifier = "prod-db"
  password   = "supersecret123"
  username   = "admin"
}

resource "aws_iam_role_policy" "admin" {
  name = "admin-policy"
  policy = jsonencode({
    Effect   = "Allow"
    Action   = "*"
    Resource = "*"
  })
}