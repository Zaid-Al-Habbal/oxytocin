from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image
from reportlab.pdfgen import canvas
from io import BytesIO


def generate_test_image(
    mode: str = "RGB",
    name: str = "test_image.jpg",
    size: tuple[int, int] | list[int] = (100, 100),
    color: float | tuple[float, ...] | str = (255, 0, 0),
    image_format: str = "JPEG",
    content_type: str = "image/jpeg",
):
    """
    Create a simple in-memory image file for use in Django tests.

    This utility generates an image of the specified mode, dimensions, and fill color,
    saves it into a bytes buffer in the chosen format, and wraps it in a
    `SimpleUploadedFile` to simulate an uploaded image without touching the filesystem.

    Parameters
    ----------
    mode : str, optional
        The color mode for the new image (e.g., "RGB", "RGBA", "L"), by default "RGB".
    name : str, optional
        The filename to assign to the uploaded image (default is "test_image.jpg").
    size : tuple[int, int] or list[int], optional
        The (width, height) in pixels for the generated image (default is (100, 100)).
    color : float, tuple of floats, or str, optional
        The fill color for the image background. For an RGB image, a 3-tuple of ints
        or a CSS-style string is valid (default is red `(255, 0, 0)`).
    image_format : str, optional
        The file format to use when encoding the image (e.g., "JPEG", "PNG"), default "JPEG".
    content_type : str, optional
        The MIME type to set on the `SimpleUploadedFile` (default is "image/jpeg").

    Returns
    -------
    SimpleUploadedFile
        A Django `SimpleUploadedFile` containing the generated image bytes,
        suitable for use in form or view tests that accept file uploads.

    Example
    -------
    ```python
    # Generate a 50x50 blue PNG for testing a profile picture upload:
    avatar = generate_test_image(
        mode="RGB",
        name="avatar.png",
        size=(50, 50),
        color=(0, 0, 255),
        image_format="PNG",
        content_type="image/png"
    )
    ```
    """
    image = Image.new(mode, size, color=color)
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type=content_type)


def generate_test_pdf(
    name: str = "test.pdf",
    text: str = "This is a test PDF file.",
):
    """
    Generates a simple in-memory PDF file with the specified text content.

    Parameters:
        name (str): The name to assign to the generated PDF file (default is "test.pdf").
        text (str): The text to be written on the PDF (default is "This is a test PDF file.").

    Returns:
        SimpleUploadedFile: A Django-compatible in-memory uploaded file object containing the PDF,
                            suitable for use in tests or file upload simulations.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, text)
    c.save()
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="application/pdf")
