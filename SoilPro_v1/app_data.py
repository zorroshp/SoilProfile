"""
Module: app_data.py
This module holds application‐specific data such as paper sizes for PDF export,
a full color palette dictionary, and helper functions (e.g. to lighten colors).
"""

# Paper sizes in millimeters
PAPER_SIZES_MM = {
    "A0": (841, 1189),
    "A1": (594, 841),
    "A3": (297, 420),
    "A4": (210, 297),
    "Letter": (216, 279),  # Approximate dimensions: 216x279 mm
}

def convert_to_lighter(hex_color: str, factor: float = 0.5) -> str:
    """
    Convert a hex color (e.g. '#RRGGBB') to a lighter version by blending it with white.
    """
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    lr = int(r + (255 - r) * factor)
    lg = int(g + (255 - g) * factor)
    lb = int(b + (255 - b) * factor)
    return f"#{lr:02x}{lg:02x}{lb:02x}"

# Color Palettes for the SoilPro Application
COLOR_PALETTES = {
    "Geotech 12": [
        "#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6",
        "#4292c6", "#2171b5", "#08519c", "#08306b", "#082252",
        "#081538", "#080c1e",
    ],
    "Earth tones": [
        "#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014",
        "#cc4c02", "#993404", "#662506", "#4d1c02", "#331302",
        "#1a0a01", "#000000",
    ],
    "Clay": [
        "#FDF4E3", "#FCEAD1", "#FBD0B9", "#F9B6A1", "#F89C89",
        "#F78271", "#F56859", "#F34E41", "#F13429", "#EE1A11",
        "#EC0000", "#D40000",
    ],
    "Rock": [
        "#EDEDED", "#DBDBDB", "#C9C9C9", "#B7B7B7", "#A5A5A5",
        "#939393", "#818181", "#6F6F6F", "#5D5D5D", "#4B4B4B",
        "#393939", "#272727",
    ],
    "Organic": [
        "#E8F5E9", "#C8E6C9", "#A5D6A7", "#81C784", "#66BB6A",
        "#4CAF50", "#43A047", "#388E3C", "#2E7D32", "#1B5E20",
        "#0D4F10", "#003300",
    ],
    "Terra Firma": [
        "#F7F1E1", "#EEDCC0", "#E4C69F", "#DAB07E", "#D0955E",
        "#C67A3D", "#BA603C", "#AE463B", "#A42C3A", "#991238",
        "#8F0037", "#850036",
    ],
    "Neon Circuit Burst": [
        "#39FF14", "#2EFEF7", "#FF073A", "#F7FE2E", "#FE2EC8",
        "#FF8000", "#FF1493", "#00BFFF", "#7FFF00", "#FF4500",
        "#ADFF2F", "#FF69B4",
    ],
    "elemental harmony": [
        "#DFF0E1", "#BCE0C9", "#99D1B1", "#76C299", "#53B381",
        "#30A269", "#0D9351", "#0A7C45", "#075C38", "#04472C",
        "#03331F", "#022015",
    ],
    "Blue Agent": [
        "#E0F7FA", "#B2EBF2", "#80DEEA", "#4DD0E1", "#26C6DA",
        "#00BCD4", "#00ACC1", "#0097A7", "#00838F", "#006064",
        "#004D40", "#00332E",
    ],
    "Desert Ember": [
        "#FFF4E6", "#FFE8CC", "#FFDBB3", "#FFCF99", "#FFC27F",
        "#FFB766", "#FFAA4D", "#FF9E33", "#FF921A", "#FF8500",
        "#E67A00", "#CC6F00",
    ],
    "Harvest Harmony": [
        "#FFF8E1", "#FFECB3", "#FFE082", "#FFD54F", "#FFCA28",
        "#FFC107", "#FFB300", "#FFA000", "#FF8F00", "#FF6F00",
        "#E65100", "#BF360C",
    ],
    "Finn": [
        "#E8EAF6", "#C5CAE9", "#9FA8DA", "#7986CB", "#5C6BC0",
        "#3F51B5", "#3949AB", "#303F9F", "#283593", "#1A237E",
        "#121858", "#0D1240",
    ],
    "Disturbed": [
        "#FDEBD0", "#FAD7A0", "#F8C471", "#F5B041", "#F39C12",
        "#E67A22", "#D35400", "#BA4A00", "#A04000", "#873600",
        "#6E2C00", "#562200",
    ],
    "Urban Slate": [
        "#E0E0E0", "#C0C0C0", "#A0A0A0", "#808080", "#606060",
        "#404040", "#202020", "#1F1F1F", "#1A1A1A", "#141414",
        "#0F0F0F", "#0A0A0A",
    ],
    "Canyon Dust": [
        "#F4E1D2", "#E8D1B8", "#DCBF9E", "#D0AD84", "#C49B6A",
        "#B88850", "#AD7526", "#A1610C", "#965000", "#8A3F00",
        "#7F2E00", "#732D00",
    ],
    "Red Shift": [
        "#FF0000", "#FF8000", "#FFFF00", "#BFFF00", "#80FF00",
        "#00FF00", "#00FF80", "#00BFFF", "#0000FF", "#4000BF",
        "#600099", "#800080",
    ],
    "Reverse Red Shift": [
        "#800080", "#600099", "#4000BF", "#0000FF", "#00BFFF", "#00FF80",
        "#00FF00", "#80FF00", "#BFFF00", "#FFFF00", "#FF8000", "#FF0000",
    ],
}

# Soil type colours dictionary.
SOIL_TYPE_COLOURS = {
    "FILL": "#8B4513",
    "MC": "#6FACF7",
    "F1": "#FFFF11",
    "F2": "#041A7D",
    "E": "#B9C10D",
    "OA(E)": "#FF0032",
    "OA(D)": "#FF0032",
    "OA(C)": "#FF335C",
    "OA(B)": "#FF335C",
    "OA(A)": "#FF4D76",
    "FCBB": "#E2581D",
    "S(VI)": "#4BB12E",
    "S(V)": "#4BB12E",
    "S(IV)": "#77D55D",
    "S(III)": "#AAE59A",
    "S(II)": "#AAE59A",
    "S(I)": "#AAE59A",
    "G(VI)": "#707070",
    "G(V)": "#707070",
    "G(IV)": "#999999",
    "G(III)": "#BFBFBF",
    "G(II)": "#BFBFBF",
    "G(I)": "#BFBFBF",
}
