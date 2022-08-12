# Revit Assembly

Pipeline to extract geometric relationship between components of Revit model.

## Installation
# Dependencies 
     - networkx
     - pprint
     - pyvis
     - json
     - os
     - sys
     - clr
# Revit plugin 
     - RevitPython
     - RevitLookup (for debugging)

# Run _revit2text.py in Revit through RevitPython plugin
   For each component in Revit family -> Try to move in XYZ direction -> Trigger Error -> Extract relevant elements in json format

# Run _text2graph.py -> create networkx graph -> visualize with PyVis


## Example dataset

examples show most basic graph with column, window from Revit library
dataset is a small sample dataset extracted with pipeline. Examples are from Revit basic library and https://www.bimobject.com/

## License
