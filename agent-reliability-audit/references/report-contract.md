# Report contract — Agent Reliability Audit v1.0

The tool is local-only and read-only. It checks report consistency and evidence bytes, **not authenticity of the claims**.

## JSON example: honestly blocked

```json
{
  "schema_version": "1.0",
  "task_id": "deployment-check-01",
  "objective": "Verify the customer's deployment is usable",
  "status": "blocked",
  "attempts": 0,
  "max_attempts": 3,
  "blockers": ["Read permission for the deployment was not granted"],
  "checks": []
}
```

A check in a completed report has these fields:

```json
{
  "id": "functional-01",
  "dimension": "functional",
  "result": "pass",
  "executed": true,
  "exit_code": 0,
  "evidence_path": "functional.txt",
  "evidence_sha256": "<actual hex SHA256 of the referenced evidence file>"
}
```

The SHA-256 above is a placeholder. Compute an actual digest for each file; the verifier requires 64 hexadecimal characters.

A `completed` report must have all four passing dimensions: `functional`, `safety`, `regression`, and `customer`. Every passing check must be executed, have exit code zero, refer to a nonempty local file and match its real SHA-256. No skipped/failed check or blocker is permitted in a completed report.

The evidence root must already exist; referenced paths must be relative, stay within the root, and contain no symlink. The validator reads up to 256 KB of report JSON and up to 10 MB per evidence file; it never runs the recorded command.

## Run

```bash
python3 scripts/verify_closeout.py --report /path/to/report.json --evidence-root /path/to/approved/evidence
```

Exit **0** = internally consistent declaration of completion; **1** = invalid report or evidence; **2** = valid unresolved task. Inspect the printed JSON verdict, rather than simply trusting a narrator.

## Negative acceptance cases

- Completed without all four gates, or with failing/skipped checks: **invalid**.
- Claimed pass without execution, evidence file or matching checksum: **invalid**.
- Missing, empty, changed, out-of-root, symlinked or overly large evidence: **invalid**.
- Malformed JSON, duplicate object keys or an exhausted retry limit: **invalid**.
- Blocked with a specific reason, zero attempts and no checks: **unresolved**.
- Regressed with an observed failed check: **unresolved**.

**Never use this verifier to claim that fake logs demonstrate genuine task execution.** Evidence must be read by an independent reviewer and compared against the original acceptance criteria before external delivery.

## 繁體中文說明

本工具只會確認證據檔案與報告的格式、雜湊值一致，不代表原任務真正完成。結案必須另外確認實際測試輸出、修改前後差異，以及客戶是否接受成果。若工具不存在、驗證失敗或缺少必要授權，應保留未完成狀態。
