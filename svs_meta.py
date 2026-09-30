"""
Engine of the SVS de-identification GUI (svs_meta_gui.py): read and edit Aperio SVS metadata
(scan date, time, scanner ID, ...) in place, without rewriting the slide.

Aperio stores its metadata as a single text string in the TIFF ImageDescription tag (270) of
*every* page, e.g.

    Aperio Leica Biosystems GT450 DX v1.0.1
    92908x44891 [0,0,92908x44891] (256x256) JPEG/YCC Q=91|AppMag = 40|Date = 04/12/2023|
    Time = 08:01:26|Time Zone = GMT+0900|ScanScope ID = SS00000|MPP = 0.263526|...

Only that string is touched here: pixel data, tile offsets and the pyramid structure are never
moved, so editing a 1.6 GB slide takes milliseconds. The first line (scanner banner) and the
geometry/format part before the first "|" are always preserved, because OpenSlide / ImageScope
parse them to recognise the file.

The slide label / macro images live in their own TIFF pages. They can be removed too: their
pixel bytes are overwritten with zeros and the page is unlinked from the TIFF page chain, so
no viewer can show them again. The file keeps its size (the freed bytes are simply unused).

Aperio SVS only. Files whose first ImageDescription does not start with "Aperio" are refused:
other TIFF-based formats use NewSubfileType = 1 for pyramid levels, which would be taken for a
label page here and wiped.
"""
import os
import shutil
import struct
from datetime import datetime

EXTS = (".svs",)
NOT_APERIO = "not an Aperio SVS file (ImageDescription does not start with 'Aperio') - skipped"
TAG_IMAGEDESCRIPTION = 270
TAG_NEWSUBFILETYPE = 254
TAG_STRIPOFFSETS = 273
TAG_STRIPBYTECOUNTS = 279
TAG_TILEOFFSETS = 324
TAG_TILEBYTECOUNTS = 325
TYPE_ASCII = 2
DEFAULT_IN_FORMATS = ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d/%m/%Y")

# TIFF field types -> (byte size, struct code); only the ones that appear in SVS files
TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 16: 8, 17: 8, 18: 8}
TYPE_FMT = {1: "B", 3: "H", 4: "I", 6: "b", 8: "h", 9: "i", 11: "f", 12: "d", 16: "Q", 17: "q", 18: "Q"}

# de-identification preset
DEID_DATE_FORMAT = "%Y-%m"
DEID_REMOVE_TIME = ["Time", "Time Zone"]
DEID_REMOVE_IDS = ["ScanScope ID", "Rack", "Slide"]


# ----------------------------------------------------------------------------
# minimal TIFF / BigTIFF walker (we only need one tag per IFD)
# ----------------------------------------------------------------------------
class DescEntry:
    """Location of one page's ImageDescription inside the file."""

    def __init__(self, page, value, offset, count, count_pos, valoff_pos, inline):
        self.page = page
        self.value = value          # str (without the trailing NUL)
        self.offset = offset        # where the bytes live (None if inline)
        self.count = count          # byte count as recorded in the IFD (includes NUL)
        self.count_pos = count_pos  # file position of the count field
        self.valoff_pos = valoff_pos
        self.inline = inline


def _read_header(fh):
    head = fh.read(16)
    if len(head) < 8 or head[:2] not in (b"II", b"MM"):
        raise ValueError("not a TIFF/SVS file")
    bo = "<" if head[:2] == b"II" else ">"
    magic = struct.unpack(bo + "H", head[2:4])[0]
    if magic == 43:                                   # BigTIFF
        offsize = struct.unpack(bo + "H", head[4:6])[0]
        if offsize != 8:
            raise ValueError(f"unsupported BigTIFF offset size {offsize}")
        return bo, True, struct.unpack(bo + "Q", head[8:16])[0]
    if magic == 42:                                   # classic TIFF
        return bo, False, struct.unpack(bo + "I", head[4:8])[0]
    raise ValueError(f"not a TIFF (magic {magic})")


class IFD:
    """One TIFF page: where it sits and where its tag values are."""

    def __init__(self, page, offset, n_entries, entries_start, next_pos, next_off):
        self.page = page
        self.offset = offset
        self.n_entries = n_entries
        self.entries_start = entries_start
        self.next_pos = next_pos      # file position of this page's "next IFD" pointer
        self.next_off = next_off      # value stored there
        self.tags = {}                # tag -> (type, count, count_pos, valoff_pos, inline)

    @property
    def subfiletype(self):
        return self.scalar(TAG_NEWSUBFILETYPE, 0)

    scalar = None                     # filled in below (needs the open file)


def read_values(fh, bo, big, typ, count, valoff_pos):
    """Read a tag's value array (bytes for ASCII, tuple otherwise)."""
    cap = 8 if big else 4
    size = TYPE_SIZE.get(typ)
    if size is None:
        return None
    total = size * count
    if total <= cap:
        fh.seek(valoff_pos)
        raw = fh.read(total)
    else:
        fh.seek(valoff_pos)
        off = struct.unpack(bo + ("Q" if big else "I"), fh.read(cap))[0]
        fh.seek(off)
        raw = fh.read(total)
    if typ in (2, 7):
        return raw
    fmt = TYPE_FMT.get(typ)
    if fmt is None or len(raw) < total:
        return None
    return struct.unpack(bo + fmt * count, raw)


def read_ifds(path):
    """Return (byteorder, is_bigtiff, [IFD, ...]) walking the whole page chain."""
    ifds = []
    with open(path, "rb") as fh:
        bo, big, off = _read_header(fh)
        esize = 20 if big else 12
        ptr_size = 8 if big else 4
        page, seen = 0, set()
        while off:
            if off in seen:                            # malformed / looping IFD chain
                raise ValueError("corrupt IFD chain")
            seen.add(off)
            fh.seek(off)
            if big:
                n = struct.unpack(bo + "Q", fh.read(8))[0]
                entries_start = off + 8
            else:
                n = struct.unpack(bo + "H", fh.read(2))[0]
                entries_start = off + 2
            next_pos = entries_start + n * esize
            fh.seek(next_pos)
            nxt = fh.read(ptr_size)
            next_off = struct.unpack(bo + ("Q" if big else "I"), nxt)[0] if len(nxt) == ptr_size else 0
            ifd = IFD(page, off, n, entries_start, next_pos, next_off)
            for i in range(n):
                pos = entries_start + i * esize
                fh.seek(pos)
                tag, typ = struct.unpack(bo + "HH", fh.read(4))
                if big:
                    count = struct.unpack(bo + "Q", fh.read(8))[0]
                    count_pos, valoff_pos, cap = pos + 4, pos + 12, 8
                else:
                    count = struct.unpack(bo + "I", fh.read(4))[0]
                    count_pos, valoff_pos, cap = pos + 4, pos + 8, 4
                ifd.tags[tag] = (typ, count, count_pos, valoff_pos,
                                 TYPE_SIZE.get(typ, 1) * count <= cap)
            ifds.append(ifd)
            off = next_off
            page += 1
    return bo, big, ifds


def ifd_values(fh, bo, big, ifd, tag):
    ent = ifd.tags.get(tag)
    if ent is None:
        return None
    typ, count, _, valoff_pos, _ = ent
    return read_values(fh, bo, big, typ, count, valoff_pos)


def ifd_description(fh, bo, big, ifd):
    raw = ifd_values(fh, bo, big, ifd, TAG_IMAGEDESCRIPTION)
    if not raw:
        return ""
    return raw.split(b"\x00", 1)[0].decode("latin-1")


def read_descriptions(path):
    """Return (byteorder, is_bigtiff, [DescEntry, ...]) for every page of the file."""
    bo, big, ifds = read_ifds(path)
    out = []
    with open(path, "rb") as fh:
        for ifd in ifds:
            ent = ifd.tags.get(TAG_IMAGEDESCRIPTION)
            if ent is None:
                continue
            typ, count, count_pos, valoff_pos, inline = ent
            if typ != TYPE_ASCII:
                continue
            voff = None
            if not inline:
                fh.seek(valoff_pos)
                voff = struct.unpack(bo + ("Q" if big else "I"), fh.read(8 if big else 4))[0]
            raw = read_values(fh, bo, big, typ, count, valoff_pos) or b""
            text = raw.split(b"\x00", 1)[0].decode("latin-1")
            out.append(DescEntry(ifd.page, text, voff, count, count_pos, valoff_pos, inline))
    return bo, big, out


# ----------------------------------------------------------------------------
# label / macro pages
# ----------------------------------------------------------------------------
def classify_pages(path):
    """Return {page_index: kind} where kind is 'label', 'macro' or 'image'."""
    bo, big, ifds = read_ifds(path)
    kinds = {}
    with open(path, "rb") as fh:
        for ifd in ifds:
            desc = ifd_description(fh, bo, big, ifd).lower()
            sub = ifd_values(fh, bo, big, ifd, TAG_NEWSUBFILETYPE)
            sub = sub[0] if sub else 0
            if "label" in desc or sub == 1:
                kinds[ifd.page] = "label"
            elif "macro" in desc or sub == 9:
                kinds[ifd.page] = "macro"
            else:
                kinds[ifd.page] = "image"
    return bo, big, ifds, kinds


def page_data_extent(fh, bo, big, ifd):
    """Return [(offset, bytecount), ...] of this page's pixel data."""
    offs = ifd_values(fh, bo, big, ifd, TAG_STRIPOFFSETS)
    cnts = ifd_values(fh, bo, big, ifd, TAG_STRIPBYTECOUNTS)
    if offs is None:
        offs = ifd_values(fh, bo, big, ifd, TAG_TILEOFFSETS)
        cnts = ifd_values(fh, bo, big, ifd, TAG_TILEBYTECOUNTS)
    if not offs or not cnts:
        return []
    return [(o, c) for o, c in zip(offs, cnts) if c]


def remove_pages(path, bo, big, ifds, victims):
    """Zero the pixel bytes of `victims` and unlink those pages from the TIFF chain."""
    ptr_fmt = bo + ("Q" if big else "I")
    victim_pages = {v.page for v in victims}
    survivors = [i for i in ifds if i.page not in victim_pages]
    zeroed = 0
    with open(path, "r+b") as fh:
        for v in victims:                       # 1. wipe the pixel data for good
            for off, cnt in page_data_extent(fh, bo, big, v):
                fh.seek(off)
                fh.write(b"\x00" * cnt)
                zeroed += cnt
        for a, b in zip(survivors, survivors[1:] + [None]):   # 2. relink the page chain
            fh.seek(a.next_pos)
            fh.write(struct.pack(ptr_fmt, b.offset if b else 0))
        if survivors and survivors[0] is not ifds[0]:          # 3. first page removed
            fh.seek(8 if big else 4)
            fh.write(struct.pack(ptr_fmt, survivors[0].offset))
        fh.flush()
        os.fsync(fh.fileno())
    return zeroed


# ----------------------------------------------------------------------------
# Aperio description string: "<banner>\r\n<geometry ...>|Key = Value|Key = Value|..."
# ----------------------------------------------------------------------------
def split_desc(text):
    """Return (prefix, [(key, value, raw_segment), ...]).

    `prefix` is the banner + geometry/format part that must stay untouched.
    """
    parts = text.split("|")
    prefix = parts[0]
    items = []
    for seg in parts[1:]:
        if "=" in seg:
            k, v = seg.split("=", 1)
            items.append((k.strip(), v.strip(), seg))
        else:
            items.append((None, None, seg))          # keep unknown segments verbatim
    return prefix, items


def join_desc(prefix, items):
    segs = [prefix]
    for key, value, raw in items:
        segs.append(raw if key is None else f"{key} = {value}")
    return "|".join(segs)


def parse_date(value, in_formats):
    for fmt in in_formats:
        try:
            return datetime.strptime(value.strip(), fmt), fmt
        except ValueError:
            continue
    return None, None


def edit_desc(text, removes, sets, date_format, in_formats):
    """Apply the requested changes to one description string. Returns (new_text, [notes])."""
    prefix, items = split_desc(text)
    notes = []
    lower_removes = {r.strip().lower() for r in removes}

    kept = []
    for key, value, raw in items:
        if key is not None and key.lower() in lower_removes:
            notes.append(f"removed  {key} = {value}")
            continue
        kept.append((key, value, raw))
    items = kept

    if date_format:
        for i, (key, value, raw) in enumerate(items):
            if key is not None and key.lower() == "date":
                dt, used = parse_date(value, in_formats)
                if dt is None:
                    notes.append(f"! Date '{value}' not parseable with {in_formats} - left unchanged")
                else:
                    new = dt.strftime(date_format)
                    items[i] = (key, new, raw)
                    notes.append(f"date     {value} -> {new}   (read as {used})")
                break

    has_kv = any(key is not None for key, _, _ in items)
    for assign in sets:
        k, _, v = assign.partition("=")
        k, v = k.strip(), v.strip()
        for i, (key, value, raw) in enumerate(items):
            if key is not None and key.lower() == k.lower():
                notes.append(f"set      {key}: {value} -> {v}")
                items[i] = (key, v, raw)
                break
        else:
            if not has_kv:
                continue          # label / macro pages carry no key=value block - leave them alone
            items.append((k, v, None))
            notes.append(f"added    {k} = {v}")

    return join_desc(prefix, items), notes


# ----------------------------------------------------------------------------
# writing
# ----------------------------------------------------------------------------
def write_descriptions(path, bo, big, entries, new_texts):
    """Write new description strings in place.

    Shorter or equal -> written over the old bytes (count field updated).
    Longer           -> appended at the end of the file and the IFD entry re-pointed.
    Pixel data is never moved.
    """
    ptr_fmt = bo + ("Q" if big else "I")
    cnt_fmt = bo + ("Q" if big else "I")
    with open(path, "r+b") as fh:
        for ent, text in zip(entries, new_texts):
            if text == ent.value:
                continue
            data = text.encode("latin-1") + b"\x00"
            if not ent.inline and len(data) <= ent.count:
                fh.seek(ent.offset)
                fh.write(data)
                fh.write(b"\x00" * (ent.count - len(data)))   # blank the leftover tail
                fh.seek(ent.count_pos)
                fh.write(struct.pack(cnt_fmt, len(data)))
            else:
                fh.seek(0, os.SEEK_END)
                new_off = fh.tell()
                if new_off % 2:                                # TIFF values start on even offsets
                    fh.write(b"\x00")
                    new_off += 1
                fh.write(data)
                fh.seek(ent.count_pos)
                fh.write(struct.pack(cnt_fmt, len(data)))
                fh.seek(ent.valoff_pos)
                fh.write(struct.pack(ptr_fmt, new_off))
        fh.flush()
        os.fsync(fh.fileno())


# ----------------------------------------------------------------------------
# GUI entry points
# ----------------------------------------------------------------------------
def iter_files(target):
    if os.path.isfile(target):
        return [target]
    files = [os.path.join(target, f) for f in sorted(os.listdir(target)) if f.lower().endswith(EXTS)]
    return files


def is_aperio(entries):
    """True when the first page carries the Aperio banner - the same test OpenSlide uses."""
    return bool(entries) and entries[0].value.lstrip().startswith("Aperio")


def plan_and_apply(path, removes, sets, date_format, in_formats,
                   remove_label=False, remove_macro=False, backup=False, apply=False, out=print):
    """Compute (and optionally write) the changes for one file.

    Returns (changed: bool, notes: [str]).  `out` receives progress lines.
    """
    name = os.path.basename(path)
    notes = []
    try:
        bo, big, entries = read_descriptions(path)
    except Exception as e:  # noqa
        out(f"{name}: ERROR {e}")
        return False, [f"ERROR {e}"]
    if not entries:
        out(f"{name}: no ImageDescription, skipped")
        return False, ["no ImageDescription"]
    if not is_aperio(entries):
        out(f"{name}: SKIPPED - {NOT_APERIO}")
        return False, [NOT_APERIO]

    new_texts, head_notes = [], []
    for ent in entries:
        new, n = edit_desc(ent.value, removes, sets, date_format, in_formats)
        new_texts.append(new)
        if not head_notes and n:
            head_notes = n
    text_changed = any(n != e.value for n, e in zip(new_texts, entries))

    victims = []
    kinds = {}
    if remove_label or remove_macro:
        try:
            bo2, big2, ifds, kinds = classify_pages(path)
            wanted = ({"label"} if remove_label else set()) | ({"macro"} if remove_macro else set())
            victims = [i for i in ifds if kinds.get(i.page) in wanted]
            if len(ifds) - len(victims) < 1:
                out(f"{name}: refusing to remove every page")
                victims = []
        except Exception as e:  # noqa
            out(f"{name}: page scan failed: {e}")

    if not text_changed and not victims:
        out(f"{name}: no change needed")
        return False, ["no change needed"]

    out(f"{name}  ({len(entries)} pages)")
    for n in head_notes:
        notes.append(n)
        out(f"    {n}")
    for v in victims:
        n = f"remove   page {v.page} ({kinds.get(v.page)} image) - pixels zeroed, page unlinked"
        notes.append(n)
        out(f"    {n}")
    grow = [(e.page, len(t.encode("latin-1")) + 1 - e.count)
            for e, t in zip(entries, new_texts) if len(t.encode("latin-1")) + 1 > e.count]
    if grow:
        out(f"    note: {len(grow)} page(s) need more space -> appended at end of file "
            f"(+{sum(g for _, g in grow)} bytes)")
    if not apply:
        return True, notes

    if backup:
        bak = path + ".bak"
        if os.path.exists(bak):
            out(f"    ! backup already exists, file skipped: {os.path.basename(bak)}")
            return False, ["backup exists, skipped"]
        out(f"    backup -> {os.path.basename(bak)} ...")
        shutil.copy2(path, bak)
    try:
        if text_changed:
            write_descriptions(path, bo, big, entries, new_texts)
        if victims:
            bo2, big2, ifds, _ = classify_pages(path)      # re-read: offsets may have moved
            victims2 = [i for i in ifds if i.page in {v.page for v in victims}]
            zeroed = remove_pages(path, bo2, big2, ifds, victims2)
            out(f"    {len(victims2)} page(s) removed, {zeroed:,} bytes of pixel data zeroed")
    except Exception as e:  # noqa
        out(f"    WRITE FAILED: {e}")
        return False, [f"WRITE FAILED: {e}"]

    try:
        _, _, check = read_descriptions(path)
        got = [c.value for c in check]
        want = [t for t, e in zip(new_texts, entries) if e.page not in {v.page for v in victims}]
        ok = got == want
        out("    written and verified" if ok else "    ! WRITTEN BUT VERIFY MISMATCH")
        notes.append("written and verified" if ok else "VERIFY MISMATCH")
    except Exception as e:  # noqa
        out(f"    ! written but re-read failed: {e}")
        notes.append(f"re-read failed: {e}")
    return True, notes
