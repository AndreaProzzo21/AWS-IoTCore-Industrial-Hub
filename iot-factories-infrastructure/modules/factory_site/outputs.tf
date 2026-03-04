output "thing_names" {

  value = [for t in aws_iot_thing.factory_device : t.name]

}



output "policy_arn" {

  value = aws_iot_policy.site_policy.arn

}



output "certificate_arns" {

  value = { for k, v in aws_iot_certificate.device_cert : k => v.arn }

}