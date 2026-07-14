import sys

from PIL import Image, ImageDraw, ImageFont


def create_composite(foreground_path, background_path, output_path):
    # Load images
    fg = Image.open(foreground_path).convert("RGBA")
    bg = Image.open(background_path).convert("RGBA")

    # Convert foreground dark background (#0D1117) to transparent
    # D2 Theme 200 uses #0D1117 for background
    data = fg.getdata()
    new_data = []
    for item in data:
        # Check if pixel is close to #0D1117 (13, 17, 23)
        if abs(item[0] - 13) < 15 and abs(item[1] - 17) < 15 and abs(item[2] - 23) < 15:
            new_data.append((255, 255, 255, 0))  # Transparent
        else:
            new_data.append(item)
    fg.putdata(new_data)

    # Resize background to cover the foreground
    fg_ratio = fg.width / fg.height
    bg_ratio = bg.width / bg.height

    if bg_ratio > fg_ratio:
        # Background is wider, resize by height and crop width
        new_height = fg.height
        new_width = int(new_height * bg_ratio)
    else:
        # Background is taller, resize by width and crop height
        new_width = fg.width
        new_height = int(new_width / bg_ratio)

    bg = bg.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Center crop the background
    left = (bg.width - fg.width) // 2
    top = (bg.height - fg.height) // 2
    right = left + fg.width
    bottom = top + fg.height
    bg = bg.crop((left, top, right, bottom))

    # Composite: paste foreground onto background using alpha channel
    bg.paste(fg, (0, 0), fg)

    # Add deterministic watermark
    draw = ImageDraw.Draw(bg)
    watermark_text = "github.com/hitanshuac"

    # Try to load a generic font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = ImageFont.load_default()

    # Position in bottom right corner
    margin = 20

    # Use textbbox to get dimensions
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = bg.width - text_width - margin
    y = bg.height - text_height - margin

    # Draw subtle shadow then text
    draw.text((x + 2, y + 2), watermark_text, font=font, fill=(0, 0, 0, 150))
    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 200))

    # Save final output
    bg.save(output_path, "PNG")
    print(f"Successfully generated composite diagram at {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python composite_diagram.py <fg_path> <bg_path> <output_path>")
        sys.exit(1)

    create_composite(sys.argv[1], sys.argv[2], sys.argv[3])
