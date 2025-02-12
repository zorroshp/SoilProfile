"""
Module: plotter.py
This module provides functions to extract borehole data from an input table,
assign colors to layers, and generate a combined soil profile plot on a single axis.
Borehole 1 is centered at x = 0 and Borehole 2 is centered at x = (plot_gap + plot_width).
In addition, manual y–axis labels are drawn:
    - For Borehole 1: labels appear on the right side of its profile.
    - For Borehole 2: labels appear on the left side of its profile.
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

def plot_borehole_profile(ax, data: list, borehole_name: str, colors: dict,
                          plot_width: float, label_side: str, font_sizes: dict,
                          x_offset: float = 0):
    """
    Plot a single borehole's soil profile on the given axis, with an optional horizontal offset.
    
    Args:
        ax: Matplotlib axis.
        data (list): List of layer dictionaries.
        borehole_name (str): Borehole name.
        colors (dict): Mapping of layer names to colors.
        plot_width (float): Width of the profile (in meters).
        label_side (str): "left" or "right" for label placement.
        font_sizes (dict): Dictionary with font sizes for 'title' and 'stack_bar'.
        x_offset (float, optional): Horizontal offset for the profile center. Defaults to 0.
    """
    if not data:
        return

    # Place the borehole name above the profile, centered at x_offset.
    ax.text(x_offset,
            max([d['start'] for d in data]) + 0.05 * (max([d['start'] for d in data]) - min([d['end'] for d in data])),
            borehole_name, ha='center', fontsize=font_sizes.get('title', 12))
    ax.set_xticks([])
    ax.set_aspect('equal', adjustable='box')
    # Center the profile at x_offset.
    ax.set_xlim(x_offset - plot_width/2, x_offset + plot_width/2)

    local_top = max(d['start'] for d in data)
    local_bottom = min(d['end'] for d in data)
    x_left, x_right = ax.get_xlim()

    # Draw an outline rectangle around the profile.
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
        # Draw the bar centered at x_offset.
        ax.bar(
            x_offset, thickness,
            width=plot_width,
            bottom=bottom_val,
            color=color,
            edgecolor='black',
            linewidth=0.5,
            zorder=2
        )
        if label_side == "left":
            text_x = (x_offset - plot_width/2) - margin
            ha = "right"
        else:
            text_x = (x_offset + plot_width/2) + margin
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
    Generate a combined soil profile plot for two boreholes on a single axis.
    
    Borehole 1 is drawn with its center at x = 0.
    Borehole 2 is drawn with its center at x = (plot_gap + plot_width).
    This guarantees that the center-to-center distance equals (plot_gap + plot_width).
    Additionally, manual y–axis labels are drawn:
      - For Borehole 1, the labels are placed on the right side of its profile.
      - For Borehole 2, the labels are placed on the left side of its profile.
    
    Args:
        figure: Matplotlib figure.
        borehole1_data (list): Data for borehole 1.
        borehole2_data (list): Data for borehole 2.
        borehole_names (tuple): Tuple of borehole names.
        plot_width (float): Profile width (m).
        plot_gap (float): Clear gap between the two profiles (m).
        font_sizes (dict): Font sizes for titles and labels.
        grid_settings (dict): Grid drawing settings.
        palette_name (str): Name of the selected color palette.
        palettes (dict): Dictionary of color palettes.
        halftone (bool): If True, apply halftone effect.
        convert_to_lighter_func (callable): Function to lighten colors.
    """
    figure.clear()
    
    # Compute overall y–range.
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

    # Use a single axis for the entire plot.
    ax = figure.add_subplot(111)
    
    # Plot Borehole 1 with center at x_offset = 0.
    if borehole1_data:
        plot_borehole_profile(ax, borehole1_data, borehole_names[0], colors, plot_width, "left", font_sizes, x_offset=0)
    # Plot Borehole 2 with center at x_offset = (plot_gap + plot_width).
    if borehole2_data:
        plot_borehole_profile(ax, borehole2_data, borehole_names[1], colors, plot_width, "right", font_sizes,
                              x_offset = plot_gap + plot_width)
    
    # Set overall x–limits: from left edge of Borehole 1 to right edge of Borehole 2.
    ax.set_xlim(-plot_width/2, (plot_gap + plot_width) + plot_width/2)
    ax.set_ylim(global_y_min, global_y_max)
    ax.patch.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    
    # Disable the default y–tick labels.
    ax.set_yticklabels([])

    # --- MANUALLY DRAW Y–AXIS LABELS WITH SWITCHED SIDES ---
    label_offset = 0.3 * plot_width  # Adjust this value as needed

    # For Borehole 1: Place labels on the right side.
    if borehole1_data:
        levels1 = sorted(set([d['start'] for d in borehole1_data]) | set([d['end'] for d in borehole1_data]), reverse=True)
        for lvl in levels1:
            # Right side of Borehole 1: center at x = 0 + plot_width/2.
            x_label = (0 + plot_width/2) + label_offset
            ax.text(x_label, lvl, f"{lvl:.3f}", ha='left', va='center', color='black',
                    fontsize=font_sizes.get('borehole_level', 10))
    
    # For Borehole 2: Place labels on the left side.
    if borehole2_data:
        levels2 = sorted(set([d['start'] for d in borehole2_data]) | set([d['end'] for d in borehole2_data]), reverse=True)
        for lvl in levels2:
            # Left side of Borehole 2: center at x = (plot_gap+plot_width) - plot_width/2.
            x_label = (plot_gap + plot_width) - plot_width/2 - label_offset
            ax.text(x_label, lvl, f"{lvl:.3f}", ha='right', va='center', color='black',
                    fontsize=font_sizes.get('borehole_level', 10))
    # -------------------------------------------------------

    # Optionally, draw horizontal grid lines.
    if grid_settings.get('grid', False):
        grid_interval = grid_settings.get('grid_interval', 1.0)
        grid_label = grid_settings.get('grid_label', False)
        grid_label_font_size = grid_settings.get('grid_label_font_size', 8)
        # Use np.arange to ensure the bottom-most grid is included.
        grid_values = np.arange(global_y_max, global_y_min - grid_interval/2, -grid_interval)
        for y in grid_values:
            ax.axhline(y, color='gray', linestyle=(0, (3,3)), linewidth=0.5, clip_on=False)
            if grid_label:
                x_center = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2
                ax.text(x_center, y, f"{y:.3f} m", ha='center', va='bottom', color='gray', fontsize=grid_label_font_size)
    
    figure.canvas.draw()
