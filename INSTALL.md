# DRAWING No. MJB-001 — installation notes

Everything here is standard-library Python 3 and GitHub Actions. No packages to install, no API keys, no third-party services.

## What is in this package

```
README.md                          the drawing set (this is your profile README)
build_sheet.py                     draws assets/sheet-dark.svg and sheet-light.svg
code39.py                          hand-written Code 39 barcode encoder used by the sheet
INSTALL.md                         this file
assets/sheet-dark.svg              hero sheet, dark cyanotype
assets/sheet-light.svg             hero sheet, light vellum
assets/testreport-dark.svg         availability and latency strip
assets/testreport-light.svg
assets/signatures-dark.svg         signature margin
assets/signatures-light.svg
assets/data/*.json                 measured data: sheet, report, as-built, guestbook
.github/scripts/testreport.py      real HTTPS checks + rolling history + strip
.github/scripts/asbuilt.py         clones the repos, writes the log + weekly chart
.github/scripts/guestbook.py       reads `sign:` issues, draws the margin
.github/workflows/sheet.yml        every 6 h: report -> as-built -> sheet -> commit
.github/workflows/guestbook.yml    on new issue: redraw signature margin
```

## Push it from a phone (Termux)

```bash
pkg install -y git python unzip
cd ~ && rm -rf bp-deploy bp_x
git clone --branch main https://github.com/Manashjyoti-Bora/Manashjyoti-Bora.git bp-deploy
cd ~/bp-deploy
mkdir -p .mjbos-backup
if [ -f README.md ] && [ ! -f .mjbos-backup/README-drawing-previous.md ]; then cp README.md .mjbos-backup/README-drawing-previous.md; fi
unzip -q -o /sdcard/Download/blueprint-profile-readme.zip -d ~/bp_x
cp -a ~/bp_x/blueprint/. .
python build_sheet.py
git add -A && git commit -m "feat(profile): drawing no. MJB-001"
git push origin main
```

When git asks: username `Manashjyoti-Bora`, password = a classic personal access token with the `repo` scope.

## After the first push

1. Open **Actions** and run **drawing sheet** once manually. It measures the three live sites, rewrites the as-built log and the weekly chart, and redraws the sheet.
2. Run **signature margin** once so `assets/signatures-*.svg` matches the live issue list.
3. Check that `Settings → Actions → Workflow permissions` is set to **Read and write**, otherwise the workflows cannot commit their own output.

## Testing locally without the network

```bash
python build_sheet.py                                  # redraw the hero sheet
REPORT_MOCK=1 python .github/scripts/testreport.py     # strip with mock readings
GUESTBOOK_MOCK=1 python .github/scripts/guestbook.py   # margin with mock signatures
```

`GUESTBOOK_MOCK=1` also rewrites the `SIGN` block in `README.md`; run the real script or `git checkout README.md` afterwards.

## Verifying the barcode is real

The bars in the title block are Code 39, encoded by `code39.py`, and they decode to `MANASHBORA.VERCEL.APP`. `code39.py` contains its own independent `decode()` so you can check the encoder against itself:

```bash
python -c "import code39; print(code39.decode(code39.elements('MANASHBORA.VERCEL.APP')))"
```

Or scan the rendered sheet with any phone barcode app — the barcode sits on a white label in both themes so it scans in dark mode too.
