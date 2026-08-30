# -*- coding: utf-8 -*-
import os
import sys
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import ddddocr

MIN_TEXT_LENGTH = 3

ocr_fast = ddddocr.DdddOcr(show_ad=False)

try:
    ocr_beta = ddddocr.DdddOcr(show_ad=False, beta=True)
except Exception:
    ocr_beta = None

def preprocess_ultrafast(image):
    image = image.convert("L")
    if image.width < 100:
        image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    return ImageEnhance.Contrast(image).enhance(2.0)

def preprocess_fast(image):
    image = image.convert("L")
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    return ImageEnhance.Contrast(image).enhance(2.5)

def preprocess_aggressive(image):
    image = image.convert("L")
    image = image.resize((image.width * 3, image.height * 3), Image.LANCZOS)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = ImageEnhance.Contrast(image).enhance(3.5)
    image = ImageEnhance.Sharpness(image).enhance(2.0)
    return ImageOps.autocontrast(image)

def clean_text(text):
    return "".join(str(text).split())

def calculate_confidence(text, attempts, processing_time):
    score = 60
    if 4 <= len(text) <= 8:
        score += 15
    if text.isalnum():
        score += 15
    if attempts == 1 and processing_time < 0.2:
        score += 10
    return min(score, 99)

def solve_image(image_path):
    start_time = time.time()
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(image_path)
    result_text = ""
    attempts = 0

    if image.width >= 150:
        processed = preprocess_ultrafast(image)
        result_text = clean_text(ocr_fast.classification(processed))
        attempts = 1

    if len(result_text) < MIN_TEXT_LENGTH:
        processed = preprocess_fast(image)
        result_text = clean_text(ocr_fast.classification(processed))
        attempts = 2

    if len(result_text) < MIN_TEXT_LENGTH:
        processed = preprocess_aggressive(image)
        result_text = clean_text(ocr_fast.classification(processed))
        attempts = 3

        if len(result_text) < MIN_TEXT_LENGTH and ocr_beta:
            beta_text = clean_text(ocr_beta.classification(processed))
            if len(beta_text) > len(result_text):
                result_text = beta_text

    processing_time = round(time.time() - start_time, 3)
    confidence = calculate_confidence(result_text, attempts, processing_time)

    print("\n" + "=" * 60)
    print(f"OCR RESULT : {result_text or '(nothing detected)'}")
    print(f"CONFIDENCE : {confidence}% (heuristic)")
    print(f"ATTEMPTS   : {attempts}")
    print(f"TIME       : {processing_time}s")
    print("=" * 60)

    return result_text

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        image_path = " ".join(sys.argv[1:])
        try:
            solve_image(image_path)
        except Exception as e:
            print(f"ERROR: {e}")