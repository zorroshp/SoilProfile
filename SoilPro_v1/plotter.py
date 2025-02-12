"""
Module: plotter.py
This module provides functions to extract borehole data from an input table,
assign colors to layers, and generate a combined borehole soil profile plot.
"""

from library import plt, np, mticker

def extract_borehole_data(table) -> list:
    """
    Extract borehole layer data from the input table.
    
    Each row must contain:
      Column 0: Layer Name
      Column 1: Start Level (m)
      Column 2: End Level (m)
      Column 3: SPT Value

    Returns:
        List[dict]: List of dictionaries with keys 'layer', 'start', 'end', 'spt',
                    sorted by 'start' in descending order.
    """
    data = []
    for row in range(table.rowCount()):
        items = [table.item(row, col) for col in range(4)]
        if not items or items[0] is None:
            continue
        try:
            start_val = float(items[1].text())
            end_val = float(items[2].text())
        except ValueError:
            continue  # Skip if conversion fails
        spt_text = items[3].text().strip() if items[3] is not None else ""
        try:
            spt_value = int(spt_text)
        except ValueError:
            spt_value = spt_text if spt_text else None
        data.append({
            'layer': items[0].text(),
            'start': start_val,
            'end': end_val,
            'spt': spt_value
        })
    return sorted(data, key=lambda x: x['start'], reverse=True)

def assign_layer_colors(layers: list, palette_name: str, palettes: dict, halftone: bool, convert_to_lighter_func) -> dict:
    """
    Assign a color to each unique layer based on the selected palette.
    
    Args:
        layers (list): Unique layer names.
        palette_name (str): Key of the desired palette.
        palettes (dict): Dictionary of available palettes.
        halftone (bool): If True, lighten each color.
        convert_to_lighter_func (callable): Function to lighten a color.

    Returns:
        dict: Mapping of layer names to hex color strings.
    """
    palette = palettes.get(palette_name, [])
    if halftone:
        palette = [convert_to_lighter_func(color) for color in palette]
    color_map = {}
    for i, layer in enumerate(layers):
        color_map[layer] = palette[i % len(palette)] if palette else "#CCCCCC"
    return color_map

def plot_borehole_profile(ax, data: list, borehole_name: str, colors: dict, plot_width: float, label_side: str, font_sizes: dict):
    """
    Plot a single borehole's soil profile on the given axis.
    
    Args:
        ax: Matplotlib axis.
        data (list): List of layer dictionaries.
        borehole_name (str): Borehole name.
        colors (dict): Mapping of layer names to colors.
        plot_width (float): Width of the profile (in meters).
        label_side (str): "left" or "right" for label placement.
        font_sizes (dict): Dictionary with font sizes for 'title' and 'stack_bar'.
    """
    if not data:
        ax.set_visible(False)
        return

    ax.set_title(borehole_name, pad=20, fontsize=font_sizes.get('title', 12))
    ax.set_xticks([])
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(-plot_width / 2, plot_width / 2)

    local_top = max(d['start'] for d in data)
    local_bottom = min(d['end'] for d in data)
    x_left, x_right = ax.get_xlim()

    rect = plt.Rectangle(
        (x_left, local_bottom),
        x_right - x_left,
        local_top - local_bottom,
        fill=False, edgecolor='black', linewidth=1, zorder=1, clip_on=False
    )
    ax.add_patch(rect)

    margin = 0.2 * plot_width
    for layer in data:
        thickness = abs(layer['start'] - layer['end'])
        bottom_val = min(layer['start'], layer['end'])
        color = colors.get(layer['layer'], "#CCCCCC")
        ax.bar(
            0, thickness,
            width=plot_width,
            bottom=bottom_val,
            color=color,
            edgecolor='black',
            linewidth=0.5,
            zorder=2
        )
        if label_side == "left":
            text_x = -plot_width / 2 - margin
            ha = "right"
        else:
            text_x = plot_width / 2 + margin
            ha = "left"
        spt_display = f"SPT: {layer['spt']}" if layer['spt'] not in [None, ""] else ""
        label_text = layer['layer'] if not spt_display else f"{layer['layer']}\n{spt_display}"
        ax.text(
            text_x,
            bottom_val + thickness / 2,
            label_text,
            ha=ha,
            va='center',
            fontsize=font_sizes.get('stack_bar', 9),
            zorder=3
        )

def generate_borehole_profile_plot(figure, borehole1_data: list, borehole2_data: list, borehole_names: tuple,
                                   plot_width: float, plot_gap: float, font_sizes: dict, grid_settings: dict,
                                   palette_name: str, palettes: dict, halftone: bool, convert_to_lighter_func):
    """
    Generate a combined soil profile plot for two boreholes on the given figure.
    
    Args:
        figure: Matplotlib figure.
        borehole1_data (list): Data for borehole 1.
        borehole2_data (list): Data for borehole 2.
        borehole_names (tuple): Tuple of borehole names.
        plot_width (float): Profile width (m).
        plot_gap (float): Spacing between plots (m).
        font_sizes (dict): Font sizes for titles and labels.
        grid_settings (dict): Grid drawing settings.
        palette_name (str): Name of the selected color palette.
        palettes (dict): Dictionary of color palettes.
        halftone (bool): If True, apply halftone effect.
        convert_to_lighter_func (callable): Function to lighten colors.
    """
    figure.clear()
    
    all_values = []
    for d in borehole1_data + borehole2_data:
        all_values.extend([d['start'], d['end']])
    if all_values:
        global_y_max = max(all_values)
        global_y_min = min(all_values)
    else:
        global_y_max, global_y_min = 1, 0

    combined_data = borehole1_data + borehole2_data
    unique_layers = {d['layer'] for d in combined_data}
    layer_tops = {layer: max(d['start'] for d in combined_data if d['layer'] == layer) for layer in unique_layers}
    sorted_layers = sorted(unique_layers, key=lambda n: layer_tops[n], reverse=True)
    colors = assign_layer_colors(sorted_layers, palette_name, palettes, halftone, convert_to_lighter_func)

    wspace = plot_gap / plot_width if plot_width != 0 else 0
    gs = figure.add_gridspec(1, 2, width_ratios=[1, 1], wspace=wspace)
    ax1 = figure.add_subplot(gs[0])
    ax2 = figure.add_subplot(gs[1])

    if borehole1_data:
        plot_borehole_profile(ax1, borehole1_data, borehole_names[0], colors, plot_width, "left", font_sizes)
    else:
        ax1.set_visible(False)
    if borehole2_data:
        plot_borehole_profile(ax2, borehole2_data, borehole_names[1], colors, plot_width, "right", font_sizes)
    else:
        ax2.set_visible(False)

    for ax in (ax1, ax2):
        if ax.get_visible():
            ax.set_ylim(global_y_min, global_y_max)
            ax.patch.set_visible(False)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(axis='both', which='both', length=0)

    if borehole1_data and ax1.get_visible():
        ticks = sorted({d['start'] for d in borehole1_data} | {d['end'] for d in borehole1_data}, reverse=True)
        ax1.set_yticks(ticks)
        ax1.yaxis.tick_right()
        ax1.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
        ax1.tick_params(axis='y', labelsize=font_sizes.get('borehole_level', 10))
    if borehole2_data and ax2.get_visible():
        ticks = sorted({d['start'] for d in borehole2_data} | {d['end'] for d in borehole2_data}, reverse=True)
        ax2.set_yticks(ticks)
        ax2.yaxis.tick_left()
        ax2.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
        ax2.tick_params(axis='y', labelsize=font_sizes.get('borehole_level', 10))

    if grid_settings.get('grid', False):
        grid_interval = grid_settings.get('grid_interval', 1.0)
        grid_label = grid_settings.get('grid_label', False)
        grid_label_font_size = grid_settings.get('grid_label_font_size', 8)
        pos1 = ax1.get_position() if ax1.get_visible() else None
        pos2 = ax2.get_position() if ax2.get_visible() else None
        if pos1 and pos2:
            gap_x0 = pos1.x1
            gap_x1 = pos2.x0
            grid_values = np.arange(global_y_max, global_y_min - grid_interval / 2, -grid_interval)
            for y in grid_values:
                fig_y = ax1.transData.transform((0, y))[1] / figure.bbox.height
                line = plt.Line2D(
                    [gap_x0, gap_x1], [fig_y, fig_y],
                    transform=figure.transFigure,
                    color='gray', linestyle=(0, (3, 3)), linewidth=0.5
                )
                figure.lines.append(line)
                if grid_label:
                    x_center = (gap_x0 + gap_x1) / 2
                    data_offset = 0.05
                    offset_fig = (ax1.transData.transform((0, y + data_offset))[1] -
                                  ax1.transData.transform((0, y))[1]) / figure.bbox.height
                    label_y = fig_y + offset_fig
                    label_text = f"{y:.3f} m"
                    figure.text(
                        x_center, label_y, label_text,
                        ha='center', va='bottom', color='gray',
                        fontsize=grid_label_font_size
                    )
    figure.canvas.draw()
