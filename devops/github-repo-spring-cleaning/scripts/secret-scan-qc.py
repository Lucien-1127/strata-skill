#!/usr/bin/env python3
"""QC Audit: scan all local repos for sensitive data before git push.
Used by the github-repo-spring-cleaning skill during Phase 5 (Security Scan).

Usage:
  python3 scripts/secret-scan-qc.py [--repos repo1,repo2,...]
  python3 scripts/secret-scan-qc.py  # scans default repos

Exits 0 if no real leaks found, 1 if real leaks detected.
"""
import os, re, subprocess, sys

HOME = os.path.expanduser("~")

SENSITIVE_PATTERNS = [
    (r'(?i)api_key\s*[:=]\s*["\']?(sk-|AIza)', "API Key (sk-/AIza prefix)"),
    (r'(?i)api_key\s*[:=]\s*["\']?[A-Za-z0-9_\-]{20,}', "API Key (generic 20+ chars)"),
    (r'-----BEGIN\s*(RSA|OPENSSH|PRIVATE|EC)\s+KEY-----', "Private Key"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?[^"\'\\s]{6,}', "Password"),
    (r'(?i)(token|secret)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{20,}', "Token/Secret"),
    (r'(?i)(DEEPSEEK|OPENAI|ANTHROPIC|OPENROUTER)_API_KEY\s*=', "Env API Key"),
]

DEFAULT_REPOS = [
    ("CineAgent", f"{HOME}/CineAgent"),
    ("strata-skill", f"{HOME}/.hermes/skills"),
    ("zhiyan-legal", f"{HOME}/zhiyan-legal"),
    ("zhiyan-mvp", f"{HOME}/zhiyan-mvp-2"),
    ("hermes-proxy-console", f"{HOME}/hermes-proxy-console"),
    ("hermes-skills", f"{HOME}/hermes-skills"),
]

DOC_PATTERNS = [
    r'sk-xxx', r'sk-YOUR_KEY', r'sk-\.\.\.', r'sk-or-\.\.\.',
    r'YOUR_API_KEY', r'<your.*key>', r'<API.*KEY>',
    r'process\.env\.', r'\$\(printf',
]
MINIFIED_PATTERNS = [
    r'password:\s*!', r"'password'\s*===",
    r'=== "password"', r'=== \x27password\x27',
]

def classify_match(filepath, line, pattern_matched):
    file_lower = filepath.lower()
    if '.env.example' in file_lower:
        return 'FP (env template)'
    for pat in DOC_PATTERNS:
        if re.search(pat, line, re.IGNORECASE):
            return 'FP (doc placeholder)'
    for pat in MINIFIED_PATTERNS:
        if re.search(pat, line):
            return 'FP (minified JS)'
    if 'process.env.' in line:
        return 'FP (env reference)'
    if re.search(r'\.get\(\s*["\']password["\']\s*\)', line):
        return 'FP (form parsing)'
    if 'docs/' in file_lower or '/references/' in file_lower or file_lower.endswith('.md'):
        if re.search(r'sk-[A-Za-z]', line):
            return 'FP (doc example)'
    return 'REAL LEAK'

def scan_repo(name, path):
    git_dir = os.path.join(path, '.git')
    if not os.path.isdir(git_dir):
        return (name, False, ["  ⏭️  Not a git repo"])
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=path, timeout=10)
    tracked = r.stdout.strip().split('\n')
    results = []
    has_real = False
    for filepath in tracked:
        if not filepath: continue
        fp = os.path.join(path, filepath)
        if not os.path.isfile(fp): continue
        try:
            with open(fp, 'rb') as fh:
                if b'\x00' in fh.read(2000): continue
        except: continue
        try:
            with open(fp, errors='replace') as fh: content = fh.read()
        except: continue
        for line_num, line in enumerate(content.split('\n'), 1):
            for pattern, label in SENSITIVE_PATTERNS:
                m = re.search(pattern, line)
                if m:
                    classification = classify_match(filepath, line, label)
                    masked = re.sub(r'["\']?[A-Za-z0-9_\-]{10,}', '***', line.strip()[:100])
                    entry = f"  {'🛑' if 'REAL' in classification else '⚠️'} [{classification}] {filepath}:{line_num}: {masked}"
                    results.append(entry)
                    if 'REAL' in classification: has_real = True
                    break
    return (name, has_real, results)

def main():
    repos = DEFAULT_REPOS
    if len(sys.argv) > 1 and '--repos' in sys.argv:
        idx = sys.argv.index('--repos')
        names = sys.argv[idx + 1].split(',')
        repos = [(n, os.path.join(HOME, n)) for n in names]
    print("=" * 60)
    print("🔍 SENSITIVE DATA QC SCAN")
    print("=" * 60)
    all_clean = True; any_real_leak = False
    for name, path in repos:
        print(f"\n📁 {name}")
        _, has_real, results = scan_repo(name, path)
        if has_real: any_real_leak = True; all_clean = False
        if not results: print("  ✅ No matches found")
        else:
            for r in results: print(r)
    print("\n" + "=" * 60)
    if any_real_leak: print("❌ REAL LEAKS DETECTED — abort push"); sys.exit(1)
    elif all_clean: print("✅ All repos clean — safe to push"); sys.exit(0)
    else: print("⚠️  False positives only — safe to push"); sys.exit(0)

if __name__ == "__main__": main()
