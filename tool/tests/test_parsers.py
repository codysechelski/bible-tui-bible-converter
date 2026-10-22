from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bibles.books import book_for_osis, find_book, BOOKS, UnknownBookError
from bibles.parsers import ParseError, parse_file
from bibles.parsers.osis import parse_osis_id

PSALM_23_1 = "The LORD is my shepherd; I shall not want."
PSALM_23_2 = "He makes me lie down in green pastures. He leads me beside still waters."
JOHN_11_35 = "Jesus wept."

# The same passage in every format, with a heading, a footnote, poetry lines and a second book.
USFM = r"""\id PSA Sample Bible
\usfm 3.0
\h Psalms
\toc1 The Book of Psalms
\mt1 Psalms
\rem Reminder text
\c 23
\s1 The Lord Is My Shepherd
\d A Psalm of David.
\q1
\v 1 The \nd LORD\nd* is my shepherd;\f + \fr 23:1 \ft Or \fq Yahweh\f*
\q2 I shall not \w want|strong="H2637"\w*.
\q1
\v 2 He makes me lie down in green pastures.
\q2 He leads me beside still waters.\x - \xo 23:2 \xt Rev 7:17\x*
\id JHN Sample Bible
\c 11
\p
\v 35 Jesus wept.
"""

USX = """<?xml version="1.0" encoding="utf-8"?>
<usx version="3.0">
  <book code="PSA" style="id">Sample Bible</book>
  <para style="h">Psalms</para>
  <para style="toc1">The Book of Psalms</para>
  <para style="mt1">Psalms</para>
  <chapter number="23" style="c" sid="PSA 23"/>
  <para style="s1">The Lord Is My Shepherd</para>
  <para style="d">A Psalm of David.</para>
  <para style="q1"><verse number="1" style="v" sid="PSA 23:1"/>The <char style="nd">LORD</char> is my shepherd;<note caller="+" style="f"><char style="fr">23:1 </char><char style="ft">Or </char><char style="fq">Yahweh</char></note></para>
  <para style="q2">I shall not <char style="w" strong="H2637">want</char>.<verse eid="PSA 23:1"/></para>
  <para style="q1"><verse number="2" style="v" sid="PSA 23:2"/>He makes me lie down in green pastures.</para>
  <para style="q2">He leads me beside still waters.<note caller="-" style="x"><char style="xo">23:2 </char><char style="xt">Rev 7:17</char></note><verse eid="PSA 23:2"/></para>
  <chapter eid="PSA 23"/>
  <book code="JHN" style="id">Sample Bible</book>
  <chapter number="11" style="c"/>
  <para style="p"><verse number="35" style="v"/>Jesus wept.</para>
</usx>
"""

OSIS = """<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText osisIDWork="SAMPLE" osisRefWork="Bible">
    <header><work osisWork="SAMPLE"><title>Sample Bible</title></work></header>
    <div type="book" osisID="Ps">
      <title type="main">Psalms</title>
      <div type="introduction"><p>An introduction to the Psalms.</p></div>
      <chapter osisID="Ps.23">
        <title type="psalm">A Psalm of David.</title>
        <div type="section"><title>The Lord Is My Shepherd</title>
          <lg>
            <l><verse sID="Ps.23.1" osisID="Ps.23.1"/>The <divineName>LORD</divineName> is my shepherd;<note type="explanation" osisRef="Ps.23.1">Or <catchWord>Yahweh</catchWord></note></l>
            <l>I shall not <w lemma="strong:H2637">want</w>.<verse eID="Ps.23.1"/></l>
            <l><verse sID="Ps.23.2" osisID="Ps.23.2"/>He makes me lie down in green pastures.</l>
            <l>He leads me beside still waters.<note type="crossReference"><reference osisRef="Rev.7.17">Rev 7:17</reference></note><verse eID="Ps.23.2"/></l>
          </lg>
        </div>
      </chapter>
    </div>
    <div type="book" osisID="John">
      <chapter osisID="John.11"><p><verse osisID="John.11.35">Jesus wept.</verse></p></chapter>
    </div>
  </osisText>
</osis>
"""

VPL = f"""PSA 23:1 {PSALM_23_1}
PSA 23:2 {PSALM_23_2}
JHN 11:35 {JOHN_11_35}
"""

USJ = json.dumps({
    "type": "USJ",
    "version": "3.1",
    "content": [
        {"type": "book", "marker": "id", "code": "PSA", "content": ["Sample Bible"]},
        {"type": "para", "marker": "h", "content": ["Psalms"]},
        {"type": "para", "marker": "mt1", "content": ["Psalms"]},
        {"type": "chapter", "marker": "c", "number": "23"},
        {"type": "para", "marker": "s1", "content": ["The Lord Is My Shepherd"]},
        {"type": "para", "marker": "d", "content": ["A Psalm of David."]},
        {"type": "para", "marker": "q1", "content": [
            {"type": "verse", "marker": "v", "number": "1"},
            "The ", {"type": "char", "marker": "nd", "content": ["LORD"]}, " is my shepherd;",
            {"type": "note", "marker": "f", "caller": "+", "content": [
                {"type": "char", "marker": "fr", "content": ["23:1 "]},
                {"type": "char", "marker": "ft", "content": ["Or "]},
                {"type": "char", "marker": "fq", "content": ["Yahweh"]},
            ]},
        ]},
        {"type": "para", "marker": "q2", "content": [
            "I shall not ", {"type": "char", "marker": "w", "strong": "H2637", "content": ["want"]}, ".",
        ]},
        {"type": "para", "marker": "q1", "content": [
            {"type": "verse", "marker": "v", "number": "2"}, "He makes me lie down in green pastures.",
        ]},
        {"type": "para", "marker": "q2", "content": [
            "He leads me beside still waters.",
            {"type": "note", "marker": "x", "caller": "-", "content": [
                {"type": "char", "marker": "xt", "content": ["Rev 7:17"]},
            ]},
        ]},
        {"type": "book", "marker": "id", "code": "JHN"},
        {"type": "chapter", "marker": "c", "number": "11"},
        {"type": "para", "marker": "p", "content": [
            {"type": "verse", "marker": "v", "number": "35"}, "Jesus wept.",
        ]},
    ],
})

SAMPLES = {"usfm": ("sample.usfm", USFM), "usx": ("sample.usx", USX), "osis": ("sample.xml", OSIS),
           "vpl": ("sample.txt", VPL), "usj": ("sample.json", USJ)}
EXPECTED = [("PSA 23:1", PSALM_23_1), ("PSA 23:2", PSALM_23_2), ("JHN 11:35", JOHN_11_35)]


class ParserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, name: str, content, encoding: str = "utf-8") -> Path:
        path = self.tmp / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding=encoding)
        return path

    def parse(self, fmt: str, content, name: str = "source"):
        return parse_file(self.write(name, content), fmt)

    def verses(self, fmt: str, content):
        return [(v.reference, v.text) for v in self.parse(fmt, content).verses()]


class CrossFormatTests(ParserTestCase):
    def test_every_format_produces_identical_verses(self) -> None:
        for fmt, (name, content) in SAMPLES.items():
            with self.subTest(format=fmt):
                bible = parse_file(self.write(name, content), fmt)
                self.assertEqual([(v.reference, v.text) for v in bible.verses()], EXPECTED)
                self.assertEqual([b.code for b in bible.books], ["PSA", "JHN"])
                self.assertEqual(bible.warnings, [])


class UsfmTests(ParserTestCase):
    def test_verse_continues_across_lines_until_next_marker(self) -> None:
        source = "\\id GEN\n\\c 1\n\\p\n\\v 1 In the beginning\nGod created\n\n the heavens.\n\\v 2 Next.\n"
        self.assertEqual(self.verses("usfm", source),
                         [("GEN 1:1", "In the beginning God created the heavens."), ("GEN 1:2", "Next.")])

    def test_multiple_books_split_in_order(self) -> None:
        source = "\\id MAT\n\\c 1\n\\p\n\\v 1 Matthew.\n\\id GEN\n\\c 1\n\\p\n\\v 1 Genesis.\n\\c 2\n\\v 1 Two.\n"
        bible = self.parse("usfm", source)
        self.assertEqual([b.code for b in bible.books], ["MAT", "GEN"])
        self.assertEqual([c.number for c in bible.books[1].chapters], [1, 2])

    def test_formatting_markers_do_not_leak(self) -> None:
        source = ("\\id JHN\n\\c 3\n\\p\n\\v 16 For God \\add so\\add* loved \\+wj the\\+wj* \\wj world\\wj*,\n"
                  "\\m that he gave \\bd his\\bd*\\it only\\it* Son.\n\\b\n\\li1 \\v 17 \\qs Selah\\qs*\n")
        self.assertEqual(self.verses("usfm", source), [
            ("JHN 3:16", "For God so loved the world, that he gave hisonly Son."),
            ("JHN 3:17", "Selah"),
        ])

    def test_non_verse_content_is_excluded(self) -> None:
        source = ("\\id GEN Title line\n\\ide UTF-8\n\\h Genesis\n\\toc1 Genesis\n\\toc2 Gen\n\\mt1 Genesis\n"
                  "\\is Introduction\n\\ip Intro paragraph.\n\\c 1\n\\cl Chapter One\n\\ms Part One\n"
                  "\\s1 Creation\n\\r (John 1:1)\n\\p\n\\v 1 In the beginning.\n\\rem not text\n\\sp Speaker\n"
                  "\\p \\v 2 Second.\n")
        self.assertEqual(self.verses("usfm", source), [("GEN 1:1", "In the beginning."), ("GEN 1:2", "Second.")])

    def test_notes_figures_and_alternate_numbers_are_removed(self) -> None:
        source = ("\\id GEN\n\\c 1\n\\p\n\\v 1 \\va 2\\va*\\vp 1a\\vp*Text\\fe + \\ft endnote \\fp more\\fe* here"
                  "\\fig A picture|src=\"a.jpg\"\\fig*.\n\\v 2 \\x - \\xo 1:2 \\xt Ps 1:1\\x*Second.\n")
        self.assertEqual(self.verses("usfm", source), [("GEN 1:1", "Text here."), ("GEN 1:2", "Second.")])

    def test_verse_range_and_segments_use_first_verse(self) -> None:
        source = "\\id GEN\n\\c 1\n\\p\n\\v 1-2 Bridged text.\n\\v 3a First part,\n\\v 3b second part.\n"
        self.assertEqual(self.verses("usfm", source),
                         [("GEN 1:1", "Bridged text."), ("GEN 1:3", "First part, second part.")])

    def test_empty_verse_is_left_out_with_warning(self) -> None:
        bible = self.parse("usfm", "\\id MAT\n\\c 17\n\\p\n\\v 20 Text.\n\\v 21 \\f + \\ft Omitted.\\f*\n\\v 22 More.\n")
        self.assertEqual([v.reference for v in bible.verses()], ["MAT 17:20", "MAT 17:22"])
        self.assertEqual(bible.warnings, ["MAT 17:21 has no text and was left out"])

    def test_byte_order_mark(self) -> None:
        bible = self.parse("usfm", ("\ufeff\\id GEN\n\\c 1\n\\p\n\\v 1 Café.\n").encode("utf-8"))
        self.assertEqual(next(bible.verses()).text, "Café.")

    def test_legacy_encoding_is_read_with_warning(self) -> None:
        bible = self.parse("usfm", "\\id GEN\n\\c 1\n\\p\n\\v 1 Café “quoted”.\n".encode("cp1252"))
        self.assertEqual(next(bible.verses()).text, "Café “quoted”.")
        self.assertIn("not valid UTF-8", bible.warnings[0])
        self.assertIn("cp1252", bible.warnings[0])

    def test_errors_name_file_and_line(self) -> None:
        cases = [
            ("\\id GEN\n\\v 1 No chapter.\n", "line 2: verse 1 appears before any book and chapter"),
            ("\\id GEN\n\\c 1\n\\p\n\\v 1 A.\n\\v 1 Again.\n", "line 5: GEN 1:1 appears more than once"),
            ("\\id GEN\n\\c x\n", "line 2: invalid chapter number 'x'"),
            ("\\id GEN\n\\c 1\n\\v", "\\\\v is missing its value"),
        ]
        for source, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ParseError, f"source.*{message}"):
                    self.parse("usfm", source)

    def test_no_verses(self) -> None:
        with self.assertRaisesRegex(ParseError, "no verses found"):
            self.parse("usfm", "\\id GEN\n\\h Genesis\n")

    def test_books_outside_the_66_are_skipped_with_warning(self) -> None:
        source = ("\\id FRT Front matter\n\\p Preface.\n\\id GEN\n\\c 1\n\\p\n\\v 1 Genesis.\n"
                  "\\id TOB\n\\c 1\n\\p\n\\v 1 Tobit.\n\\id tob\n\\c 2\n\\v 1 Again.\n"
                  "\\id REV\n\\c 1\n\\p\n\\v 1 Revelation.\n")
        bible = self.parse("usfm", source)
        self.assertEqual([v.reference for v in bible.verses()], ["GEN 1:1", "REV 1:1"])
        self.assertEqual(bible.warnings, ["skipped book FRT: not one of the 66 canonical books",
                                          "skipped book TOB: not one of the 66 canonical books"])


class UsxTests(ParserTestCase):
    def test_usx2_without_end_milestones_and_id_attribute(self) -> None:
        source = ('<usx version="2.0"><book id="GEN" style="id"/><chapter number="1" style="c"/>'
                  '<para style="p"><verse number="1" style="v"/>In the beginning.</para>'
                  '<para style="s">Heading</para>'
                  '<para style="p"><verse number="2" style="v"/>Second <char style="add">verse</char>.</para></usx>')
        self.assertEqual(self.verses("usx", source),
                         [("GEN 1:1", "In the beginning."), ("GEN 1:2", "Second verse.")])

    def test_numbers_from_sid_when_number_missing(self) -> None:
        source = ('<usx><book code="GEN"/><chapter sid="GEN 1"/><para style="p">'
                  '<verse sid="GEN 1:1"/>Text.<verse eid="GEN 1:1"/></para></usx>')
        self.assertEqual(self.verses("usx", source), [("GEN 1:1", "Text.")])

    def test_text_after_end_milestone_is_not_verse_text(self) -> None:
        source = ('<usx><book code="GEN"/><chapter number="1"/><para style="p">'
                  '<verse number="1"/>Text.<verse eid="GEN 1:1"/> stray</para></usx>')
        self.assertEqual(self.verses("usx", source), [("GEN 1:1", "Text.")])

    def test_several_books_in_document_order(self) -> None:
        source = ('<usx><book code="REV"/><chapter number="1"/><para style="p"><verse number="1"/>R.</para>'
                  '<book code="GEN"/><chapter number="1"/><para style="p"><verse number="1"/>G.</para></usx>')
        self.assertEqual([b.code for b in self.parse("usx", source).books], ["REV", "GEN"])

    def test_books_outside_the_66_are_skipped(self) -> None:
        source = ('<usx><book code="SIR"/><chapter number="1"/><para style="p"><verse number="1"/>Sirach.</para>'
                  '<book code="MAT"/><chapter number="1"/><para style="p"><verse number="1"/>Matthew.</para></usx>')
        bible = self.parse("usx", source)
        self.assertEqual([v.reference for v in bible.verses()], ["MAT 1:1"])
        self.assertEqual(bible.warnings, ["skipped book SIR: not one of the 66 canonical books"])

    def test_non_usx_xml_is_rejected(self) -> None:
        with self.assertRaisesRegex(ParseError, r"not a USX document \(root element is <osis>"):
            self.parse("usx", OSIS)
        with self.assertRaisesRegex(ParseError, "not well-formed XML"):
            self.parse("usx", "<usx><para>")
        with self.assertRaisesRegex(ParseError, "no verses found"):
            self.parse("usx", '<usx><book code="GEN"/></usx>')


class OsisTests(ParserTestCase):
    def test_version_from_header(self) -> None:
        bible = self.parse("osis", OSIS)
        self.assertEqual((bible.version, bible.version_name), ("SAMPLE", "Sample Bible"))

    def test_container_verses_and_non_default_namespace(self) -> None:
        source = ('<o:osis xmlns:o="http://example.com/custom-osis"><o:osisText osisIDWork="X">'
                  '<o:div type="book" osisID="Gen"><o:title>Genesis</o:title><o:chapter osisID="Gen.1">'
                  '<o:verse osisID="Gen.1.1">In the <o:transChange type="added">very</o:transChange> beginning.'
                  '</o:verse> stray <o:verse osisID="Gen.1.2 Gen.1.3">Bridged.</o:verse>'
                  '</o:chapter></o:div></o:osisText></o:osis>')
        self.assertEqual(self.verses("osis", source),
                         [("GEN 1:1", "In the very beginning."), ("GEN 1:2", "Bridged.")])

    def test_no_namespace_and_heading_between_milestones(self) -> None:
        source = ('<osis><osisText><div type="book" osisID="1Sam"><chapter sID="1Sam.1"/>'
                  '<verse sID="1Sam.1.1" osisID="1Sam.1.1"/>One.<verse eID="1Sam.1.1"/>'
                  '<title>Heading</title> between '
                  '<verse sID="1Sam.1.2" osisID="1Sam.1.2"/>Two<note>a note</note>.<verse eID="1Sam.1.2"/>'
                  '<chapter eID="1Sam.1"/></div></osisText></osis>')
        self.assertEqual(self.verses("osis", source), [("1SA 1:1", "One."), ("1SA 1:2", "Two.")])

    def test_osis_id_parsing(self) -> None:
        self.assertEqual(parse_osis_id("Gen.1.1"), ("GEN", 1, 1))
        self.assertEqual(parse_osis_id("KJV:Ps.23.1!a"), ("PSA", 23, 1))
        self.assertEqual(parse_osis_id("Rev.22.20-Rev.22.21"), ("REV", 22, 20))
        self.assertEqual(parse_osis_id("GEN.1.1"), ("GEN", 1, 1))
        with self.assertRaises(UnknownBookError):
            parse_osis_id("Tob.1.1")
        with self.assertRaises(ValueError):
            parse_osis_id("Gen.1")

    def test_books_outside_the_66_are_skipped(self) -> None:
        source = ('<osis><osisText><div type="book" osisID="Tob"><chapter osisID="Tob.1">'
                  '<verse osisID="Tob.1.1">Tobit.</verse></chapter></div>'
                  '<div type="book" osisID="Matt"><chapter osisID="Matt.1">'
                  '<verse osisID="Matt.1.1">Matthew.</verse></chapter></div></osisText></osis>')
        bible = self.parse("osis", source)
        self.assertEqual([v.reference for v in bible.verses()], ["MAT 1:1"])
        self.assertEqual(bible.warnings, ["skipped book TOB: not one of the 66 canonical books"])

    def test_no_verse_references(self) -> None:
        source = '<osis><osisText><div type="book" osisID="Gen"><p>Only text.</p></div></osisText></osis>'
        with self.assertRaisesRegex(ParseError, "contains no verse references"):
            self.parse("osis", source)

    def test_non_osis_xml_is_rejected(self) -> None:
        with self.assertRaisesRegex(ParseError, "not an OSIS document"):
            self.parse("osis", USX)


class VplTests(ParserTestCase):
    def test_both_reference_forms(self) -> None:
        source = "GEN 1:1 In the beginning.\nGEN.1.2 The earth.\nGen 1:3 Light.\n1 John 1:1 That which was.\n"
        self.assertEqual(self.verses("vpl", source), [
            ("GEN 1:1", "In the beginning."), ("GEN 1:2", "The earth."), ("GEN 1:3", "Light."),
            ("1JN 1:1", "That which was."),
        ])

    def test_blank_lines_and_empty_verses_are_absent(self) -> None:
        bible = self.parse("vpl", "MAT 17:20 Text.\n\nMAT 17:21\nMAT 17:22 More.\n")
        self.assertEqual([v.reference for v in bible.verses()], ["MAT 17:20", "MAT 17:22"])
        self.assertEqual(bible.warnings, [])

    def test_verse_range_kept_on_first_verse(self) -> None:
        source = "ROM 3:1 One.\nROM 3:2-3 Whole range text.\nROM 3:3 <range>\nROM 3:4 Four.\n"
        self.assertEqual(self.verses("vpl", source),
                         [("ROM 3:1", "One."), ("ROM 3:2", "Whole range text."), ("ROM 3:4", "Four.")])

    def test_line_that_is_not_a_verse_is_reported(self) -> None:
        bible = self.parse("vpl", "# Sample Bible\nGEN 1:1 Text.\n")
        self.assertEqual([v.reference for v in bible.verses()], ["GEN 1:1"])
        self.assertEqual(len(bible.warnings), 1)
        self.assertIn("line 1: not a verse reference", bible.warnings[0])

    def test_unknown_book_is_skipped_and_duplicate_is_an_error(self) -> None:
        bible = self.parse("vpl", "GEN 1:1 Text.\nTOB 1:1 Tobit.\nTOB 1:2 More.\n4ES 1:1 Esdras.\nGEN 1:2 Two.\n")
        self.assertEqual([v.reference for v in bible.verses()], ["GEN 1:1", "GEN 1:2"])
        self.assertEqual(bible.warnings, ["skipped book TOB: not one of the 66 canonical books",
                                          "skipped book 4ES: not one of the 66 canonical books"])
        with self.assertRaisesRegex(ParseError, "line 2: GEN 1:1 appears more than once"):
            self.parse("vpl", "GEN 1:1 Text.\nGEN 1:1 Again.\n")


class UsjTests(ParserTestCase):
    def test_nested_paragraph_and_character_markers(self) -> None:
        source = json.dumps({"type": "USJ", "content": [
            {"type": "book", "marker": "id", "code": "GEN"},
            {"type": "chapter", "marker": "c", "number": "1"},
            {"type": "para", "marker": "p", "content": [
                {"type": "verse", "marker": "v", "number": "1"},
                "In the ", {"type": "char", "marker": "add", "content": [
                    {"type": "char", "marker": "+nd", "content": ["very"]}]},
                " beginning.",
            ]},
        ]})
        self.assertEqual(self.verses("usj", source), [("GEN 1:1", "In the very beginning.")])

    def test_mark_property_is_accepted(self) -> None:
        source = json.dumps({"type": "USJ", "content": [
            {"mark": "id", "code": "GEN"}, {"mark": "c", "number": "1"},
            {"type": "para", "mark": "p", "content": [{"mark": "v", "number": "1"}, "Text."]},
        ]})
        self.assertEqual(self.verses("usj", source), [("GEN 1:1", "Text.")])

    def test_several_books_in_document_order(self) -> None:
        source = json.dumps({"type": "USJ", "content": [
            {"type": "book", "code": "REV"}, {"type": "chapter", "number": "1"},
            {"type": "para", "marker": "p", "content": [{"type": "verse", "number": "1"}, "R."]},
            {"type": "book", "code": "GEN"}, {"type": "chapter", "number": "1"},
            {"type": "para", "marker": "p", "content": [{"type": "verse", "number": "1"}, "G."]},
        ]})
        self.assertEqual([b.code for b in self.parse("usj", source).books], ["REV", "GEN"])

    def test_books_outside_the_66_are_skipped(self) -> None:
        source = json.dumps({"type": "USJ", "content": [
            {"type": "book", "code": "GLO"}, {"type": "chapter", "number": "1"},
            {"type": "para", "marker": "p", "content": [{"type": "verse", "number": "1"}, "Glossary."]},
            {"type": "book", "code": "GEN"}, {"type": "chapter", "number": "1"},
            {"type": "para", "marker": "p", "content": [{"type": "verse", "number": "1"}, "G."]},
        ]})
        bible = self.parse("usj", source)
        self.assertEqual([v.reference for v in bible.verses()], ["GEN 1:1"])
        self.assertEqual(bible.warnings, ["skipped book GLO: not one of the 66 canonical books"])

    def test_malformed_json_names_file_and_failure(self) -> None:
        path = self.write("broken.json", '{"type": "USJ", "content": [\n  {"type": "book",\n')
        with self.assertRaisesRegex(ParseError, r"broken\.json: malformed JSON at line 3, column 1"):
            parse_file(path, "usj")

    def test_non_usj_json_is_rejected(self) -> None:
        with self.assertRaisesRegex(ParseError, "not a USJ document"):
            self.parse("usj", '{"type": "other"}')
        with self.assertRaisesRegex(ParseError, "no verses found"):
            self.parse("usj", '{"type": "USJ", "content": []}')


class ParseFileTests(ParserTestCase):
    def test_unknown_format_and_unreadable_file(self) -> None:
        with self.assertRaisesRegex(ParseError, "no parser"):
            parse_file(self.write("a", "x"), "docx")
        with self.assertRaisesRegex(ParseError, "cannot read"):
            parse_file(self.tmp / "missing.usfm", "usfm")


class BookLookupTests(unittest.TestCase):
    def test_osis_codes(self) -> None:
        self.assertEqual(book_for_osis("Ps").usfm_code, "PSA")
        self.assertEqual(book_for_osis("1sam").usfm_code, "1SA")
        self.assertEqual(book_for_osis("JHN").usfm_code, "JHN")
        self.assertEqual(len({b.osis_code for b in BOOKS}), 66)

    def test_codes_and_names_never_collide(self) -> None:
        for book in BOOKS:
            for token in (book.usfm_code, book.osis_code, book.canonical_name, book.common_name,
                          book.common_name.lower()):
                self.assertIs(find_book(token), book, token)
        with self.assertRaises(UnknownBookError):
            find_book("Tobit")

    def test_aliases(self) -> None:
        for alias, code in (("SOL", "SNG"), ("EZE", "EZK"), ("JOE", "JOL"), ("MAR", "MRK"), ("JOH", "JHN"),
                            ("PHI", "PHP"), ("JAM", "JAS"), ("1JO", "1JN"), ("2jo", "2JN"), ("3JO", "3JN")):
            self.assertEqual(find_book(alias).usfm_code, code)
        with self.assertRaises(UnknownBookError):
            book_for_osis("SOL")


if __name__ == "__main__":
    unittest.main()
