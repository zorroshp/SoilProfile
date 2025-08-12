"""
Module: plotter.py
This module provides functions to extract borehole data from an input table,
assign colors to layers, and generate a combined soil profile plot on a single axis.
Borehole 1 is centered at x = 0 and Borehole 2 is centered at x = (plot_gap + plot_width).
In addition, manual y–axis labels are drawn:
    - For Borehole 1: labels appear on the right side.
    - For Borehole 2: labels appear on the left side.
"""

from library import plt, np, mticker

def extract_borehole_data(table) -> list:
    """
    Extract borehole layer data from the input table.
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
            continue
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
    Plot a single borehole's soil profile on the given axis.
    """
    if not data:
        return

    ax.text(x_offset,
            max([d['start'] for d in data]) + 0.05 * (max([d['start'] for d in data]) - min([d['end'] for d in data])),
            borehole_name, ha='center', fontsize=font_sizes.get('title', 12))
    ax.set_xticks([])
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(x_offset - plot_width/2, x_offset + plot_width/2)

    local_top = max(d['start'] for d in data)
    local_bottom = min(d['end'] for d in data)
    x_left, x_right = ax.get_xlim()

    rect = plt.Rectangle((x_left, local_bottom), x_right - x_left, local_top - local_bottom,
                         fill=False, edgecolor='black', linewidth=1, zorder=1, clip_on=False)
    ax.add_patch(rect)

    margin = 0.2 * plot_width
    for layer in data:
        thickness = abs(layer['start'] - layer['end'])
        bottom_val = min(layer['start'], layer['end'])
        color = colors.get(layer['layer'], "#CCCCCC")
        ax.bar(x_offset, thickness, width=plot_width, bottom=bottom_val,
               color=color, edgecolor='black', linewidth=0.5, zorder=2)
        if label_side == "left":
            text_x = (x_offset - plot_width/2) - margin
            ha = "right"
        else:
            text_x = (x_offset + plot_width/2) + margin
            ha = "left"
        spt_display = f"SPT: {layer['spt']}" if layer['spt'] not in [None, ""] else ""
        label_text = layer['layer'] if not spt_display else f"{layer['layer']}\n{spt_display}"
        ax.text(text_x, bottom_val + thickness / 2, label_text,
                ha=ha, va='center', fontsize=font_sizes.get('stack_bar', 9), zorder=3)

def generate_borehole_profile_plot(figure, borehole1_data: list, borehole2_data: list, borehole_names: tuple,
                                   plot_width: float, plot_gap: float, font_sizes: dict, grid_settings: dict,
                                   palette_name: str, palettes: dict, halftone: bool, convert_to_lighter_func,
                                   color_mode: str = "palette", soil_type_colors=None):
    """
    Generate a combined soil profile plot for two boreholes.
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
    
    if color_mode == "soil":
        if soil_type_colors is None:
            soil_type_colors = {}
        colors = {layer: soil_type_colors.get(layer.strip(), "#CCCCCC") for layer in sorted_layers}
    else:
        colors = assign_layer_colors(sorted_layers, palette_name, palettes, halftone, convert_to_lighter_func)

    ax = figure.add_subplot(111)
    
    if borehole1_data:
        plot_borehole_profile(ax, borehole1_data, borehole_names[0], colors, plot_width, "left", font_sizes, x_offset=0)
    if borehole2_data:
        plot_borehole_profile(ax, borehole2_data, borehole_names[1], colors, plot_width, "right", font_sizes,
                              x_offset = plot_gap + plot_width)
    
    ax.set_xlim(-plot_width/2, (plot_gap + plot_width) + plot_width/2)
    ax.set_ylim(global_y_min, global_y_max)
    ax.patch.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    ax.set_yticklabels([])

    label_offset = 0.3 * plot_width
    if borehole1_data:
        levels1 = sorted(set([d['start'] for d in borehole1_data]) | set([d['end'] for d in borehole1_data]), reverse=True)
        for lvl in levels1:
            x_label = (0 + plot_width/2) + label_offset
            ax.text(x_label, lvl, f"{lvl:.3f}", ha='left', va='center', color='black',
                    fontsize=font_sizes.get('borehole_level', 10))
    if borehole2_data:
        levels2 = sorted(set([d['start'] for d in borehole2_data]) | set([d['end'] for d in borehole2_data]), reverse=True)
        for lvl in levels2:
            x_label = (plot_gap + plot_width) - plot_width/2 - label_offset
            ax.text(x_label, lvl, f"{lvl:.3f}", ha='right', va='center', color='black',
                    fontsize=font_sizes.get('borehole_level', 10))
    
    if grid_settings.get('grid', False):
        grid_interval = grid_settings.get('grid_interval', 1.0)
        grid_label = grid_settings.get('grid_label', False)
        grid_label_font_size = grid_settings.get('grid_label_font_size', 8)
        grid_values = np.arange(global_y_max, global_y_min - grid_interval/2, -grid_interval)
        for y in grid_values:
            ax.axhline(y, color='gray', linestyle=(0, (3,3)), linewidth=0.5, clip_on=False)
            if grid_label:
                x_center = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2
                ax.text(x_center, y, f"{y:.3f} m", ha='center', va='bottom', color='gray', fontsize=grid_label_font_size)
    
    figure.canvas.draw()
