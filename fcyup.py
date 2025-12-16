
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


def move_to_fencydir(file_name: str):
    import shutil, os, pathlib, platform 

    src = pathlib.Path(file_name)
    dst_dir = pathlib.Path.home() / ".fency" / "bin"
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    short_name = src.name.split('-')[0]
    dst = dst_dir / short_name
    
    shutil.move(src, dst)
    dst.chmod(0o755)  # making it executable 

    system = platform.system()
    if system == "windows":
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
    os, arch = get_platform()
    if "darwin" in os.lower():
        os = "macos"
    if "arm64" in arch.lower():
        arch = "aarch64"

    # dloading voxvm
    owner, repo = "Freemorger", "voxvm"
    tag = get_latest_tag(owner, repo)
    print(f"Found voxvm release with tag {tag}")
    fname = f"voxvm-{tag}-{os.lower()}-{arch.lower()}"
    github_api = f"https://github.com/{owner}/{repo}/releases/download/{tag}"
    download(f"{github_api}/{fname}", fname)
    move_to_fencydir(fname)

    # dloading fencyc 
    owner, repo = "The-Fency-Project", "fencyc"
    tag = get_latest_tag(owner, repo)
    print(f"Found fencyc release with tag {tag}")
    fname = f"fencyc-{tag}-{os.lower()}-{arch.lower()}"
    github_api = f"https://github.com/{owner}/{repo}/releases/download/{tag}"
    download(f"{github_api}/{fname}", fname)
    move_to_fencydir(fname)
    

if __name__ == "__main__":
    main()

