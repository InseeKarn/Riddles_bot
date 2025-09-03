from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("src/fonts/bold_font.ttf", 80)
img = Image.new("RGB", (500, 200), (30, 30, 30))
draw = ImageDraw.Draw(img)
draw.text((10, 50), "🤔 Hello 🤔", font=font, fill="white")
img.show()