"""
Module: pdf_export.py
This module exports the current model-space figure to a PDF in paper space.
It simulates industry practices (similar to CAD) where the model drawing is scaled
onto a paper layout. The drawing’s annotations remain unchanged, but its physical
dimensions on paper reflect the specified scale.

This implementation uses the Pillow library to resize the rendered model image to the 
correct pixel dimensions based on the desired scale and paper DPI.
"""

import matplotlib.pyplot as plt
from library import QMessageBox
import io

try:
    from PIL import Image
except ImportError:
    raise ImportError("Pillow is required for PDF export. Install it using 'pip install Pillow'.")

def export_scaled_pdf(figure, paper: str, orientation: str, scale_str: str, output_filename: str) -> bool:
    """
    Export the given model-space figure as a PDF in paper space.
    
    Process:
      1. Retrieve paper dimensions (in inches) from app_data.PAPER_SIZES_INCHES and adjust for orientation.
      2. Parse the scale parameter (e.g. "1:100") to get the denominator.
      3. From the primary axis of the model figure (assumed in meters), extract extents.
      4. Compute the drawing's physical size on paper (in inches):
             drawing_size_in = model_size_in_m * (39.37 / scale_denominator)
         For example, at 1:100, a 4 m distance becomes about 1.5748 inches (~40 mm).
      5. Render the model figure to a PNG image (via an in-memory buffer).
      6. Use Pillow to resize this image to the required pixel dimensions based on a chosen DPI.
      7. Create a new paper space figure (with the paper dimensions and DPI).
      8. Center the resized image on the paper space using figimage.
      9. Save the new figure as a PDF.
    
    Args:
        figure: The Matplotlib figure (model space) to export.
        paper (str): Paper size key (e.g., "A0", "A1", "A3", "A4", "Letter").
        orientation (str): "Portrait" or "Landscape".
        scale_str (str): Scale parameter as a string (e.g., "1:100").
        output_filename (str): Output PDF file name.
    
    Returns:
        bool: True if export is successful, False otherwise.
    """
    from app_data import PAPER_SIZES_INCHES

    # Retrieve desired paper dimensions (in inches)
    desired_dims = PAPER_SIZES_INCHES.get(paper, (8.27, 11.69))  # default to A4 if not found
    if orientation.lower() == "landscape":
        desired_dims = (desired_dims[1], desired_dims[0])
    paper_width, paper_height = desired_dims

    # Parse scale parameter (expected format "1:100")
    try:
        parts = scale_str.split(":")
        scale_denominator = float(parts[1])
    except Exception:
        scale_denominator = 100.0  # fallback default

    # Get the primary axis from the model figure (assumed model units are meters)
    if not figure.axes:
        QMessageBox.critical(None, "Export Error", "No axes found in the figure.")
        return False
    ax = figure.axes[0]
    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    model_width = abs(xlims[1] - xlims[0])  # in meters
    model_height = abs(ylims[1] - ylims[0])  # in meters

    # Conversion: 1 m = 39.37 inches (at 1:1 scale)
    conv = 39.37
    drawing_width_in = model_width * (conv / scale_denominator)
    drawing_height_in = model_height * (conv / scale_denominator)

    # Check if the drawing fits on the paper
    if drawing_width_in > paper_width or drawing_height_in > paper_height:
        msg = (
            f"The scaled drawing size is {drawing_width_in*25.4:.2f} x {drawing_height_in*25.4:.2f} mm, "
            f"which exceeds the paper size of {paper_width*25.4:.2f} x {paper_height*25.4:.2f} mm.\n"
            "Please choose a different scale."
        )
        QMessageBox.critical(None, "Figure Does Not Fit", msg)
        return False

    # Render the model-space figure to a PNG image in memory.
    buf = io.BytesIO()
    figure.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    
    # Load the image using Pillow
    model_image = Image.open(buf)

    # Define the paper DPI for the output PDF
    paper_dpi = 300

    # Compute desired drawing dimensions in pixels
    drawing_width_px = int(drawing_width_in * paper_dpi)
    drawing_height_px = int(drawing_height_in * paper_dpi)

    # Resize the rendered model image to exactly the desired pixel dimensions.
    # This ensures that, for example, a 4 m distance becomes 1.5748 inches (~40 mm) on paper.
    resized_image = model_image.resize((drawing_width_px, drawing_height_px), Image.LANCZOS)

    # Create a new paper space figure with the specified paper size and DPI.
    new_fig = plt.figure(figsize=(paper_width, paper_height), dpi=paper_dpi)
    
    # Calculate paper dimensions in pixels.
    paper_width_px = int(paper_width * paper_dpi)
    paper_height_px = int(paper_height * paper_dpi)
    
    # Determine the top-left coordinates to center the drawing on the paper.
    left_px = (paper_width_px - drawing_width_px) // 2
    top_px = (paper_height_px - drawing_height_px) // 2

    # Use figimage to place the resized image at the correct pixel coordinates.
    # Note: figimage's origin is at the upper-left corner.
    new_fig.figimage(resized_image, xo=left_px, yo=top_px, origin='upper')

    try:
        # Save the new paper-space figure as a PDF.
        new_fig.savefig(output_filename, format='pdf', dpi=paper_dpi)
        plt.close(new_fig)
        return True
    except Exception as e:
        plt.close(new_fig)
        QMessageBox.critical(None, "Export Error", f"Could not save PDF: {str(e)}")
        return False
