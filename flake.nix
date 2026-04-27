{
  description = "hop - fuzzy SSH host selector";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.default =
        pkgs.writers.writePython3Bin "hop" { } (builtins.readFile ./quick-ssh.py);
    };
}
