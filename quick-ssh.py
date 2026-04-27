#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DATA_FILE = Path.home() / ".local/share/quick-ssh/hosts.json"
OLD_DATA_FILE = Path.home() / "my-projects/quick-ssh/lists.json"
HISTORY_LIMIT = 10


def natural_key(s):
    return [
        int(c) if c.isdigit() else c.lower()
        for c in re.split(r"(\d+)", s)
    ]


def migrate(old):
    ignore = {"metadata", "quick_hist", "ext_ashwin_na_ad_tech"}
    return {
        "hosts": {k: v for k, v in old.items() if k not in ignore},
        "history": old.get("quick_hist", []),
        "history_limit": (
            old.get("metadata", {}).get("history_limit", HISTORY_LIMIT)
        ),
    }


def load_data():
    if not DATA_FILE.exists():
        if OLD_DATA_FILE.exists():
            try:
                data = migrate(json.loads(OLD_DATA_FILE.read_text()))
                save_data(data)
                return data
            except Exception:
                pass
        return {"hosts": {}, "history": [], "history_limit": HISTORY_LIMIT}

    try:
        data = json.loads(DATA_FILE.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in {DATA_FILE}: {e}")

    if "metadata" in data:
        data = migrate(data)
        save_data(data)
    return data


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    for user in data.get("hosts", {}):
        data["hosts"][user] = sorted(
            data["hosts"][user], key=natural_key
        )
    DATA_FILE.write_text(json.dumps(data, indent=4))


def fzf_select(items):
    result = subprocess.run(
        ["fzf", "--prompt=hop> ", "--height=40%", "--reverse",
         "--no-sort"],
        input="\n".join(items),
        text=True,
        stdout=subprocess.PIPE,
    )
    if result.returncode != 0:
        sys.exit(0)
    return result.stdout.strip()


def get_ssh_user(host):
    result = subprocess.run(
        ["ssh", "-G", host], capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if line.startswith("user "):
            return line.split(" ", 1)[1].strip()
    return None


def update_history(data, entry):
    hist = data.setdefault("history", [])
    if entry in hist:
        hist.remove(entry)
    hist.insert(0, entry)
    data["history"] = hist[: data.get("history_limit", HISTORY_LIMIT)]


def connect(user, host, use_mosh=False, forward=False, as_root=False):
    actual_user = "root" if as_root else user
    target = f"{actual_user}@{host}"
    ssh_cmd = ["ssh", "-A", target] if forward else ["ssh", target]

    if not use_mosh:
        subprocess.run(ssh_cmd)
        return

    mosh_ssh = "ssh -A" if forward else "ssh"
    result = subprocess.run(["mosh", f"--ssh={mosh_ssh}", target])
    if result.returncode != 0:
        print("mosh failed, falling back to ssh")
        subprocess.run(ssh_cmd)


def cmd_connect(args):
    data = load_data()
    entries = []
    seen = set()

    for entry in data.get("history", []):
        entries.append(f"[h] {entry}")
        seen.add(entry)

    for user, hosts in data.get("hosts", {}).items():
        for host in hosts:
            entry = f"{user}@{host}"
            if entry not in seen:
                entries.append(entry)

    if not entries:
        sys.exit("No hosts configured. Use 'hop add <host>'.")

    selected = fzf_select(entries)
    if selected.startswith("[h] "):
        selected = selected[4:]

    user, host = selected.split("@", 1)
    update_history(data, f"{user}@{host}")
    save_data(data)
    connect(
        user, host,
        use_mosh=args.mosh,
        forward=args.forward,
        as_root=args.root,
    )


def cmd_add(args):
    data = load_data()
    host = args.host
    user = args.user or get_ssh_user(host)

    if not user:
        sys.exit(f"Cannot detect user for {host}. Use -u to specify.")

    user_hosts = data.setdefault("hosts", {}).setdefault(user, [])

    if host in user_hosts:
        print(f"Already in list: {user}@{host}")
        return

    user_hosts.append(host)
    save_data(data)
    print(f"Added {user}@{host}")


def cmd_rm(args):
    data = load_data()
    host = args.host
    removed = []

    for user, hosts in data.get("hosts", {}).items():
        if host in hosts:
            hosts.remove(host)
            removed.append(f"{user}@{host}")

    if not removed:
        sys.exit(f"Not found: {host}")

    for r in removed:
        print(f"Removed {r}")
    save_data(data)


def cmd_sync(args):
    data = load_data()
    known = Path.home() / ".ssh/known_hosts"

    if not known.exists():
        sys.exit("~/.ssh/known_hosts not found")

    hosts_by_user = data.setdefault("hosts", {})
    added = 0

    for line in known.read_text().splitlines():
        if not line or line.startswith(("#", "|")):
            continue
        host = line.split()[0]
        if "," in host or host.startswith("["):
            continue

        user = get_ssh_user(host)
        if not user:
            continue

        user_hosts = hosts_by_user.setdefault(user, [])
        if host not in user_hosts:
            user_hosts.append(host)
            added += 1

    save_data(data)
    print(f"Synced: +{added} new hosts")


def main():
    parser = argparse.ArgumentParser(
        prog="hop", description="Fuzzy SSH host selector"
    )
    parser.add_argument(
        "-m", "--mosh", action="store_true",
        help="use mosh (default: ssh)",
    )
    parser.add_argument(
        "-A", "--forward", action="store_true",
        help="SSH agent forwarding",
    )
    parser.add_argument(
        "--root", action="store_true", help="connect as root"
    )

    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="add a host")
    p_add.add_argument("host")
    p_add.add_argument(
        "-u", "--user",
        help="SSH user (auto-detected from ~/.ssh/config if omitted)",
    )

    p_rm = sub.add_parser("rm", help="remove a host")
    p_rm.add_argument("host")

    sub.add_parser("sync", help="populate from ~/.ssh/known_hosts")

    args = parser.parse_args()
    dispatch = {"add": cmd_add, "rm": cmd_rm, "sync": cmd_sync}
    dispatch.get(args.cmd, cmd_connect)(args)


if __name__ == "__main__":
    main()
