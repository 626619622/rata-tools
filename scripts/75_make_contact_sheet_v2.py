"""Create a final contact sheet using the corrected Figure 5."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures" / "paper1"
OUT = FIG / "ContactSheet_v2.png"

FIGURES = [
    ("Figure 1", FIG / "Figure1_evidence_capacity.png"),
    ("Figure 2", FIG / "Figure2_selection_gate.png"),
    ("Figure 3", FIG / "Figure3_transport_and_role_adjustment.png"),
    ("Figure 4", FIG / "Figure4_pituitary_positive_control.png"),
    ("Figure 5", FIG / "Figure5_invasion_and_operating_characteristics_v2.png"),
]


def main() -> None:
    thumb_w, thumb_h = 1000, 700
    margin = 40
    header_h = 52
    canvas = Image.new(
        "RGB",
        (2 * thumb_w + 3 * margin, 3 * (thumb_h + header_h) + 4 * margin),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=28)

    for index, (label, path) in enumerate(FIGURES):
        row, column = divmod(index, 2)
        x = margin + column * (thumb_w + margin)
        y = margin + row * (thumb_h + header_h + margin)
        draw.text((x, y), label, fill="black", font=font)
        with Image.open(path) as source:
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

    canvas.save(OUT, dpi=(180, 180))
    print(OUT)


if __name__ == "__main__":
    main()
