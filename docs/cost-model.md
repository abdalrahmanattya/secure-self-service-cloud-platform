# Cost model

Cost controls are part of the request contract and the deployment preflight.
The simulation shows a requested monthly budget and alert thresholds; it does
not query provider prices or create a bill.

## Inputs and controls

| Input | Control |
| --- | --- |
| owner and cost centre | mandatory tags and chargeback dimension |
| environment and expiry | non-production lifetime and cleanup queue |
| cluster size | approved capacity tiers |
| monthly budget | provider budget with 80% warning and 100% breach alert |
| provider/mode | sandbox limits and enterprise account/subscription attribution |
| egress and storage | review of NAT, logs, backups, and retention assumptions |

AWS uses tags and AWS Budgets; Azure uses tags and Cost Management budgets.
Actual estimates must be generated in the operator's approved account or
subscription using current price data. No public document should present a
price as a live quote or embed real billing identifiers.

## Cost response

At warning, operations reviews idle capacity, expiry, log retention, and
egress. At breach, new proposals pause for the affected scope and the owner is
notified. An expired non-production environment enters the destroy review
queue. Production budget exceptions require an auditable approver and an
explicit time limit.
