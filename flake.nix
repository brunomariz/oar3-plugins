{
  description = "oar3 plugins";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
    kapack.url = "github:oar-team/nur-kapack?ref=master";
    #kapack.url = "github:oar-team/nur-kapack?ref=dynres";
    #kapack.url = "path:/home/auguste/dev/nur-kapack/dynres";
    kapack.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils,  kapack}:

    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        kapackpkgs = kapack.packages.${system};
        
        app = pkgs.python3Packages.buildPythonPackage {
          pname = "oar-plugins";
          version = "0.1.1";
          format = "pyproject";
          src = ./.;
          nativeBuildInputs = [ pkgs.python3Packages.poetry-core ];
          propagatedBuildInputs = [ kapackpkgs.oar ];
        };

        packageName = "oar-plugins";
      in {
        packages.${packageName} = app;
        defaultPackage = self.packages.${system}.${packageName};

        devShells = {
            default = pkgs.mkShell {
              packages = with pkgs; [
                python3Packages.pytest
                app
                pre-commit
              ];
            };
        };
    });
}
