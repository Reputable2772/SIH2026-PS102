{
  description = "SIH PS102 (MoSPI - MPLADS) Prototype";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      devShells = forEachSupportedSystem ({ pkgs }:
        let
          pythonEnv = pkgs.python3.withPackages (ps: with ps; [
            requests
            pandas
          ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              pythonEnv
              pkgs.curl
              pkgs.jq
            ];

            shellHook = ''
              echo "SIH PS102 (MPLADS) environment loaded."
              echo "Python: $(python3 --version)"
            '';
          };
        });

      packages = forEachSupportedSystem ({ pkgs }:
        let
          pythonEnv = pkgs.python3.withPackages (ps: with ps; [
            requests
            pandas
          ]);
        in
        {
          mplads-scraper = pkgs.writeShellApplication {
            name = "mplads-scraper";
            runtimeInputs = [ pythonEnv ];
            text = ''
              exec python3 "${./scraper/mplads/mplads_scraper.py}" "$@"
            '';
          };

          default = self.packages.${pkgs.stdenv.hostPlatform.system}.mplads-scraper;
        });
    };
}
