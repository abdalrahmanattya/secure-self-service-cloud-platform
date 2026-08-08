package azure

deny contains msg if {
  input.provider == "azure"
  input.resources.aks.private_cluster_enabled != true
  msg := "AKS private cluster mode must be enabled"
}

deny contains msg if {
  input.provider == "azure"
  input.resources.aks.network_plugin != "azure"
  msg := "AKS must use the approved Azure CNI network plugin"
}

deny contains msg if {
  input.provider == "azure"
  input.resources.aks.workload_identity_enabled != true
  msg := "AKS workload identity must be enabled"
}

deny contains msg if {
  input.provider == "azure"
  input.resources.key_vault.purge_protection != true
  msg := "Key Vault purge protection must be enabled"
}

deny contains msg if {
  input.provider == "azure"
  input.resources.key_vault.public_network_access != false
  msg := "Key Vault public network access must be disabled"
}

deny contains msg if {
  input.provider == "azure"
  input.resources.activity_log.enabled != true
  msg := "Azure Activity Log export must be enabled"
}

deny contains msg if {
  input.provider == "azure"
  input.resources.state_storage.https_only != true
  msg := "Azure state storage must require HTTPS"
}

deny contains msg if {
  input.provider == "azure"
  input.resources.state_storage.public_network_access != false
  msg := "Azure state storage public network access must be disabled"
}

deny contains msg if {
  input.provider == "azure"
  input.identity.federation.issuer != "https://token.actions.githubusercontent.com"
  msg := "Azure GitHub federation issuer must be exact"
}

deny contains msg if {
  input.provider == "azure"
  not regex.match("^repo:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+:environment:[a-z0-9][a-z0-9-]{1,31}$", input.identity.federation.subject)
  msg := "Azure federated credential subject must be an exact repository Environment subject"
}

deny contains msg if {
  input.provider == "azure"
  input.identity.federation.lifecycle_roles.plan == input.identity.federation.lifecycle_roles.apply
  msg := "Azure plan and apply identities must be separate"
}

deny contains msg if {
  input.provider == "azure"
  input.identity.federation.lifecycle_roles.apply == input.identity.federation.lifecycle_roles.destroy
  msg := "Azure apply and destroy identities must be separate"
}
