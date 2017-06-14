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
        lines = sketch.sketchCurves.sketchLines;

        line1 = lines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(3, 0, 0))
        sketch.geometricConstraints.addHorizontal(line1)
        dimension1 = sketch.sketchDimensions.addDistanceDimension(
            line1.startSketchPoint,
            line1.endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            line1.startSketchPoint.geometry) # howto: a good place to place the dimension
        dimension1.parameter.value = 2; # howto: set a fixed value for a dimension, 2 cm
        # do dimension params exist across sketches? YES IT DOES!!!
        # dimension1.parameter.expression = "d1"; # test referencing this dimension's length to a line in another sketch
        dimension1_param_name = dimension1.parameter.name # howto: get the name for a dimension's parameter

        line2 = lines.addByTwoPoints(
            adsk.core.Point3D.create(5, 0, 0),
            adsk.core.Point3D.create(6, 0, 0))
        sketch.geometricConstraints.addHorizontal(line2)
        dimension2 = sketch.sketchDimensions.addDistanceDimension(
            line2.startSketchPoint,
            line2.endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            line2.startSketchPoint.geometry) # howto: get Point3D from SketchPoint
        dimension2.parameter.expression = dimension1_param_name; # howto: set a calculated value for a dimension

        sketch.geometricConstraints.addCoincident(
            line1.endSketchPoint,
            sketch.originPoint) # howto: make a line coincident to the origin, origin Point entity
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))