#!/usr/bin/env python3
"""Runs one Codex CLI session in a bubblewrap container that cannot see the project or the real home directory (deviation D22).

The container holds only: read-only /usr and /etc (and the usual /bin, /lib links), a private /tmp, /proc and /dev, the native
Codex executable (read-only, /opt/codex), a fresh CODEX_HOME with a copy of the authentication file and a minimal configuration,
and the working directory (/work). The environment is cleared. Nothing else of the host filesystem is mounted, so neither the CLI
nor any child process can read the project, earlier Codex sessions, global AGENTS.md, memories, skills or hooks.

Used by code_q3_codex.py (RQ3) and by the RQ4 second reading. Requires bwrap (bubblewrap) and the native Codex binary.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

VENDOR = Path.home() / ".local/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl"
HOST_HOME = str(Path.home())
INNER_HOME = "/home/coder"
INNER_CODEX_HOME = f"{INNER_HOME}/.codex"
# Developer blocks that Codex CLI 0.162.0 sends on its own (observed in an isolated session on 17 Oct 2026): the bundled skills
# list (with the permissions and collaboration-mode sections), and two fixed multi-agent texts that it still sends with the
# multi_agent feature disabled. None of them carries user or project content.
ALLOWED_DEVELOPER_TAGS = {"permissions instructions", "collaboration_mode", "apps_instructions", "skills_instructions",
                          "multi_agent_role", "multi_agent_mode"}


def minimal_config(model: str, effort: str) -> str:
    # multi-agent off, so no team-role instructions; no MCP servers, no profiles, no project trust entries.
    return f'model = "{model}"\nmodel_reasoning_effort = "{effort}"\n\n[features]\nmulti_agent = false\n'


def make_codex_home(root: Path, auth: Path, model: str, effort: str) -> Path:
    home = root / "codex-home"
    home.mkdir(parents=True)
    shutil.copy2(auth, home / "auth.json")
    os.chmod(home / "auth.json", 0o600)
    (home / "config.toml").write_text(minimal_config(model, effort))
    return home


def bwrap_argv(codex_home: Path, workdir: Path, ro_binds: tuple[tuple[Path, str], ...] = (), vendor: Path = VENDOR) -> list[str]:
    argv = ["bwrap", "--die-with-parent", "--new-session", "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--clearenv",
            "--ro-bind", "/usr", "/usr", "--symlink", "usr/bin", "/bin", "--symlink", "usr/sbin", "/sbin",
            "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
            "--ro-bind", "/etc", "/etc", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
            "--ro-bind", str(vendor), "/opt/codex",
            "--tmpfs", "/home", "--dir", INNER_HOME,
            "--bind", str(codex_home), INNER_CODEX_HOME,
            "--bind", str(workdir), "/work"]
    for src, dst in ro_binds:
        argv += ["--ro-bind", str(src), dst]
    argv += ["--setenv", "HOME", INNER_HOME, "--setenv", "CODEX_HOME", INNER_CODEX_HOME,
             "--setenv", "PATH", "/opt/codex/bin:/opt/codex/codex-path:/usr/bin:/bin", "--setenv", "LANG", "C.UTF-8",
             "--chdir", "/work"]
    return argv


def codex_exec_args(model: str, effort: str, schema_inner: str | None, reply_inner: str = "/work/reply.txt") -> list[str]:
    args = ["/opt/codex/bin/codex", "exec", "-s", "read-only", "-c", 'approval_policy="never"', "--json", "-o", reply_inner,
            "--disable", "apps", "--disable", "plugins", "--disable", "multi_agent", "-c", "notify=[]", "--skip-git-repo-check",
            "-m", model, "-c", f'model_reasoning_effort="{effort}"']
    if schema_inner:
        args += ["--output-schema", schema_inner]
    return args + ["-"]


def probe(codex_home: Path, workdir: Path, ro_binds=(), vendor: Path = VENDOR) -> dict:
    """Inside the same container, the host home, the project and the real ~/.codex must not exist."""
    targets = [HOST_HOME, f"{HOST_HOME}/Desktop/redazione", f"{HOST_HOME}/.codex", f"{HOST_HOME}/.claude", "/run/user"]
    script = "for p in " + " ".join(f"'{t}'" for t in targets) + "; do if [ -e \"$p\" ]; then echo \"VISIBLE $p\"; fi; done; echo done"
    r = subprocess.run(bwrap_argv(codex_home, workdir, ro_binds, vendor) + ["/bin/sh", "-c", script],
                       capture_output=True, text=True, timeout=60)
    visible = [l[len("VISIBLE "):] for l in r.stdout.splitlines() if l.startswith("VISIBLE ")]
    ok = r.returncode == 0 and r.stdout.strip().endswith("done") and not visible
    return {"ok": ok, "visible": visible, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr[-2000:]}


def run_session(prompt: str, root: Path, auth: Path, model: str, effort: str, schema: dict | None = None,
                ro_binds=(), timeout: int = 900, vendor: Path = VENDOR) -> dict:
    """One fresh session. Returns the record; the caller decides validity with check_context()."""
    workdir = root / "work"
    workdir.mkdir(parents=True)
    codex_home = make_codex_home(root, auth, model, effort)
    if schema is not None:
        (workdir / "schema.json").write_text(json.dumps(schema))
    pr = probe(codex_home, workdir, ro_binds, vendor)
    record = {"probe": pr, "model": model, "effort": effort, "prompt": prompt}
    if not pr["ok"]:
        record["status"] = "probe-failed"
        return record
    argv = bwrap_argv(codex_home, workdir, ro_binds, vendor) + codex_exec_args(model, effort, "/work/schema.json" if schema else None)
    record["argv"] = argv
    (root / "argv.json").write_text(json.dumps(argv, indent=1))
    with open(root / "events.jsonl", "wb") as out, open(root / "stderr.txt", "wb") as err:
        p = subprocess.run(argv, input=prompt.encode(), stdout=out, stderr=err, timeout=timeout)
    record["exit_code"] = p.returncode
    reply = workdir / "reply.txt"
    record["reply"] = reply.read_text() if reply.exists() else None
    rollouts = sorted(codex_home.glob("sessions/*/*/*/rollout-*.jsonl"))
    record["rollouts"] = [str(r.relative_to(root)) for r in rollouts]
    (codex_home / "auth.json").unlink(missing_ok=True)  # never keep a credential copy next to the evidence
    record["status"] = "completed" if p.returncode == 0 and record["reply"] else "failed"
    return record


def _messages(rollout: Path):
    for line in rollout.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        p = d.get("payload")
        if d.get("type") == "response_item" and isinstance(p, dict) and p.get("type") == "message":
            text = "".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict))
            yield p.get("role"), text


def check_context(rollout: Path, prompt: str) -> dict:
    """Allowed initial context: the CLI's own developer instructions (allowlisted tags), one <environment_context> block,
    and our prompt. Rejected: any AGENTS.md block, any other user message, any developer block outside the allowlist,
    any reference to the host home directory."""
    problems, tags, users = [], [], 0
    for role, text in _messages(rollout):
        if role == "assistant":
            break
        if HOST_HOME in text:
            problems.append(f"{role} message mentions the host home directory")
        if "AGENTS.md instructions" in text:
            problems.append("AGENTS.md instructions present")
        if role == "developer":
            head = text.lstrip()[:80]
            tag = head[1:head.index(">")] if head.startswith("<") and ">" in head else None
            tags.append(tag)
            if tag not in ALLOWED_DEVELOPER_TAGS:
                problems.append(f"developer block not allowlisted: {tag or head[:40]!r}")
        elif role == "user":
            users += 1
            if text.lstrip().startswith("<environment_context>"):
                continue
            if text.strip() != prompt.strip():
                problems.append("user message other than the prompt and the environment context")
    if users == 0:
        problems.append("no user message found")
    return {"ok": not problems, "problems": problems, "developer_tags": tags}
