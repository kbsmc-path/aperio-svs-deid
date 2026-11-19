# Aperio SVS De-identification

**A small desktop tool that removes the scan date, scanner IDs and the slide label image from Aperio `.svs`
whole-slide images — in place, without touching the tissue image.**

> **Aperio SVS files only.** Files from other scanners or formats (Hamamatsu `.ndpi`, 3DHISTECH `.mrxs`,
> Philips iSyntax / TIFF, Leica `.scn`, OME-TIFF, DICOM, generic pyramidal TIFF, …) are not supported. The tool
> checks every file and skips anything whose metadata does not start with the `Aperio` banner.

## What it does

Besides the pixels, an Aperio slide carries information that can identify a patient, a specimen or an institution:

| Where | What | This tool |
|---|---|---|
| Metadata text of every page | `Date` | coarsens to `YYYY-MM` (default), or other formats, or removes it |
| | `Time`, `Time Zone` | removes |
| | `ScanScope ID`, `Rack`, `Slide` | removes |
| | any other key you list | removes |
| Label image | photo of the slide label (specimen number, barcode, sometimes patient name) | wipes |
| Macro image | photo of the whole glass slide (may show the label too) | wipes (on by default; untick to keep it) |

Only the metadata is edited, in place. The pyramid image data is never moved or re-encoded, so a 1.6 GB slide is
processed in milliseconds, and the scanner banner and geometry fields that viewers use to recognise the file are
kept (verified with OpenSlide: still read as an Aperio slide, all levels intact). Removed label and macro images are
overwritten with zeros and unlinked from the file, so no viewer can show them again.

## Install and run

Requires **Python 3.8+** with tkinter (included in the python.org installer). No other packages. The program is
distributed as source only — there is no `.exe` download (see [Build your own .exe](#build-your-own-exe-optional)
for why).

**Windows, without git**

1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/).
2. On this page: **Code › Download ZIP**.
3. Right-click the ZIP › **Properties** › at the bottom tick **Unblock** › **OK** — *before* extracting
   (see [If Windows blocks it](#if-windows-blocks-it-smart-app-control)).
4. Extract the ZIP and double-click `run.bat` (or drag a folder onto it). A black console window opens alongside —
   it is the log window; close the main window to exit.

Keep all files in one folder (`svs_meta_gui.py` needs `svs_meta.py` and `i18n.py`). `run.bat` uses `.venv` if
present, otherwise the `python` on PATH or the `py` launcher.

**With git, or on Linux / macOS**

```bat
git clone https://github.com/kbsmc-path/aperio-svs-deid.git
cd aperio-svs-deid
python svs_meta_gui.py
```

If something is missing, the program says what and how to install it
(Linux: `sudo apt install python3-tk`; macOS Homebrew: `brew install python-tk`).

## If Windows blocks it (Smart App Control)

On Windows 11 with **Smart App Control** turned on, files downloaded from the internet are marked, and a marked
`run.bat` is refused with *"Smart App Control blocked …"* / *"Dangerous file extension from the web"*. Unblocking the
ZIP before extracting it (step 3 above) removes the mark from everything inside.

Already extracted without unblocking? Either of these works:

- Right-click `run.bat` › Properties › tick **Unblock** (or in PowerShell in that folder:
  `Get-ChildItem | Unblock-File`), then double-click it as usual.
- Or start it from a command window, which is not blocked: open the extracted folder in Explorer, click the address
  bar, type `cmd` and press Enter, then type `run.bat` and press Enter.

**한국어:** exe 파일은 배포하지 않고 소스로만 제공합니다 (서명되지 않은 exe는 Windows 스마트 앱 컨트롤이 차단합니다).
[python.org](https://www.python.org/downloads/)에서 Python 3.8 이상 설치 → 이 페이지에서 **Code › Download ZIP** →
**압축을 풀기 전에** ZIP 우클릭 › **속성** › **차단 해제** 체크 › **확인** → 압축을 풀고 `run.bat` 더블클릭.
함께 뜨는 검은 창은 기록 창입니다. 이미 압축을 풀었는데 "스마트 앱 컨트롤이 차단했습니다"가 뜨면 `run.bat`
우클릭 › 속성 › 차단 해제 하면 됩니다. 또는 압축을 푼 폴더의 주소 표시줄에 `cmd`를 입력하고 Enter → 열린 창에
`run.bat`을 입력하고 Enter 하면 차단 해제 없이도 실행됩니다.

## How to use

1. **Work on a copy.** Copy the slides to a separate folder first (see *Warnings*).
2. **Folder → Scan.** The table lists every `.svs` with its Date, Time, ScanScope ID and whether it has a label image.
   Non-Aperio or damaged files are shown as `ERROR` and will not be touched.
3. **Choose what to change** (right panel):
   - *Scan date*: `YYYY-MM` (default) · `YYYY-MM-DD` · `YY-MM-DD` · `YYYY` · remove · keep
   - *Also remove*: Time / Time Zone · ScanScope ID / Rack / Slide · label image · macro image · extra keys
   - *Selected files only* and *Back up originals (.bak)* options
4. **Preview.** Shows exactly what would change for each file. Nothing is written.
5. **Apply.** Confirm the dialog. Each file is edited, re-read and reported as *written and verified*.
6. **Check the result.** Scan again, and open a few slides in your viewer before using the files.

The interface starts in English; Korean is available from the toolbar (*Language*). Everything shown in the log pane is also
appended to `svs_deid.log` next to the program.

## ⚠ Warnings — read before use

**Changes are permanent**
- Files are modified **in place**. Removing the label or macro image **cannot be undone**.
- Always run it on a **copy** of your data first and keep the originals somewhere safe until you have checked the
  results. The `.bak` option doubles the disk space needed.

**Aperio SVS only**
- Other formats store their images differently; editing them with this tool could destroy image data. Files
  without the `Aperio` banner are refused, but files *converted* to SVS by other software can carry a copied banner
  — only use slides produced by Aperio scanners / software.
- Tested with Aperio GT450 / GT450 DX slides. Check a few files from other Aperio models before a batch run.

**While it runs**
- Close the slides in ImageScope, QuPath or any other viewer first — open files cannot be written.
- Do not stop the program, unplug a drive or let the PC sleep during **Apply**. An interrupted write can leave a
  file damaged. Prefer local disks over network drives or cloud-synced folders (OneDrive etc.).

**It is not a complete de-identification by itself**
- **File and folder names are not changed.** Rename files whose names contain specimen numbers or patient data.
- If you **untick the macro image**, it stays in the file — it is a photo of the whole glass slide and often shows the
  label. Both label and macro removal are on by default.
- Only the keys listed above are removed. Check the remaining metadata (Preview / Scan) for anything else your
  institution considers identifying.
- The tissue image itself is not inspected (e.g. ink marks or text written on the glass).
- File-system timestamps (created / modified) are not changed by this tool.
- **Leftover copies still hold the original data:** `.bak` backups, and `svs_deid.log`, which records file names and
  the removed values. Delete or secure them before sharing data.

**Your responsibility**
- De-identification requirements depend on your institution, IRB and local law (e.g. HIPAA, GDPR, PIPA). Verify the
  output yourself before sharing any data. This software is provided **"as is", without warranty of any kind** (see
  [LICENSE](LICENSE)).

## Build your own .exe (optional)

No `.exe` is published: it would not be code-signed, and Windows Smart App Control blocks unsigned executables it does not know
(whether built as console or windowed) with no way for the user to allow them. For PCs where Smart App Control is
off, you can build one yourself:

```bat
python -m pip install pyinstaller
python build_exe.py            :: -> exe\SVS_Deid.exe
```

## License

[MIT](LICENSE)
