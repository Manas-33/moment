from moviepy import TextClip, ImageClip, VideoClip, CompositeVideoClip
from PIL import Image, ImageFilter, ImageFont, ImageDraw
import numpy
import math
import tempfile

text_cache = {}

class Character:
    def __init__(self, text, color=None):
        self.text = text
        self.color = color

    def set_color(self, color):
        self.color = color

class Word:
    def __init__(self, word, color=None):
        self.word = word
        self.color = color
        self.characters = []

        for char in word:
            self.characters.append(Character(char, color))

    def set_color(self, color):
        self.color = color
        for char in self.characters:
            char.set_color(color)

class TextClipEx(TextClip):
    def __init__(self, txt=None, fontsize=None, font=None, color="black",
                 bg_color="transparent", stroke_color=None, stroke_width=0,
                 kerning=None, method="label", align=None, **kwargs):
        # Translate the moviepy 1.x kwargs this project used to the 2.x TextClip API:
        # txt->text, fontsize->font_size, bg 'transparent'->None, drop kerning/align,
        # and only apply a stroke when a stroke color is given.
        if bg_color == "transparent":
            bg_color = None
        super().__init__(
            font=font,
            text=txt,
            font_size=fontsize,
            color=color,
            bg_color=bg_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width if stroke_color else 0,
            method="label",
        )
        self.text = txt

def moviepy_to_pillow(clip) -> Image:
    temp_file = tempfile.NamedTemporaryFile(suffix=".png").name
    clip.save_frame(temp_file)
    image = Image.open(temp_file)
    return image

def get_text_size(text, fontsize, font, stroke_width):
    text_clip = create_text(text, fontsize=fontsize, color="white", font=font, stroke_width=stroke_width)
    return text_clip.size

def get_text_size_ex(text, font, fontsize, stroke_width):
    text_clip = create_text_ex(text, fontsize=fontsize, color="white", font=font, stroke_width=stroke_width)
    return text_clip.size

def blur_text_clip(text_clip, blur_radius: int) -> VideoClip:
    # Convert TextClip to a PIL image
    pil_img = moviepy_to_pillow(text_clip)

    # Offset blur to make it centered
    offset = int(blur_radius * 0.6)

    # Add empty space around text for blur
    pil_img_padded = Image.new("RGBA", (pil_img.width + blur_radius * 3, pil_img.height + blur_radius * 3))
    pil_img_padded.paste(moviepy_to_pillow(text_clip), (blur_radius+offset, blur_radius+offset))

    # Create a blurred version of the text
    pil_img_padded = pil_img_padded.filter(
        ImageFilter.GaussianBlur(radius=blur_radius)
    )

    text_clip = ImageClip(numpy.array(pil_img_padded))
    text_clip = text_clip.with_duration(text_clip.duration)

    return text_clip

def create_text(
    text: str,
    fontsize: int,
    color: str,
    font: str,
    bg_color: str = 'transparent',
    blur_radius: int = 0,
    opacity: float = 1.0,
    stroke_color: str | None = None,
    stroke_width: int = 1,
    kerning: float = 0.0,
) -> VideoClip:
    global text_cache

    arg_hash = hash((text, fontsize, color, font, bg_color, blur_radius, opacity, stroke_color, stroke_width, kerning))

    if arg_hash in text_cache:
        return text_cache[arg_hash].copy()

    text_clip = TextClipEx(txt=text, fontsize=fontsize, color=color, bg_color=bg_color, font=font, stroke_color=stroke_color, stroke_width=stroke_width, kerning=kerning, method="caption", align="east")

    text_clip = text_clip.with_opacity(opacity)

    if blur_radius:
        text_clip = blur_text_clip(text_clip, blur_radius)

    text_cache[arg_hash] = text_clip.copy()

    return text_clip

def create_text_chars(
    text: list[Word] | list[Character],
    fontsize,
    color,
    font,
    bg_color = 'transparent',
    blur_radius: int = 0,
    opacity = 1,
    stroke_color = None,
    stroke_width = 1,
    add_space_between_words = True,
) -> list[VideoClip]:
    # Create a clip for each character
    clips = []
    for i, item in enumerate(text):
        if isinstance(item, Word):
            chars = item.characters
            if add_space_between_words and i < len(text) - 1:
                chars.append(Character(" ", item.color))
        else:
            chars = [item]

        for char in chars:
            clip = create_text(char.text, fontsize, char.color or color, font, bg_color, blur_radius, opacity, stroke_color, stroke_width)
            clips.append(clip)

    return clips

def create_composite_text(text_clips: list[VideoClip], font, font_size) -> CompositeVideoClip:
    clips = []

    font = ImageFont.truetype(font, font_size)
    scale_factor = 3.012 # factor to convert Pillow to MoviePy width

    full_width = 0
    for clip in text_clips[:-1]:
        width = font.getlength(clip.text) * scale_factor
        full_width += width

    full_width += text_clips[-1].size[0]
    offset_x = 0

    for clip in text_clips:
        clip.size = (int(full_width), clip.size[1])
        clip = clip.with_position((int(offset_x), 0))
        width = font.getlength(clip.text)
        offset_x += width * scale_factor
        clips.append(clip)

    return CompositeVideoClip(clips)

def str_to_charlist(text: str) -> list[Character]:
    return [Character(char) for char in text]

def _render_tokens_pil(
    tokens: list[tuple[str, str]],
    fontsize: int,
    font_path: str,
    stroke_color: str | None,
    stroke_width: int,
    opacity: float,
) -> ImageClip:
    """Draw a run of coloured tokens ("word", "#hex") onto one RGBA image.

    Every token is drawn into the same full em-box (ascent + descent) at a shared
    baseline, so the tops of tall glyphs are never clipped and words with and without
    descenders stay aligned. This replaces the old per-character MoviePy compositor,
    whose ``fontsize // 3`` / ``scale_factor`` width hack and clip-size mangling broke
    (clipped tops, overlapping glyphs) once the font was scaled below its 110px design.
    """
    pil_font = ImageFont.truetype(font_path, fontsize)
    ascent, descent = pil_font.getmetrics()
    pad = stroke_width + 2
    space_w = pil_font.getlength(" ")

    # Measure total width first.
    total_w = 0.0
    widths = []
    for i, (word, _c) in enumerate(tokens):
        w = pil_font.getlength(word)
        widths.append(w)
        total_w += w
        if i < len(tokens) - 1:
            total_w += space_w

    height = ascent + descent + pad * 2
    width = int(math.ceil(total_w)) + pad * 2
    img = Image.new("RGBA", (max(width, 1), max(height, 1)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    x = float(pad)
    for i, (word, col) in enumerate(tokens):
        draw.text(
            (x, pad),
            word,
            font=pil_font,
            fill=col,
            stroke_width=stroke_width if stroke_color else 0,
            stroke_fill=stroke_color,
        )
        x += widths[i] + (space_w if i < len(tokens) - 1 else 0)

    if opacity < 1:
        alpha = img.split()[3].point(lambda a: int(a * opacity))
        img.putalpha(alpha)

    return ImageClip(numpy.array(img))


def create_text_ex(
    text: list[Word] | list[Character] | str,
    fontsize,
    color,
    font,
    bg_color='transparent',
    blur_radius: int = 0,
    opacity = 1,
    stroke_color = None,
    stroke_width = 1,
    kerning = 0,
) -> VideoClip:
    # A plain string renders as a single clip: MoviePy's own text engine spaces and
    # baselines it correctly, so there is nothing to composite (used for shadows and
    # for line-size measurement).
    if isinstance(text, str):
        return create_text(text, fontsize, color, font, bg_color, blur_radius, opacity, stroke_color, stroke_width)

    # A list of Word/Character tokens: each may carry its own colour (for the karaoke
    # word highlight), so draw them as one baseline-aligned run.
    tokens: list[tuple[str, str]] = []
    for item in text:
        if isinstance(item, Word):
            tokens.append((item.word, item.color or color))
        elif isinstance(item, Character):
            tokens.append((item.text, item.color or color))
        else:
            tokens.append((str(item), color))

    clip = _render_tokens_pil(tokens, int(fontsize), font, stroke_color, int(stroke_width), opacity)
    if blur_radius:
        clip = blur_text_clip(clip, blur_radius)
    return clip
