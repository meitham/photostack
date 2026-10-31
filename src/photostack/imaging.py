"""Non-generative image operations backed by ExifTool and ImageMagick."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


class PhotoStackError(Exception):
    """An actionable error raised by a PhotoStack operation."""


_MODES = {
    'normal': 'Over',
    'multiply': 'Multiply',
    'screen': 'Screen',
    'overlay': 'Overlay',
    'softlight': 'SoftLight',
}

_RAW_EXTENSIONS = {
    '.arw',
    '.cr2',
    '.cr3',
    '.dng',
    '.nef',
    '.nrw',
    '.orf',
    '.pef',
    '.raf',
    '.rw2',
}


def _tool(name: str, environment_variable: str) -> str:
    candidate = os.environ.get(environment_variable, name)
    if Path(candidate).is_file():
        return candidate
    found = shutil.which(candidate)
    if found is None:
        raise PhotoStackError(
            f'Cannot find {candidate!r}. Install the required command-line tool '
            f'or set {environment_variable}.'
        )
    return found


def _run_text(args: list[str], *, tool_name: str) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise PhotoStackError(f'Could not run {tool_name}: {exc}') from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PhotoStackError(detail or f'{tool_name} exited with {result.returncode}')
    return result.stdout


def _run_bytes(args: list[str], *, tool_name: str) -> bytes:
    try:
        result = subprocess.run(args, capture_output=True, check=False)
    except OSError as exc:
        raise PhotoStackError(f'Could not run {tool_name}: {exc}') from exc
    if result.returncode:
        detail = result.stderr.decode(errors='replace').strip()
        raise PhotoStackError(detail or f'{tool_name} exited with {result.returncode}')
    return result.stdout


def _prepare_output(
    output: Path,
    *,
    overwrite: bool,
    sources: tuple[Path, ...] = (),
) -> Path:
    output = output.expanduser()
    if not output.suffix:
        raise PhotoStackError(f'Output needs a file extension: {output}')
    if any(output.resolve() == source.expanduser().resolve() for source in sources):
        raise PhotoStackError('Output must be a different file from every input.')
    if output.exists() and not overwrite:
        raise PhotoStackError(
            f'Output already exists: {output} (pass --overwrite to replace it).'
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _batch_output_paths(
    inputs: list[Path],
    output_dir: Path,
    *,
    suffix: str,
    extension: str | None,
    overwrite: bool,
) -> list[Path]:
    output_dir = output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for source in inputs:
        output_extension = source.suffix if extension is None else extension
        output = output_dir / f'{source.stem}{suffix}{output_extension}'
        _prepare_output(output, overwrite=overwrite, sources=(source,))
        outputs.append(output)
    if len(set(outputs)) != len(outputs):
        raise PhotoStackError('Input files produce duplicate output names.')
    return outputs


def extract_preview(source: Path, output: Path, *, overwrite: bool = False) -> Path:
    """Extract a camera-rendered JPEG preview from a RAW file."""
    source = source.expanduser()
    if not source.is_file():
        raise PhotoStackError(f'Input file does not exist: {source}')
    if source.suffix.lower() not in _RAW_EXTENSIONS:
        raise PhotoStackError(
            f'{source.name} is not a recognized RAW extension. '
            'Use preview for RAW files only.'
        )
    output = _prepare_output(output, overwrite=overwrite, sources=(source,))
    exiftool = _tool('exiftool', 'PHOTOSTACK_EXIFTOOL')

    payload = b''
    for tag in ('PreviewImage', 'JpgFromRaw', 'ThumbnailImage'):
        payload = _run_bytes(
            [exiftool, '-b', f'-{tag}', str(source)], tool_name='ExifTool'
        )
        if payload:
            break
    if not payload:
        raise PhotoStackError(
            f'No embedded preview was found in {source}. '
            'This command extracts an existing camera preview; it does not '
            'develop RAW sensor data.'
        )
    if not payload.startswith(b'\xff\xd8'):
        raise PhotoStackError(
            f'The preview extracted from {source.name} is not a JPEG image.'
        )

    output.write_bytes(payload)

    # The embedded JPEG may omit orientation metadata even when the RAW has it.
    orientation = _run_text(
        [exiftool, '-s3', '-Orientation', str(source)], tool_name='ExifTool'
    ).strip()
    if orientation:
        _run_text(
            [
                exiftool,
                '-overwrite_original',
                '-tagsFromFile',
                str(source),
                '-Orientation',
                str(output),
            ],
            tool_name='ExifTool',
        )
    return output


def extract_previews(
    sources: list[Path],
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> list[Path]:
    outputs = _batch_output_paths(
        sources,
        output_dir,
        suffix='',
        extension='.jpg',
        overwrite=overwrite,
    )
    return [
        extract_preview(source, output, overwrite=overwrite)
        for source, output in zip(sources, outputs, strict=True)
    ]


def orient_image(source: Path, output: Path, *, overwrite: bool = False) -> Path:
    """Apply EXIF orientation to pixels and write a new image."""
    source = source.expanduser()
    if not source.is_file():
        raise PhotoStackError(f'Input file does not exist: {source}')
    if source.suffix.lower() in _RAW_EXTENSIONS:
        raise PhotoStackError(
            f'{source.name} is a RAW file. Run preview first, then orient the '
            'extracted JPEG.'
        )
    output = _prepare_output(output, overwrite=overwrite, sources=(source,))
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')
    _run_text(
        [magick, str(source), '-auto-orient', '+repage', str(output)],
        tool_name='ImageMagick',
    )
    return output


def orient_images(
    sources: list[Path],
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> list[Path]:
    outputs = _batch_output_paths(
        sources,
        output_dir,
        suffix='',
        extension=None,
        overwrite=overwrite,
    )
    return [
        orient_image(source, output, overwrite=overwrite)
        for source, output in zip(sources, outputs, strict=True)
    ]


def _image_size(path: Path) -> tuple[int, int]:
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')
    result = _run_text(
        [magick, 'identify', '-format', '%w %h', str(path)],
        tool_name='ImageMagick',
    )
    try:
        width, height = result.split()
        return int(width), int(height)
    except (ValueError, TypeError) as exc:
        raise PhotoStackError(f'Could not read image dimensions for {path}.') from exc


def _opacity_percent(opacity: float) -> int:
    if not 0 <= opacity <= 1:
        raise PhotoStackError('Opacity must be between 0 and 1.')
    return int(opacity * 100 + 0.5)


def _blend_pair(
    base: Path,
    layer: Path,
    output: Path,
    *,
    mode: str,
    opacity: float,
    overwrite: bool,
) -> Path:
    base = base.expanduser()
    layer = layer.expanduser()
    if not base.is_file():
        raise PhotoStackError(f'Base image does not exist: {base}')
    if not layer.is_file():
        raise PhotoStackError(f'Layer image does not exist: {layer}')
    if mode not in _MODES:
        raise PhotoStackError(f'Unsupported blend mode: {mode}')
    if _image_size(base) != _image_size(layer):
        raise PhotoStackError(
            f'Image dimensions differ: {base.name} is {_image_size(base)}, '
            f'{layer.name} is {_image_size(layer)}. Orient, resize, or crop '
            'the inputs to matching dimensions first.'
        )
    output = _prepare_output(output, overwrite=overwrite, sources=(base, layer))
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')
    source_percent = _opacity_percent(opacity)
    destination_percent = 100 - source_percent

    with tempfile.TemporaryDirectory(prefix='photostack-') as temp_dir:
        mode_result = Path(temp_dir) / 'mode-result.miff'
        _run_text(
            [
                magick,
                str(base),
                str(layer),
                '-compose',
                _MODES[mode],
                '-composite',
                str(mode_result),
            ],
            tool_name='ImageMagick',
        )
        _run_text(
            [
                magick,
                str(base),
                str(mode_result),
                '-compose',
                'blend',
                '-define',
                f'compose:args={source_percent},{destination_percent}',
                '-composite',
                str(output),
            ],
            tool_name='ImageMagick',
        )
    return output


def blend_images(
    base: Path,
    layer: Path,
    output: Path,
    *,
    mode: str = 'overlay',
    opacity: float = 0.2,
    overwrite: bool = False,
) -> Path:
    """Blend one layer over a base at the requested opacity."""
    return _blend_pair(
        base,
        layer,
        output,
        mode=mode,
        opacity=opacity,
        overwrite=overwrite,
    )


def stack_images(
    sources: list[Path],
    output: Path,
    *,
    mode: str = 'overlay',
    opacity: float = 0.2,
    overwrite: bool = False,
) -> Path:
    """Apply each image after the first as a sequential blend layer."""
    if len(sources) < 2:
        raise PhotoStackError('stack needs at least two input images.')
    output = _prepare_output(output, overwrite=overwrite, sources=tuple(sources))
    if mode not in _MODES:
        raise PhotoStackError(f'Unsupported blend mode: {mode}')
    _opacity_percent(opacity)
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')

    with tempfile.TemporaryDirectory(prefix='photostack-') as temp_dir:
        current = Path(temp_dir) / 'current.miff'
        _run_text(
            [magick, str(sources[0]), str(current)],
            tool_name='ImageMagick',
        )
        for index, layer in enumerate(sources[1:], start=1):
            next_image = Path(temp_dir) / f'layer-{index:04d}.miff'
            _blend_pair(
                current,
                layer,
                next_image,
                mode=mode,
                opacity=opacity,
                overwrite=False,
            )
            current = next_image
        _run_text(
            [magick, str(current), str(output)],
            tool_name='ImageMagick',
        )
    return output


def average_images(
    sources: list[Path], output: Path, *, overwrite: bool = False
) -> Path:
    """Average all input frames with equal weight."""
    if len(sources) < 2:
        raise PhotoStackError('average needs at least two input images.')
    dimensions = {_image_size(path) for path in sources}
    if len(dimensions) != 1:
        raise PhotoStackError(
            'All images must have matching dimensions before averaging.'
        )
    output = _prepare_output(output, overwrite=overwrite, sources=tuple(sources))
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')
    _run_text(
        [
            magick,
            *(str(source) for source in sources),
            '-evaluate-sequence',
            'mean',
            str(output),
        ],
        tool_name='ImageMagick',
    )
    return output


def tone_image(
    source: Path,
    output: Path,
    *,
    gamma: float,
    overwrite: bool = False,
) -> Path:
    if gamma <= 0:
        raise PhotoStackError('Gamma must be greater than zero.')
    source = source.expanduser()
    output = _prepare_output(output, overwrite=overwrite, sources=(source,))
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')
    _run_text(
        [magick, str(source), '-gamma', str(gamma), str(output)],
        tool_name='ImageMagick',
    )
    return output


def crop_image(
    source: Path,
    output: Path,
    *,
    geometry: str,
    overwrite: bool = False,
) -> Path:
    source = source.expanduser()
    output = _prepare_output(output, overwrite=overwrite, sources=(source,))
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')
    _run_text(
        [
            magick,
            str(source),
            '-crop',
            geometry,
            '+repage',
            str(output),
        ],
        tool_name='ImageMagick',
    )
    return output


def make_contact_sheet(
    sources: list[Path],
    output: Path,
    *,
    columns: int = 4,
    cell_size: str = '360x520',
    font: str = 'DejaVu-Sans',
    overwrite: bool = False,
) -> Path:
    if not sources:
        raise PhotoStackError('sheet needs at least one input image.')
    if columns < 1:
        raise PhotoStackError('columns must be a positive integer.')
    output = _prepare_output(output, overwrite=overwrite, sources=tuple(sources))
    magick = _tool('magick', 'PHOTOSTACK_MAGICK')
    _run_text(
        [
            magick,
            'montage',
            *(str(source) for source in sources),
            '-font',
            font,
            '-set',
            'label',
            '%f',
            '-thumbnail',
            cell_size,
            '-tile',
            f'{columns}x',
            '-geometry',
            '+8+24',
            '-background',
            'white',
            str(output),
        ],
        tool_name='ImageMagick',
    )
    return output


def _capture_datetime(value: str) -> datetime:
    for format_string in ('%Y:%m:%d %H:%M:%S', '%Y:%m:%d %H:%M:%S.%f'):
        try:
            return datetime.strptime(value, format_string)
        except ValueError:
            continue
    raise ValueError(f'unsupported capture timestamp: {value}')


def group_by_capture_gap(
    sources: list[Path],
    *,
    gap_seconds: float = 60,
) -> dict[str, Any]:
    """Group files by capture-time gaps; subject/angle review stays manual."""
    if gap_seconds <= 0:
        raise PhotoStackError('gap-seconds must be greater than zero.')
    exiftool = _tool('exiftool', 'PHOTOSTACK_EXIFTOOL')
    result = _run_text(
        [
            exiftool,
            '-json',
            '-FileName',
            '-DateTimeOriginal',
            *(str(source) for source in sources),
        ],
        tool_name='ExifTool',
    )
    try:
        metadata = json.loads(result)
    except json.JSONDecodeError as exc:
        raise PhotoStackError('ExifTool returned invalid JSON metadata.') from exc

    records: list[tuple[datetime, str]] = []
    ungrouped: list[str] = []
    for item in metadata:
        filename = item.get('SourceFile') or item.get('FileName')
        captured = item.get('DateTimeOriginal')
        if not filename or not captured:
            if filename:
                ungrouped.append(filename)
            continue
        try:
            records.append((_capture_datetime(captured), filename))
        except ValueError:
            ungrouped.append(filename)

    records.sort(key=lambda record: (record[0], record[1]))
    groups: list[dict[str, Any]] = []
    for captured, filename in records:
        if (
            not groups
            or (captured - groups[-1]['_end']).total_seconds() > gap_seconds
        ):
            groups.append(
                {
                    'sequence': f'{len(groups) + 1:03d}',
                    'start': captured.isoformat(sep=' '),
                    'end': captured.isoformat(sep=' '),
                    'files': [filename],
                    '_end': captured,
                }
            )
        else:
            groups[-1]['files'].append(filename)
            groups[-1]['end'] = captured.isoformat(sep=' ')
            groups[-1]['_end'] = captured

    for group in groups:
        group['count'] = len(group['files'])
        del group['_end']
    return {'groups': groups, 'ungrouped': sorted(ungrouped)}


def write_groups(
    sources: list[Path],
    output: Path | None,
    *,
    gap_seconds: float = 60,
    overwrite: bool = False,
) -> str:
    result = group_by_capture_gap(sources, gap_seconds=gap_seconds)
    payload = json.dumps(result, indent=2) + '\n'
    if output is None:
        return payload
    output = _prepare_output(output, overwrite=overwrite, sources=tuple(sources))
    output.write_text(payload, encoding='utf-8')
    return str(output)
