"""Assemble final figure set with the corrected architecture panel."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figures" / "paper1"
BIO_V2 = ROOT / "figures" / "bioinformatics_v2"
OUT = ROOT / "figures" / "bioinformatics_final_v2"
OUT.mkdir(parents=True, exist_ok=True)

FIGURES = [
    (
        BIO_V2 / "Figure1_software_architecture.pdf",
        BIO_V2 / "Figure1_software_architecture.png",
        "Figure1",
    ),
    (SOURCE / "Figure1_evidence_capacity.pdf", SOURCE / "Figure1_evidence_capacity.png", "Figure2"),
    (SOURCE / "Figure2_selection_gate.pdf", SOURCE / "Figure2_selection_gate.png", "Figure3"),
    (
        SOURCE / "Figure3_transport_and_role_adjustment.pdf",
        SOURCE / "Figure3_transport_and_role_adjustment.png",
        "Figure4",
    ),
    (
        SOURCE / "Figure4_pituitary_positive_control.pdf",
        SOURCE / "Figure4_pituitary_positive_control.png",
        "Figure5",
    ),
    (
        SOURCE / "Figure5_invasion_and_operating_characteristics_v2.pdf",
        SOURCE / "Figure5_invasion_and_operating_characteristics_v2.png",
        "Figure6",
    ),
]


def main() -> None:
    for pdf, png, stem in FIGURES:
        shutil.copy2(pdf, OUT / f"{stem}.pdf")
        shutil.copy2(png, OUT / f"{stem}.png")

    thumb_w, thumb_h = 940, 650
    margin = 36
    header_h = 46
    canvas = Image.new(
        "RGB",
        (2 * thumb_w + 3 * margin, 3 * (thumb_h + header_h) + 4 * margin),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=26)
    for index, (_, png, stem) in enumerate(FIGURES):
        row, column = divmod(index, 2)
        x = margin + column * (thumb_w + margin)
        y = margin + row * (thumb_h + header_h + margin)
        draw.text((x, y), stem, fill="black", font=font)
        with Image.open(png) as source:
            image = source.convert("RGB")
            image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            image_x = x + (thumb_w - image.width) // 2
            image_y = y + header_h + (thumb_h - image.height) // 2
            canvas.paste(image, (image_x, image_y))
            draw.rectangle(
                [x, y + header_h, x + thumb_w, y + header_h + thumb_h],
                outline=(210, 210, 210),
                width=2,
            )
    canvas.save(OUT / "Figure_ContactSheet.png", dpi=(180, 180))
    print(OUT / "Figure_ContactSheet.png")


if __name__ == "__main__":
    main()
