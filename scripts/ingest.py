#!/usr/bin/env python3
"""取得公開來源與可核對的摘要，不呼叫任何模型或讀取金鑰。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify():
    entries = json.loads((SOURCES / "registry.json").read_text(encoding="utf-8"))
    expected_ids = [source["id"] for source in json.loads((SOURCES / "catalog.json").read_text(encoding="utf-8"))]
    if [entry["id"] for entry in entries] != expected_ids:
        raise ValueError("registry 來源編號或順序與 catalog 不一致")
    for entry in entries:
        path = ROOT / entry["raw_path"]
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f'{entry["id"]} 本機原文與 registry 雜湊不符')
        if entry["http_status"] != 200 or not entry["resolved_url"].startswith("https://"):
            raise ValueError(f'{entry["id"]} HTTP 紀錄不合格')
        print(f'{entry["id"]} OK {len(data)} bytes sha256={entry["sha256"]}')
    print(f"VERIFY PASS: {len(entries)} sources")


def ingest():
    catalog = json.loads((SOURCES / "catalog.json").read_text(encoding="utf-8"))
    ids = [source["id"] for source in catalog]
    if len(ids) != len(set(ids)):
        raise ValueError("catalog 來源編號重複")
    raw_dir = SOURCES / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    # 全部來源皆成功才取代先前原文和清單，失敗不把半份資料當完成。
    with tempfile.TemporaryDirectory(prefix="ingest-", dir=raw_dir) as temp:
        stage = Path(temp)
        for source in catalog:
            target = stage / source["filename"]
            result = subprocess.run([
                "curl", "--fail", "--location", "--silent", "--show-error",
                "--proto", "=https", "--proto-redir", "=https",
                "--connect-timeout", "15", "--max-time", "90",
                "--user-agent", "Campusward-coursework-source-check/1.0",
                "--output", str(target), "--write-out", "%{json}", source.get("download_url", source["url"]),
            ], capture_output=True, text=True, check=False)
            if result.returncode:
                raise RuntimeError(f'{source["id"]} curl {result.returncode}: {result.stderr.strip()}')
            meta = json.loads(result.stdout)
            if meta["http_code"] != 200:
                raise RuntimeError(f'{source["id"]} HTTP {meta["http_code"]}，未收錄')
            data = target.read_bytes()
            text = data.decode(source.get("encoding", "utf-8"))
            if len(data) < 100 or not all(token.casefold() in text.casefold() for token in source["expected"]):
                raise ValueError(f'{source["id"]} 原文內容不符，可能是登入頁或錯誤頁')
            entry = {key: source[key] for key in ("id", "title", "url", "kind")}
            if "download_url" in source:
                entry["download_url"] = source["download_url"]
            entry.update({
                "retrieved_at": now(), "sha256": hashlib.sha256(data).hexdigest(),
                "raw_path": f'sources/raw/{source["filename"]}', "bytes": len(data),
                "notes": source["notes"], "cautions": source["cautions"],
                "http_status": meta["http_code"], "resolved_url": meta["url_effective"],
                "content_type": meta.get("content_type"),
            })
            entries.append(entry)
            print(f'{source["id"]} HTTP 200 {len(data)} bytes {meta["url_effective"]}', flush=True)
        for source in catalog:
            (stage / source["filename"]).replace(raw_dir / source["filename"])
        write_json(SOURCES / "registry.json", entries)
    for entry in entries:
        lines = [f'# {entry["id"]} {entry["title"]}', "", f'[原文]({entry["url"]})', ""]
        lines += [f'- {note}' for note in entry["notes"]]
        lines += ["", "限制：" + "；".join(entry["cautions"]) + "。", ""]
        (SOURCES / f'{entry["id"]}.md').write_text("\n".join(lines), encoding="utf-8")
    with (SOURCES / "ingest-log.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"at": now(), "status": "ok", "count": len(entries), "ids": ids}, ensure_ascii=False) + "\n")
    print(f"INGEST PASS: {len(entries)} sources")
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="只核對本機原文大小、雜湊和 HTTP 紀錄")
    args = parser.parse_args()
    try:
        verify() if args.verify_only else ingest()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
