---
name: gcp-cost-optimization
description: "Analyze GCP billing, identify cost-saving opportunities, and implement resource right-sizing recommendations."
status: stable
---
# gcp-cost-optimization

## 📖 Description

>-

---

# GCP Cost Optimization — CLI-First Playbook

## Core Principle

This user operates via **CLI, not browser**. Every optimization step below uses `gcloud` commands. Only fall back to the browser URL when the API has no CLI equivalent (e.g., viewing credit details).

## Quick Wins (per resource type)

### 1. orphaned Persistent Disks

Disks detached from any VM still incur storage costs. Find them:

```bash
# List all disks and check the USERS column — empty = orphaned
gcloud compute disks list --project=<PROJECT_ID>

# Describe a specific disk to confirm no users
gcloud compute disks describe <DISK_NAME> --zone=<ZONE> --project=<PROJECT_ID> --format="table(name, status, users)"

# Delete orphaned disk
gcloud compute disks delete <DISK_NAME> --zone=<ZONE> --project=<PROJECT_ID>
```

**Regional disks** (used by Cloud Workstations) cost more than zonal. A 200GB pd-standard regional disk costs ~€18/month even when the workstation is STOPPED. Either delete the workstation config and disk, or accept the cost as a data-preservation fee.

```bash
# List workstations — check which are STOPPED
gcloud workstations list --region=<REGION> --project=<PROJECT_ID>

# Delete workstation + its config + its disk (irreversible — loses all data)
gcloud workstations delete <NAME> --region=<REGION> --project=<PROJECT_ID>
gcloud workstations configs delete <CONFIG> --region=<REGION> --project=<PROJECT_ID>
gcloud workstations clusters delete <CLUSTER> --region=<REGION> --project=<PROJECT_ID>
```

### 2. VM Rightsizing + Machine Type Migration

**Step 1: Identify over-provisioned VMs**

```bash
gcloud compute instances list --project=<PROJECT_ID> \
  --format="table(name, zone, machineType, status)" 
```

**Step 2: Check CPU/memory utilization** via Cloud Monitoring

If you don't have 30+ days of data for the Recommender to fire, check manually:
```bash
# Get instance ID
gcloud compute instances describe <NAME> --zone=<ZONE> \
  --project=<PROJECT_ID> --format="value(id)"
```

**Step 3: Migrate Intel (N2/E2) → AMD (N2D) for savings**

N2D (AMD) offers equivalent or better performance at ~25% lower cost than N2 (Intel).

**⚠️ Cross-architecture migration (Intel→AMD) cannot use `set-machine-type` directly.**
The VM's minimum CPU platform (`cascadelake` for Intel) conflicts with the AMD requirement (`rome`). The `gcloud alpha compute instances set-min-cpu-platform` command requires Alpha API access which most accounts lack.

**Working approach:** Create a new VM reusing the old boot disk (see `references/n2-to-n2d-migration.md` for full steps):

```bash
# 1. Stop + delete old instance (preserves disk — do NOT add --delete-disks=boot)
gcloud compute instances stop <NAME> --zone=<ZONE>
gcloud compute instances delete <NAME> --zone=<ZONE> --quiet

# 2. Verify disk survived
gcloud compute disks list --project=<PROJECT> --filter="name:<OLD_DISK>"

# 3. Create new VM with AMD type, reusing old disk
gcloud compute instances create <NEW_NAME> \
  --zone=<ZONE> --machine-type=n2d-standard-4 \
  --disk=name=<OLD_DISK>,boot=yes --project=<PROJECT>
```

**Example migrations that save money:**
| Current | Target | Monthly savings |
|---------|--------|-----------------|
| n2-standard-4 (Intel, 4 vCPU) | n2d-standard-4 (AMD, 4 vCPU) | ~€17/month |

### 3. Committed Use Discounts (CUD)

For 24/7 workloads, 1-year CUD saves ~30%; 3-year saves ~50-70%.

**Check eligibility:** The VM must run 24/7. Spot VMs and micro instances are not eligible.

**Buy via CLI:**
```bash
# List available commitments
gcloud compute commitments list --region=<REGION> --project=<PROJECT_ID>

# Purchase 1-year CUD for N2D CPUs + memory
gcloud compute commitments create cud-1y-n2d-<REGION> \
  --region=<REGION> --project=<PROJECT_ID> \
  --resources=vcpu=<COUNT>,memory=<MEM-GB> \
  --plan=12-month --type=n2d-amd
```

**CUD covers:** CPU, memory, GPU, local SSD. It does NOT cover premium OS licenses, network egress, or disk storage.

### 4. Budget Alerts

Enable the Budget API, then create a threshold-based budget:

```bash
gcloud services enable billingbudgets.googleapis.com --project=<PROJECT_ID>

gcloud billing budgets create \
  --billing-account=<BILLING_ACCOUNT_ID> \
  --display-name="<NAME>-月預算" \
  --budget-amount=<AMOUNT>EUR \
  --threshold-rule=percent=0.50 \
  --threshold-rule=percent=0.90 \
  --threshold-rule=percent=1.0
```

**Note:** Email notifications require a PubSub topic + subscription setup. The `--notification-rule=email=` flag is NOT supported in gcloud CLI. For email alerts, open the Cloud Console budgets page once and add the email recipient there.

### 5. Storage Lifecycle Management

For Cloud Storage buckets with logs/backups:
```bash
# Set lifecycle rule: auto-archive objects older than 30 days
gcloud storage buckets update gs://<BUCKET_NAME> \
  --lifecycle-file=<(echo '{"lifecycle":{"rule":[{"action":{"type":"SetStorageClass","storageClass":"ARCHIVE"},"condition":{"age":30}}]}}')
```

## IAM Optimization (Prerequisite for any production deployment)

Before buying CUD or making changes, ensure the app uses a **dedicated service account**, not a personal user account:

```bash
# 1. Create service account
gcloud iam service-accounts create sa-<app-name> --project=<PROJECT_ID>

# 2. Grant only the roles it needs
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# 3. Download key (add to .gitignore!)
gcloud iam service-accounts keys create ./vertex-sa-key.json \
  --iam-account=sa-<app-name>@<PROJECT_ID>.iam.gserviceaccount.com

# 4. Remove redundant roles from the personal account
#    (e.g., if user has both `roles/owner` and `roles/aiplatform.user`,
#     remove the latter — Owner covers everything)
gcloud projects remove-iam-policy-binding <PROJECT_ID> \
  --member="user:<EMAIL>" --role="roles/aiplatform.user"
```

## Billing Credits Analysis

**To determine if credits can offset costs:**

1. Check billing account ID: `gcloud billing projects describe <PROJECT_ID>`
2. Open the credits page in a browser (no CLI equivalent):
   `https://console.cloud.google.com/billing/<BILLING_ID>/credits?project=<PROJECT_ID>`
3. **Credit types matter**: Some credits are service-specific (e.g., Gemini Code Assist trial credits cover ONLY specific subscription SKUs, not Compute Engine or Vertex AI inference). Read the "適用於下列 SKU" section carefully.
   - See `references/credits-in-practice.md` for a real-world example.
4. Credits apply **automatically** at billing time — no action needed to "activate" them. They just make the balance last longer.

## The Optimization Sequence (recommended order)

```
Phase 1 (same day)        Phase 2 (this week)       Phase 3 (next month)
────────────────────────  ────────────────────────  ────────────────────────
Delete orphaned disks     Purchase CUD (if 24/7)    Set up storage lifecycle
N2→N2D VM migration       Create budget alerts      Review Recommender suggestions
Enable Budget API         Remove redundant IAM      Check if Spot VMs fit
```

## Credits / Promotions: What to look for

Standard GCP credit programs:

| Program | Typical Amount | Scope | Duration |
|---------|---------------|-------|----------|
| Free Tier | $300 | All services (first 90 days) | 90 days |
| Google for Startups | $2,000–$200,000 | All services (varies) | 1–2 years |
| Partner/Reseller credits | Variable | Contract-specific | Contract duration |
| Service-specific trials | €979 (Gemini Code Assist) | Single service only | 30 days |

**Key question:** If credits are service-specific (e.g., only Gemini Code Assist), they do NOT offset VM/disk/Vertex AI costs. The cost optimization measures above still save real money from the billing account.

## Project Organization & Restructuring

### Rename a project

```bash
gcloud projects update <PROJECT_ID> --name="<New Display Name>"
```

**Constraint:** Display name cannot contain Chinese characters or special characters. Use ASCII only.

### Delete a project

```bash
gcloud projects delete <PROJECT_ID> --quiet
```

Deleted projects enter a 30-day "pending delete" state. The project ID cannot be reused during this period.

### Create a new project under an organization

```bash
gcloud projects create <NEW_PROJECT_ID> \
  --name="<DISPLAY_NAME>" \
  --organization=<ORG_ID>
```

## Pitfalls

- **Stale process holds port.** After refactoring, the old Express server may still hold port 5000. `taskkill /F /IM node.exe` (Windows) before restarting. Symptom: SSE returns `{"done":true}` with no text chunks.
- **Gemini model generations differ on region.** `gemini-2.5-flash` uses `us-central1`; `gemini-3.5-flash` requires `us` multi-region. Wrong region → 404 `Publisher model not found`.
- **Budget email notifications require PubSub** in gcloud CLI. Use the Console UI once to add email recipients, or accept threshold-only alerts without email.
- **CUD is regional and machine-family-specific.** An `n2d-amd` CUD doesn't cover `n2-standard-*` (Intel). Plan CUD purchases per machine series.
- **IAM propagation delay.** Role changes via `gcloud projects add-iam-policy-binding` take 30-90 seconds to propagate. Test after that delay, not immediately.
- **ADC vs gcloud auth.** `gcloud auth login` updates CLI credentials only. `gcloud auth application-default login` updates the ADC file used by client libraries. After switching accounts, do BOTH.
- **GCP credits page has no CLI equivalent.** The `cloudbilling.googleapis.com/v1/billingAccounts/*/promotions` endpoint returns empty for service-specific credits. Always open the browser console to check actual credit balance and SKU restrictions.
- **`--delete-disks=boot` is destructive.** When using `gcloud compute instances delete`, the `--delete-disks=boot` flag **deletes the boot disk** along with the instance. Data is lost unless a snapshot exists. Default behavior (no flag) preserves all disks. Always verify with `gcloud compute disks list` after deletion.
- **Service-specific trial credits are misleading.** A credit named "Trial for service cloudaicompanion.googleapis.com" worth €979 is restricted to specific SKUs (e.g., Gemini Code Assist subscriptions). It does NOT cover Compute Engine, Vertex AI inference, or Cloud Storage. Read the "適用於下列 SKU" section carefully before assuming credits offset costs.
