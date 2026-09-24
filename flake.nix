{
  description = "SIH PS102 (MoSPI - MPLADS) Prototype";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forEachSupportedSystem =
        f:
        nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            pkgs = import nixpkgs { inherit system; };
          }
        );
    in
    {
      formatter = forEachSupportedSystem ({ pkgs }: pkgs.nixfmt);

      devShells = forEachSupportedSystem (
        { pkgs }:
        let
          pythonEnv = pkgs.python3.withPackages (
            ps: with ps; [
              requests
              pandas
              numpy
              scipy
              scikit-learn
              pyarrow
              joblib
              pytest
              fastapi
              uvicorn
              pyjwt
              python-multipart
              httpx
            ]
          );
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.nixfmt
              pkgs.ruff
              pythonEnv
              pkgs.nodejs
              pkgs.pnpm
              pkgs.curl
              pkgs.jq
            ];

            shellHook = ''
              echo "SIH PS102 (MPLADS Full-Stack) environment loaded."
              echo "Python: $(python3 --version)"
              echo "Node: $(node --version 2>/dev/null || echo 'N/A')"
              echo "pnpm: $(pnpm --version 2>/dev/null || echo 'N/A')"
            '';
          };
        }
      );

      packages = forEachSupportedSystem (
        { pkgs }:
        let
          pythonEnv = pkgs.python3.withPackages (
            ps: with ps; [
              requests
              pandas
              numpy
              scipy
              scikit-learn
              pyarrow
              joblib
              pytest
            ]
          );
        in
        {
          default = pkgs.writeShellApplication {
            name = "mplads-engine";
            runtimeInputs = [ pythonEnv ];
            text = ''
              export PYTHONPATH=".:detectors:''${PYTHONPATH:-}"
              exec python3 -m detectors.src.cli "$@"
            '';
          };

          mplads-engine = pkgs.writeShellApplication {
            name = "mplads-engine";
            runtimeInputs = [ pythonEnv ];
            text = ''
              export PYTHONPATH=".:detectors:''${PYTHONPATH:-}"
              exec python3 -m detectors.src.cli "$@"
            '';
          };

          mplads-scraper = pkgs.writeShellApplication {
            name = "mplads-scraper";
            runtimeInputs = [ pythonEnv ];
            text = ''
              exec python3 "${./scraper/mplads/mplads_scraper.py}" "$@"
            '';
          };
        }
      );
    };
}
