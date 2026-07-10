---
name: drive-organization
description: "Google Drive file organization, cleanup, and maintenance — scanning, dedup, moving, and bulk operations beyond the basic"
status: stable
---
# drive-organization

## 📖 Description

Google Drive file organization, cleanup, and maintenance — scanning, dedup, moving, and bulk operations beyond the basic wrapper

---

# Drive Organization

Google Drive maintenance workflows — scanning folder hierarchies, identifying duplicates, moving files between folders, and bulk cleanup. Complements the `google-workspace` skill for operations the basic CLI wrapper doesn't support.

## Prerequisites

- `google-workspace` skill set up and authenticated
- Google Drive API enabled in Cloud Console
- Token at `google_token.json` (location varies by platform)

## Scanning Drive Structure

### List root-level folders

```bash
GAPI="python /c/Users/ysga1/AppData/Local/hermes/skills/productivity/google-workspace/scripts/google_api.py"
python "$GAPI" drive search "mimeType='application/vnd.google-apps.folder' and 'root' in parents" --raw-query --max 50
```

**⚠️ Shell quoting on Windows**: Always use `--raw-query` for queries with single-quoted `mimeType=` values. Without `--raw-query`, the CLI wrapper wraps the query in `fullText contains` which breaks `mimeType=` expressions.

### List contents of a specific folder

```bash
python "$GAPI" drive search "'FOLDER_ID' in parents" --raw-query --max 50
```

### Deep scan: check nested subfolders for duplicates

When you see multiple child folders with identical names under the same parent, list each one's contents to confirm they're duplicates:

```bash
for FID in ID1 ID2 ID3 ID4 ID5; do
  echo "=== Folder $FID ==="
  python "$GAPI" drive search "'$FID' in parents" --raw-query --max 5
done
```

## Moving Files Between Folders

The `google_api.py` wrapper does **not** have a `move` command. Use Python with the Google Drive API directly:

```python
import json, os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Platform-aware token path
TOKEN_PATH = os.path.expanduser("~/.hermes/google_token.json")
# On Windows with Hermes in AppData:
# TOKEN_PATH = "C:/Users/<user>/AppData/Local/hermes/google_token.json"

with open(TOKEN_PATH) as f:
    cred_data = json.load(f)

creds = Credentials.from_authorized_user_info(cred_data)
drive_service = build("drive", "v3", credentials=creds)

def move_file(file_id, file_name, source_folder_id, target_folder_id):
    """Move a file by adding target parent and removing source parent."""
    drive_service.files().update(
        fileId=file_id,
        addParents=target_folder_id,
        removeParents=source_folder_id,
        fields="id, parents"
    ).execute()
```

### Pitfalls

- **Token path**: On Windows with Hermes, the token is at `AppData/Local/hermes/google_token.json`, NOT `~/.hermes/`
- **Moving folders**: Same API works for folders — pass the folder file ID like any other file
- **`--raw-query` is required** for complex Drive queries on Windows/bash to avoid shell quoting corruption
- **Bulk operations**: When moving 15+ items, wrap in a list and iterate with `addParents`/`removeParents`. Each call takes ~1-2 seconds

## Deleting Files

Prefer trash (reversible) over permanent delete:

```bash
python "$GAPI" drive delete FILE_ID        # trashed (reversible)
python "$GAPI" drive delete FILE_ID --permanent  # irreversible
```

To trash via Python API:

```python
drive_service.files().update(
    fileId=file_id,
    body={"trashed": True}
).execute()
```

## Identifying Duplicates

- **Same name, same parent, same modified time** → almost certainly duplicates
- **Partial duplicates** — compare subfolder count; the one with more subfolders is likely the original
- **Sync artifacts**: Obsidian vault sync (Syncthing, git, Google Backup & Sync) often creates copies of "知識庫" folders. Delete all partial copies and keep the most complete one

## Reference Files

- `references/drive-api-move.py` — reusable `DriveMover` class with `move()`, `trash()`, `list_folder()`, `delete_permanent()`. Copy into any `execute_code` block.

## Verification

After moving/deleting, verify the source folder is empty before deleting it:

```bash
python "$GAPI" drive search "'SOURCE_FOLDER_ID' in parents and trashed=false" --raw-query --max 50
```

If empty, you can safely trash the source folder:

```bash
python "$GAPI" drive delete SOURCE_FOLDER_ID
```
