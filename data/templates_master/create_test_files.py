import os

from PIL import Image


def create_test_images():
    # Dimensioni A3 a 72 DPI per il test (veloce e leggero)
    # 1191 x 842 pixel
    size = (1191, 842)
    
    # Crea la Cover (Rossa)
    cover = Image.new('RGB', size, color=(200, 50, 50))
    cover.save('test_cover.jpg')
    print("Creato: test_cover.jpg")
    
    # Crea l'Interno (Blu)
    inner = Image.new('RGB', size, color=(50, 50, 200))
    inner.save('test_inner.jpg')
    print("Creato: test_inner.jpg")

if __name__ == "__main__":
    create_test_images()
if __name__ == "__main__":
    create_test_images()
