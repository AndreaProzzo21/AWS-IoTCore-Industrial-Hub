# 1. Le "Things" (Oggetti IoT)
resource "aws_iot_thing" "factory_device" {
  for_each = toset(var.device_list)
  name     = "${var.factory_name}-${each.value}"
  attributes = { 
    Factory_Site = var.factory_name 
    Device_Type  = each.value
  }
}

# 2. I Certificati X.509
resource "aws_iot_certificate" "device_cert" {
  for_each = toset(var.device_list)
  active   = true
}

# 3. Policy di Sicurezza Industriale (Isolamento per Sito)
resource "aws_iot_policy" "site_policy" {
  name = "Policy-${var.factory_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["iot:Connect"]
        Resource = ["arn:aws:iot:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:client/${var.factory_name}-*"]
      },
      {
        Effect   = "Allow"
        Action   = ["iot:Publish", "iot:Receive"]
        Resource = ["arn:aws:iot:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:topic/factory/${var.factory_name}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["iot:Subscribe"]
        Resource = ["arn:aws:iot:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:topicfilter/factory/${var.factory_name}/*"]
      }
    ]
  })
}

# 4. Collegamenti (Policy -> Certificato -> Thing)
resource "aws_iot_policy_attachment" "att_policy" {
  for_each = toset(var.device_list)
  policy   = aws_iot_policy.site_policy.name
  target   = aws_iot_certificate.device_cert[each.key].arn
}

resource "aws_iot_thing_principal_attachment" "att_thing" {
  for_each  = toset(var.device_list)
  principal = aws_iot_certificate.device_cert[each.key].arn
  thing     = aws_iot_thing.factory_device[each.key].name
}

# 5. Salvataggio certificati organizzato per Reparto/Sito
resource "local_file" "cert_files" {
  for_each = toset(var.device_list)
  content  = aws_iot_certificate.device_cert[each.key].certificate_pem
  filename = "${path.root}/certs/${var.factory_name}/${each.value}.cert.pem"
}

resource "local_file" "key_files" {
  for_each = toset(var.device_list)
  content  = aws_iot_certificate.device_cert[each.key].private_key
  filename = "${path.root}/certs/${var.factory_name}/${each.value}.private.key"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}