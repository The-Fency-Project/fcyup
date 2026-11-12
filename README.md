# The Fency programming language toolchain installation script  
This script installs (or updates) fencyc, the matching compiled standard
library, and the platform runtime. The resulting layout is:

```text
~/.fency/
  bin/fencyc
  libs/std/std.fmeta
  libs/std/std.fmeta.objects/
  runtime/<os>-<arch>/libfcyrt.a
```

The standard library is built from the sources in the matching fencyc release,
so its metadata and objects use the same compiler version.  
Just run it with python as normally, e.g. `python3 fcyup.py`  
## Faster installation way 
```sh
curl --proto '=https' --tlsv1.2 -sSL https://raw.githubusercontent.com/The-Fency-Project/fcyup/refs/heads/main/fcyup.py | python3 -
```
