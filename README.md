# Vector Recursion Workbench
This is a tool for laying out and generating recursively nested polygons that can be exported as an SVG. Designed with laser cutting in mind. Programmed by [Nathan Williams](https://github.com/nathanlws) and designed by Jason Fletcher.

![screenshot1](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Archive/Vector-Recursion-Workbench_screenshot1.JPG)

![screenshot2](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Archive/Vector-Recursion-Workbench_screenshot2.JPG)


## Archived
This software is no longer being maintained and issues will not be fixed, but you are welcome to fork it.


## Dependencies
Python 2.7.8  
wxPython 3.0  
PyOpenGL 3.1.1a1  


## Usage
Run this script in a CMD shell to initiate the Vector Recursion Workbench GUI:  
```python VRW-gui.py```

-----

## Documentation
### Preview Window
- **Draw Guide Line**: Allows you to draw a guide line onto the canvas. (hotkey is ‘d’.) To cancel drawing a guide line hit ‘ESC’. If you need to slice a specific shape, then first click to select that shape and then draw the guide line within it.  
- **Delete Guide Lines**: Allows you to delete a specific guide line by clicking on it. (hotkey is ‘x’.) Useful mainly for creating shapes such as a pentagon. Beware: deleting a line is risky and may break your layout, so be sure to save prior.  
- Undo (cmd-z) and Redo (cmd-shft-z) are functional. Beware: undo-ing a guide line is risky and may break your layout, so be sure to save prior.  
- **Snapping**: When drawing a guide line, the cursor will snap to the nearest corner when within a certain proximity.  
- **Hide Guide Lines**: Makes the guide lines invisible within the preview area so that you can see the recursion as it will be exported.  
- **Hide Shape #’s**: Makes the shape #’s invisible within the preview area. But you can still select a shape.  
- **Preview**: Allows you to preview just the guide lines, or preview the guide lines and recursion in tandem.  
- **Aspect Ratio**: Allows you to fit the recursion to the canvas, or stretch the recursion to the canvas. When exporting, fit will always be used. But stretch is useful if you’re doing projection mapping and want to layout in context.

### Shape Attributes
- Select a shape by click on the # within the preview window.  
- **Direction**: Decide whether the recursion iterates clockwise or counter-clockwise.  
- **Depth**: Limits the amount of iterations.  
- **Step**: Increases or decreases the spacing of the shape recursion.  
- **Inner**: Increases or decreases the spacing of the shape recursion, but affecting the inner iterations more heavily. This allows you to decide on the complexity of the inner iterations without affecting the outer iterations.  
- **Reverse Colors**: Swap the starting color. This is important for maintaining a cohesive pattern when laying out a piece.  
- **Disable**: This will turn off recursions for the currently selected shape and it will not render when exported. This is useful for creating unique canvas shapes, such as a hexagon. It’s also useful for creating empty spaces within your layout. Or approaching it creatively to create a silhouette within your layout.  
- **Footer**: Adds extra spacing around each triangle. Affects the overall recursion evenly.  
- **Buffer**: Adds extra spacing around each triangle. Affects the inner iterations more heavily.  
- **Offset**: Adjusts the starting point of which the Buffer begins within the outer iterations.

### Global Attributes
- **Step**: Increases or decreases the spacing of the shape recursion for the whole layout. Every shape is affected equally, without resetting the individual Shape Step setting.  
- **Colors**: Determine what two colors are used to alternate within the recursion.  
- **Canvas Width/Height**: Set in pixels of your monitor. Just a way to determine the aspect ratio since the SVG exports are vector in nature.  
- **Load Background Image**: Allows you to load a background image within the preview window. This background image does not export, it’s only used as a helper for you to layout Guide Lines. It can be helpful for tracing complex patterns you want to draw. Within the Examples folder check out the ‘FaceSilhouette_001’ and ‘Hands_001’ examples.

### Saving & Rendering
- **File > Save as**: Writes an JSON file which can be opened later and edited.  
- **File > Export**: Writes an SVG of the whole canvas. This is the easiest approach for when you’re doing a single laser cut piece.  
- **File > Export Shapes**: Writes multiple SVG’s, one SVG for each individual shape on the canvas. This option is useful if you want to laser cut each shape individually and then assemble them all together after completed. So long as you plan with the max dimensions of your laser cutter in mind, then you can precisely fill a wall of unlimited scale.

### Post-Production
- If you need to alter the exported SVG or combine multiple SVG’s, [Inkscape](https://inkscape.org/) is free and highly recommended.

-----

## History
This software was programmed by [Nathan Williams](https://github.com/nathanlws) and designed by Jason Fletcher.

I was first introduced to this technique through drawing by hand. Over the years I experimented with different approaches and started using an exacto blade to cutout the patterns into paper. I loved the resulting artworks but the effort required was enormous and difficult on my hands. So for many years I dreamed of creating a software which would automate the process and make laser cutting possible. While studying in college, Alex Horn helped me to create an early version of the idea first in Pure Data and then Adobe Flash. Then many years later I met Nathan Williams and randomly shared my idea over a beer and a collaboration bloomed. This software is the result.

Check out the Archive folder to see early sketches of this software.


## License
The MIT License (MIT)  
Copyright (c) 2014-2016 Nathan Williams, Jason Fletcher  
It is free software and may be redistributed under the terms specified in the LICENSE file.


## Example Renders Gallery
![gallery1](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/hexagon_001_rasterized.jpg)

![gallery2](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/hexagon_001_cutout_rasterized.jpg)

![gallery3](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/vanilla_007_rasterized.jpg)

![gallery4](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/vanilla_007_cutout_rasterized.jpg)

![gallery5](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/hexagon_003b_rasterized.jpg)

![gallery6](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/handcut_mimic_001b_rasterized.jpg)

![gallery7](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/GoldenRatio_002_rasterized.jpg)

![gallery8](https://raw.githubusercontent.com/nuclearsugar/VectorRecursionWorkbench/master/Examples/GoldenRatio_001_rasterized.jpg)
