"""
Module: pdf_export.py
This module provides a function to export the current soil profile figure 
(as displayed on the canvas) to a PDF file using the specified paper size, 
orientation, and scale parameter. This function does not recreate or modify 
the drawing; it simply checks whether the current figure size (in inches) fits 
within the desired paper dimensions. If the current figure is larger than the 
desired dimensions, it prompts the user to decide whether to continue with the export.
Note: The current design prints exactly the canvas as is. (The scale parameter 
does not affect the drawing unless the plot is regenerated.)
"""

import matplotlib.pyplot as plt
from library import QMessageBox

def export_scaled_pdf(figure, paper: str, orientation: str, scale_str: str, output_filename: str) -> bool:
    """
    Export the given figure (as displayed on the canvas) to a PDF file using the 
    specified paper size, orientation, and scale parameter.
    
    The function checks whether the current figure size (in inches) fits within 
    the desired paper dimensions. If it does not, it prompts the user to decide 
    whether to continue. Note that the scale parameter is not applied to the canvas 
    figure; the exported PDF will match exactly what is shown on the canvas.
    
    Args:
        figure: The Matplotlib figure to be exported.
        paper (str): The paper size key (e.g., "A0", "A1", "A3", "A4", "Letter").
        orientation (str): The desired orientation ("Portrait" or "Landscape").
        scale_str (str): The scale string (e.g., "1:50"). (Note: This value is not used to 
                         modify the drawing in this implementation.)
        output_filename (str): The filename (with .pdf extension) where the PDF will be saved.
        
    Returns:
        bool: True if the PDF was saved successfully; False otherwise.
    """
    from app_data import PAPER_SIZES_INCHES

    # Retrieve desired paper dimensions (in inches)
    desired_dims = PAPER_SIZES_INCHES.get(paper, (8.27, 11.69))  # default to A4 if not found
    if orientation.lower() == "landscape":
        desired_dims = (desired_dims[1], desired_dims[0])
    desired_width, desired_height = desired_dims

    # (Optional) Warn if the scale parameter is not the default.
    default_scale = "1:50"  # or whichever you consider the default
    if scale_str.strip() != default_scale:
        # Inform the user that the current canvas figure is not re-scaled by the export function.
        reply = QMessageBox.question(
            None,
            "Scale Parameter Ignored",
            f"The current PDF export does not apply the scale parameter (currently set to {scale_str}).\n"
            f"To use a different scale, please regenerate the plot accordingly.\n"
            "Do you want to continue exporting the current figure?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return False

    # Get the current figure size in inches.
    current_size = figure.get_size_inches()
    current_width, current_height = current_size

    # Check if the current figure size fits within the desired paper dimensions.
    if current_width > desired_width or current_height > desired_height:
        reply = QMessageBox.question(
            None,
            "Figure Size Mismatch",
            f"The current figure size ({current_width:.2f} x {current_height:.2f} inches) exceeds "
            f"the desired paper size ({desired_width:.2f} x {desired_height:.2f} inches).\n"
            "Do you want to continue saving the PDF as is?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return False

    try:
        # Save the figure exactly as shown on the canvas.
        figure.savefig(output_filename, format="pdf", dpi=300, bbox_inches='tight')
        return True
    except Exception as e:
        raise e
