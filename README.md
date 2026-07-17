# ALMODER TV — APK Rebrand

Scripts and assets to rebrand the base Android app to **ALMODER TV**, changing the
app name, launcher icon, splash logo and theme colors, then rebuilding and
re-signing the APK.

## What gets changed

| Item        | Before                         | After                                   |
| ----------- | ------------------------------ | --------------------------------------- |
| App name    | الأسطورة TV                     | **ALMODER TV**                          |
| Launcher icon | red adaptive icon            | ALMODER TV logo (all densities + round) |
| Splash logo | `res/drawable/logo.png`        | ALMODER TV logo                         |
| Primary color | red `#bc1115` / `#b71c1c`     | navy `#0A2540` (dark `#071B30`)         |
| Accent color | red                           | green `#6DC72A`                         |

The palette is sampled from `assets/almoder_tv_logo.png` — navy background with a
green accent, chosen for a calm, sporty look.

## Layout

```
assets/almoder_tv_logo.png   Source logo (1920x1920, used for icon + splash)
scripts/rebrand.py           Applies name/color/icon changes to a decoded project
scripts/rebrand.sh           Decode -> patch -> rebuild -> sign pipeline
```

## Requirements

- JDK 17+
- [`apktool`](https://apktool.org/) (`apktool.jar`)
- [`uber-apk-signer`](https://github.com/patrickfav/uber-apk-signer) (`uber-apk-signer.jar`)
- Python 3 with Pillow (`pip install pillow`)

Place the two jars in `tools/` (or point to them with the `APKTOOL` / `SIGNER`
environment variables):

```bash
mkdir -p tools
curl -L -o tools/apktool.jar          https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar
curl -L -o tools/uber-apk-signer.jar  https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar
```

## Usage

```bash
scripts/rebrand.sh path/to/base.apk ALMODER_TV.apk
```

## Notes

- The rebuilt APK is re-signed with a **new key** (a debug keystore by default),
  so it has a different signature than the original. It cannot be installed as an
  update over the original build — uninstall the old app first.
- To sign with your own release key, pass it to `uber-apk-signer` (`--ks`,
  `--ksAlias`, `--ksPass`, `--ksKeyPass`) instead of the embedded debug key.
- The package name is left unchanged (`com.t4w.ostora516`). Changing it would also
  require updating Firebase / Google Services configuration.
