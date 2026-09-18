#!/usr/bin/env python3
"""تطبيق ملفات الـ migration على Supabase عبر Management API.

يتطلب متغيرين من البيئة:
  SUPABASE_ACCESS_TOKEN  — Personal Access Token (sbp_...) من https://supabase.com/dashboard/account/tokens
  SUPABASE_PROJECT_REF   — معرّف المشروع (مثل vsffmvrpuwhodgqpjzcg)

الاستخدام:
  python scripts/apply_migration.py supabase/migrations/*.sql
"""
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.supabase.com/v1"


def main() -> None:
    token = os.environ.get("SUPABASE_ACCESS_TOKEN", "").strip()
    ref = os.environ.get("SUPABASE_PROJECT_REF", "").strip()
    if not token:
        sys.exit("Missing SUPABASE_ACCESS_TOKEN (sbp_...). Create one at https://supabase.com/dashboard/account/tokens")
    if not ref:
        sys.exit("Missing SUPABASE_PROJECT_REF")

    files = [f for f in sys.argv[1:] if f.lower().endswith(".sql")]
    if not files:
        sys.exit("Usage: apply_migration.py <migration.sql> [...]")
    files.sort()

    for path in files:
        with open(path, encoding="utf-8") as fh:
            sql = fh.read()
        if not sql.strip():
            continue
        print(f"applying {path} ({len(sql)} chars)")
        _run_query(ref, token, sql, history_files=files)


def _run_query(ref: str, token: str, sql: str, history_files: list[str]) -> None:
    body = {"query": sql}
    req = urllib.request.Request(
        f"{API}/projects/{ref}/database/query",
        data=__import__("json").dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "salaq-migration",
        },
        method="POST",
    )
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                print(f"  OK ({resp.status})")
                return
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:400]
            if exc.code in (408, 429, 500, 502, 503, 504) and attempt < 3:
                print(f"  retry {attempt} after {exc.code}...")
                time.sleep(4)
                continue
            sys.exit(f"  FAILED HTTP {exc.code}: {detail}")
        except Exception as exc:  # noqa: BLE001
            sys.exit(f"  FAILED {exc}")


if __name__ == "__main__":
    main()