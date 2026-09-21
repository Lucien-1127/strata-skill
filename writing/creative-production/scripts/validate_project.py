"""Read-only personal production contract checker. No network or rendering."""
import argparse
import json
from pathlib import Path


def validate(project, root):
    errors = []
    counts = {'units': 0}
    if not isinstance(project, dict):
        return {'ok': False, 'errors': ['專案必須是 JSON 物件'], 'checks': counts, 'executed': False}
    if type(project.get('schema_version')) is not int or project['schema_version'] != 1:
        errors.append('schema_version 必須為 1')
    if not isinstance(project.get('project_id'), str) or not project['project_id'].strip():
        errors.append('project_id 不可空白')
    if project.get('domain') not in ('narrative', 'nonfiction'):
        errors.append('domain 必須為 narrative 或 nonfiction')
    if project.get('mode') not in ('writing', 'screen'):
        errors.append('mode 必須為 writing 或 screen')
    units = project.get('units')
    if not isinstance(units, list) or not units:
        errors.append('units 必須是非空陣列')
    else:
        counts['units'] = len(units)
        seen = set()
        for unit in units:
            if not isinstance(unit, dict):
                errors.append('units 項目必須是物件')
                continue
            ident = unit.get('id')
            if not text(ident) or ident in seen:
                errors.append('unit id 空白或重複')
            else:
                seen.add(ident)
            if unit.get('status') not in ('draft', 'approved'):
                errors.append('unit status 必須為 draft 或 approved')
            path = local_file(root, unit.get('file'), errors)
            limits = unit.get('length')
            if not isinstance(limits, dict) or any(type(limits.get(k)) is not int for k in ('min', 'max')):
                errors.append('字數 length 必須含整數 min/max')
            elif not 0 <= limits['min'] <= limits['max']:
                errors.append('字數範圍無效')
            elif path:
                try:
                    count = sum(not c.isspace() for c in path.read_text(encoding='utf-8'))
                    if not limits['min'] <= count <= limits['max']:
                        errors.append('字數不在指定範圍內')
                except (OSError, UnicodeError):
                    errors.append('稿件檔案必須是 UTF-8 文字')
    versions = project.get('versions')
    consumed = project.get('consumed_versions')
    if not isinstance(versions, dict) or not isinstance(consumed, dict):
        errors.append('versions / consumed_versions 必須是物件')
    else:
        required = ['outline'] + (['characters'] if project.get('domain') == 'narrative' else [])
        if any(not text(versions.get(k)) for k in required):
            errors.append('缺少必要規劃版本')
        if versions != consumed or any(not text(v) for v in versions.values()):
            errors.append('消費的規劃版本不一致或空白')
    if project.get('mode') == 'screen':
        validate_screen(project, root, errors, counts)
    elif 'generation' in project:
        gen = project['generation']
        if not isinstance(gen, dict) or set(gen) != {'requested'} or gen['requested'] is not False:
            errors.append('generation 必須是離線計畫 requested:false，不接受生成請求')
    return {'ok': not errors, 'errors': errors, 'checks': counts, 'executed': False}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def local_file(root, value, errors):
    if not text(value):
        errors.append('缺少檔案路徑')
        return None
    try:
        path = Path(value)
        resolved = (root / path).resolve()
        if path.is_absolute() or not resolved.is_relative_to(root.resolve()):
            errors.append('檔案路徑必須位於專案內')
        elif not resolved.is_file():
            errors.append('引用的檔案不存在')
        else:
            return resolved
    except (OSError, ValueError, RuntimeError):
        errors.append('無效檔案路徑')
    return None


def indexed(value, label, errors, allow_empty=False):
    if not isinstance(value, list) or (not value and not allow_empty):
        errors.append(label + '必須是陣列' + ('且不可空白' if not allow_empty else ''))
        return {}
    index = {}
    for item in value:
        if not isinstance(item, dict) or not text(item.get('id')):
            errors.append(label + '項目必須有 id')
        elif item['id'] in index:
            errors.append(label + ' id 重複')
        else:
            index[item['id']] = item
    return index


def validate_screen(project, root, errors, counts):
    import math
    if not isinstance(project.get('versions'), dict) or not text(project['versions'].get('script')):
        errors.append('缺少劇本版本')
    units = project.get('units')
    if not isinstance(units, list) or any(not isinstance(u, dict) or u.get('status') != 'approved' for u in units):
        errors.append('進入分鏡前劇本必須核准')
    level = project.get('continuity_level')
    if level not in ('A0', 'A1', 'A2', 'A3'):
        errors.append('continuity_level 必須為 A0–A3')
    gen = project.get('generation')
    if not isinstance(gen, dict) or 'requested' not in gen:
        errors.append('generation.requested 必須明確設定 false')
    elif gen.get('requested') is not False:
        errors.append('本工具只接受離線計畫，不接受生成請求')
    assets = indexed(project.get('assets'), '資產', errors, allow_empty=True)
    scenes = indexed(project.get('scenes'), '場景', errors)
    shots = indexed(project.get('shots'), '鏡頭', errors)
    counts.update(assets=len(assets), scenes=len(scenes), shots=len(shots))
    for asset in assets.values():
        if asset.get('kind') not in ('CHR', 'SCN', 'PRP', 'AUD'):
            errors.append('資產 kind 必須為 CHR/SCN/PRP/AUD')
        if not text(asset.get('version')):
            errors.append('資產版本不可空白')
        if asset.get('status') not in ('draft', 'approved'):
            errors.append('資產狀態必須為 draft 或 approved')
    for shot in shots.values():
        scene = shot.get('scene_id')
        if not text(scene) or scene not in scenes:
            errors.append('鏡頭引用不存在的場景')
        refs = shot.get('asset_refs')
        if not isinstance(refs, list):
            errors.append('鏡頭資產引用必須是陣列')
            refs = []
        if level in ('A2', 'A3') and not refs:
            errors.append('A2/A3 鏡頭至少需要一個核准資產引用')
        for ref in refs:
            if not isinstance(ref, dict) or not text(ref.get('id')) or ref['id'] not in assets:
                errors.append('鏡頭引用不存在的資產')
                continue
            asset = assets[ref['id']]
            if not text(ref.get('version')) or ref['version'] != asset.get('version'):
                errors.append('鏡頭資產版本不一致')
            if asset.get('status') != 'approved':
                errors.append('引用的資產尚未核准')
            local_file(root, asset.get('file'), errors)
        duration = shot.get('duration')
        if not isinstance(duration, dict):
            errors.append('鏡頭缺少時長及時長來源')
            continue
        seconds = duration.get('seconds')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0:
            errors.append('時長必須是有限正數')
        source = duration.get('source')
        if source not in ('estimated', 'authored', 'measured'):
            errors.append('時長來源必須為 estimated/authored/measured')
        if source == 'measured':
            if not duration.get('evidence_file'):
                errors.append('量測時長必須附 evidence_file')
            else:
                local_file(root, duration['evidence_file'], errors)


class DuplicateKeyError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError()
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description='唯讀檢查創作專案，不生成、不發布、不收費。')
    parser.add_argument('project', type=Path)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.project.read_text(encoding='utf-8'), object_pairs_hook=unique_object), args.project.resolve().parent)
    except DuplicateKeyError:
        result = {'ok': False, 'errors': ['JSON 含重複欄位，請先消除歧義'], 'checks': {}, 'executed': False}
    except (OSError, ValueError):
        result = {'ok': False, 'errors': ['無法讀取有效 JSON 專案'], 'checks': {}, 'executed': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
