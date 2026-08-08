module "state" {
  source = "../aws/modules/bootstrap"

  name_prefix                = var.name_prefix
  state_bucket_name          = var.state_bucket_name
  github_repository          = var.github_repository
  github_plan_environment    = var.github_plan_environment
  github_apply_environment   = var.github_apply_environment
  github_destroy_environment = var.github_destroy_environment
}
