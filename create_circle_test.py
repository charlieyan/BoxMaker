import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try: 
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        rootComp = design.rootComponent

        # Create a new sketch on the xy plane.
        sketches = rootComp.sketches;
        xzPlane = rootComp.xZConstructionPlane
        sketch = sketches.add(xzPlane)
        circles = sketch.sketchCurves.sketchCircles
        circle1 = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2)
        circle2 = circles.addByCenterRadius(adsk.core.Point3D.create(8, 3, 0), 3)
        circle3 = circles.addByCenterRadius(circle2.centerSketchPoint, 4)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))