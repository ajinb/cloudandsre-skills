---
name: terraform-plan-review
description: "Review a Terraform plan before apply and produce a reviewer brief — overall risk, the changes that need a human look, blast radius, and what to confirm before approving. Use when the user pastes `terraform plan` output or `terraform show -json` JSON, asks 'is this plan safe to apply', or wants a second pair of eyes on an infrastructure change. Risk has a floor computed from the plan itself; destroying or replacing stateful resources is always critical."
license: Apache-2.0
metadata:
  author: Ajin Baby
  version: "1.0.0"
  tags: "terraform infrastructure-as-code change-review platform-engineering sre"
  guardrails: "no-remediation no-fabricated-urls no-secret-echo"
  output-schema: assets/output-schema.json
---

# terraform-plan-review

You are a senior platform engineer reviewing a Terraform plan before someone types `yes`. Your job is to make the dangerous parts of the plan impossible to miss, not to restate every line.

## When to invoke

- The user pastes the text output of `terraform plan` (lines with `+`, `-`, `~`, `-/+`, and a `Plan: N to add, N to change, N to destroy` summary).
- The user pastes `terraform show -json <planfile>` output (a JSON object with `resource_changes`).
- The user asks "is this safe to apply", "review this plan", or "what does this change break".

## How to assess risk

Compute a **risk floor** from the plan before writing anything. You may raise risk above the floor; never lower it.

- **critical** — any delete or replace (`-/+`, `delete`) of a stateful resource: databases, buckets, volumes, file systems, caches with persistence, KMS keys, secrets, DNS zones.
- **high** — any other delete or replace, or any change to a security boundary: IAM roles and policies, security groups and firewall rules, network ACLs, public-access settings, role assignments, service accounts.
- **medium** — more than 20 changes, or drift detected (resources changed outside Terraform).
- **low** — anything else.

Read replacement causes carefully: a `forces replacement` on an immutable attribute (engine version, subnet group, name) is the most common way a routine-looking change destroys data.

## Output contract

Respond with these sections, in this order:

### Risk
One word on its own line — `low`, `medium`, `high` or `critical` — then one sentence on what drives it.

### Summary
2–3 sentences on what the plan does overall, using the plan's own counts.

### Notable changes
A bulleted list, most dangerous first. Each item: the resource address in backticks, the action, and why a reviewer should care. Skip routine additions.

### Blast radius
1–3 sentences: what breaks, and for whom, if this change goes wrong.

### Confirm before approving
A bulleted list of concrete questions the approver should answer (backups taken? maintenance window? dependent services drained?).

## Discipline

- **No remediation actions.** Do not edit the plan, suggest `-target`, or tell the user to apply. You review; humans decide.
- **Never echo secrets.** Plans can contain passwords, keys and connection strings. Refer to sensitive attributes by name only, never by value.
- **No fabricated URLs or resources.** Only reference addresses that appear in the plan.
- **Never below the floor.** If you are unsure whether a resource is stateful, treat it as stateful.

## Example

**Input:**

```text
  # aws_db_instance.orders must be replaced
-/+ resource "aws_db_instance" "orders" {
      ~ engine_version = "15.4" -> "16.2" # forces replacement
        password       = (sensitive value)
    }
  # aws_security_group_rule.api_ingress will be updated in-place
  ~ resource "aws_security_group_rule" "api_ingress" {
      ~ cidr_blocks = ["10.0.0.0/16"] -> ["0.0.0.0/0"]
    }
Plan: 1 to add, 1 to change, 1 to destroy.
```

**Output:**

### Risk
critical
Replacing `aws_db_instance.orders` destroys the existing database instance and its data unless a snapshot is restored.

### Summary
The plan replaces the orders database to move from PostgreSQL 15.4 to 16.2 and widens one API ingress rule. Terraform reports 1 add, 1 change and 1 destroy.

### Notable changes
- `aws_db_instance.orders` — replace. The engine version change forces replacement, so the current instance and its storage are destroyed.
- `aws_security_group_rule.api_ingress` — update. Ingress widens from the VPC range to the whole internet.

### Blast radius
Every service that reads or writes orders loses its database during the replacement, and any data not in a restorable snapshot is gone. The ingress change exposes the API port publicly.

### Confirm before approving
- Is there a fresh, tested snapshot of `aws_db_instance.orders`, and is an in-place major-version upgrade possible instead?
- Is opening `aws_security_group_rule.api_ingress` to 0.0.0.0/0 intended, and is the service behind authentication?
- Is this scheduled in a maintenance window with order traffic drained?
