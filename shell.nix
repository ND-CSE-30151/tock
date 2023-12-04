with import <nixpkgs> {};
let 
  myPython = python310.withPackages (ps: with ps; [
          pip setuptools twine
          mypy
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