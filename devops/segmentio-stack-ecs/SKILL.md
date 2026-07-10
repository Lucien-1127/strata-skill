---
name: segmentio-stack-ecs
description: Provision AWS ECS services, workers and VPCs with Terraform modules.
version: 0.1.0
author: Hermes
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [AWS, ECS, Terraform, Docker, Infrastructure]
---

# Segmentio Stack ECS Terraform Modules

Deploy production-ready ECS infrastructure on AWS using Segmentio's curated Terraform modules — VPC, auto-scaling clusters, bastion hosts, services with ELB+Route53, workers, and RDS. Dependencies: Terraform >= 0.12, AWS CLI configured with credentials.

## When to Use

- "Set up an ECS cluster with auto-scaling on AWS"
- "Deploy a Docker service with an internal ELB and DNS discovery"
- "Create a VPC with multi-AZ subnets and a bastion jump host"
- "Add a background worker without a load balancer"
- "Provision an RDS Aurora cluster behind a VPC"

## Prerequisites

- Terraform >= 0.12 installed
- AWS credentials configured (`aws configure` or `aws-vault`)
- Docker images pushed to Docker Hub (service modules pull images from there)
- SSH key pair created in AWS EC2 (for bastion access)
- Clone or reference modules via `github.com/segmentio/stack//<module>`

## How to Run

Invoke through the `terminal` tool: write a `terraform.tf` file, then run `terraform plan` and `terraform apply`.

## Quick Reference

| Resource | Terraform source |
|----------|-----------------|
| Full stack (VPC + ECS + bastion) | `github.com/segmentio/stack` |
| ECS service + internal ELB + DNS | `github.com/segmentio/stack//service` |
| ECS service + **public** ELB + DNS | `github.com/segmentio/stack//web-service` |
| Background worker (no ELB) | `github.com/segmentio/stack//worker` |
| ECS task definition only | `github.com/segmentio/stack//task` |
| VPC with subnets | `github.com/segmentio/stack//vpc` |
| Bastion jump host | `github.com/segmentio/stack//bastion` |
| ECS cluster (ASG + EBS) | `github.com/segmentio/stack//ecs-cluster` |
| IAM role for ECS | `github.com/segmentio/stack//iam-role` |
| RDS Aurora cluster | `github.com/segmentio/stack//rds-cluster` |
| Route53 private DNS zone | `github.com/segmentio/stack//dns` |
| ELB + healthcheck | `github.com/segmentio/stack//elb` |
| S3 bucket for ELB logs | `github.com/segmentio/stack//s3-logs` |
| Security groups | `github.com/segmentio/stack//security-groups` |

## Procedure

### 1. Base Stack — VPC + ECS Cluster + Bastion

```hcl
module "stack" {
  source      = "github.com/segmentio/stack"
  name        = "my-app"
  environment = "prod"
  key_name    = "my-ssh-key"
}
```

Outputs available: `vpc_id`, `cluster`, `iam_role`, `zone_id`, `internal_subnets`, `external_subnets`, `internal_elb`, `external_elb`, `bastion_ip`, `log_bucket_id`.

### 2. Internal Service — Docker + ELB + Route53 DNS

```hcl
module "nginx" {
  source          = "github.com/segmentio/stack//service"
  name            = "nginx"
  image           = "nginx"
  port            = 80
  environment     = "${module.stack.environment}"
  cluster         = "${module.stack.cluster}"
  iam_role        = "${module.stack.iam_role}"
  security_groups = "${module.stack.internal_elb}"
  subnet_ids      = "${module.stack.internal_subnets}"
  log_bucket      = "${module.stack.log_bucket_id}"
  zone_id         = "${module.stack.zone_id}"
}
```

Service discovers itself at `http://nginx.stack.local` (via Route53 private zone).

Key variables:
| Variable | Default | Description |
|----------|---------|-------------|
| `container_port` | `3000` | Container port |
| `healthcheck` | `/` | Healthcheck HTTP path |
| `desired_count` | `2` | Number of containers |
| `memory` | `512` | MiB reserved |
| `cpu` | `512` | CPU units reserved |
| `env_vars` | `[]` | JSON array of `{name, value}` |
| `version` | `latest` | Docker image tag |

### 3. Web Service — Public HTTPS ELB

```hcl
module "web" {
  source             = "github.com/segmentio/stack//web-service"
  name               = "web"
  image              = "my-app"
  port               = 443
  ssl_certificate_id = "arn:aws:iam::123456:server-certificate/my-cert"
  environment        = "${module.stack.environment}"
  cluster            = "${module.stack.cluster}"
  iam_role           = "${module.stack.iam_role}"
  security_groups    = "${module.stack.external_elb}"
  subnet_ids         = "${module.stack.external_subnets}"
  log_bucket         = "${module.stack.log_bucket_id}"
  external_zone_id   = "${module.stack.zone_id}"
  internal_zone_id   = "${module.stack.zone_id}"
}
```

Outputs: `dns`, `external_fqdn`, `internal_fqdn`, `elb`.

### 4. Background Worker (no ELB)

```hcl
module "worker" {
  source       = "github.com/segmentio/stack//worker"
  name         = "my-worker"
  image        = "my-worker"
  cluster      = "${module.stack.cluster}"
  environment  = "${module.stack.environment}"
  desired_count = 1
}
```

No DNS, no ELB — pure ECS task, ideal for queue consumers or cron jobs.

### 5. ECS Task Definition Only

```hcl
module "task" {
  source   = "github.com/segmentio/stack//task"
  name     = "my-task"
  image    = "my-image"
  memory   = 512
  cpu      = 512
  env_vars = "[{\"name\": \"ENV\",\"value\": \"prod\"}]"
  command  = "[\"--flag=value\"]"
  ports    = "[{\"containerPort\": 8080, \"hostPort\": 8080}]"
}
```

Outputs: `name` (family), `arn` (full ARN), `revision`.

### 6. RDS Aurora Cluster

```hcl
module "rds" {
  source              = "github.com/segmentio/stack//rds-cluster"
  name                = "mydb"
  environment         = "prod"
  vpc_id              = "${module.stack.vpc_id}"
  zone_id             = "${module.stack.zone_id}"
  security_groups     = ["${module.stack.vpc_security_group}"]
  subnet_ids          = "${module.stack.internal_subnets}"
  availability_zones  = "${module.stack.availability_zones}"
  database_name       = "mydb"
  master_username     = "admin"
  master_password     = "..."
}
```

Outputs: `id`, `endpoint`, `port`.

### 7. Plan and Apply

```bash
terraform init
terraform plan
terraform apply
terraform output  # print outputs including bastion_ip
```

SSH to bastion:
```bash
ssh -i <key> ubuntu@<bastion-ip>
# then from bastion:
ssh ubuntu@<internal-instance-ip>
```

### 8. Update Docker Image Version (zero-downtime)

```hcl
module "nginx" {
  source   = "github.com/segmentio/stack//service"
  # ... same as before
  version  = "1.19"   # bump docker image tag
}
```

The `task` module uses `lifecycle { ignore_changes = ["image"] }` so `terraform apply` picks up the new tag without destroying the task family.

## Architecture Summary

```
internet
   |
   | (HTTPS)
   v
[web-service] → public ELB
                    |
                    v
              [service] → internal ELB + Route53 DNS
                    |
                    v
              [ecs-cluster] (auto-scaling, multi-AZ)
                    |
         ┌──────────┼──────────┐
         v          v          v
     [service]  [worker]   [...more]
     
[vpc] — internal subnet (private) / external subnet (ELB-facing)
[dns] — private Route53 zone (stack.local)
[bastion] — jump host for SSH
[s3-logs] — ELB access logs
[rds-cluster] — RDS Aurora in private subnets
```

Default CIDR: `10.30.0.0/16` with 3 AZs.

## Pitfalls

- **Unmaintained repo**: last commit ~2019. AWS/ECS APIs have changed; review Terraform AWS provider compatibility before production use.
- **NAT Gateway cost**: defaults use AWS NAT Gateway (~$30/month). Set `use_nat_instances = true` for dev environments to cut cost.
- **Docker auth**: if pulling from private registries, set `ecs_docker_auth_type` and `ecs_docker_auth_data` on the `ecs-cluster` or `stack` module.
- **env_vars/command format**: must be raw JSON arrays (e.g. `[{"name":"FOO","value":"bar"}]` not a Terraform map), otherwise they render as literal strings in the container.
- **ignore_changes on image**: task definition ignores `image` changes so you can update the tag via `version` without triggering destroy-recreate; verify the new image tag is actually deployed.
- **Service discovery requires the `dns` module**: Route53 DNS names like `nginx.stack.local` only work when the `dns` module is part of the stack (it is, when using the root `stack` module).

## Verification

```bash
terraform show -no-color | grep -E "aws_ecs_service|aws_ecs_task_definition|module\." | head -20
```

Or check individual outputs:
```bash
terraform output bastion_ip
terraform output cluster
terraform output vpc_id
```

> ⚠️ Note: `segmentio/stack` is marked **unmaintained** in its README. Evaluate AWS provider compatibility before production use.

*模型：deepseek-v4-flash*