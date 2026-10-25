# Adding a Bible to the collection

The `bibles/` directory at the repository root holds the converted databases that ship with this repository.
Only add translations whose licence allows redistribution (see
[Copyright and licensing](../../README.md#copyright-and-licensing)).

1. Download the source and convert the downloaded zip as it is (or the folder it unzips to). Without a Digital
   Bible Library `metadata.xml` in the bundle, the source name becomes the database's `version`, so name the
   copy after the translation's short name:

   ```sh
   cp eng-web_usfm.zip WEB.zip
   tool/bin/bibles WEB.zip -n bible_web        # writes bibles/bible_web.sqlite (version WEB)
   ```

2. Check the run's warnings: skipped books should be only non-canonical ones, and missing verses should be
   ones the translation genuinely omits. The conversion fails if any validation check fails.
3. Add the database to both tables in the README's "Converted Bibles" section (source URL, date of the source
   files, SHA-256 of the download, licence) and to `COLLECTION` in `tool/tests/test_collection.py`, which checks
   that every database in `bibles/` is listed, validates and has the expected schema.
4. Commit the `.sqlite` file in `bibles/`. Re-converting the same download must give the same books, chapters
   and verses; only `created_at_utc` changes.
