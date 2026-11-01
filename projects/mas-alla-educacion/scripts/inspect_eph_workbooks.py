from __future__ import annotations

import glob
import json
import zipfile
from pathlib import Path

import openpyxl


def main() -> None:
    out = []
    for path in sorted(glob.glob("data/raw/*.zip")):
        item = {"zip": path, "members": []}
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                with archive.open(name) as stream:
                    wb = openpyxl.load_workbook(stream, read_only=True, data_only=True)
                    sheets = []
                    for ws in wb.worksheets:
                        rows = ws.iter_rows(values_only=True)
                        header = list(next(rows))
                        sheets.append({
                            "name": ws.title,
                            "rows_including_header": ws.max_row,
                            "columns": ws.max_column,
                            "header": header,
                        })
                    item["members"].append({"name": name, "size": archive.getinfo(name).file_size, "sheets": sheets})
        out.append(item)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
