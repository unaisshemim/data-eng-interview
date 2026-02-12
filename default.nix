let
   pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/cf8cc1201be8bc71b7cbbbdaf349b22f4f99c7ae.tar.gz") {};
    stdenv = pkgs.stdenv;
in pkgs.mkShell rec {
    name = "interview";
    shellHook = ''
        source .bashrc
        playwright install  firefox


    '';
    buildInputs = (with pkgs; [
        bashInteractive

        (pkgs.python3.buildEnv.override {
            ignoreCollisions = true;
            extraLibs = with pkgs.python3.pkgs; [
                # package list: https://search.nixos.org/packages
                # be parsimonious with 3rd party dependencies; better to show off your own code than someone else's
                ipython
                nose
                requests
                psutil
                aiohttp
                beautifulsoup4
                playwright
            ];
        })
    ]);
}
