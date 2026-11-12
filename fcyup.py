#!/usr/bin/python3
"""Install the Fency compiler, standard library, and runtime."""
import json
import os
import pathlib
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

FENCY_DIR = pathlib.Path.home() / ".fency"


def get_platform() -> tuple[str, str]:
    system = platform.system().lower()
    arch = platform.machine().lower()
    if system == "darwin":
        system = "macos"
    if system in {"windows", "win32"}:
        system = "windows"
    if arch in {"amd64", "x86-64"}:
        arch = "x86_64"
    elif arch in {"arm64", "aarch64"}:
        arch = "aarch64"
    return system, arch


def dload_progress(count, blksize, totsize):
    dloaded = count * blksize
    if totsize > 0:
        print(f"Dload progress: {(dloaded / totsize) * 100.0:.1f}%", end="\r")
    else:
        print(f"Downloaded {dloaded / 1024:.0f}kB", end="\r")


def get_latest_tag(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    request = urllib.request.Request(url, headers={"User-Agent": "fcyup"})
    with urllib.request.urlopen(request) as resp:
        return json.loads(resp.read().decode())["tag_name"]


def download(url: str, fname: pathlib.Path):
    urllib.request.urlretrieve(url, filename=str(fname), reporthook=dload_progress)
    print(f"\nDownloaded {fname.name}")


def add_bin_to_path(bin_dir: pathlib.Path):
    if platform.system() == "Windows":
        print(f"Please add this directory to PATH: {bin_dir}")
        return
    for name in (".zshrc", ".bashrc", ".profile"):
        profile = pathlib.Path.home() / name
        if profile.exists():
            path_line = f'export PATH="{bin_dir}:$PATH"\n'
            text = profile.read_text()
            if path_line not in text:
                profile.write_text(path_line + text)
                print(f"Added {bin_dir} to {profile}")
            print("Restart your shell so the PATH change applies")
            return
    print(f"Please add this directory to PATH: {bin_dir}")


def install_fencyc(downloaded: pathlib.Path) -> pathlib.Path:
    destination = FENCY_DIR / "bin" / "fencyc"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(downloaded), str(destination))
    if platform.system() != "Windows":
        destination.chmod(0o755)
    add_bin_to_path(destination.parent)
    return destination


def install_runtime(downloaded: pathlib.Path, os_name: str, arch: str, extension: str) -> pathlib.Path:
    destination = FENCY_DIR / "runtime" / f"{os_name}-{arch}" / f"libfcyrt{extension}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    shutil.move(str(downloaded), str(destination))
    return destination


def install_stdlib(fencyc: pathlib.Path, tag: str):
    """Build the std metadata with the just-installed compiler.

    Keeping this step source based means the metadata and object archive always
    match the compiler release that installed them.
    """
    archive_name = f"fencyc-{tag}.tar.gz"
    with tempfile.TemporaryDirectory(prefix="fcyup-std-") as temporary:
        archive = pathlib.Path(temporary) / archive_name
        url = f"https://github.com/The-Fency-Project/fencyc/archive/refs/tags/{tag}.tar.gz"
        download(url, archive)
        with tarfile.open(archive, "r:gz") as tar:
            members = [m for m in tar.getmembers() if "/std/" in f"/{m.name}/" or m.name.endswith("/std")]
            if not members:
                raise RuntimeError("compiler release does not contain stdlib sources")
            tar.extractall(temporary, members=members)
        source_root = next(path for path in pathlib.Path(temporary).iterdir() if path.is_dir() and (path / "std").is_dir()) / "std"
        build_root = pathlib.Path(temporary) / "stdlib-build"
        shutil.copytree(source_root, build_root)
        env = os.environ.copy()
        env["PATH"] = str(fencyc.parent) + os.pathsep + env.get("PATH", "")
        subprocess.run([str(fencyc), "build"], cwd=build_root, env=env, check=True)

        metadata = build_root / "std.fmeta"
        objects = build_root / "std.fmeta.objects"
        if not metadata.is_file() or not objects.is_dir():
            raise RuntimeError("stdlib build did not produce std.fmeta and std.fmeta.objects")
        destination = FENCY_DIR / "libs" / "std"
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(metadata, destination / metadata.name)
        installed_objects = destination / objects.name
        if installed_objects.exists():
            shutil.rmtree(installed_objects)
        shutil.copytree(objects, installed_objects)
        source_destination = destination / "src"
        if source_destination.exists():
            shutil.rmtree(source_destination)
        shutil.copytree(source_root, source_destination)


def main():
    os_name, arch = get_platform()
    github = "https://github.com/The-Fency-Project"

    compiler_tag = get_latest_tag("The-Fency-Project", "fencyc")
    print(f"Found fencyc release with tag {compiler_tag}")
    compiler_name = f"fencyc-{compiler_tag}-{os_name}-{arch}"
    compiler_download = pathlib.Path(compiler_name)
    download(f"{github}/fencyc/releases/download/{compiler_tag}/{compiler_name}", compiler_download)
    fencyc = install_fencyc(compiler_download)

    runtime_tag = get_latest_tag("The-Fency-Project", "runtime")
    print(f"Found runtime release with tag {runtime_tag}")
    extension = ".lib" if os_name == "windows" else ".a"
    runtime_name = f"libfcyrt-{runtime_tag}-{os_name}-{arch}{extension}"
    runtime_download = pathlib.Path(runtime_name)
    download(f"{github}/runtime/releases/download/{runtime_tag}/{runtime_name}", runtime_download)
    runtime = install_runtime(runtime_download, os_name, arch, extension)

    print("Building the standard library")
    install_stdlib(fencyc, compiler_tag)
    print(f"Installed runtime at {runtime}")
    print(f"Installed stdlib at {FENCY_DIR / 'libs' / 'std'}")
    print("\nYou still need qbe (apt/pacman/homebrew or https://c9x.me/compile/).")


if __name__ == "__main__":
    main()
