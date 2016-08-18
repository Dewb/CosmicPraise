#Author-Michael Dewberry
#Description-Generate data for an OPC pixel layout from the splines in selected sketches

import adsk.core, adsk.fusion, adsk.cam, traceback
import json

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        numLEDs = 113;  
        output = {}
        
        for sel in ui.activeSelections:
            sketch = adsk.fusion.Sketch.cast(sel.entity)
            if sketch:
                splines = sketch.sketchCurves.sketchFittedSplines
                for index, spline in enumerate(splines):
                    name = sketch.name + str(index)
                    pts = splineToLEDPoints(spline, numLEDs)
                    output[name] = pts
                    
        print(json.dumps(output))
                
    except:
        print('Failed:\n{}'.format(traceback.format_exc()))
     

def splineToLEDPoints(spline, numLEDs):

    pts = []
    for i in range(numLEDs):
        pts.append(spline.worldGeometry.evaluator.getPointAtParameter(i/numLEDs)[1].asArray())
        
    return pts
        


    