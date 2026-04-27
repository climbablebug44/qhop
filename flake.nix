{
  description = "qhop - fuzzy SSH host selector";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      qhop = pkgs.writeShellApplication {
        name = "qhop";
        runtimeInputs = [ pkgs.fzf pkgs.openssh pkgs.mosh ];
        text = ''
          exec ${pkgs.python3}/bin/python3 ${./quick-ssh.py} "$@"
        '';
      };
    in
    {
      packages.${system}.default = qhop;
      apps.${system}.default = {
        type = "app";
        program = "${qhop}/bin/qhop";
      };
    };
}
