#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Constants/settings definition
"""

# Thresholds for processing and data creation
THRESHOLD_MIN_CUISINES = 14
THRESHOLD_MIN_LANGUAGES = 12
THRESHOLD_MIN_VOICE_LENGTH = 4000

# Preprocessing for visualization
Y_REPLACE_LANGUAGES_ABBREVIATIONS = True
X_ADD_CUISINE = False
Y_ADD_LANGUAGE = False
X_ADD_FLAGS = True
Y_ADD_FLAGS = True

# Plot layout
AXIS_ANNOTATION_TEXT_SIZE = 16

# Heatmap color palettes
# yapf: disable
HEATMAP_COLORSCALE_GREEN=[[0,   "rgb(178, 233, 201)"],
                          [0.1, "rgb(91, 207, 139)"],
                          [0.2, "rgb(69, 201, 123)"],
                          [0.3, "rgb(48, 164, 96)"],
                          [0.4, "rgb(35, 121, 70)"],
                          [0.5, "rgb(29, 99, 58)"],
                          [0.6, "rgb(22, 77, 45)"],
                          [0.7, "rgb(16, 55, 32)"],
                          [0.8, "rgb(10, 33, 19)"],
                          [0.9, "rgb(10, 33, 19)"],
                          [1.0, "rgb(10, 33, 19)"]]
HEATMAP_COLORSCALE_BLUE=[[0,   "rgb(197, 226, 254)"],
                         [0.1, "rgb(119, 188, 253)"],
                         [0.2, "rgb(42, 150, 252)"],
                         [0.3, "rgb(3, 131, 252)"],
                         [0.4, "rgb(50, 111, 213)"],
                         [1.0, "rgb(100, 0, 150)"]]
# yapf: enable
