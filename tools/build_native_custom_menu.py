"""Build experimental ASI and run OFFLINE tests. Never starts or installs the game."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    compiler = ROOT / "tmp/native-menu-toolchain/tcc/tcc.exe"
    if not compiler.is_file():
        raise SystemExit("TinyCC x86 is required locally; see native-custom-menu/README.md")
    output = ROOT / "build/HD2.CustomMenu.experimental.asi"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(compiler), "-shared", "-o", str(output),
                    str(ROOT / "native-custom-menu/CustomMenu.c"),
                    str(ROOT / "native-custom-menu/Hooks.S")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tests/test_native_custom_menu.py")], check=True)
    print("Experimental build only. NOT installed. GUI validation pending.")


if __name__ == "__main__":
    main()
