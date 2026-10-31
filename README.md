# PhotoStack

PhotoStack is a small command-line toolkit for building layered, multi-view
still-life images from your own photographs. Its operations are deterministic
and use ImageMagick and ExifTool; it does not generate or retouch image content
with AI.

The workflow keeps the creative decisions in your hands: review contact sheets,
choose which frames show distinct angles, set their order, and adjust the crop
or blend settings. PhotoStack handles repeatable file operations such as
extracting camera JPEG previews, applying EXIF orientation, averaging frames,
and blending layers.

## Requirements

- Python 3.10 or newer
- ImageMagick 7, with the `magick` command available
- ExifTool, with the `exiftool` command available (needed for RAW previews and
  capture-time grouping)

Install the Python package in an active virtual environment:

```sh
python -m pip install -e .
```

If the tools are not on `PATH`, set `PHOTOSTACK_MAGICK` and/or
`PHOTOSTACK_EXIFTOOL` to their executable paths.

## Example workflow

Each command writes new files. The next command takes those files as explicit
inputs, so you can inspect and adjust each stage.

```sh
# Extract embedded camera-rendered JPEGs from RAW files.
photostack preview /path/to/card/DCIM/100CAM/*.CR3 -d work/previews

# Apply the RAW frame's EXIF orientation to each extracted JPEG.
photostack orient work/previews/*.jpg -d work/oriented

# Make a labeled sheet. Review it and choose the frames by hand.
photostack sheet work/oriented/*.jpg -o work/contact-sheet.jpg

# Average the chosen angle views, then apply a subtle soft-light finish.
photostack average work/oriented/IMG_101.jpg work/oriented/IMG_108.jpg \
  work/oriented/IMG_115.jpg -o work/average.jpg
photostack blend work/average.jpg work/average.jpg --mode softlight \
  --opacity 0.2 -o work/softlight.jpg

# Crop the finished image. ImageMagick geometry is WIDTHxHEIGHT+LEFT+TOP.
photostack crop work/softlight.jpg --geometry 2400x4200+500+300 \
  -o work/final.jpg
```

For a direct ordered overlay stack instead of an equal-weight average:

```sh
photostack stack angle-01.jpg angle-02.jpg angle-03.jpg \
  --mode overlay --opacity 0.2 -o stack.jpg
```

See [CLI reference](docs/cli/index.md) and
[workflow notes](docs/getting-started/workflows.md) for
details. Run `photostack --help` or `photostack COMMAND --help` for options.

## Limitations

Grouping uses EXIF capture-time gaps to suggest sessions. It does not identify
the subject, classify camera angles, align moving objects, or normalize
exposure and white balance. Select and order frames manually, and verify the
composites visually.
