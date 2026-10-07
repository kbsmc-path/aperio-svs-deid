"""
Korean / English strings for both tools.

One program, two languages — rather than two copies of each program that drift apart.
The GUI rebuilds itself when the language changes (all state lives on the App object,
not in the widgets), so no per-widget bookkeeping is needed.

    import i18n
    from i18n import t
    i18n.set_lang("en")
    t("move_sel")                      -> "Move selected (Enter)"
    t("sel_count", n=3, total=628)     -> "3 selected of 628"
"""

LANGS = [("English", "en"), ("한국어", "ko")]
DEFAULT = "en"                  # language the program starts in
_lang = DEFAULT


def set_lang(code):
    global _lang
    _lang = code if code in STRINGS else DEFAULT


def get_lang():
    return _lang


def lang_label(code=None):
    code = code or _lang
    for label, c in LANGS:
        if c == code:
            return label
    return LANGS[0][0]


def code_for(label):
    for lb, c in LANGS:
        if lb == label:
            return c
    return DEFAULT


def t(key, **kw):
    s = STRINGS.get(_lang, {}).get(key)
    if s is None:
        s = STRINGS[DEFAULT].get(key, key)
    return s.format(**kw) if kw else s


STRINGS = {
# =============================================================== 한국어
"ko": {
    # ---- shared ----
    "language": "언어",
    "browse": "찾아보기...",
    "cancel": "취소",
    "close_confirm_title": "종료 확인",
    "none": "없음",
    "yes_have": "있음",

    # ---- wsi_review: toolbar ----
    "app_title": "WSI 썸네일 리뷰",
    "src_folder": "원본 폴더",
    "dst_folder": "이동 폴더",
    "rescan": "다시 스캔 (F5)",
    "move_sel": "선택 파일 이동 (Enter)",
    "undo_btn": "이동 취소 (Ctrl+Z)",
    "group_btn": "그룹 지정 (G)",
    "sort": "정렬",
    "size": "크기",
    "find_name": "파일명 찾기",
    "clear": "지우기",
    "adjust_title": "보기 보정 (화면에만 적용, 파일은 그대로)",
    "saturation": "채도",
    "gamma": "감마",
    "gamma_hint": "(낮추면 진해짐)",
    "reset": "원래대로",
    "faint_preset": "연한 슬라이드용",
    "zoom_reset": "줌 초기화 (0)",
    "unpin": "고정 해제",
    "pick_slide": "(슬라이드를 선택하세요)",
    "pin_none": "고정 슬라이드: 없음 (P 키로 고정)",
    "pin_on": "고정: {name}{hidden}   (위쪽과 같은 배율)",
    "pin_hidden": "  [필터에 가려짐]",
    "zoom_pct": "   [줌 {pct:.0f}%]",

    # ---- sorts ----
    "sort_name": "이름",
    "sort_name_desc": "이름 역순",
    "sort_mtime_asc": "수정일 (오래된 순)",
    "sort_mtime_desc": "수정일 (최신 순)",
    "sort_size_asc": "크기 (작은 순)",
    "sort_size_desc": "크기 (큰 순)",

    # ---- wsi_review: status ----
    "pick_src": "원본 폴더를 선택하세요. [찾아보기...] 버튼을 누르거나 경로를 직접 입력하고 F5.",
    "folder_missing": "폴더를 찾을 수 없습니다: {path}",
    "folder_missing_title": "폴더 없음",
    "folder_missing_msg": "원본 폴더를 찾을 수 없습니다:\n{path}",
    "scanning": "{n}개 파일 발견. 썸네일 읽는 중...",
    "plan": "캐시된 썸네일 {cached}개, 새로 읽을 것 {missing}개 ...",
    "loading": "썸네일 읽는 중... {done}/{total}",
    "ready": "{n}개 준비 완료 ({sec:.1f}초, 캐시 {cached}개 / 새로 읽음 {fresh}개",
    "ready_err": ", 오류 {errs}개)",
    "ready_hint": "   Ctrl+클릭/Space=선택  Enter=이동  P=고정  Ctrl+Z=취소",
    "shown": "{shown} / {total}개 표시",
    "hidden_n": " ({n}개 숨김)",
    "sel_count": "{n}개 선택 / 전체 {total}개",
    "sel_hidden": "  (그 중 {n}개는 현재 필터에 가려져 있지만 이동 대상에 포함됩니다)",
    "sel_hint": "   Enter = 선택 파일 이동",
    "size_status": "썸네일 크기: {name} ({px}px), 한 줄에 {cols}개",
    "busy": "이전 작업이 끝날 때까지 기다려 주세요.",
    "no_pin": "고정된 슬라이드가 없습니다.",
    "unpinned": "고정 해제: {name}",

    # ---- wsi_review: move ----
    "nothing_selected": "선택된 파일이 없습니다 (Ctrl+클릭 또는 Space로 선택).",
    "set_dst_first": "이동 폴더를 먼저 지정하세요.",
    "same_folder": "이동 폴더가 원본 폴더와 같습니다.",
    "error": "오류",
    "diff_drive_title": "다른 드라이브",
    "diff_drive_msg": "원본과 이동 폴더가 서로 다른 드라이브입니다. 파일이 복사된 뒤 삭제되므로 "
                      "수 GB 슬라이드는 매우 느립니다.\n\n계속할까요?",
    "moving": "{n}개 이동 중 → {dst}",
    "move_failed": "이동 실패",
    "moved": "{n}개 이동 완료. {left}개 남음.  (Ctrl+Z로 되돌리기)",
    "close_busy_move": "파일 이동이 진행 중입니다. 정말 종료하시겠습니까?",
    "nothing_undo": "되돌릴 작업이 없습니다.",
    "undoing": "{what} 되돌리는 중... {n}개",
    "undo_move": "이동",
    "undo_rename": "이름 변경",
    "undo_failed": "되돌리기 실패",
    "undo_done": "되돌리기 완료: {n}개",

    # ---- wsi_review: group rename ----
    "group_pick_first": "그룹으로 묶을 파일을 먼저 선택하세요 (Ctrl+클릭 또는 Space).",
    "name_format_title": "이름 형식",
    "name_format_msg": "쉼표로 구분된 블록 항목이 없어 그룹을 지정할 수 없습니다:\n\n{names}",
    "renaming": "이름 변경 중... {n}개",
    "rename_failed": "이름 변경 실패",
    "rename_exists": "{name}: 같은 이름의 파일이 이미 있습니다",
    "rename_done": "{n}개 이름 변경 완료 (선택 해제됨). 이름순으로 정렬하면 같은 그룹끼리 "
                   "붙어서 보입니다.  (Ctrl+Z로 되돌리기)",
    "dlg_group_title": "그룹 지정 - 정렬이 맞는 슬라이드 묶기",
    "dlg_group_info": "정렬이 맞는 H&E와 면역염색 슬라이드를 하나의 블록 그룹으로 묶습니다.\n"
                      "블록 항목 뒤에 표시가 붙어서, 이름순으로 정렬하면 그 쌍이 붙어서 보입니다.",
    "dlg_suffix": "블록 뒤에 붙일 표시:",
    "dlg_suffix_hint": "(비우면 그룹 표시를 제거합니다)",
    "dlg_apply": "이름 변경",
    "dlg_no_change": "(변경 없음)",
    "dlg_exists": "[같은 이름이 이미 있음]",
    "dlg_no_block": "블록 항목이 없어 변경 불가",
    "dlg_clearing": "\n표시를 비웠으므로 기존 그룹 표시가 제거됩니다.\n",

    # ---- svs_deid ----
    "deid_title": "SVS 메타데이터 비식별 도구",
    "folder": "폴더",
    "scan": "스캔 (F5)",
    "col_file": "파일",
    "col_label": "Label",
    "col_pages": "Pages",
    "col_result": "결과",
    "box_date": "검사 날짜 (Date)",
    "box_remove": "함께 제거할 항목",
    "box_extra": "추가 삭제 항목 (쉼표 구분)",
    "box_run": "실행",
    "date_ym": "YYYY-MM  (일자 삭제, 권장)",
    "date_ymd": "YYYY-MM-DD",
    "date_yymd": "YY-MM-DD",
    "date_y": "YYYY  (연도만)",
    "date_drop": "Date 항목 삭제",
    "date_keep": "변경 안 함",
    "sample_drop": "예: {s}  ->  (항목 삭제)",
    "sample_fmt": "예: {s}  ->  {out}",
    "sample_keep": "예: {s}  ->  {s} (그대로)",
    "rm_time": "Time, Time Zone (스캔 시각)",
    "rm_ids": "ScanScope ID, Rack, Slide (장비/위치)",
    "rm_label": "Label 이미지 (검체번호 인쇄됨)",
    "rm_macro": "Macro 이미지 (유리슬라이드 사진)",
    "backup": "원본 .bak 백업 (디스크 2배 필요)",
    "sel_only": "선택한 파일만 처리",
    "preview_btn": "미리보기 (변경 없음)",
    "apply_btn": "적용 (파일 수정)",
    "log": "로그",
    "deid_start_hint": "폴더를 선택하고 [스캔]을 누르세요.",
    "deid_no_folder": "폴더를 찾을 수 없습니다:\n{path}",
    "deid_scan_head": "=== 스캔: {path}  ({n} 파일) ===",
    "deid_scan_done": "스캔 완료: {n} 파일, Label 이미지 보유 {label}",
    "deid_scan_status": "{n} 파일 스캔 완료 (Label 이미지 보유: {label})",
    "deid_no_files": "처리할 파일이 없습니다.",
    "deid_pick_items": "변경할 항목을 선택하세요.",
    "deid_notice": "알림",
    "deid_confirm_title": "적용 확인",
    "deid_confirm_head": "{n}개 파일을 수정합니다. 되돌릴 수 없습니다.\n",
    "deid_confirm_date": "  Date  : {v}",
    "deid_confirm_remove": "  삭제  : {v}",
    "deid_confirm_label": "  Label 이미지 삭제 (픽셀 0으로 덮어씀)",
    "deid_confirm_macro": "  Macro 이미지 삭제 (픽셀 0으로 덮어씀)",
    "deid_confirm_backup": "  백업  : {v}",
    "deid_backup_on": "생성함",
    "deid_backup_off": "생성 안 함",
    "deid_run_head": "=== {mode}: {n} 파일 ===",
    "deid_mode_apply": "적용",
    "deid_mode_preview": "미리보기 (변경 없음)",
    "deid_opt_date": "    검사 날짜 : {v}",
    "deid_opt_remove": "    삭제 항목 : {v}",
    "deid_opt_images": "    Label 이미지 : {label}    Macro 이미지 : {macro}",
    "deid_opt_backup": "    백업 : {v}",
    "deid_removed": "제거",
    "deid_kept": "유지",
    "deid_none": "(없음)",
    "deid_done": "{mode} 완료: {n}개 변경",
    "deid_done_fail": ", {n}개 실패",
    "deid_done_dry": " (아직 파일은 수정되지 않았습니다)",
    "deid_recheck_fail": "재확인 실패: {e}",
    "deid_complete": "완료",
    "deid_close_busy": "작업이 진행 중입니다. 정말 종료하시겠습니까?",
    "deid_no_desc": "ImageDescription 없음",
    "deid_row_nochange": "변경 없음",
    "deid_mode_apply_s": "적용",
    "deid_mode_preview_s": "미리보기",
    "con_start_time": "시작 시각: {v}",
    "con_start_folder": "시작 폴더: {v}",
    "con_no_folder": "폴더가 지정되지 않았습니다. 창에서 [찾아보기...]로 폴더를 선택하세요.",
    "con_unexpected": "!! 예기치 않은 오류가 발생했습니다:",
    "con_report": "이 내용을 복사해서 알려주시면 원인을 찾을 수 있습니다.",
    "con_press_enter": "Enter 키를 누르면 창이 닫힙니다...",
    "con_quit": "프로그램을 종료합니다. 기록은 다음 파일에 저장되었습니다:",
},

# =============================================================== English
"en": {
    # ---- shared ----
    "language": "Language",
    "browse": "Browse...",
    "cancel": "Cancel",
    "close_confirm_title": "Confirm exit",
    "none": "no",
    "yes_have": "yes",

    # ---- wsi_review: toolbar ----
    "app_title": "WSI Thumbnail Review",
    "src_folder": "Source",
    "dst_folder": "Move to",
    "rescan": "Rescan (F5)",
    "move_sel": "Move selected (Enter)",
    "undo_btn": "Undo (Ctrl+Z)",
    "group_btn": "Group (G)",
    "sort": "Sort",
    "size": "Size",
    "find_name": "Find by name",
    "clear": "Clear",
    "adjust_title": "Display correction (view only — files are never changed)",
    "saturation": "Saturation",
    "gamma": "Gamma",
    "gamma_hint": "(lower = darker)",
    "reset": "Reset",
    "faint_preset": "Faint slides",
    "zoom_reset": "Reset zoom (0)",
    "unpin": "Unpin",
    "pick_slide": "(select a slide)",
    "pin_none": "Pinned reference: none (press P)",
    "pin_on": "Pinned: {name}{hidden}   (same zoom as above)",
    "pin_hidden": "  [hidden by filter]",
    "zoom_pct": "   [zoom {pct:.0f}%]",

    # ---- sorts ----
    "sort_name": "Name",
    "sort_name_desc": "Name (Z→A)",
    "sort_mtime_asc": "Modified (oldest)",
    "sort_mtime_desc": "Modified (newest)",
    "sort_size_asc": "Size (smallest)",
    "sort_size_desc": "Size (largest)",

    # ---- wsi_review: status ----
    "pick_src": "Choose a source folder — click [Browse...] or type a path and press F5.",
    "folder_missing": "Folder not found: {path}",
    "folder_missing_title": "Folder not found",
    "folder_missing_msg": "Source folder not found:\n{path}",
    "scanning": "{n} files found. Reading thumbnails...",
    "plan": "{cached} thumbnails cached, {missing} to extract ...",
    "loading": "Reading thumbnails... {done}/{total}",
    "ready": "{n} slides ready in {sec:.1f}s ({cached} from cache, {fresh} newly extracted",
    "ready_err": ", {errs} errors)",
    "ready_hint": "   Ctrl+Click/Space=select  Enter=move  P=pin  Ctrl+Z=undo",
    "shown": "showing {shown} / {total}",
    "hidden_n": " ({n} hidden)",
    "sel_count": "{n} selected of {total}",
    "sel_hidden": "  ({n} of them are hidden by the filter but will still be moved)",
    "sel_hint": "   Enter = move selected",
    "size_status": "Thumbnail size: {name} ({px}px), {cols} per row",
    "busy": "Please wait for the previous operation to finish.",
    "no_pin": "No slide is pinned.",
    "unpinned": "Unpinned: {name}",

    # ---- wsi_review: move ----
    "nothing_selected": "Nothing selected (Ctrl+Click or Space to select).",
    "set_dst_first": "Set a 'Move to' folder first.",
    "same_folder": "The target folder is the same as the source folder.",
    "error": "Error",
    "diff_drive_title": "Different drive",
    "diff_drive_msg": "Source and target are on different drives, so files will be copied and "
                      "then deleted — very slow for multi-GB slides.\n\nContinue?",
    "moving": "Moving {n} file(s) → {dst}",
    "move_failed": "Move failed",
    "moved": "Moved {n} file(s). {left} remaining.  (Ctrl+Z to undo)",
    "close_busy_move": "A file move is still running. Exit anyway?",
    "nothing_undo": "Nothing to undo.",
    "undoing": "Undoing {what}... {n} file(s)",
    "undo_move": "move",
    "undo_rename": "rename",
    "undo_failed": "Undo failed",
    "undo_done": "Undo complete: {n} file(s)",

    # ---- wsi_review: group rename ----
    "group_pick_first": "Select the files to group first (Ctrl+Click or Space).",
    "name_format_title": "Filename format",
    "name_format_msg": "These names have no comma-separated block field, so they cannot be "
                       "grouped:\n\n{names}",
    "renaming": "Renaming {n} file(s)...",
    "rename_failed": "Rename failed",
    "rename_exists": "{name}: a file with that name already exists",
    "rename_done": "Renamed {n} file(s) (selection cleared). Sort by name and each group stays "
                   "together.  (Ctrl+Z to undo)",
    "dlg_group_title": "Group — tie matching slides together",
    "dlg_group_info": "Ties an H&E slide to the IHC section it actually lines up with.\n"
                      "A tag is added to the block field, so sorting by name keeps the pair "
                      "side by side.",
    "dlg_suffix": "Tag to append to the block:",
    "dlg_suffix_hint": "(leave empty to remove the tag)",
    "dlg_apply": "Rename",
    "dlg_no_change": "(no change)",
    "dlg_exists": "[name already taken]",
    "dlg_no_block": "no block field — cannot rename",
    "dlg_clearing": "\nThe tag is empty, so existing group tags will be removed.\n",

    # ---- svs_deid ----
    "deid_title": "SVS Metadata De-identification",
    "folder": "Folder",
    "scan": "Scan (F5)",
    "col_file": "File",
    "col_label": "Label",
    "col_pages": "Pages",
    "col_result": "Result",
    "box_date": "Scan date (Date)",
    "box_remove": "Also remove",
    "box_extra": "Extra keys to delete (comma separated)",
    "box_run": "Run",
    "date_ym": "YYYY-MM  (drop the day, recommended)",
    "date_ymd": "YYYY-MM-DD",
    "date_yymd": "YY-MM-DD",
    "date_y": "YYYY  (year only)",
    "date_drop": "Delete the Date key",
    "date_keep": "Leave unchanged",
    "sample_drop": "e.g. {s}  ->  (key removed)",
    "sample_fmt": "e.g. {s}  ->  {out}",
    "sample_keep": "e.g. {s}  ->  {s} (unchanged)",
    "rm_time": "Time, Time Zone (scan time)",
    "rm_ids": "ScanScope ID, Rack, Slide (scanner / position)",
    "rm_label": "Label image (specimen ID is printed on it)",
    "rm_macro": "Macro image (photo of the whole glass slide)",
    "backup": "Back up originals as .bak (needs 2x disk)",
    "sel_only": "Only the selected files",
    "preview_btn": "Preview (no changes)",
    "apply_btn": "Apply (write to files)",
    "log": "Log",
    "deid_start_hint": "Choose a folder and press [Scan].",
    "deid_no_folder": "Folder not found:\n{path}",
    "deid_scan_head": "=== Scan: {path}  ({n} files) ===",
    "deid_scan_done": "Scan complete: {n} files, {label} with a label image",
    "deid_scan_status": "{n} files scanned ({label} carry a label image)",
    "deid_no_files": "No files to process.",
    "deid_pick_items": "Choose at least one thing to change.",
    "deid_notice": "Notice",
    "deid_confirm_title": "Confirm apply",
    "deid_confirm_head": "{n} file(s) will be modified. This cannot be undone.\n",
    "deid_confirm_date": "  Date   : {v}",
    "deid_confirm_remove": "  Remove : {v}",
    "deid_confirm_label": "  Delete the label image (pixels overwritten with zeros)",
    "deid_confirm_macro": "  Delete the macro image (pixels overwritten with zeros)",
    "deid_confirm_backup": "  Backup : {v}",
    "deid_backup_on": "yes",
    "deid_backup_off": "no",
    "deid_run_head": "=== {mode}: {n} files ===",
    "deid_mode_apply": "Apply",
    "deid_mode_preview": "Preview (no changes)",
    "deid_opt_date": "    Scan date : {v}",
    "deid_opt_remove": "    Removing  : {v}",
    "deid_opt_images": "    Label image : {label}    Macro image : {macro}",
    "deid_opt_backup": "    Backup : {v}",
    "deid_removed": "remove",
    "deid_kept": "keep",
    "deid_none": "(none)",
    "deid_done": "{mode} complete: {n} file(s) changed",
    "deid_done_fail": ", {n} failed",
    "deid_done_dry": " (no files have been modified yet)",
    "deid_recheck_fail": "re-read failed: {e}",
    "deid_complete": "done",
    "deid_close_busy": "An operation is still running. Exit anyway?",
    "deid_no_desc": "no ImageDescription",
    "deid_row_nochange": "no change",
    "deid_mode_apply_s": "Apply",
    "deid_mode_preview_s": "Preview",
    "con_start_time": "Started: {v}",
    "con_start_folder": "Start folder: {v}",
    "con_no_folder": "No folder given. Use [Browse...] in the window to pick one.",
    "con_unexpected": "!! An unexpected error occurred:",
    "con_report": "Copy this text and send it along so the cause can be found.",
    "con_press_enter": "Press Enter to close this window...",
    "con_quit": "Closing. The log has been saved to:",
},
}
