# Sample Bibles

The same three books of the King James Version (Ruth, Jonah and 3 John: 3 books, 9 chapters, 147 verses) in
each text format, plus the same books of the ASV as RTF. They are real files from eBible.org, cut down to three books, and the test suite
(`tests/test_samples.py`) converts every one of them end to end.

| File | Format | Where it comes from |
| --- | --- | --- |
| `kjv.usfm` | USFM | eBible.org `eng-kjv_usfm.zip`: the files `09-RUTeng-kjv.usfm`, `33-JONeng-kjv.usfm` and `94-3JNeng-kjv.usfm`, concatenated unchanged |
| `kjv.usx` | USX 3.0 | Generated from those three USFM files by [usfm-grammar](https://github.com/Bridgeconn/usfm-grammar) 3.2.1 (`USFMParser.to_usx`) |
| `kjv.usj` | USJ 3.1 | Generated from the same USFM files by usfm-grammar 3.2.1 (`USFMParser.to_usj`) |
| `kjv.osis.xml` | OSIS 2.1.1 | eBible.org's OSIS export of `eng-kjv` (as mirrored in [open-bibles](https://github.com/seven1m/open-bibles) `eng-kjv.osis.xml`), with every other book `div` removed |
| `kjv.vpl.txt` | VPL | eBible.org `eng-kjv_vpl.zip`: the `RUT`, `JON` and `3JO` lines of `eng-kjv_vpl.txt`, unchanged |

`asv-rtf/` holds the same three books of the American Standard Version (1901) as RTF, one file per book:
`RUT.rtf`, `JON.rtf` and `3JN.rtf`, copied unchanged from `release/USX_1/` of the bundle
`American Standard Version of 1901 [eng] ASV.zip` (SHA-256
`10bf3a168ed56ff189fc91e9874f56c035b4869b464cc87f3b2d5746df9233d1`), a Digital Bible Library style bundle whose
`USX_1` folder holds RTF rather than USX. The test suite converts the folder, and a zip built from it, end to
end. The ASV is in the public domain.

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

The samples hold three books, not 66, so they need `--allow-partial`. From the repository root:

```sh
tool/bin/bibles tool/samples/kjv.usfm --allow-partial -o build/
tool/bin/bibles tool/samples/kjv.usx --allow-partial -o build/kjv-usx.sqlite
tool/bin/bibles tool/samples/kjv.osis.xml --allow-partial -o build/
tool/bin/bibles tool/samples/kjv.vpl.txt --allow-partial -o build/
tool/bin/bibles tool/samples/kjv.usj --allow-partial -o build/kjv-usj.sqlite
tool/bin/bibles tool/samples/asv-rtf/ --allow-partial -o build/asv-rtf.sqlite
```
