# Sample Bibles

The same three books of the King James Version (Ruth, Jonah and 3 John: 3 books, 9 chapters, 147 verses) in
each supported format. They are real files from eBible.org, cut down to three books, and the test suite
(`tests/test_samples.py`) converts every one of them end to end.

| File | Format | Where it comes from |
| --- | --- | --- |
| `kjv.usfm` | USFM | eBible.org `eng-kjv_usfm.zip`: the files `09-RUTeng-kjv.usfm`, `33-JONeng-kjv.usfm` and `94-3JNeng-kjv.usfm`, concatenated unchanged |
| `kjv.usx` | USX 3.0 | Generated from those three USFM files by [usfm-grammar](https://github.com/Bridgeconn/usfm-grammar) 3.2.1 (`USFMParser.to_usx`) |
| `kjv.usj` | USJ 3.1 | Generated from the same USFM files by usfm-grammar 3.2.1 (`USFMParser.to_usj`) |
| `kjv.osis.xml` | OSIS 2.1.1 | eBible.org's OSIS export of `eng-kjv` (as mirrored in [open-bibles](https://github.com/seven1m/open-bibles) `eng-kjv.osis.xml`), with every other book `div` removed |
| `kjv.vpl.txt` | VPL | eBible.org `eng-kjv_vpl.zip`: the `RUT`, `JON` and `3JO` lines of `eng-kjv_vpl.txt`, unchanged |

The King James Version is in the public domain (outside the United Kingdom, where the Crown holds rights to it).
eBible.org distributes these files as public domain.

## Expected differences

USFM, USX and USJ come from the same source and produce identical verse text. The other two files are
eBible.org's own exports and differ in their text, not in their markup:

- The OSIS file is a slightly different KJV edition (for example `Bethlehemjudah` instead of
  `Beth-lehem-judah`) and leaves out the paragraph mark `¶` that begins some verses.
- The VPL file marks words the translators added with brackets (`the man [was] Elimelech`), where the other
  formats use the `\add` marker, whose text is kept without brackets.

## Converting them

The samples hold three books, not 66, so they need `--allow-partial`:

```sh
./bin/bibles samples/kjv.usfm --allow-partial -o build/
./bin/bibles samples/kjv.usx --allow-partial -o build/kjv-usx.sqlite
./bin/bibles samples/kjv.osis.xml --allow-partial -o build/
./bin/bibles samples/kjv.vpl.txt --allow-partial -o build/
./bin/bibles samples/kjv.usj --allow-partial -o build/kjv-usj.sqlite
```
