with import <nixpkgs> {};
let 
  myPython = python38.withPackages (ps: with ps; [
          pip setuptools
          sphinx nbsphinx
          jupyter
          pydot
          openpyxl
  ]);
  myHaskell = haskellPackages.ghcWithPackages (ps: with ps; [
          pandoc
  ]);
in  
mkShell {
  buildInputs = [ myPython myHaskell graphviz ];
}