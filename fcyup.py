#!/usr/bin/python3
import json
from platform import platform
import urllib.request

def get_platform() -> tuple[str, str]:
    import platform
    pl_sys = platform.system()
    pl_arch = platform.machine()
    return pl_sys, pl_arch 

def dload_progress(count, blksize, totsize):
    dloaded = count * blksize
    if totsize > 0:
        percent = (dloaded / totsize) * 100.0
        print(f"Dload progress: {percent}%", end='\r')
    else:
        print(f"Downloaded {dloaded/1024}kB", end='\r')


def move_to_fencydir(file_name: str, subdir: str = "bin"):
    import shutil, os, pathlib, platform 

    src = pathlib.Path(file_name)
    dst_dir = pathlib.Path.home() / ".fency" / subdir
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    short_name = src.name.split('-')[0]
    dst = dst_dir / short_name
    
    shutil.move(src, dst)
    dst.chmod(0o755)  # making it executable 

    system = platform.system()
    if system == "Windows":
        print(f"✅ Almost done; please manually add this program to your PATH: {dst_dir}\\{short_name}")
    else:
        shell_profiles = [".zshrc", ".bashrc", ".profile"]
        profile = None
        for prof in shell_profiles:
            prof_path = pathlib.Path.home() / prof
            if prof_path.exists():
                profile = prof_path
                break
        
        if profile:
            path_line = f'export PATH="{dst_dir}:$PATH"\n'
            if path_line not in profile.read_text():
                profile.write_text(path_line + profile.read_text())
                print(f"✅ Added to profile {profile}")
            print("🔄 Please restart your shell so the changes apply")
        else:
            print(f"Please add this file to your PATH: {short_name}")
    
    return str(dst)

def get_latest_tag(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())
        return data['tag_name']

def download(url: str, fname: str):
    urllib.request.urlretrieve(url, filename=fname, reporthook=dload_progress)
    print(f"\nDownloaded {fname}")

def main():
    os_name, arch = get_platform()
    os_lower = os_name.lower()
    arch_lower = arch.lower()

    if "darwin" in os_lower:
        os_lower = "macos"
    if "arm64" in arch_lower:
        arch_lower = "aarch64"

    # Download and install fencyc
    owner, repo = "The-Fency-Project", "fencyc"
    tag = get_latest_tag(owner, repo)
    print(f"Found fencyc release with tag {tag}")
    fname = f"fencyc-{tag}-{os_lower}-{arch_lower}"
    github_api = f"https://github.com/{owner}/{repo}/releases/download/{tag}"
    download(f"{github_api}/{fname}", fname)
    move_to_fencydir(fname)

    # Download runtime library
    owner, repo = "The-Fency-Project", "runtime"
    tag = get_latest_tag(owner, repo)
    print(f"Found runtime release with tag {tag}")

    ext_map = {
        "linux": ".a",
        "darwin": ".a",
        "macos": ".a",
        "windows": ".lib",
    }
    ext = ext_map.get(os_lower, ".a")  # default to .a if unknown
    runtime_fname = f"libfcyrt-{tag}-{os_lower}-{arch_lower}{ext}"
    github_api = f"https://github.com/{owner}/{repo}/releases/download/{tag}"
    download(f"{github_api}/{runtime_fname}", runtime_fname)
    move_to_fencydir(runtime_fname, subdir="runtime")

    print("\n⚠️ You now need to install 'qbe' yourself via your package manager (apt/pacman/etc) or build from source:")
    print("   https://c9x.me/compile/")

if __name__ == "__main__":
    main()
