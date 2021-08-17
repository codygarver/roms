# roms.py
Automatically filter video game roms using blacklists and whitelists and (optionally) transfer them.
## How it works
roms.py uses filenames to determine characteristics of roms and whether or not they're desirable.

For example, it automatically blacklists `BIOS`, `Program` and `Beta` files. And it has a Western bias, so it whitelists filenames that include `(U)` or `(USA)` or `En`. 

### Blacklists and Whitelists

These lists are produced in each console subdirectory:
* `blacklist.auto.txt`
* `whitelist.auto.txt`

Lists content can be overridden by entries in `blacklist.custom.txt` and/or `whitelist.custom.txt`.

### Transferring files

Local files will never be deleted _BUT_ using `--destination-dir` will delete remote files _IF_ they're contained in `blacklist.auto.txt`.

## Installation
Download [roms.py](https://raw.githubusercontent.com/codygarver/roms/main/roms.py) and place it in the root of your rom collection (or use the `--base-dir` flag to point to that directory).

## Usage
1. Place your rom files in a directory named after the system. (The directory name is arbitrary but should ideally match the standard name used by your emulator setup in case you want to transfer them. For Sony PlayStation 1 on RetroArch this would be `psx`.)
2. Automatically generate blacklist(s) and whitelist(s):
```
./roms.py --console-dir psx
00:00:00.000 INFO     psx: blacklist generated
00:00:00.000 INFO     psx: whitelist generated
```
3. (Optional) If you wish to override the automatically generated lists, add filenames to `blacklist.custom.txt` or `whitelist.custom.txt` and repeat Step 2. Changes will be reflected in `blacklist.auto.txt` and `whitelist.auto.txt`.
4. (Optional) To copy the whitelisted files (and delete the blacklisted files) to another location, add `--destination-dir` to Step 2.
