"""llama.cpp 转换所需最小源码集下载器（2 路并发、按文件续传）。

仅下载 convert_hf_to_gguf.py 所需源码；不下载/解压二进制，不执行转换/量化，不写产物。
方案与 CLI 契约见 .code/state/qwen3-q4km-export/spec.md。
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = "ggml-org/llama.cpp"
API_SUBTREE = "https://api.github.com/repos/{repo}/git/trees/{branch}:{sub}?recursive=1"
API_ROOT_TREE = "https://api.github.com/repos/{repo}/git/trees/{branch}"
RAW_HOSTS = (
    "https://cdn.jsdelivr.net/gh/{repo}@{branch}/{path}",
    "https://raw.githubusercontent.com/{repo}/{branch}/{path}",
)
SOURCE_SUBTREES = ("conversion", "gguf-py", "requirements")
SOURCE_TOP_FILES = ("convert_hf_to_gguf.py",)
SRC_STATE = ".llama_src.json"

WANT_FILES = {"convert_hf_to_gguf.py", "gguf-py/pyproject.toml", "gguf-py/README.md"}
WANT_PREFIX = ("conversion/", "gguf-py/gguf/", "requirements/")
PURGE_DIRS = ("conversion", "gguf-py", "requirements")
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz")
CHECK_FILES = (
    "convert_hf_to_gguf.py",
    "conversion/__init__.py",
    "gguf-py/gguf/__init__.py",
    "gguf-py/gguf/gguf_writer.py",
    "requirements/requirements-convert_hf_to_gguf.txt",
)


def get_token():
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def http_get(url, timeout=30, retries=3):
    headers = {"User-Agent": "llama-min-dl/1.0"}
    tok = get_token()
    if tok and "api.github.com" in url:
        headers["Authorization"] = "Bearer " + tok
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                raise
            last = e
        except Exception as e:
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError("GET failed: %s :: %s" % (url, last))


def fetch_tree(branch):
    """返回 {path: size}（tree API 的 blob size）；整棵仓库树约 1.3MB 会被本机网络截断，故分子树取。"""
    out = {}
    # 顶层文件（convert_hf_to_gguf.py）走非递归根树，取真实 size 用于续传/版本比对
    try:
        data = json.loads(http_get(API_ROOT_TREE.format(repo=REPO, branch=branch)))
        if data.get("truncated"):
            print("[!] root tree 被截断，顶层文件可能不全", file=sys.stderr)
        for it in data.get("tree", []):
            if it.get("type") == "blob" and it.get("path") in SOURCE_TOP_FILES:
                out[it["path"]] = it.get("size")
    except Exception as e:
        print("[!] 顶层 tree 查询失败：%s（顶层文件 size 未知）" % e, file=sys.stderr)
    for rel in SOURCE_TOP_FILES:
        out.setdefault(rel, None)

    for sub in SOURCE_SUBTREES:
        url = API_SUBTREE.format(repo=REPO, branch=branch, sub=sub)
        try:
            data = json.loads(http_get(url))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                print("[x] GitHub API 限流：等几分钟，或先 set GH_TOKEN=你的PAT 再跑", file=sys.stderr)
            raise
        if data.get("truncated"):
            print("[!] %s tree 被截断，结果可能不全" % sub, file=sys.stderr)
        for it in data.get("tree", []):
            if it.get("type") == "blob":
                out["%s/%s" % (sub, it["path"])] = it.get("size")
    return out


def raw_get(branch, rel, expect=None):
    """原始文件下载：多镜像回退（CDN 优先，GitHub raw 兜底），逐镜像校验期望长度。"""
    last = None
    for tmpl in RAW_HOSTS:
        url = tmpl.format(repo=REPO, branch=branch, path=rel)
        try:
            data = http_get(url, timeout=40, retries=2)
            if expect is not None and len(data) != expect:
                # CDN 可能缓存旧版本：长度不符即换下一个镜像，不算该文件失败
                raise RuntimeError("长度 %d != 期望 %d（%s 缓存可能过期）" % (len(data), expect, tmpl))
            return data
        except Exception as e:
            last = e
    raise RuntimeError("raw GET failed for %s :: %s" % (rel, last))


def want(path):
    if path in WANT_FILES:
        return True
    if path.startswith(WANT_PREFIX):
        return not path.endswith(SKIP_SUFFIX)
    return False


def purge(out):
    for d in PURGE_DIRS:
        p = out / d
        if p.exists():
            print("[clean] 删除 " + str(p))
            shutil.rmtree(p, ignore_errors=True)
    p = out / "convert_hf_to_gguf.py"
    if p.exists():
        print("[clean] 删除 " + str(p))
        p.unlink()


def sources_ok(out):
    """静默判断源码最小集是否齐全（用于离线兜底）。"""
    if not all((out / rel).exists() for rel in CHECK_FILES):
        return False
    conv = out / "conversion"
    return conv.exists() and len(list(conv.glob("*.py"))) >= 5


def src_sig(items):
    """版本签名：{path: size} 排序后 JSON 的 sha256（branch 另行判定）。"""
    blob = json.dumps(sorted(items.items()), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def load_src_state(out):
    try:
        d = json.loads((out / SRC_STATE).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def save_src_state(out, branch, sig, files):
    (out / SRC_STATE).write_text(
        json.dumps({"branch": branch, "sig": sig, "files": files}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def verify(out):
    print("\n[verify]")
    bad = 0
    for rel in CHECK_FILES:
        p = out / rel
        if p.exists():
            print("  OK   " + rel)
        else:
            print("  MISS " + rel)
            bad += 1
    conv = out / "conversion"
    if conv.exists():
        n = len(list(conv.glob("*.py")))
        print("  conversion/*.py = %d" % n)
        if n < 5:
            bad += 1
    gg = out / "gguf-py" / "gguf"
    if gg.exists():
        print("  gguf-py/gguf/**/*.py = %d" % len(list(gg.rglob("*.py"))))
    print("")
    if bad:
        print("[x] 有 %d 项缺失" % bad)
    else:
        print("[ok] 最小集齐全")
    return bad


def ensure_sources(out, branch, skip_download):
    """源码就绪：同版本按文件续传（只补缺失/大小不符），版本变化清理后全量重下；2 线程并发。"""
    print("\n=== 源码下载 ===")
    if skip_download:
        print("[skip] --skip-download，仅校验已有源码")
        return verify(out) == 0

    offline = False
    try:
        tree = fetch_tree(branch)
    except Exception as e:
        print("[x] 获取源码文件列表失败：%s（检查网络/GH_TOKEN/--branch）" % e, file=sys.stderr)
        state = load_src_state(out)
        cached = None
        if state and state.get("branch") == branch and isinstance(state.get("files"), dict) and state["files"]:
            cached = {p: s for p, s in state["files"].items() if want(p) and s is not None}
        if cached:
            print("[i] 离线续传：使用本地清单（branch=%s，%d 个文件）" % (branch, len(cached)))
            tree = cached
            offline = True
        elif sources_ok(out):
            print("[!] 本地源码最小集齐全，离线继续（无法确认是否为上游最新版本）", file=sys.stderr)
            verify(out)
            return True
        else:
            return False

    targets = {p: s for p, s in tree.items() if want(p)}
    if not targets:
        print("[x] 未匹配到任何文件", file=sys.stderr)
        return False
    if offline:
        # 本地清单的 size 已知，按同版本处理：不 purge、不回写清单，只补缺失/不符项
        sig = None
        same = True
        write_state = False
    else:
        unknown = [p for p, s in targets.items() if s is None]
        if unknown:
            # None 不能进签名：否则根树恢复后 sig 变化会被误判成版本变化而整体重下
            print("[!] %d 个目标 size 未知（如 %s）：跳过按文件续传，当次全量下载且不写清单" %
                  (len(unknown), unknown[0]), file=sys.stderr)
            sig = None
            same = False
            write_state = False
        else:
            sig = src_sig(targets)
            print("[i] branch=%s 目标 %d 个文件 sig=%s" % (branch, len(targets), sig[:12]))
            state = load_src_state(out)
            same = bool(state) and state.get("branch") == branch and state.get("sig") == sig
            write_state = True

    if not same:
        print("[i] 无清单或版本变化（branch / 文件集 / 大小改变）→ 清理后全量下载")
        purge(out)
        try:
            (out / SRC_STATE).unlink(missing_ok=True)
        except OSError:
            pass
    if write_state:
        # 下载前落盘：中途失败/Ctrl+C 后签名仍一致，重跑只补缺失项，不再 purge 整体重下
        save_src_state(out, branch, sig, targets)
        print("[i] 已写源码清单 %s" % (out / SRC_STATE))

    # 主线程先筛掉已存在且大小一致的项（不进线程池），只把待下载项交给线程池
    pending = []
    skip_n = 0
    for rel, expect in sorted(targets.items()):
        dst = out / rel
        if same and dst.exists():
            try:
                cur = dst.stat().st_size
            except OSError:
                cur = -1
            if cur == expect:
                skip_n += 1
                continue
        pending.append((rel, expect))

    print("[i] 并发=2（待下载 %d 个文件，主线程跳过 %d 个）" % (len(pending), skip_n))
    lock = threading.Lock()
    counters = {"get": 0, "fail": 0}

    def fetch_one(i, rel, expect):
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = raw_get(branch, rel, expect)
            dst.write_bytes(data)
            with lock:
                counters["get"] += 1
                print("  [%d/%d] [get] %s (%.1f KB)" % (i, len(pending), rel, len(data) / 1024.0))
        except Exception as e:
            with lock:
                counters["fail"] += 1
                print("  [%d/%d] [x] %s :: %s" % (i, len(pending), rel, e), file=sys.stderr)
            # 失败只删该项，不影响其它线程；重跑只补失败项
            try:
                dst.unlink(missing_ok=True)
            except OSError:
                pass

    if pending:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(fetch_one, i, rel, expect)
                       for i, (rel, expect) in enumerate(pending, 1)]
            for future in futures:
                future.result()

    get_n = counters["get"]
    fail_n = counters["fail"]
    print("\n[done] [skip] %d 已存在 / [get] %d 下载 / [x] %d 失败" % (skip_n, get_n, fail_n))
    if fail_n:
        print("[!] 有 %d 个文件失败（只删了失败项，其余保留）；清单已写，重跑只补失败项" % fail_n, file=sys.stderr)
        return False
    return verify(out) == 0


def main():
    # Windows 重定向日志时默认 GBK，非 GBK 字符会导致 print 崩溃
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    script_dir = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(
        description="下载 llama.cpp 转换所需最小源码集（2 路并发、按文件续传）；不做转换/量化，不写产物"
    )
    ap.add_argument("--branch", default="master", help="llama.cpp 源码分支（默认 master）")
    ap.add_argument("--out", default=str(script_dir), help="源码工作区（默认脚本所在目录）")
    ap.add_argument("--skip-download", action="store_true", help="不联网，仅校验本地已有源码")
    a = ap.parse_args()

    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    print("[i] repo=%s branch=%s out=%s" % (REPO, a.branch, out))
    try:
        ok = ensure_sources(out, a.branch, a.skip_download)
    except KeyboardInterrupt:
        print("\n[!] 用户中断（Ctrl+C），退出 130", file=sys.stderr)
        return 130
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
