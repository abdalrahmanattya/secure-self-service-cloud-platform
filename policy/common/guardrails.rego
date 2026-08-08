package common

deny contains msg if {
  not input.provider
  msg := "provider must be selected explicitly"
}

deny contains msg if {
  input.provider != "aws"
  input.provider != "azure"
  msg := "provider must be exactly aws or azure"
}

deny contains msg if {
  input.request.provider != input.provider
  msg := "request provider must match the immutable installation provider"
}

deny contains msg if {
  not input.owner
  msg := "owner is required for accountability"
}

deny contains msg if {
  not input.cost_centre
  msg := "cost_centre is required for attribution"
}

deny contains msg if {
  not input.data_classification
  msg := "data_classification is required"
}

deny contains msg if {
  input.budget.monthly_limit <= 0
  msg := "monthly budget must be greater than zero"
}

deny contains msg if {
  not input.budget.alerts_enabled
  msg := "budget alerts must be enabled"
}

deny contains msg if {
  input.mode == "sandbox"
  lower(input.environment) == "production"
  msg := "sandbox mode cannot target production"
}

deny contains msg if {
  input.mode == "simulation"
  input.cloud_identifiers_used == true
  msg := "simulation examples must not contain real cloud identifiers"
}

deny contains msg if {
  input.network.kubernetes_api_private != true
  msg := "Kubernetes API endpoint must be private"
}

deny contains msg if {
  input.network.nodes_private != true
  msg := "Kubernetes worker nodes must use private subnets"
}

deny contains msg if {
  input.encryption.at_rest != true
  msg := "encryption at rest is required"
}

deny contains msg if {
  input.encryption.in_transit != true
  msg := "encryption in transit is required"
}

deny contains msg if {
  input.encryption.key_rotation != true
  msg := "customer-managed key rotation is required"
}

deny contains msg if {
  input.logging.central != true
  msg := "central logging is required"
}

deny contains msg if {
  input.logging.audit != true
  msg := "audit logging is required"
}

deny contains msg if {
  input.logging.control_plane != true
  msg := "Kubernetes control-plane logging is required"
}

deny contains msg if {
  input.identity.least_privilege != true
  msg := "least-privilege identity policy is required"
}

deny contains msg if {
  input.identity.federation.issuer != "https://token.actions.githubusercontent.com"
  msg := "GitHub federation issuer must be the exact Actions issuer"
}

deny contains msg if {
  input.identity.federation.audience == ""
  msg := "GitHub federation audience is required"
}

deny contains msg if {
  input.identity.federation.subject == "*"
  msg := "GitHub federation subject cannot be wildcard-only"
}

deny contains msg if {
  regex.match("\\*", input.identity.federation.subject)
  msg := "GitHub federation subject must not contain wildcards"
}
