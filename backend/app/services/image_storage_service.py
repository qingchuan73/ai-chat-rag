import base64
import os
import uuid


GENERATED_IMAGE_DIR = os.getenv(
    "GENERATED_IMAGE_DIR",
    os.path.join(os.getcwd(), "generated_images")
)


def save_generated_image(image_data: str) -> str:
    if not image_data.startswith("data:image/"):
        return image_data

    header, encoded = image_data.split(",", 1)
    extension = "png"

    if "image/jpeg" in header or "image/jpg" in header:
        extension = "jpg"
    elif "image/webp" in header:
        extension = "webp"

    os.makedirs(GENERATED_IMAGE_DIR, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{extension}"
    filepath = os.path.join(GENERATED_IMAGE_DIR, filename)

    with open(filepath, "wb") as file:
        file.write(base64.b64decode(encoded))

    return f"/api/generated-images/{filename}"
