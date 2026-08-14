# Assume role policy for Lambda
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# -----------------------------------------------------------------------------
# Ingress Lambda IAM Role & Policies
# -----------------------------------------------------------------------------
resource "aws_iam_role" "ingress" {
  name               = "${local.resource_name_prefix}-ingress-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "ingress_policy" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    sid    = "DynamoDBWriteAccess"
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.sessions.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ingress" {
  name   = "${local.resource_name_prefix}-ingress-policy"
  role   = aws_iam_role.ingress.id
  policy = data.aws_iam_policy_document.ingress_policy.json
}

# -----------------------------------------------------------------------------
# Worker Lambda IAM Role & Policies
# -----------------------------------------------------------------------------
resource "aws_iam_role" "worker" {
  name               = "${local.resource_name_prefix}-worker-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "worker_policy" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    sid    = "DynamoDBFullAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
    ]
    resources = [
      aws_dynamodb_table.sessions.arn,
    ]
  }

  statement {
    sid    = "DynamoDBStreamsAccess"
    effect = "Allow"
    actions = [
      "dynamodb:DescribeStream",
      "dynamodb:GetRecords",
      "dynamodb:GetShardIterator",
      "dynamodb:ListStreams",
    ]
    resources = [
      "${aws_dynamodb_table.sessions.arn}/stream/*",
    ]
  }
}

resource "aws_iam_role_policy" "worker" {
  name   = "${local.resource_name_prefix}-worker-policy"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker_policy.json
}
