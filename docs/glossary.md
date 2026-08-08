# Glossary

| Term | Meaning |
| --- | --- |
| adapter | Provider-specific implementation behind the common platform port |
| bundle | Sanitized deterministic request, policy, and generated-input evidence |
| drift | Difference between approved configuration/state and observed provider state |
| enterprise | Separated account/subscription operating mode with shared services |
| fingerprint | SHA-256 identity of canonical normalized request data |
| installation | Provider-locked platform configuration and state boundary |
| OIDC | Short-lived identity federation from GitHub to a cloud provider |
| proposal | Reviewable GitHub change containing a deterministic bundle |
| protected Environment | GitHub approval boundary for privileged workflow jobs |
| sandbox | Single-account/subscription constrained non-production mode |
| simulation | Credential-free local execution using mocked provider behavior |
| saved plan | Protected Terraform plan artifact tied to commit and state snapshot |
| state backend | Durable, encrypted Terraform state storage for one boundary |
| request ID | Stable identifier derived from normalized request fingerprint |
