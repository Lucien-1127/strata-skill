# 增量索引與子代理模式

## 增量索引機制

`build_index.py` 使用 SHA256 檔案 hash 追蹤更新：

```
每個 .md 檔案 → 計算 SHA256 hash
                    ↓
        與 .file_hashes.yaml 比對
          ↙              ↘
      一致 → 跳過     不同 → 重新 embedding + 取代舊 chunks
```

hash store 位於 `vector_store/.file_hashes.yaml`，自動管理。

### 何時需要清除重建

```bash
# 如果換了 embedding 模型（維度不同）或發現索引異常
rm -rf /home/ysga1/zhiyan-search/vector_store/
python build_index.py
```

## 子代理執行模式

建索引是長時間任務（2-5 分鐘），應透過 sub-agent 背景執行：

```python
delegate_task(
    goal="cd /home/ysga1/zhiyan-search && python build_index.py",
    context="專案路徑: /home/ysga1/zhiyan-search\n.env 已有 HUGGINGFACE_TOKEN\n相依已安裝"
)
```

優點：
- 不阻塞主對話
- 子代理完成後自動回報結果
- 可同時做其他事

## 搜尋驗證

建完索引後，用以下查詢做冒煙測試：

```bash
python search.py "Persona 骨架的安全規則"    # 核心控制層
python search.py "引用政策"                    # 模式與引用層
python search.py "民法第幾條"                  # 法條查詢
```

預期結果：前 3 筆應包含 `10_核心控制層/` 或 `20_模式與引用層/` 相關檔案。
