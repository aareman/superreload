{ pkgs, lib, config, inputs, ... }:

{
  name = "superreload";

  languages.python = {
    enable = true;
    venv.enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  packages = with pkgs; [
    git
    curl
    jq
  ];

  scripts.test.exec = ''
    pytest "$@"
  '';

  scripts.lint.exec = ''
    ruff check src tests
  '';

  scripts.fmt.exec = ''
    ruff format src tests
  '';

  scripts.typecheck.exec = ''
    mypy src
  '';

  enterShell = ''
    echo ""
    echo "🔥 superreload development environment"
    echo "   Python: $(python --version 2>&1)"
    echo "   uv: $(uv --version 2>&1)"
    echo ""
    echo "   Commands: test, lint, fmt, typecheck"
    echo ""
  '';

  enterTest = ''
    echo "Running superreload tests"
    pytest
  '';

  git-hooks.hooks = {
    ruff.enable = true;
    ruff-format.enable = true;
  };

  devcontainer.enable = true;
  devcontainer.settings = {
    image = "ghcr.io/cachix/devenv:latest";
    overrideCommand = false;
    updateContentCommand = "devenv test";
    customizations = {
      vscode = {
        extensions = [
          "ms-python.python"
          "ms-python.vscode-pylance"
          "charliermarsh.ruff"
          "tamasfe.even-better-toml"
          "jnoortheen.nix-ide"
        ];
        settings = {
          "python.analysis.typeCheckingMode" = "basic";
          "editor.formatOnSave" = true;
          "[python]" = {
            "editor.defaultFormatter" = "charliermarsh.ruff";
          };
        };
      };
    };
  };
}
