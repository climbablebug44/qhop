# qhop

Fuzzy SSH host selector. Manages a list of servers and connects to them via `fzf`.

## Usage

```
qhop                      # fuzzy select → ssh
qhop -m / --mosh          # fuzzy select → mosh (falls back to ssh)
qhop -A / --forward       # SSH agent forwarding
qhop --root               # connect as root

qhop add <host>           # add host (user auto-detected from ~/.ssh/config)
qhop add <host> -u USER   # add host with explicit user
qhop rm <host>            # remove host
qhop sync                 # populate from ~/.ssh/known_hosts
```

## Try it

```bash
nix run github:climbablebug44/qhop
```

## Installation

### NixOS + home-manager

Add as a flake input in your `flake.nix`:

```nix
inputs.qhop = {
  url = "github:climbablebug44/qhop";
  inputs.nixpkgs.follows = "nixpkgs";
};
```

Pass to home-manager and add to packages:

```nix
home.packages = [ inputs.qhop.packages.${pkgs.system}.default ];
```

## Data

Hosts are stored in `~/.local/share/quick-ssh/hosts.json`. User is auto-detected
per host via `ssh -G`, which reads your `~/.ssh/config` patterns.

History (last 10 connections) is shown at the top of the fuzzy list with a `[h]` prefix.
