# Workflow notes

## Multi-view still-life composite

1. Extract embedded JPEG previews with `preview` if your source is RAW.
2. Run `orient` so camera orientation is reflected in the actual pixels.
3. Create a `sheet` and inspect the frames. Pick views with visibly different
   angles; a run of nearly front-facing views adds little rotation.
4. If you made several exposures from each camera position, combine each
   position's exposures first. PhotoStack's `average` gives each selected
   frame equal weight. For an exposure stack that needs a different treatment,
   use an editor or adjust the process manually.
5. Combine the selected angle images using `average` or `stack`, then review
   the result. Use `blend` for a separate finishing layer if desired.
6. Adjust tone and crop after you inspect the composite.

For example, an average followed by a soft-light pass and crop:

```sh
photostack average angle-1.jpg angle-2.jpg angle-3.jpg -o work/mean.jpg
photostack blend work/mean.jpg work/mean.jpg --mode softlight \
  --opacity 0.2 -o work/softlight.jpg
photostack crop work/softlight.jpg --geometry 2400x4200+500+300 \
  -o work/final.jpg
```

## What stays manual

Capture-time grouping cannot tell whether a subject rotated between frames or
whether the camera moved. You decide which frames represent separate angles,
what order to use, how much opacity to apply, and where to crop. If camera
position, focus, exposure, or white balance changed, inspect the output and
adjust or reject frames as needed. PhotoStack does not automatically align,
mask, retouch, or normalize images.

## Repeatable runs

Keep each stage in a separate directory (`previews`, `oriented`, `composites`,
and `final`) so you can review intermediate results and rerun a later command
without modifying source files. Use `--overwrite` only when intentionally
replacing a generated output.
