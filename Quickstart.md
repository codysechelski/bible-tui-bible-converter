# Quickstart

This guide takes you from a Bible you downloaded to a single database file you can use. You type a few
commands into a terminal; each one is shown below, ready to copy.

You don't need to know anything about Bible file formats. Downloads come in several formats, and the tool works
out which one you have.

## What you need

- **Python 3.9 or newer.** macOS and Linux usually have it already. To check, open a terminal (on a Mac:
  press ⌘ Space, type _Terminal_ and press Return) and type:

  ```sh
  python3 --version
  ```

  If it prints `Python 3.9` or higher, you're set. If not, install Python from
  [python.org](https://www.python.org/downloads/).

- **This project on your computer.** On its GitHub page, click **Code → Download ZIP**, then unzip it
  somewhere easy to find, such as your home folder. (If you use git, `git clone` works too.)

## 1. Download a Bible

[eBible.org](https://ebible.org/download.php) has hundreds of translations that are free to download. Choose a
translation, and on its page download the file in the **USFM** row (for example `eng-web_usfm.zip` for the
World English Bible).

[open.bible](https://www.open.bible/bibles) is another great source for open Bibles.

Keep the file zipped; the tool reads the zip directly. An unzipped folder works too.

Check the translation's licence before you share the result with anyone. Many translations are free to read
but not free to redistribute.

## 2. Open a terminal in the project folder

In the terminal, type `cd` and a space. Then drag the project folder (the one that contains `tool` and
`bibles`) from Finder into the terminal window and press Return. Dragging a file or folder into the terminal
types its full location for you, which saves typing long paths.

## 3. Convert it

Type the following. Instead of typing the path to the zip, you can drag the zip file into the terminal at that
point.

```sh
tool/bin/bibles ~/Downloads/eng-web_usfm.zip --name bible_web
```

- `~/Downloads/eng-web_usfm.zip` is the Bible you downloaded. `~` means your home folder.
- `--name bible_web` is the name of the database file to create. Without it, the file is named after the
  download.

If a file or folder name contains spaces, put quotes around the path and write it out in full, because `~`
doesn't work inside quotes: `tool/bin/bibles "/Users/you/Downloads/My Bible.zip" --name my_bible`. Dragging the
file in handles all of this for you.

## 4. Read the result

A successful run ends like this:

```
Validation passed: 15 checks, 0 failed, 2 warnings
Output: /Users/you/bibles/bibles/bible_web.sqlite
Wrote 66 books, 1189 chapters and 31098 verses (version eng-web_usfm)
```

The database is in the project's `bibles` folder, at the path shown after `Output:`. It is a standard SQLite
file that any SQLite tool can open.

Some lines in the output start with `Warning:`. They are normal:

- `skipped book TOB: not one of the 66 canonical books` means a book outside the 66 books of the Protestant
  Bible (here, Tobit from the Apocrypha) was left out on purpose. Only the 66 books are kept.
- `ACT 8:37 has no text and was left out` means the translation doesn't include that verse. Many modern
  translations leave out a few verses that older ones have, so the database doesn't include them either.

If the run fails, the last lines say why, followed by `no database was written`. Nothing is left half finished.

## Common problems

**`Book count: expected 66 books, found 27`.** The download is only part of the Bible, such as a New Testament.
Add `--allow-partial` to the command to accept it:

```sh
tool/bin/bibles ~/Downloads/some-new-testament.zip --name my_nt --allow-partial
```

**`could not detect the format` or `no Bible files found`.** The file isn't a Bible format the tool reads. On
eBible.org, use the **USFM** download. PDF, ePub and HTML downloads won't work.

**`No such file or directory` or `command not found`.** The terminal isn't in the project folder. Repeat step 2,
then try again.

**On Windows.** The `tool/bin/bibles` command needs a Mac or Linux terminal. On Windows, open the project's
`tool` folder in a terminal and type `python -m bibles` instead, followed by the rest of the command:

```sh
python -m bibles C:\Users\you\Downloads\eng-web_usfm.zip --name bible_web
```

## More options

To see every option, type:

```sh
tool/bin/bibles --help
```

[Command line usage](tool/docs/usage.md) covers all of them, [supported formats](tool/docs/formats.md) lists what
each format can hold, and [database schema](tool/docs/schema.md) shows how the database is laid out.
