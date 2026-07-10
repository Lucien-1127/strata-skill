# Session Context: zhiyan-prod VM Configuration

**Captured from session on 2026-07-04**

## VM Specs
- **Hostname**: zhiyan-prod.us-west1-a.c.gen-lang-client-0435318113.internal
- **Project**: gen-lang-client-0435318113
- **Zone**: us-west1-a
- **OS**: Ubuntu 24.04.4 LTS (Noble Numbat)
- **Kernel**: Linux 6.17.0-1020-gcp (x86_64)
- **CPU**: 1 vCPU / 2 threads (Intel Xeon @ 2.20GHz)
- **RAM**: 7.8 GB
- **Disk**: 50 GB root + 10 GB secondary (/mnt/data)

## Services Running
| Service | Port | Status |
|---------|------|--------|
| FreeLLMAPI | :3001 | ✅ Active |
| zhiyan-legal | :8000 | ✅ Active |
| Hermes Gateway | — | ✅ Active (PID varies) |

## Disk Configuration
| Device | Mount | Size | fstab Entry |
|--------|-------|------|---------------|
| /dev/sdb | /mnt/data | 10 GB | UUID=2bc304cd-c4f9-48de-b46e-50d7a2ec0b38 /mnt/data ext4 defaults 0 2 |

## SSH / Git
- **GitHub**: SSH key `id_ed25519_github` in ~/.ssh/
- **Remote URL**: git@github.com:Lucien-1127/zhiyan-legal.git
- **SSH auth**: ✅ Confirmed working

## GCP SA
- **Compute SA**: 674313935168-compute@developer.gserviceaccount.com
- **Scope**: Project-wide VM, Storage, Firewall access

## Notes
- User prefers **CLI over Cloud Console** for all GCP operations
- Hermes runs directly on this VM (not via SSH from local machine)
- No GPU available (NVIDIA not installed)
- No swap configured (7.8 GB RAM, typically ~14% usage)
- Python 3.12.3 with venv support
