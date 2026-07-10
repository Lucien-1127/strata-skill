# 新增永久磁碟至 GCP VM

## 場景
在 GCP VM 上掛載額外資料磁碟（persistent disk）。

## 前置條件
- VM 已建立且運行中
- 磁碟已建立 but **未附加**（如 `disk-20260704-070721`）

## 步驟

### 1. 附加磁碟到 VM
```bash
gcloud compute instances attach-disk zhiyan-prod \
  --disk=disk-20260704-070721 \
  --zone=us-west1-a
```

### 2. 在 VM 內確認磁碟
```bash
lsblk
# 應該看到 /dev/sdb （或類似名稱）
```

### 3. 格式化（首次使用）
```bash
sudo mkfs.ext4 /dev/sdb
```

### 4. 建立掛載點並掛載
```bash
sudo mkdir -p /mnt/data
sudo mount /dev/sdb /mnt/data
```

### 5. 永久性設定（fstab）
```bash
echo '/dev/sdb /mnt/data ext4 defaults 0 2' | sudo tee -a /etc/fstab
```

### 6. 驗證
```bash
df -h /mnt/data
```

## 常見問題
- **Disk already contains a filesystem**：磁碟已格式化過，可直接掛載
- **Permission denied**：使用 `sudo` 或確認在 `disk` group
- **Mount point busy**：確認沒有其他程序使用該掛載點

## 參考
- https://cloud.google.com/compute/docs/disks/add-persistent-disk