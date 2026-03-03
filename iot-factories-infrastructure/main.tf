provider "aws" {
  region = var.aws_region
}

# --- SITI INDUSTRIALI ---
# Questo modulo crea i certificati e le "Things" per ogni fabbrica
module "factory_sites" {
  for_each     = var.factories
  source       = "./modules/factory_site"
  factory_name = each.key
  device_list  = each.value.devices
}

# Recupero l'endpoint IoT specifico per la tua regione
data "aws_iot_endpoint" "base_endpoint" {
  endpoint_type = "iot:Data-ATS"
}

# --- 1. IAM ROLE E POLICIES PER LA LAMBDA ---
resource "aws_iam_role" "lambda_multiplexer_role" {
  name = "lambda_multiplexer_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Permessi base (Scrittura Log su CloudWatch)
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_multiplexer_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permessi specifici (Solo SNS, dato che Influx è esterno via HTTP)
resource "aws_iam_role_policy" "lambda_sns_policy" {
  name = "lambda_sns_publish_policy"
  role = aws_iam_role.lambda_multiplexer_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.factory_alerts.arn
      }
    ]
  })
}

# --- 2. SNS (SISTEMA DI ALLERTA EMAIL) ---
resource "aws_sns_topic" "factory_alerts" {
  name = "industrial-factory-alerts"
}

resource "aws_sns_topic_subscription" "admin_email" {
  topic_arn = aws_sns_topic.factory_alerts.arn
  protocol  = "email"
  endpoint  = "and.prozzo@gmail.com" 
}

# --- 3. LAMBDA FUNCTION ---
# Ricorda: questa caricherà tutto ciò che è dentro la cartella /package
data "archive_file" "lambda_multiplexer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/package"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "multiplexer" {
  filename         = data.archive_file.lambda_multiplexer_zip.output_path
  source_code_hash = data.archive_file.lambda_multiplexer_zip.output_base64sha256
  function_name    = "Factory-Data-Multiplexer"
  role             = aws_iam_role.lambda_multiplexer_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 20 # Timeout generoso per gestire la latenza di rete verso la EC2

  environment {
    variables = {
      CONFIG_FILE    = "thresholds.json"
      SNS_TOPIC_ARN  = aws_sns_topic.factory_alerts.arn
      
      # InfluxDB Configuration (Endpoint esterno sulla tua EC2)
      INFLUX_URL     = "http://3.72.7.195:8086" # <--- Inserisci IP
      INFLUX_TOKEN   = "XCVhxS7b4LmALMP03ws36WqRFnPnsq4QzQBRm10kkwF92RZx1jaeeYKfrPWeqfqfaqS5R3dwuNudp9Ek8VKMUQ=="  # <--- Inserisci Token
      INFLUX_ORG     = "my-factories"
      INFLUX_BUCKET  = "telemetry"
    }
  }
}

# --- 4. IOT CORE RULE (IL TRIGGER) ---
resource "aws_lambda_permission" "allow_iot_multiplexer" {
  statement_id  = "AllowExecutionFromIoT"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.multiplexer.function_name
  principal     = "iot.amazonaws.com"
}

resource "aws_iot_topic_rule" "global_factory_rule" {
  name        = "GlobalFactoryDataRule"
  description = "Invia i dati MQTT alla Lambda Multiplexer"
  enabled     = true
  # Seleziona i dati e identifica il sito dal secondo livello del topic
  sql         = "SELECT *, topic(2) as site_id FROM 'factory/+/data'"
  sql_version = "2016-03-23"

  lambda {
    function_arn = aws_lambda_function.multiplexer.arn
  }
}

# --- OUTPUT ---
output "iot_endpoint" {
  value = data.aws_iot_endpoint.base_endpoint.endpoint_address
}