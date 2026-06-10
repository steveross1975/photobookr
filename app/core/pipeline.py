import os

import cv2
import numpy as np


def _white_balance(img):
    """Gray world assumption: neutralizza i cast di colore."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    avg_a = np.mean(lab[:, :, 1])
    avg_b = np.mean(lab[:, :, 2])
    lab[:, :, 1] -= (avg_a - 128) * (lab[:, :, 0] / 255.0) * 1.1
    lab[:, :, 2] -= (avg_b - 128) * (lab[:, :, 0] / 255.0) * 1.1
    lab = np.clip(lab, 0, 255).astype(np.uint8)
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _auto_contrast(img):
    """CLAHE sul canale L (LAB): migliora il contrasto locale senza bruciare le alte luci."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _denoise(img):
    """Non-local means: riduce il rumore preservando i bordi."""
    return cv2.fastNlMeansDenoisingColored(img, None, h=10, hColor=10,
                                           templateWindowSize=7, searchWindowSize=21)


def _sharpen(img):
    """Unsharp mask: aumenta la nitidezza per la stampa."""
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=3)
    return cv2.addWeighted(img, 1.5, blurred, -0.5, 0)


def enhance_photo(original_path, optimized_path):
    """
    Pipeline completa di ottimizzazione per la stampa.
    Salva il risultato in optimized_path e restituisce il path.
    """
    img = cv2.imread(original_path)
    if img is None:
        raise ValueError(f"Impossibile leggere l'immagine: {original_path}")

    img = _white_balance(img)
    img = _auto_contrast(img)
    img = _denoise(img)
    img = _sharpen(img)

    os.makedirs(os.path.dirname(optimized_path), exist_ok=True)
    cv2.imwrite(optimized_path, img)
    return optimized_path
