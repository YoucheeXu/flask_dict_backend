import shutil
import subprocess
from pathlib import Path


def rm_dir(p: Path):
    if p.exists():
        print(f"[clean] removing {p}")
        shutil.rmtree(p)

def main():
    rm_dir(Path("build"))
    rm_dir(Path("dist"))
    # 调用 pyinstaller
    _ = subprocess.run(["pyinstaller", "server.spec"], check=True)
    rm_dir(Path("build"))
    rm_dir(Path("dist"))

if __name__ == "__main__":
    main()
