"""Mirror upstream and maintain one review proposal; never execute upstream code.

Only main may be synchronized. The compatibility branch and local applications
are never modified by this coordinator. Authentication is supplied to gh by Actions.
"""
from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path
from urllib.parse import urlencode

REPOSITORY = "KATOUIV/claude-desktop-zh-cn"
UPSTREAM = "javaht/claude-desktop-zh-cn"
BASE = "katou/windows-compat"
BEGIN = "<!-- upstream-tracking:start -->"
END = "<!-- upstream-tracking:end -->"


class GitHub:
    @staticmethod
    def run(command, payload=None):
        result = subprocess.run(command, input=payload, capture_output=True, text=True, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{command[0]} failed ({result.returncode}): {result.stderr.strip()[:2000]}")
        return result.stdout

    def sync(self):
        # gh rejects a divergent mirror by default. Never pass --force.
        self.run(["gh", "repo", "sync", REPOSITORY, "--source", UPSTREAM, "--branch", "main"])

    def api(self, endpoint, method="GET", data=None):
        command = ["gh", "api", "--method", method, endpoint]
        if data is not None:
            command += ["--input", "-"]
        return json.loads(self.run(command, json.dumps(data) if data is not None else None))


def replace_block(body, block):
    """Replace only our own machine-written section; retain human review notes."""
    if BEGIN not in body and END not in body:
        return body.rstrip() + ("\n\n" if body.strip() else "") + block
    if body.count(BEGIN) != 1 or body.count(END) != 1 or body.index(BEGIN) > body.index(END):
        raise ValueError("Ambiguous tracking markers; preserve review text and stop")
    start, finish = body.index(BEGIN), body.index(END) + len(END)
    return body[:start] + block + body[finish:]


def track(client, repository=REPOSITORY):
    if repository != REPOSITORY:
        raise ValueError("Tracking writes are restricted to the configured personal Fork")
    client.sync()  # A failure must stop all subsequent API mutations.
    release = client.api(f"repos/{UPSTREAM}/releases/latest")
    mirror_sha = client.api(f"repos/{REPOSITORY}/git/ref/heads/main")["object"]["sha"]
    compare = client.api(f"repos/{REPOSITORY}/compare/katou%2Fwindows-compat...{mirror_sha}")
    pending = int(compare["ahead_by"])
    report = {"status": "current" if pending == 0 else "review_needed", "release": release["tag_name"],
              "release_url": release["html_url"], "mirror_sha": mirror_sha,
              "pending_commits": pending, "compatibility_only_commits": compare["behind_by"]}
    if pending == 0:
        return report

    matches = []
    page = 1
    while True:
        query = urlencode({"state": "open", "base": BASE, "per_page": 100, "page": page})
        prs = client.api(f"repos/{REPOSITORY}/pulls?{query}")
        matches.extend(pr for pr in prs if pr.get("head", {}).get("ref") == "main"
                       and (pr["head"].get("repo") or {}).get("full_name") == REPOSITORY)
        if len(prs) < 100:
            break
        page += 1
    if len(matches) > 1:
        raise ValueError("Multiple upstream review PRs exist; stop instead of creating a duplicate")

    files = compare.get("files", [])
    names = "\n".join("- <code>" + html.escape(f["filename"]) + "</code>" for f in files[:30])
    block = (f"{BEGIN}\n## 自动上游追踪\n\n"
             f"正式 Release：[{release['tag_name']}]({release['html_url']})。\n\n"
             f"镜像提交：`{report['mirror_sha']}`；待审上游提交：{pending}。\n\n"
             f"相关文件（最多显示 30 个，完整差异见 PR Files changed）：\n{names}\n\n"
             "本区块仅记录同步信息，不代表兼容性或测试通过。正式 Release 之后的 main 提交可能尚未发布。\n\n"
             "云端仅快进 main，绝不自动合并维护分支、解决代码冲突或安装客户端补丁。"
             "GitHub 内置令牌创建的 PR 不会自动触发后续 CI；由 Codex 审阅、必要时在整合分支解决冲突，"
             "推送后等待 Windows/Linux 必需检查通过，再按保护规则合并。\n"
             f"{END}")
    if matches:
        pr = matches[0]
        body = replace_block(pr.get("body") or "", block)
        if body != (pr.get("body") or ""):
            client.api(f"repos/{REPOSITORY}/pulls/{pr['number']}", "PATCH", {"body": body})
    else:
        pr = client.api(f"repos/{REPOSITORY}/pulls", "POST", {
            "title": "审阅上游更新（保留 Windows 兼容修复）", "head": "main", "base": BASE,
            "draft": True, "body": block})
    report["pull_request"] = pr["html_url"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = track(GitHub(), args.repository)
    except Exception as error:
        report = {"status": "failed", "error": str(error)}
        raise
    finally:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.summary.write_text("## Upstream tracking\n\n```json\n" + json.dumps(report, ensure_ascii=False, indent=2)
                                + "\n```\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
