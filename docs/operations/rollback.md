# Rollback

Rollback is a protected change that restores the last known-good approved
state. It is not an automatic promise that every provider operation is
reversible: data migrations, managed control-plane upgrades, and external side
effects require a service-specific recovery plan.

The implemented manual rollback workflow uses `platform-apply`, the apply
identity, the exact saved plan artifact from a supplied plan run, binding hash
verification, and typed `ROLLBACK provider/mode/proposal-id`. It has not run.

1. declare the incident or failed deployment and freeze competing mutations;
2. identify the last known-good proposal, commit, state version, and health
   evidence;
3. verify provider, environment, state lock, and OIDC identity;
4. obtain protected reviewer approval with self-review prohibited;
5. run the rollback plan against the exact intended state and record its hash;
6. verify health, security controls, logs, budgets, and drift; and
7. close or escalate the incident with a new proposal for permanent repair.

AWS rollback must consider provider-managed dependencies,
EKS node/control-plane compatibility, IAM and security-service continuity,
and KMS/Secrets Manager availability. Azure rollback must consider AKS
control-plane/node compatibility, Entra role propagation, Key Vault recovery,
private DNS/endpoints, and Policy remediation state.
