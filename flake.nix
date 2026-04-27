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
        pkgs.writeShellScriptBin "hop" ''
          exec ${pkgs.python3}/bin/python3 ${./quick-ssh.py} "$@"
        '';
    };
}
