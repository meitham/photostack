# Command reference

Every image command writes to a new path. Existing outputs are protected by
default; pass `--overwrite` to replace one. Most commands print the output path
when they finish. Use `photostack --help` and `photostack COMMAND --help` for
the live option list.

## `preview`

Extract the camera-rendered JPEG preview embedded in each RAW file:

```sh
photostack preview IMG_100.CR3 IMG_101.CR3 -d work/previews
```

Supported extensions are ARW, CR2, CR3, DNG, NEF, NRW, ORF, PEF, RAF, and RW2.
This does not develop RAW sensor data. A JPEG preview must be embedded in the
RAW file.

## `orient`

Apply EXIF orientation to image pixels and write corrected copies:

```sh
photostack orient work/previews/*.jpg -d work/oriented
```

Use this as its own step before comparing dimensions, averaging, or blending.
RAW files should go through `preview` first.

## `groups`

Group images by capture-time gaps to help find a burst or session:

```sh
photostack groups /path/to/card/DCIM/100CAM/*.CR3 \
  --gap-seconds 45 -o work/groups.json
```

Files with no usable `DateTimeOriginal` appear in the JSON `ungrouped` list.
Time groups are suggestions; inspect the files and choose frames manually.

## `sheet`

Create a labeled contact sheet for manual review:

```sh
photostack sheet work/oriented/*.jpg -o work/contact-sheet.jpg \
  --columns 5 --cell-size 360x520
```

## `average`

Combine two or more same-sized images with equal weights:

```sh
photostack average angle-a-1.jpg angle-a-2.jpg angle-b.jpg -o average.jpg
```

Images must have matching pixel dimensions. Averaging is useful when you want
each selected view to contribute evenly. It does not register or align frames.

## `blend`

Blend a layer over a base image. Supported modes: `normal`, `multiply`,
`screen`, `overlay`, and `softlight`.

```sh
photostack blend base.jpg layer.jpg --mode softlight --opacity 0.2 \
  -o result.jpg
```

Opacity is from 0 to 1 and controls the layer contribution. Inputs must have
matching dimensions.

## `stack`

Apply a sequence of blend layers in the order given. The first input is the
base; the same mode and opacity are used for every subsequent input:

```sh
photostack stack view-1.jpg view-2.jpg view-3.jpg \
  --mode overlay --opacity 0.2 -o result.jpg
```

## `tone`

Apply an ImageMagick gamma adjustment. Choose the value by visual review:

```sh
photostack tone composite.jpg --gamma 1.05 -o toned.jpg
```

## `crop`

Crop with ImageMagick geometry syntax `WIDTHxHEIGHT+LEFT+TOP`:

```sh
photostack crop toned.jpg --geometry 2400x4200+500+300 -o final.jpg
```
