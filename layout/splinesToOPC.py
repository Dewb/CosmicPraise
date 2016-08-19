#Author-Michael Dewberry
#Description-Generate data for an OPC pixel layout from the splines in selected sketches

import adsk.core, adsk.fusion, adsk.cam, traceback
import json

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        res = ui.inputBox("Number of LEDs per spline:")        
        
        if res[1] or int(res[0]) <= 0: # cancelled        
            return
        
        numLEDs = int(res[0])  
        output = {}
        output['_names'] = []
        
        for sel in ui.activeSelections:
            sketch = adsk.fusion.Sketch.cast(sel.entity)
            if sketch:
                splines = sketch.sketchCurves.sketchFittedSplines
                for index, spline in enumerate(splines):
                    name = sketch.name + str(index)
                    pts = splineToLEDPoints(spline, numLEDs)
                    output[name] = pts
                    output['_names'].append(name)
                    
        output['_names'].sort()
                    
        #print(json.dumps(output))
         
        fd = ui.createFileDialog()
        fd.isMultiSelectEnabled = False
        fd.title = "Specify filename to save points to"
        fd.filter = 'JSON files (*.json)'
        fd.filterIndex = 0
        dialogResult = fd.showSave()
        if dialogResult == adsk.core.DialogResults.DialogOK:
            stream = open(fd.filename, 'w')
            stream.writelines(json.dumps(output, indent=2, sort_keys=True))
            stream.close()
        else:
            return
         
    except:
        print('Failed:\n{}'.format(traceback.format_exc()))
     

def splineToLEDPoints(spline, numLEDs):

    pts = []
    for i in range(numLEDs):
        pts.append(spline.worldGeometry.evaluator.getPointAtParameter(i/numLEDs)[1].asArray())
        
    return pts
        


    