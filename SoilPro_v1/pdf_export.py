"""
Module: pdf_export.py
Exports the figure to a scaled PDF using precise metric scaling (millimeters) and vector graphics.
The original model-space plot (in meters) is re‐rendered on a new figure (with the selected paper size)
and then the drawing is scaled and centered according to the chosen scale.
The process follows these steps:
  1. Retrieve paper dimensions (in mm) from app_data.PAPER_SIZES_MM and convert to inches.
  2. Parse the scale (e.g., "1:100" → 100).
  3. Extract model dimensions (in m) from the original figure.
  4. Compute the drawing’s physical size in mm: (model_size_m/scale)×1000.
  5. Check that the drawing fits within the paper dimensions.
  6. Convert the drawing size to inches.
  7. Create a new figure with page size equal to the selected paper.
  8. Compute margins and embed the vector re‑rendered plot (via generate_borehole_profile_plot) centered on the page.
  9. Save the new figure as a PDF.
"""

import matplotlib.pyplot as plt
from library import QMessageBox

def export_scaled_pdf(figure, paper: str, orientation: str, scale_str: str, output_filename: str, **kwargs) -> bool:
    # Step 1: Get paper dimensions (in mm) and convert to inches.
    from app_data import PAPER_SIZES_MM
    paper_dims = PAPER_SIZES_MM.get(paper, (210, 297))
    if orientation.lower() == "landscape":
        paper_width_mm, paper_height_mm = paper_dims[1], paper_dims[0]
    else:
        paper_width_mm, paper_height_mm = paper_dims
    paper_width_in = paper_width_mm / 25.4
    paper_height_in = paper_height_mm / 25.4

    # Step 2: Parse scale string (format "1:100")
    try:
        scale_den = float(scale_str.split(":")[1])
    except Exception:
        QMessageBox.critical(None, "Error", "Invalid scale format. Use '1:100'.")
        return False

    # Step 3: Extract model dimensions (in meters) from original figure.
    if not figure.axes:
        QMessageBox.critical(None, "Export Error", "No axes found in the figure.")
        return False
    ax0 = figure.axes[0]
    xlim_min, xlim_max = ax0.get_xlim()
    ylim_min, ylim_max = ax0.get_ylim()
    model_width_m = xlim_max - xlim_min
    model_height_m = ylim_max - ylim_min

    # Step 4: Compute drawing size in mm.
    drawing_width_mm = (model_width_m / scale_den) * 1000
    drawing_height_mm = (model_height_m / scale_den) * 1000

    # Step 5: Check if drawing fits within paper.
    if drawing_width_mm > paper_width_mm or drawing_height_mm > paper_height_mm:
        msg = (f"Scaled drawing size: {drawing_width_mm:.1f} x {drawing_height_mm:.1f} mm\n"
               f"Paper size: {paper_width_mm} x {paper_height_mm} mm")
        QMessageBox.critical(None, "Error", msg)
        return False

    # Step 6: Convert drawing size to inches.
    drawing_width_in = drawing_width_mm / 25.4
    drawing_height_in = drawing_height_mm / 25.4

    # Step 7: Create new figure with paper size.
    new_fig = plt.figure(figsize=(paper_width_in, paper_height_in))

    # Step 8: Compute placement (margins) to center drawing.
    left_margin_in = (paper_width_in - drawing_width_in) / 2
    bottom_margin_in = (paper_height_in - drawing_height_in) / 2
    norm_left = left_margin_in / paper_width_in
    norm_bottom = bottom_margin_in / paper_height_in
    norm_width = drawing_width_in / paper_width_in
    norm_height = drawing_height_in / paper_height_in

    # Clear the figure and re-render the plot vectorially using generate_borehole_profile_plot.
    try:
        from plotter import generate_borehole_profile_plot
        new_fig.clear()
        generate_borehole_profile_plot(
            new_fig,
            kwargs.get('borehole1_data', []),
            kwargs.get('borehole2_data', []),
            kwargs.get('borehole_names', ("Borehole-1", "Borehole-2")),
            kwargs.get('plot_width', 2),
            kwargs.get('plot_gap', 15),
            kwargs.get('font_sizes', {'title': 12, 'stack_bar': 9, 'borehole_level': 10}),
            kwargs.get('grid_settings', {'grid': False}),
            kwargs.get('palette_name', "Geotech 12"),
            kwargs.get('palettes', {}),
            kwargs.get('halftone', False),
            kwargs.get('convert_to_lighter_func', lambda c, f=0.5: c),
            kwargs.get('color_mode', "palette"),
            kwargs.get('soil_type_colors', None)
        )
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to regenerate plot: {str(e)}")
        plt.close(new_fig)
        return False

    # After the plot is generated, obtain its axis and set its position.
    if new_fig.axes:
        ax_new = new_fig.axes[0]
        ax_new.set_position([norm_left, norm_bottom, norm_width, norm_height])
    else:
        QMessageBox.critical(None, "Error", "No axis generated in new figure.")
        plt.close(new_fig)
        return False

    # Step 9: Save new figure as PDF.
    try:
        new_fig.savefig(output_filename, format="pdf")
        plt.close(new_fig)
        return True
    except Exception as e:
        plt.close(new_fig)
        QMessageBox.critical(None, "Error", f"PDF save failed: {str(e)}")
        return False
