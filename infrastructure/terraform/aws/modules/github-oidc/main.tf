locals {
  subjects = {
    plan    = "repo:${var.github_repository}:environment:${var.github_plan_environment}"
    apply   = "repo:${var.github_repository}:environment:${var.github_apply_environment}"
    destroy = "repo:${var.github_repository}:environment:${var.github_destroy_environment}"
  }

  github_trust_policies = {
    for lifecycle, subject in local.subjects : lifecycle => jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect = "Allow"
        Action = "sts:AssumeRoleWithWebIdentity"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = subject
          }
        }
      }]
    })
  }

  state_statements = {
    plan = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetBucketLocation", "s3:GetBucketVersioning", "s3:ListBucket"]
        Resource = var.state_bucket_arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion"]
        Resource = "${var.state_bucket_arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:DescribeKey"]
        Resource = var.state_kms_key_arn
      }
    ]
    apply = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetBucketLocation", "s3:GetBucketVersioning", "s3:ListBucket"]
        Resource = var.state_bucket_arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${var.state_bucket_arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
        Resource = var.state_kms_key_arn
      }
    ]
    destroy = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetBucketLocation", "s3:GetBucketVersioning", "s3:ListBucket"]
        Resource = var.state_bucket_arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${var.state_bucket_arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
        Resource = var.state_kms_key_arn
      }
    ]
  }

  lifecycle_policies = {
    plan = {
      Version = "2012-10-17"
      Statement = concat(local.state_statements.plan, [{
        Effect = "Allow"
        Action = [
          "budgets:Describe*", "budgets:ViewBudget", "cloudtrail:Describe*",
          "cloudtrail:Get*", "cloudtrail:List*", "ec2:Describe*", "ec2:Get*",
          "eks:Describe*", "eks:List*", "iam:Get*", "iam:List*",
          "kms:Describe*", "kms:Get*", "kms:List*", "logs:Describe*",
          "logs:List*", "s3:Get*", "s3:List*", "sts:GetCallerIdentity"
        ]
        Resource = "*"
      }])
    }
    apply = {
      Version = "2012-10-17"
      Statement = concat(local.state_statements.apply, [
        {
          Effect = "Allow"
          Action = [
            "budgets:CreateBudget", "budgets:DeleteBudget", "budgets:ModifyBudget",
            "budgets:ViewBudget", "cloudtrail:AddTags", "cloudtrail:Create*",
            "cloudtrail:Delete*", "cloudtrail:Describe*", "cloudtrail:Get*",
            "cloudtrail:List*", "cloudtrail:RemoveTags", "cloudtrail:StartLogging",
            "cloudtrail:StopLogging", "cloudtrail:Update*", "ec2:AllocateAddress",
            "ec2:AssociateAddress", "ec2:Attach*", "ec2:AuthorizeSecurityGroup*",
            "ec2:Create*", "ec2:Delete*", "ec2:Describe*", "ec2:Detach*",
            "ec2:DisassociateAddress", "ec2:Modify*", "ec2:ReleaseAddress",
            "ec2:RevokeSecurityGroup*", "eks:Create*", "eks:Delete*",
            "eks:Describe*", "eks:List*", "eks:TagResource", "eks:UntagResource",
            "eks:Update*", "iam:AttachRolePolicy", "iam:CreateRole", "iam:DeleteRole",
            "iam:DeleteRolePolicy", "iam:DetachRolePolicy", "iam:Get*", "iam:List*",
            "iam:PutRolePolicy", "iam:TagRole", "iam:UntagRole",
            "iam:UpdateAssumeRolePolicy", "kms:CancelKeyDeletion", "kms:Create*",
            "kms:Delete*", "kms:Describe*", "kms:Disable*", "kms:Enable*",
            "kms:GenerateDataKey*", "kms:Put*", "kms:ScheduleKeyDeletion",
            "kms:TagResource", "kms:UntagResource", "logs:Create*", "logs:Delete*",
            "logs:Describe*", "logs:Put*", "logs:TagResource", "logs:UntagResource",
            "s3:Create*", "s3:Delete*", "s3:Get*", "s3:List*", "s3:Put*",
            "sts:GetCallerIdentity"
          ]
          Resource = "*"
        },
        {
          Effect    = "Allow"
          Action    = ["ec2:CreateTags", "ec2:DeleteTags"]
          Resource  = "*"
          Condition = { StringEquals = { "aws:RequestTag/managed-by" = "terraform" } }
        },
        {
          Effect    = "Allow"
          Action    = ["iam:PassRole"]
          Resource  = "*"
          Condition = { StringEquals = { "iam:PassedToService" = ["eks.amazonaws.com", "ec2.amazonaws.com"] } }
        }
      ])
    }
    destroy = {
      Version = "2012-10-17"
      Statement = concat(local.state_statements.destroy, [
        {
          Effect = "Allow"
          Action = [
            "ec2:AllocateAddress", "ec2:AssociateAddress", "ec2:Delete*",
            "ec2:Describe*", "ec2:Detach*", "ec2:DisassociateAddress",
            "ec2:ReleaseAddress", "ec2:RevokeSecurityGroup*"
          ]
          Resource  = "*"
          Condition = { StringEquals = { "aws:ResourceTag/managed-by" = "terraform" } }
        },
        {
          Effect = "Allow"
          Action = [
            "eks:Delete*", "eks:Describe*", "eks:List*", "eks:UntagResource",
            "iam:DeleteRole", "iam:DeleteRolePolicy", "iam:DetachRolePolicy",
            "iam:Get*", "iam:List*", "kms:CancelKeyDeletion", "kms:Disable*",
            "kms:ScheduleKeyDeletion", "logs:Delete*", "s3:Delete*", "s3:Get*",
            "s3:List*", "s3:Put*", "cloudtrail:Delete*", "cloudtrail:Describe*",
            "cloudtrail:Get*", "cloudtrail:List*", "cloudtrail:StopLogging",
            "budgets:DeleteBudget", "budgets:ModifyBudget"
          ]
          Resource = "*"
        }
      ])
    }
  }
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
  tags            = var.tags
}

resource "aws_iam_role" "github" {
  for_each           = local.subjects
  name               = "${var.name_prefix}-github-${each.key}"
  assume_role_policy = local.github_trust_policies[each.key]
  tags               = merge(var.tags, { lifecycle = each.key })
}

resource "aws_iam_role_policy" "lifecycle" {
  for_each = local.lifecycle_policies
  name     = "${var.name_prefix}-github-${each.key}"
  role     = aws_iam_role.github[each.key].id
  policy   = jsonencode(each.value)
}
