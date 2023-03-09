{
  description = "chir.rs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:DarkKirb/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  } @ inputs:
    flake-utils.lib.eachSystem ["x86_64-linux" "aarch64-linux" "riscv64-linux"] (system: let
      pkgs = import nixpkgs {
        inherit system;
      };
    in rec {
      devShells.default =
        (pkgs.poetry2nix.mkPoetryEnv {
          projectDir = ./.;
        })
        .overrideAttrs (super: {
          buildInputs =
            (super.buildInputs or [])
            ++ (with pkgs; [
              sqlite
              poetry
              yapf
              postgresql
            ]);
        });

      packages = {
        default = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
        };
      };

      nixosModules.default = import ./nixos {
        inherit inputs system;
      };
      hydraJobs =
        packages
        // {
          inherit devShells formatter;
        };
      formatter = pkgs.alejandra;
    });
}
