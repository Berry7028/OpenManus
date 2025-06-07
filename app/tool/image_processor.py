"""
Image Processor Tool for handling image operations.
"""

import os
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import requests
from typing import Optional, Tuple
from pathlib import Path

from app.tool.base import BaseTool, ToolResult


class ImageProcessor(BaseTool):
    """Tool for processing, analyzing, and manipulating images."""

    name: str = "image_processor"
    description: str = """Process, analyze, and manipulate images.

    Available commands:
    - resize: Resize image to specified dimensions
    - crop: Crop image to specified area
    - rotate: Rotate image by specified angle
    - enhance: Enhance image (brightness, contrast, saturation)
    - filter: Apply filters (blur, sharpen, edge enhance)
    - convert: Convert image format
    - info: Get image information
    - thumbnail: Create thumbnail
    - watermark: Add text watermark
    - download: Download image from URL
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["resize", "crop", "rotate", "enhance", "filter", "convert", "info", "thumbnail", "watermark", "download"],
                "type": "string",
            },
            "image_path": {
                "description": "Path to input image file.",
                "type": "string",
            },
            "output_path": {
                "description": "Path for output image file.",
                "type": "string",
            },
            "width": {
                "description": "Width for resize/crop operations.",
                "type": "integer",
            },
            "height": {
                "description": "Height for resize/crop operations.",
                "type": "integer",
            },
            "x": {
                "description": "X coordinate for crop operation.",
                "type": "integer",
            },
            "y": {
                "description": "Y coordinate for crop operation.",
                "type": "integer",
            },
            "angle": {
                "description": "Rotation angle in degrees.",
                "type": "number",
            },
            "enhancement_type": {
                "description": "Enhancement type (brightness, contrast, saturation, sharpness).",
                "type": "string",
            },
            "enhancement_factor": {
                "description": "Enhancement factor (1.0 = no change).",
                "type": "number",
            },
            "filter_type": {
                "description": "Filter type (blur, sharpen, edge_enhance, emboss).",
                "type": "string",
            },
            "format": {
                "description": "Output image format (JPEG, PNG, GIF, BMP).",
                "type": "string",
            },
            "quality": {
                "description": "JPEG quality (1-100).",
                "type": "integer",
            },
            "watermark_text": {
                "description": "Text for watermark.",
                "type": "string",
            },
            "url": {
                "description": "URL to download image from.",
                "type": "string",
            },
            "maintain_aspect": {
                "description": "Maintain aspect ratio when resizing.",
                "type": "boolean",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        image_path: Optional[str] = None,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        angle: Optional[float] = None,
        enhancement_type: Optional[str] = None,
        enhancement_factor: Optional[float] = None,
        filter_type: Optional[str] = None,
        format: Optional[str] = None,
        quality: Optional[int] = None,
        watermark_text: Optional[str] = None,
        url: Optional[str] = None,
        maintain_aspect: bool = True,
        **kwargs
    ) -> ToolResult:
        """Execute image processor command."""
        try:
            if command == "resize":
                return self._resize_image(image_path, output_path, width, height, maintain_aspect)
            elif command == "crop":
                return self._crop_image(image_path, output_path, x, y, width, height)
            elif command == "rotate":
                return self._rotate_image(image_path, output_path, angle)
            elif command == "enhance":
                return self._enhance_image(image_path, output_path, enhancement_type, enhancement_factor)
            elif command == "filter":
                return self._filter_image(image_path, output_path, filter_type)
            elif command == "convert":
                return self._convert_image(image_path, output_path, format, quality)
            elif command == "info":
                return self._get_image_info(image_path)
            elif command == "thumbnail":
                return self._create_thumbnail(image_path, output_path, width, height)
            elif command == "watermark":
                return self._add_watermark(image_path, output_path, watermark_text)
            elif command == "download":
                return self._download_image(url, output_path)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing image processor command '{command}': {str(e)}")

    def _resize_image(self, image_path: Optional[str], output_path: Optional[str],
                     width: Optional[int], height: Optional[int], maintain_aspect: bool) -> ToolResult:
        """Resize image to specified dimensions."""
        if not image_path or not width or not height:
            return ToolResult(error="image_path, width, and height are required")

        try:
            with Image.open(image_path) as img:
                if maintain_aspect:
                    img.thumbnail((width, height), Image.Resampling.LANCZOS)
                    resized_img = img
                else:
                    resized_img = img.resize((width, height), Image.Resampling.LANCZOS)

                if output_path:
                    resized_img.save(output_path)
                    return ToolResult(output=f"Image resized and saved to: {output_path}\n"
                                            f"New size: {resized_img.size}")
                else:
                    output_path = image_path.replace('.', '_resized.')
                    resized_img.save(output_path)
                    return ToolResult(output=f"Image resized and saved to: {output_path}\n"
                                            f"New size: {resized_img.size}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error resizing image: {str(e)}")

    def _crop_image(self, image_path: Optional[str], output_path: Optional[str],
                   x: Optional[int], y: Optional[int], width: Optional[int], height: Optional[int]) -> ToolResult:
        """Crop image to specified area."""
        if not image_path or x is None or y is None or not width or not height:
            return ToolResult(error="image_path, x, y, width, and height are required")

        try:
            with Image.open(image_path) as img:
                box = (x, y, x + width, y + height)
                cropped_img = img.crop(box)

                if output_path:
                    cropped_img.save(output_path)
                    return ToolResult(output=f"Image cropped and saved to: {output_path}\n"
                                            f"Crop area: {box}\n"
                                            f"New size: {cropped_img.size}")
                else:
                    output_path = image_path.replace('.', '_cropped.')
                    cropped_img.save(output_path)
                    return ToolResult(output=f"Image cropped and saved to: {output_path}\n"
                                            f"Crop area: {box}\n"
                                            f"New size: {cropped_img.size}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error cropping image: {str(e)}")

    def _rotate_image(self, image_path: Optional[str], output_path: Optional[str], angle: Optional[float]) -> ToolResult:
        """Rotate image by specified angle."""
        if not image_path or angle is None:
            return ToolResult(error="image_path and angle are required")

        try:
            with Image.open(image_path) as img:
                rotated_img = img.rotate(angle, expand=True)

                if output_path:
                    rotated_img.save(output_path)
                    return ToolResult(output=f"Image rotated by {angle}° and saved to: {output_path}")
                else:
                    output_path = image_path.replace('.', f'_rotated_{angle}.')
                    rotated_img.save(output_path)
                    return ToolResult(output=f"Image rotated by {angle}° and saved to: {output_path}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error rotating image: {str(e)}")

    def _enhance_image(self, image_path: Optional[str], output_path: Optional[str],
                      enhancement_type: Optional[str], enhancement_factor: Optional[float]) -> ToolResult:
        """Enhance image (brightness, contrast, saturation, sharpness)."""
        if not image_path or not enhancement_type or enhancement_factor is None:
            return ToolResult(error="image_path, enhancement_type, and enhancement_factor are required")

        try:
            with Image.open(image_path) as img:
                if enhancement_type.lower() == "brightness":
                    enhancer = ImageEnhance.Brightness(img)
                elif enhancement_type.lower() == "contrast":
                    enhancer = ImageEnhance.Contrast(img)
                elif enhancement_type.lower() == "saturation":
                    enhancer = ImageEnhance.Color(img)
                elif enhancement_type.lower() == "sharpness":
                    enhancer = ImageEnhance.Sharpness(img)
                else:
                    return ToolResult(error=f"Unknown enhancement type: {enhancement_type}")

                enhanced_img = enhancer.enhance(enhancement_factor)

                if output_path:
                    enhanced_img.save(output_path)
                    return ToolResult(output=f"Image enhanced ({enhancement_type}: {enhancement_factor}) and saved to: {output_path}")
                else:
                    output_path = image_path.replace('.', f'_enhanced_{enhancement_type}.')
                    enhanced_img.save(output_path)
                    return ToolResult(output=f"Image enhanced ({enhancement_type}: {enhancement_factor}) and saved to: {output_path}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error enhancing image: {str(e)}")

    def _filter_image(self, image_path: Optional[str], output_path: Optional[str], filter_type: Optional[str]) -> ToolResult:
        """Apply filters to image."""
        if not image_path or not filter_type:
            return ToolResult(error="image_path and filter_type are required")

        try:
            with Image.open(image_path) as img:
                if filter_type.lower() == "blur":
                    filtered_img = img.filter(ImageFilter.BLUR)
                elif filter_type.lower() == "sharpen":
                    filtered_img = img.filter(ImageFilter.SHARPEN)
                elif filter_type.lower() == "edge_enhance":
                    filtered_img = img.filter(ImageFilter.EDGE_ENHANCE)
                elif filter_type.lower() == "emboss":
                    filtered_img = img.filter(ImageFilter.EMBOSS)
                elif filter_type.lower() == "smooth":
                    filtered_img = img.filter(ImageFilter.SMOOTH)
                elif filter_type.lower() == "detail":
                    filtered_img = img.filter(ImageFilter.DETAIL)
                else:
                    return ToolResult(error=f"Unknown filter type: {filter_type}")

                if output_path:
                    filtered_img.save(output_path)
                    return ToolResult(output=f"Filter '{filter_type}' applied and saved to: {output_path}")
                else:
                    output_path = image_path.replace('.', f'_filtered_{filter_type}.')
                    filtered_img.save(output_path)
                    return ToolResult(output=f"Filter '{filter_type}' applied and saved to: {output_path}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error applying filter: {str(e)}")

    def _convert_image(self, image_path: Optional[str], output_path: Optional[str],
                      format: Optional[str], quality: Optional[int]) -> ToolResult:
        """Convert image format."""
        if not image_path or not format:
            return ToolResult(error="image_path and format are required")

        try:
            with Image.open(image_path) as img:
                # Convert RGBA to RGB for JPEG
                if format.upper() == "JPEG" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                if not output_path:
                    base_name = Path(image_path).stem
                    output_path = f"{base_name}.{format.lower()}"

                save_kwargs = {}
                if format.upper() == "JPEG" and quality:
                    save_kwargs["quality"] = quality

                img.save(output_path, format=format.upper(), **save_kwargs)
                return ToolResult(output=f"Image converted to {format.upper()} and saved to: {output_path}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error converting image: {str(e)}")

    def _get_image_info(self, image_path: Optional[str]) -> ToolResult:
        """Get image information."""
        if not image_path:
            return ToolResult(error="image_path is required")

        try:
            with Image.open(image_path) as img:
                info = {
                    "filename": os.path.basename(image_path),
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                }

                # Get file size
                file_size = os.path.getsize(image_path)
                info["file_size"] = f"{file_size:,} bytes ({file_size / 1024:.1f} KB)"

                # Get additional info if available
                if hasattr(img, 'info') and img.info:
                    info["additional_info"] = img.info

                output = "Image Information:\n"
                output += "=" * 30 + "\n"
                for key, value in info.items():
                    if key != "additional_info":
                        output += f"{key.replace('_', ' ').title()}: {value}\n"

                if "additional_info" in info:
                    output += "\nAdditional Info:\n"
                    for key, value in info["additional_info"].items():
                        output += f"  {key}: {value}\n"

                return ToolResult(output=output)
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error getting image info: {str(e)}")

    def _create_thumbnail(self, image_path: Optional[str], output_path: Optional[str],
                         width: Optional[int], height: Optional[int]) -> ToolResult:
        """Create thumbnail."""
        if not image_path:
            return ToolResult(error="image_path is required")

        # Default thumbnail size
        thumb_width = width or 128
        thumb_height = height or 128

        try:
            with Image.open(image_path) as img:
                img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)

                if not output_path:
                    base_name = Path(image_path).stem
                    ext = Path(image_path).suffix
                    output_path = f"{base_name}_thumb{ext}"

                img.save(output_path)
                return ToolResult(output=f"Thumbnail created and saved to: {output_path}\n"
                                        f"Thumbnail size: {img.size}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error creating thumbnail: {str(e)}")

    def _add_watermark(self, image_path: Optional[str], output_path: Optional[str], watermark_text: Optional[str]) -> ToolResult:
        """Add text watermark to image."""
        if not image_path or not watermark_text:
            return ToolResult(error="image_path and watermark_text are required")

        try:
            with Image.open(image_path) as img:
                # Create a copy to work with
                watermarked = img.copy()
                draw = ImageDraw.Draw(watermarked)

                # Calculate font size based on image size
                font_size = max(20, min(img.width, img.height) // 20)

                try:
                    # Try to use a default font
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    # Fall back to default font
                    font = ImageFont.load_default()

                # Get text size
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Position watermark at bottom right
                x = img.width - text_width - 10
                y = img.height - text_height - 10

                # Add semi-transparent background
                draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill=(0, 0, 0, 128))

                # Add text
                draw.text((x, y), watermark_text, fill=(255, 255, 255, 255), font=font)

                if not output_path:
                    base_name = Path(image_path).stem
                    ext = Path(image_path).suffix
                    output_path = f"{base_name}_watermarked{ext}"

                watermarked.save(output_path)
                return ToolResult(output=f"Watermark added and saved to: {output_path}")
        except FileNotFoundError:
            return ToolResult(error=f"Image file not found: {image_path}")
        except Exception as e:
            return ToolResult(error=f"Error adding watermark: {str(e)}")

    def _download_image(self, url: Optional[str], output_path: Optional[str]) -> ToolResult:
        """Download image from URL."""
        if not url:
            return ToolResult(error="url is required")

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            if not output_path:
                # Try to get filename from URL
                filename = url.split('/')[-1]
                if '.' not in filename:
                    filename = "downloaded_image.jpg"
                output_path = filename

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify it's a valid image
            with Image.open(output_path) as img:
                img_info = f"Format: {img.format}, Size: {img.size}, Mode: {img.mode}"

            return ToolResult(output=f"Image downloaded successfully to: {output_path}\n{img_info}")
        except requests.RequestException as e:
            return ToolResult(error=f"Error downloading image: {str(e)}")
        except Exception as e:
            return ToolResult(error=f"Error processing downloaded image: {str(e)}")
