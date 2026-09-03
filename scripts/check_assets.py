#!/usr/bin/env python3
"""
HTML 파일 안의 이미지/영상/폰트 참조를 전부 찾아서:
  1. 로컬 경로면 실제로 그 파일이 저장소 안에 있는지 (대소문자까지) 확인
  2. 외부 URL이면 실제로 접속되는지(HTTP 상태코드) 확인
깨진 게 하나라도 있으면 실패(exit 1)하고 목록을 출력한다.

이 파일은 파일 시스템에 존재하는지, 외부 링크가 살아있는지만 확인한다.
"어떤 도메인이 문제였는지"는 신경 쓰지 않는다 — 존재하고 접속되면 통과.
"""
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HTML_FILES = sorted(REPO_ROOT.glob("*.html"))

# src="...", href="...(이미지/영상/폰트 확장자만)", url('...')  세 패턴에서 자산 경로 추출
ASSET_EXT = r"png|jpe?g|gif|svg|webp|avif|mp4|webm|mov|mp3|woff2?|ttf|otf|ico"
PATTERNS = [
    re.compile(r'(?:src|href)\s*=\s*["\']([^"\']+\.(?:' + ASSET_EXT + r'))["\']', re.IGNORECASE),
    re.compile(r'url\(\s*["\']?([^"\')]+\.(?:' + ASSET_EXT + r'))["\']?\s*\)', re.IGNORECASE),
]

UA = "Mozilla/5.0 (compatible; MYRO-asset-checker/1.0)"


def find_asset_refs(html_text: str) -> set[str]:
    refs = set()
    for pat in PATTERNS:
        for m in pat.finditer(html_text):
            refs.add(m.group(1))
    return refs


def check_local(path_str: str) -> str | None:
    """로컬 파일이 실제로 있는지 (대소문자 정확히) 확인. 문제 있으면 에러 메시지, 없으면 None."""
    clean = path_str.split("?")[0].split("#")[0]
    target = (REPO_ROOT / clean).resolve()
    if not str(target).startswith(str(REPO_ROOT)):
        return f"저장소 바깥 경로: {path_str}"
    if not target.exists():
        return f"파일 없음: {clean}"
    # 대소문자 확인 (macOS는 대소문자 구분 안 하지만 GitHub Pages는 구분함)
    try:
        actual_name = target.name
        real_children = {p.name for p in target.parent.iterdir()}
        if actual_name not in real_children:
            return f"대소문자 불일치 의심: {clean}"
    except Exception:
        pass
    return None


def check_remote(url: str) -> str | None:
    """외부 URL이 실제로 접속되는지 확인. 문제 있으면 에러 메시지, 없으면 None."""
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status >= 400:
                return f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"접속 실패: {e}"
    return None


def main() -> int:
    problems: list[tuple[str, str, str]] = []  # (html파일, 자산경로, 에러)

    for html_path in HTML_FILES:
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        for ref in sorted(find_asset_refs(text)):
            if ref.startswith("data:"):
                continue
            if ref.startswith("http://") or ref.startswith("https://") or ref.startswith("//"):
                url = ref if not ref.startswith("//") else "https:" + ref
                err = check_remote(url)
            else:
                err = check_local(ref)
            if err:
                problems.append((html_path.name, ref, err))

    if problems:
        print(f"\n깨진 자산 {len(problems)}개 발견:\n")
        for html_file, ref, err in problems:
            print(f"  [{html_file}] {ref}\n      -> {err}")
        print("\n로컬 파일은 저장소에 실제로 추가하고, 외부 링크는 접속 가능한 주소인지 확인하세요.")
        return 1

    total = sum(len(find_asset_refs(p.read_text(encoding='utf-8', errors='ignore'))) for p in HTML_FILES)
    print(f"모든 자산 정상 ({total}개 확인, {len(HTML_FILES)}개 HTML 파일)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
