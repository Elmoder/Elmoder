#!/usr/bin/env python3
"""Rebrand the base APK to "ALMODER TV".

Applies the name, launcher icon, splash logo and theme (navy + green) changes
to a decompiled apktool project. Run via rebrand.sh, which handles decompile,
build and signing around this step.

Usage:
    python3 rebrand.py <decompiled_project_dir> <logo_png>
"""
import shutil
import sys
import re
from pathlib import Path

from PIL import Image, ImageDraw

APP_NAME = "ALMODER TV"
PKG_PATH = "com/t4w/ostora516"

# Brand palette sampled from the logo (ARGB hex).
NAVY = "#ff0a2540"        # primary
NAVY_DARK = "#ff071b30"   # status/nav bar, primary dark
GREEN = "#ff6dc72a"       # accent / secondary
GREEN_DARK = "#ff57a91f"  # secondary variant

# Density -> (legacy launcher px, adaptive foreground px @108dp)
DENSITIES = {
    "mdpi": (48, 108),
    "hdpi": (72, 162),
    "xhdpi": (96, 216),
    "xxhdpi": (144, 324),
    "xxxhdpi": (192, 432),
}


def patch_strings(res: Path) -> None:
    f = res / "values" / "strings.xml"
    text = f.read_text(encoding="utf-8")
    text = re.sub(
        r'(<string name="app_name">).*?(</string>)',
        rf"\g<1>{APP_NAME}\g<2>",
        text,
    )
    text = re.sub(
        r'(<string name="update_text">).*?(</string>)',
        r"\g<1>يوجد تحديث جديد لتطبيق ALMODER TV\g<2>",
        text,
    )
    f.write_text(text, encoding="utf-8")


def patch_colors(res: Path) -> None:
    f = res / "values" / "colors.xml"
    text = f.read_text(encoding="utf-8")
    replacements = {
        "colorPrimary": NAVY,
        "colorPrimaryDark": NAVY_DARK,
        "colorAccent": GREEN,
        "frame_color": NAVY,
        "text_color": NAVY,
        "teal_200": GREEN,
        "teal_700": NAVY,
        "ic_launcher_background": NAVY,
    }
    for name, value in replacements.items():
        text = re.sub(
            rf'(<color name="{name}">)[^<]*(</color>)',
            rf"\g<1>{value}\g<2>",
            text,
        )
    f.write_text(text, encoding="utf-8")


def patch_theme(res: Path) -> None:
    f = res / "values" / "styles.xml"
    text = f.read_text(encoding="utf-8")
    theme_items = {
        "android:statusBarColor": NAVY_DARK,
        "android:navigationBarColor": NAVY_DARK,
        "colorPrimary": NAVY,
        "colorPrimaryDark": NAVY_DARK,
        "colorPrimaryVariant": NAVY_DARK,
        "colorSecondary": GREEN,
        "colorSecondaryVariant": GREEN_DARK,
    }

    def rewrite(match: re.Match) -> str:
        block = match.group(0)
        for name, value in theme_items.items():
            block = re.sub(
                rf'(<item name="{re.escape(name)}">)[^<]*(</item>)',
                rf"\g<1>{value}\g<2>",
                block,
            )
        return block

    text = re.sub(
        r'<style name="Theme\.MyApplication(\.NoActionBar)?"[^>]*>.*?</style>',
        rewrite,
        text,
        flags=re.DOTALL,
    )
    f.write_text(text, encoding="utf-8")


def _rounded(img: Image.Image, radius_frac: float = 0.18) -> Image.Image:
    w, h = img.size
    r = int(min(w, h) * radius_frac)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out


def _circle(img: Image.Image) -> Image.Image:
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, w - 1, h - 1], fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out


def patch_icons(res: Path, logo_path: Path) -> None:
    src = Image.open(logo_path).convert("RGBA")
    for dens, (launch_sz, fg_sz) in DENSITIES.items():
        d = res / f"mipmap-{dens}"
        d.mkdir(parents=True, exist_ok=True)
        base = src.resize((launch_sz, launch_sz), Image.LANCZOS)
        _rounded(base).save(d / "ic_launcher.webp", "WEBP", quality=95)
        _circle(base).save(d / "ic_launcher_round.webp", "WEBP", quality=95)

        canvas = Image.new("RGBA", (fg_sz, fg_sz), (0, 0, 0, 0))
        inner = int(fg_sz * 0.70)
        logo = src.resize((inner, inner), Image.LANCZOS)
        off = (fg_sz - inner) // 2
        canvas.paste(logo, (off, off), logo)
        canvas.save(d / "ic_launcher_foreground.webp", "WEBP", quality=95)

    # Splash logo used by activity_start.xml
    src.resize((192, 192), Image.LANCZOS).save(res / "drawable" / "logo.png", "PNG")


def remove_info_menu(res: Path) -> None:
    """Drop the "Contact us" / "Website" info submenu from the nav drawer."""
    f = res / "menu" / "activity_main_drawer.xml"
    if not f.is_file():
        return
    text = f.read_text(encoding="utf-8")
    text = re.sub(
        r'\s*<item android:title="@string/menu_title_info">.*?</item>',
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )
    f.write_text(text, encoding="utf-8")


def replace_hardcoded_old_name(project: Path) -> None:
    """Replace baked-in "الأسطورة TV" strings in smali with the new name.

    The home fragment overrides the ActionBar title with a hardcoded old name,
    and MainActivity uses it as an email subject.
    """
    old_a = '"\\u0627\\u0644\\u0623\\u0633\\u0637\\u0648\\u0631\\u0629 TV"'  # "الأسطورة TV"
    old_b = '"TV \\u0627\\u0644\\u0623\\u0633\\u0637\\u0648\\u0631\\u0629"'  # "TV الأسطورة"
    new = '"ALMODER TV"'
    for smali in (project / "smali").rglob("*.smali"):
        text = smali.read_text(encoding="utf-8")
        if old_a in text or old_b in text:
            smali.write_text(
                text.replace(old_a, new).replace(old_b, new), encoding="utf-8"
            )


def disable_startup_popup(project: Path) -> None:
    """Skip the update/announcement popup (custom_dialog_update) shown on open.

    The home fragment shows it when a version-string comparison fails; force the
    branch to always jump to :cond_0 so the popup is never built or shown.
    """
    branch = re.compile(r"^(\s*)if-nez (p\d+|v\d+), :cond_0\s*$")
    for smali in (project / "smali").rglob("*.smali"):
        lines = smali.read_text(encoding="utf-8").splitlines(keepends=True)
        popup = next(
            (i for i, ln in enumerate(lines) if "custom_dialog_update:I" in ln),
            None,
        )
        if popup is None:
            continue
        # Scan upward for the branch that skips the popup block; force it to
        # always jump to :cond_0 so the popup is never built or shown.
        for i in range(popup, -1, -1):
            m = branch.match(lines[i])
            if m:
                lines[i] = f"{m.group(1)}goto :cond_0\n"
                smali.write_text("".join(lines), encoding="utf-8")
                break


def add_welcome_dialog(project: Path) -> None:
    """Add the Welcome dialog class and show it once on MainActivity launch."""
    smali_root = project / "smali" / PKG_PATH
    welcome_src = Path(__file__).parent / "smali" / "Welcome.smali"
    if not smali_root.is_dir() or not welcome_src.is_file():
        return
    shutil.copyfile(welcome_src, smali_root / "Welcome.smali")

    main_activity = smali_root / "MainActivity.smali"
    text = main_activity.read_text(encoding="utf-8")
    call = (
        "    invoke-static {p0}, "
        f"L{PKG_PATH}/Welcome;->show(Landroid/content/Context;)V\n"
    )
    if "Welcome;->show" not in text:
        # Insert right after the first-launch init call inside `if (savedState == null)`.
        anchor = f"invoke-virtual {{p0}}, L{PKG_PATH}/MainActivity;->\u2c57()V\n"
        if anchor in text:
            text = text.replace(anchor, anchor + "\n" + call, 1)
        main_activity.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    project = Path(sys.argv[1])
    logo = Path(sys.argv[2])
    res = project / "res"
    if not res.is_dir():
        sys.exit(f"res/ not found under {project}")

    patch_strings(res)
    patch_colors(res)
    patch_theme(res)
    patch_icons(res, logo)
    remove_info_menu(res)
    replace_hardcoded_old_name(project)
    disable_startup_popup(project)
    add_welcome_dialog(project)
    print(f"Rebranded {project} -> {APP_NAME}")


if __name__ == "__main__":
    main()
