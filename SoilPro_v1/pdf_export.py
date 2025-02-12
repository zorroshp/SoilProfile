"""
Module: pdf_export.py
This module provides a function to export the soil profile plots to a scaled PDF.
"""

from library import plt, np, mticker
from app_data import PAPER_SIZES_INCHES

def export_scaled_pdf(borehole1_data: list, borehole2_data: list, borehole_names: tuple, plot_width: float, plot_gap: float,
                      scale_str: str, paper: str, orientation: str, font_sizes: dict, grid_settings: dict,
                      palette_name: str, palettes: dict, halftone: bool, convert_to_lighter_func, output_filename: str) -> bool:
    """
    Generate a scaled PDF of the soil profiles and save it to output_filename.

    Args:
        borehole1_data (list): Data for borehole 1.
        borehole2_data (list): Data for borehole 2.
        borehole_names (tuple): Names of the boreholes.
        plot_width (float): Profile width in meters.
        plot_gap (float): Spacing between profiles.
        scale_str (str): Scale string (e.g. "1:50").
        paper (str): Paper size key.
        orientation (str): "Portrait" or "Landscape".
        font_sizes (dict): Font sizes for various text elements.
        grid_settings (dict): Grid line settings.
        palette_name (str): Selected color palette.
        palettes (dict): Dictionary of color palettes.
        halftone (bool): If True, apply halftone effect.
        convert_to_lighter_func (callable): Function to lighten colors.
        output_filename (str): Filename for the saved PDF.

    Returns:
        bool: True if the PDF was saved successfully; otherwise, an exception is raised.
    """
    try:
        scale_factor = float(scale_str.split(":")[1])
    except Exception:
        scale_factor = 50.0

    paper_dims = PAPER_SIZES_INCHES.get(paper, (8.27, 11.69))
    if orientation.lower() == "landscape":
        paper_dims = (paper_dims[1], paper_dims[0])

    fig = plt.figure(figsize=paper_dims)
    wspace = plot_gap / plot_width if plot_width != 0 else 0
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=wspace)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    combined = borehole1_data + borehole2_data
    all_vals = [d['start'] for d in combined] + [d['end'] for d in combined]
    if all_vals:
        y_min = min(all_vals)
        y_max = max(all_vals)
    else:
        y_min, y_max = 0, 1

    unique_layers = {d['layer'] for d in combined}
    layer_tops = {layer: max(d['start'] for d in combined if d['layer'] == layer) for layer in unique_layers}
    sorted_layers = sorted(unique_layers, key=lambda n: layer_tops[n], reverse=True)
    palette = palettes.get(palette_name, [])
    if halftone:
        palette = [convert_to_lighter_func(c) for c in palette]
    colors = {layer: palette[i % len(palette)] for i, layer in enumerate(sorted_layers)} if palette else {}

    def plot_scaled_borehole(ax, data: list, name: str, label_side: str):
        """
        Plot a single borehole profile on a scaled axis for PDF export.
        """
        if not data:
            ax.set_visible(False)
            return
        ax.set_title(name, pad=20, fontsize=font_sizes.get('title', 12))
        ax.set_xticks([])
        ax.set_aspect('equal', adjustable='box')
        scaled_width = (plot_width * 1000.0) / scale_factor
        ax.set_xlim(-scaled_width / 2, scaled_width / 2)
        local_top = max(d['start'] for d in data)
        local_bottom = min(d['end'] for d in data)
        scaled_top = (local_top * 1000.0) / scale_factor
        scaled_bottom = (local_bottom * 1000.0) / scale_factor
        x_left, x_right = ax.get_xlim()
        rect = plt.Rectangle(
            (x_left, scaled_bottom),
            x_right - x_left,
            scaled_top - scaled_bottom,
            fill=False, edgecolor='black', linewidth=1, zorder=1, clip_on=False
        )
        ax.add_patch(rect)
        margin = 0.2 * scaled_width
        for layer in data:
            thickness_m = abs(layer['start'] - layer['end'])
            thickness_scaled = (thickness_m * 1000.0) / scale_factor
            btm = min(layer['start'], layer['end'])
            scaled_btm = (btm * 1000.0) / scale_factor
            color = colors.get(layer['layer'], "#CCCCCC")
            ax.bar(
                0, thickness_scaled,
                width=scaled_width,
                bottom=scaled_btm,
                color=color, edgecolor='black', linewidth=0.5, zorder=2
            )
            if label_side == "left":
                text_x = x_left - margin
                ha = "right"
            else:
                text_x = x_right + margin
                ha = "left"
            spt_display = f"SPT: {layer['spt']}" if layer['spt'] not in [None, ""] else ""
            label_text = layer['layer'] if not spt_display else f"{layer['layer']}\n{spt_display}"
            ax.text(
                text_x,
                scaled_btm + thickness_scaled / 2,
                label_text,
                ha=ha, va='center',
                fontsize=font_sizes.get('stack_bar', 9),
                zorder=3
            )

    plot_scaled_borehole(ax1, borehole1_data, borehole_names[0], "left")
    plot_scaled_borehole(ax2, borehole2_data, borehole_names[1], "right")

    scaled_min = (y_min * 1000.0) / scale_factor
    scaled_max = (y_max * 1000.0) / scale_factor
    for ax in (ax1, ax2):
        ax.set_ylim(scaled_min, scaled_max)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.tick_params(axis='both', which='both', length=0)

    if borehole1_data and ax1.get_visible():
        ticks = sorted({(d["start"] * 1000.0) / scale_factor for d in borehole1_data} |
                       {(d["end"] * 1000.0) / scale_factor for d in borehole1_data}, reverse=True)
        ax1.set_yticks(ticks)
        def format_meters(val, pos):
            real_m = (val * scale_factor) / 1000.0
            return f"{real_m:.3f}"
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(format_meters))
        ax1.yaxis.tick_right()
        ax1.tick_params(axis='y', labelsize=font_sizes.get('borehole_level', 10))
    if borehole2_data and ax2.get_visible():
        ticks = sorted({(d["start"] * 1000.0) / scale_factor for d in borehole2_data} |
                       {(d["end"] * 1000.0) / scale_factor for d in borehole2_data}, reverse=True)
        ax2.set_yticks(ticks)
        def format_meters(val, pos):
            real_m = (val * scale_factor) / 1000.0
            return f"{real_m:.3f}"
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(format_meters))
        ax2.yaxis.tick_left()
        ax2.tick_params(axis='y', labelsize=font_sizes.get('borehole_level', 10))

    if grid_settings.get('grid', False) and ax1.get_visible() and ax2.get_visible():
        pos1 = ax1.get_position()
        pos2 = ax2.get_position()
        gap_x0 = pos1.x1
        gap_x1 = pos2.x0
        interval_m = grid_settings.get('grid_interval', 1.0)
        scaled_interval = (interval_m * 1000.0) / scale_factor
        scaled_vals = np.arange(scaled_max, scaled_min - scaled_interval/2, -scaled_interval)
        for y_val in scaled_vals:
            fig_y = ax1.transData.transform((0, y_val))[1] / fig.bbox.height
            line = plt.Line2D([gap_x0, gap_x1], [fig_y, fig_y],
                              transform=fig.transFigure,
                              color='gray', linestyle=(0, (3,3)), linewidth=0.5)
            fig.lines.append(line)
            if grid_settings.get('grid_label', False):
                x_center = (gap_x0 + gap_x1) / 2
                offset_val = (0.05 * 1000.0) / scale_factor
                off_fig = (ax1.transData.transform((0, y_val + offset_val))[1] -
                           ax1.transData.transform((0, y_val))[1]) / fig.bbox.height
                label_y = fig_y + off_fig
                real_m = (y_val * scale_factor) / 1000.0
                label_text = f"{real_m:.3f} m"
                fig.text(
                    x_center, label_y, label_text,
                    ha='center', va='bottom', color='gray',
                    fontsize=grid_settings.get('grid_label_font_size', 8)
                )
    try:
        fig.savefig(output_filename, format="pdf", dpi=300)
        plt.close(fig)
        return True
    except Exception as e:
        plt.close(fig)
        raise e
