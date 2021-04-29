# comics.py

This is a download for comics from readcomiconline.to.

## Installation

Run `pip install .` in the git directory.
Then you can call the program with `comic-dl`.

## Usage

```help
Usage: comics.py download [OPTIONS] URL

  Downloads a comicbook series or chapter.

  The URL can be a link to a chapter or series on readcomiconline.to. If URL
  leads to a series, all chapters will be downloaded.

Options:
  -d, --directory TEXT  The directory to download to
  --keep / --no-keep    Keep raw image files after converting to pdf [Default:
                        True]

  --pdf / --no-pdf      Convert images to pdf [Default: True]
  --help                Show this message and exit.
```

- Go to <https://readcomiconline.to> and find a comic you like.
- Copy the comic and run:

  ```shell
  ./comics.py download --no-keep --pdf <URL>
  ```

## Credits

Most of this is based of the code from here:
<https://github.com/Xonshiz/comic-dl>
