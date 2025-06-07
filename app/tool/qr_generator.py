"""
QR Code Generator Tool for creating QR codes.
"""

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer
from qrcode.image.styles.colorfills import SolidFillColorMask
from PIL import Image
import io
import base64
from typing import Optional

from app.tool.base import BaseTool, ToolResult


class QrGenerator(BaseTool):
    """Tool for generating QR codes with various customization options."""

    name: str = "qr_generator"
    description: str = """Generate QR codes with customization options.

    Available commands:
    - generate: Generate basic QR code
    - generate_styled: Generate styled QR code with colors and shapes
    - generate_logo: Generate QR code with logo in center
    - batch_generate: Generate multiple QR codes
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["generate", "generate_styled", "generate_logo", "batch_generate"],
                "type": "string",
            },
            "data": {
                "description": "Data to encode in QR code.",
                "type": "string",
            },
            "output_path": {
                "description": "Output file path for QR code image.",
                "type": "string",
            },
            "size": {
                "description": "Size of QR code (default: 10).",
                "type": "integer",
            },
            "border": {
                "description": "Border size (default: 4).",
                "type": "integer",
            },
            "error_correction": {
                "description": "Error correction level (L, M, Q, H).",
                "type": "string",
            },
            "fill_color": {
                "description": "Fill color (default: black).",
                "type": "string",
            },
            "back_color": {
                "description": "Background color (default: white).",
                "type": "string",
            },
            "module_drawer": {
                "description": "Module drawer style (square, circle, rounded).",
                "type": "string",
            },
            "logo_path": {
                "description": "Path to logo image for center.",
                "type": "string",
            },
            "data_list": {
                "description": "Comma-separated list of data for batch generation.",
                "type": "string",
            },
            "format": {
                "description": "Output format (PNG, JPEG, SVG).",
                "type": "string",
            },
        },
        "required": ["command", "data"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        data: str,
        output_path: Optional[str] = None,
        size: int = 10,
        border: int = 4,
        error_correction: str = "M",
        fill_color: str = "black",
        back_color: str = "white",
        module_drawer: str = "square",
        logo_path: Optional[str] = None,
        data_list: Optional[str] = None,
        format: str = "PNG",
        **kwargs
    ) -> ToolResult:
        """Execute QR generator command."""
        try:
            if command == "generate":
                return self._generate_qr(data, output_path, size, border, error_correction, fill_color, back_color, format)
            elif command == "generate_styled":
                return self._generate_styled_qr(data, output_path, size, border, error_correction,
                                              fill_color, back_color, module_drawer, format)
            elif command == "generate_logo":
                return self._generate_qr_with_logo(data, output_path, logo_path, size, border,
                                                 error_correction, fill_color, back_color, format)
            elif command == "batch_generate":
                return self._batch_generate_qr(data_list or data, size, border, error_correction,
                                             fill_color, back_color, format)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing QR generator command '{command}': {str(e)}")

    def _get_error_correction(self, level: str):
        """Get error correction level."""
        levels = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H,
        }
        return levels.get(level.upper(), qrcode.constants.ERROR_CORRECT_M)

    def _get_module_drawer(self, drawer_type: str):
        """Get module drawer style."""
        drawers = {
            "square": SquareModuleDrawer(),
            "circle": CircleModuleDrawer(),
            "rounded": RoundedModuleDrawer(),
        }
        return drawers.get(drawer_type.lower(), SquareModuleDrawer())

    def _generate_qr(self, data: str, output_path: Optional[str], size: int, border: int,
                    error_correction: str, fill_color: str, back_color: str, format: str) -> ToolResult:
        """Generate basic QR code."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=self._get_error_correction(error_correction),
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color=fill_color, back_color=back_color)

            if not output_path:
                output_path = f"qrcode.{format.lower()}"

            if format.upper() == "SVG":
                # For SVG, we need to use a different factory
                from qrcode.image.svg import SvgPathImage
                qr_svg = qrcode.QRCode(
                    version=1,
                    error_correction=self._get_error_correction(error_correction),
                    box_size=size,
                    border=border,
                    image_factory=SvgPathImage
                )
                qr_svg.add_data(data)
                qr_svg.make(fit=True)
                img_svg = qr_svg.make_image()
                img_svg.save(output_path)
            else:
                img.save(output_path, format=format.upper())

            return ToolResult(output=f"QR code generated successfully!\n"
                                   f"Data: {data}\n"
                                   f"Size: {size}x{size}\n"
                                   f"Error Correction: {error_correction}\n"
                                   f"Format: {format.upper()}\n"
                                   f"Saved to: {output_path}")
        except Exception as e:
            return ToolResult(error=f"Error generating QR code: {str(e)}")

    def _generate_styled_qr(self, data: str, output_path: Optional[str], size: int, border: int,
                           error_correction: str, fill_color: str, back_color: str,
                           module_drawer: str, format: str) -> ToolResult:
        """Generate styled QR code with colors and shapes."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=self._get_error_correction(error_correction),
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create styled image
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=self._get_module_drawer(module_drawer),
                color_mask=SolidFillColorMask(back_color=back_color, front_color=fill_color)
            )

            if not output_path:
                output_path = f"styled_qrcode.{format.lower()}"

            img.save(output_path, format=format.upper())

            return ToolResult(output=f"Styled QR code generated successfully!\n"
                                   f"Data: {data}\n"
                                   f"Size: {size}x{size}\n"
                                   f"Style: {module_drawer}\n"
                                   f"Colors: {fill_color} on {back_color}\n"
                                   f"Error Correction: {error_correction}\n"
                                   f"Format: {format.upper()}\n"
                                   f"Saved to: {output_path}")
        except Exception as e:
            return ToolResult(error=f"Error generating styled QR code: {str(e)}")

    def _generate_qr_with_logo(self, data: str, output_path: Optional[str], logo_path: Optional[str],
                              size: int, border: int, error_correction: str,
                              fill_color: str, back_color: str, format: str) -> ToolResult:
        """Generate QR code with logo in center."""
        try:
            if not logo_path:
                return ToolResult(error="logo_path is required for this command")

            # Generate base QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=self._get_error_correction(error_correction),
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color=fill_color, back_color=back_color)

            # Open and resize logo
            logo = Image.open(logo_path)

            # Calculate logo size (about 1/5 of QR code size)
            qr_width, qr_height = img.size
            logo_size = min(qr_width, qr_height) // 5

            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Create a white background for logo if it has transparency
            if logo.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', logo.size, back_color)
                background.paste(logo, mask=logo.split()[-1] if logo.mode == 'RGBA' else None)
                logo = background

            # Calculate position to center logo
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)

            # Paste logo onto QR code
            img.paste(logo, logo_pos)

            if not output_path:
                output_path = f"qrcode_with_logo.{format.lower()}"

            img.save(output_path, format=format.upper())

            return ToolResult(output=f"QR code with logo generated successfully!\n"
                                   f"Data: {data}\n"
                                   f"Size: {size}x{size}\n"
                                   f"Logo: {logo_path}\n"
                                   f"Logo Size: {logo_size}x{logo_size}\n"
                                   f"Error Correction: {error_correction}\n"
                                   f"Format: {format.upper()}\n"
                                   f"Saved to: {output_path}")
        except FileNotFoundError:
            return ToolResult(error=f"Logo file not found: {logo_path}")
        except Exception as e:
            return ToolResult(error=f"Error generating QR code with logo: {str(e)}")

    def _batch_generate_qr(self, data_list: str, size: int, border: int, error_correction: str,
                          fill_color: str, back_color: str, format: str) -> ToolResult:
        """Generate multiple QR codes."""
        try:
            # Parse data list
            data_items = [item.strip() for item in data_list.split(',') if item.strip()]

            if not data_items:
                return ToolResult(error="No valid data items found")

            generated_files = []

            for i, data_item in enumerate(data_items):
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=self._get_error_correction(error_correction),
                    box_size=size,
                    border=border,
                )
                qr.add_data(data_item)
                qr.make(fit=True)

                img = qr.make_image(fill_color=fill_color, back_color=back_color)

                # Generate filename
                safe_filename = "".join(c for c in data_item if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_filename = safe_filename[:50]  # Limit length
                if not safe_filename:
                    safe_filename = f"qrcode_{i+1}"

                output_path = f"{safe_filename}.{format.lower()}"
                img.save(output_path, format=format.upper())
                generated_files.append(output_path)

            output = f"Batch QR code generation completed!\n"
            output += f"Generated {len(generated_files)} QR codes:\n"
            for i, (data_item, file_path) in enumerate(zip(data_items, generated_files), 1):
                output += f"  {i}. {data_item[:30]}{'...' if len(data_item) > 30 else ''} -> {file_path}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error in batch QR generation: {str(e)}")
