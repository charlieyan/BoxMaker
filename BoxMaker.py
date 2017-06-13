import adsk.core
import adsk.fusion
import traceback

import os
import sys
sys.path.append(os.path.dirname(__file__))
from itertools import chain

IDEAL_NOTCH_WIDTH = 4

# global set of event handlers to keep them referenced for the duration of the command
handlers = []

app = adsk.core.Application.get()
if app:
    ui = app.userInterface
    product_units_mgr = app.activeProduct.unitsManager
    design = adsk.fusion.Design.cast(app.activeProduct)
    all_params = design.allParameters

DEFAULT_WIDTH = '500 mm'
DEFAULT_HEIGHT = '300 mm'
DEFAULT_DEPTH = '400 mm'
DEFAULT_THICKNESS = '6 mm'

'''
110 mm deep
80 mm wide
80 mm tall
'''

def genHorizontalLinePoints(x, y, length, notchHeight, offset):
    idealNotch = abs(notchHeight) * IDEAL_NOTCH_WIDTH
    notchCount = int(abs(length) / idealNotch)

    if notchCount % 2 == 0:
        notchCount += 1

    notchWidth = length / notchCount

    # First point
    yield (x + offset, y)

    # Two points for every side of a notch
    for i in range(1, notchCount):
        x = x + notchWidth
        yield (x, y if ((i % 2) == 1) else y + notchHeight)
        yield (x, y if ((i % 2) == 0) else y + notchHeight)
    # Last point is omitted (because it will be the first point of the next side)

def genVerticalLinePoints(x, y, length, notchHeight, offset):
    # Symmetrical with the horizontal version, but with x & y swapped
    points = genHorizontalLinePoints(y, x, length, notchHeight, offset)
    for y, x in points:
        yield (x, y)

def genBackPoints(w, h, d, t):
    return genFrontPoints(w, h, d, t)

def genLeftPoints(w, h, d, t):
    return chain(
        genHorizontalLinePoints(0, 0, -d, t, -t),
        genVerticalLinePoints(-d + t, 0, h, -t, 0),
        genHorizontalLinePoints(-d, h - t, d, t, t),
        genVerticalLinePoints(-t, h, -h, t, -t),
    )

def genRightPoints(w, h, d, t):
    return genLeftPoints(w, h, d, t)

def genBottomPoints(w, h, d, t):
    return chain(
        genHorizontalLinePoints(0, -t, w, t, t),
        genVerticalLinePoints(w - t, 0, -d, t, -t),
        genHorizontalLinePoints(w, -d + t, -w, -t, -t),
        genVerticalLinePoints(t, -d, d, -t, t),
    )

def genTopPoints(w, h, d, t):
    return chain(
        genHorizontalLinePoints(0, 0, w, -t, 0),
        genVerticalLinePoints(w, 0, -d, -t, 0),
        genHorizontalLinePoints(w, -d, -w, t, 0),
        genVerticalLinePoints(0, -d, d, t, 0),
    )

def getSelectedObjects(selectionInput):
    objects = []
    for i in range(0, selectionInput.selectionCount):
        selection = selectionInput.selection(i)
        selectedObj = selection.entity
        if adsk.fusion.BRepBody.cast(selectedObj) or \
           adsk.fusion.BRepFace.cast(selectedObj) or \
           adsk.fusion.Occurrence.cast(selectedObj) or \
           adsk.fusion.SketchLine.cast(selectedObj): # SketchLine is the type, derived from SketchCurve
           objects.append(selectedObj)
    return objects

def buildAll(component, w, h, d, t):
    # expected dimensions in cm
    # builds a box on the x,z plane
    # with y being height, depth being along the z axis

    buildFront(component, w, h, d, t)
    # buildBack(component, w, h, d, thickness)
    # buildLeft(component, w, h, d, thickness)
    # buildRight(component, w, h, d, thickness)
    # buildBottom(component, w, h, d, thickness)
    # buildTop(component, w, h, d, thickness)

def genFrontPoints(w, h, d, t):
    return chain(
        genHorizontalLinePoints(0, 0, w, t, 0), # bottom
        genVerticalLinePoints(w, 0, h, -t, 0), # right
        genHorizontalLinePoints(w, h - t, -w, t, 0), # top
        genVerticalLinePoints(0, h, -h, t, -t), # left
    )

def buildFront(component, w, h, d, t):
    sketch = component.sketches.add(component.xYConstructionPlane)
    # included_t = sketch.project(t).item(0) # include
    points = list(genFrontPoints(
        w.length,
        h.length,
        d.length,
        t.length))
    ui.messageBox("len(points): " + str(len(points)))
    sketchPoints(sketch, points, w, h, t)
    e = extrudeSketch(component, sketch, t.length)
    e.faces[0].body.name = "Front"
    moveExt(component, e, 'z', d.length - t.length)

'''
    lines = sketch.sketchCurves.sketchLines
    constraints = sketch.geometricConstraints
    # lastX, lastY = points[-1]
    is_notch = False
    lastX = None
    lastY = None
    last_line = None
    last_notch_line = None
    for (x, y) in points:
        if (lastX != None and lastY != None):
            new_line = None
            if (not is_notch):
                new_line = lines.addByTwoPoints(
                    adsk.core.Point3D.create(lastX, lastY, 0),
                    adsk.core.Point3D.create(x, y, 0),
                )
            else:
                point_1 = adsk.core.Point3D.create(lastX, lastY, 0)
                point_2 = adsk.core.Point3D.create(x, y, 0)
                new_line = lines.addByTwoPoints(point_1, point_2)
                # sketch_dimension = sketch.sketchDimensions.addDistanceDimension(
                #     new_line.startSketchPoint,
                #     new_line.endSketchPoint,
                #     adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                #     adsk.core.Point3D.create(5.5, -1, 0))
                # constraints.addEqual(new_line, t)
                if (last_notch_line != None):
                    constraints.addEqual(last_notch_line, new_line)
                last_notch_line = new_line
            is_notch = not is_notch
            if (last_line != None and new_line != None):
                constraints.addCoincident(
                    last_line.endSketchPoint,
                    new_line.startSketchPoint)
            last_line = new_line
        lastX = x
        lastY = y
'''

def sketchPoints(sketch, points, plane_ref_1, plane_ref_2, t): # plane_ref_2 is the 'height' dimension
    lines = sketch.sketchCurves.sketchLines
    constraints = sketch.geometricConstraints
    lastX, lastY = points[-1]
    is_notch = False
    last_notch_line = None
    last_line = None
    for i, (x, y) in enumerate(points):
        new_line = lines.addByTwoPoints(
            adsk.core.Point3D.create(lastX, lastY, 0),
            adsk.core.Point3D.create(x, y, 0),
        )

        # if (is_notch):
        #     if (last_notch_line != None):
        #         constraints.addEqual(last_notch_line, new_line)
        #     last_notch_line = new_line

        if (last_line != None and new_line != None):
            constraints.addCoincident(
                last_line.endSketchPoint,
                new_line.startSketchPoint)

        lastX, lastY = x, y

        is_notch = not is_notch
        side_i = i % len(points) / 4
        if (side_i == 0):
            is_notch = False

        last_line = new_line

def buildBack(component, w, h, d, thickness):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketchPoints(sketch, genBackPoints(w, h, d, thickness))
    e = extrudeSketch(component, sketch, thickness)
    e.faces[0].body.name = "Back"

def buildLeft(component, w, h, d, thickness):
    sketch = component.sketches.add(component.yZConstructionPlane)
    sketchPoints(sketch, genLeftPoints(w, h, d, thickness))
    e = extrudeSketch(component, sketch, thickness)
    e.faces[0].body.name = "Left"

def buildRight(component, w, h, d, thickness):
    sketch = component.sketches.add(component.yZConstructionPlane)
    sketchPoints(sketch, genRightPoints(w, h, d, thickness))
    e = extrudeSketch(component, sketch, thickness)
    e.faces[0].body.name = "Right"
    moveExt(component, e, 'x', w - thickness)

def buildBottom(component, w, h, d, thickness):
    sketch = component.sketches.add(component.xZConstructionPlane)
    sketchPoints(sketch, genBottomPoints(w, h, d, thickness))
    e = extrudeSketch(component, sketch, thickness)
    e.faces[0].body.name = "Bottom"

def buildTop(component, w, h, d, thickness):
    sketch = component.sketches.add(component.xZConstructionPlane)
    sketchPoints(sketch, genTopPoints(w, h, d, thickness))
    e = extrudeSketch(component, sketch, thickness)
    e.faces[0].body.name = "Top"
    moveExt(component, e, 'y', h - thickness)

def moveExt(component, ext, axis, distance):
    if axis not in ('x', 'y', 'z'):
        raise ValueError("Axis must be one of x, y, z.")

    entities1 = adsk.core.ObjectCollection.create()
    entities1.add(ext.bodies.item(0))

    # Create a transform to do move
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(
        distance if axis == 'x' else 0.0,
        distance if axis == 'y' else 0.0,
        distance if axis == 'z' else 0.0,
    )

    # Create a move feature
    moveFeats = component.features.moveFeatures
    moveFeatureInput = moveFeats.createInput(entities1, transform)
    moveFeats.add(moveFeatureInput)

def extrudeSketch(component, sketch, thickness):
    # Get the profile defined by item#0.
    prof = sketch.profiles.item(0)

    # Create an extrusion feature
    extrudes = component.features.extrudeFeatures
    extInput = extrudes.createInput(
        prof,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )

    # Define the extrude distance based on thickness
    distance = adsk.core.ValueInput.createByReal(thickness)
    extInput.setDistanceExtent(False, distance)

    # Create the extrusion.
    return extrudes.add(extInput)

class BoxMakerCommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            design = app.activeProduct
            if not design:
                ui.messageBox('No active Fusion design', 'No Design')
                return
            component = design.rootComponent
            unitsMgr = design.unitsManager

            inputs = {}
            w_input_obj = None
            h_input_obj = None
            d_input_obj = None
            t_input_obj = None
            for input in command.commandInputs:
                inputs[input.id] = input
                if (input.id == "w_line_input"):
                    w_input_objs = getSelectedObjects(input)
                    if (len(w_input_objs) > 0):
                        w_input_obj = w_input_objs[0]
                elif (input.id == "h_line_input"):
                    h_input_objs = getSelectedObjects(input)
                    if (len(h_input_objs) > 0):
                        h_input_obj = h_input_objs[0]
                elif (input.id == "d_line_input"):
                    d_input_objs = getSelectedObjects(input)
                    if (len(d_input_objs) > 0):
                        d_input_obj = d_input_objs[0]
                elif (input.id == "t_line_input"):
                    t_input_objs = getSelectedObjects(input)
                    if (len(t_input_objs) > 0):
                        t_input_obj = t_input_objs[0]

            if (w_input_obj == None
                or h_input_obj == None
                or d_input_obj == None
                or t_input_obj == None
                ):
                ui.messageBox("Missing something")
                return

            # Built it!
            buildAll(
                component,
                w_input_obj,
                h_input_obj,
                d_input_obj,
                t_input_obj
            )
            args.isValidResult = True
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class BoxMakerCommandDestroyHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class BoxMakerCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command

            onExecute = BoxMakerCommandExecuteHandler()
            onDestroy = BoxMakerCommandDestroyHandler()
            cmd.execute.add(onExecute)
            cmd.destroy.add(onDestroy)

            # keep the handler referenced globally
            handlers.append(onExecute)
            handlers.append(onDestroy)

            w_line_input = cmd.commandInputs.addSelectionInput(
                'w_line_input',
                'Select W Line',
                'Select W Line'
                )
            w_line_input.setSelectionLimits(1,1)
            w_line_input.addSelectionFilter('SketchLines')

            h_line_input = cmd.commandInputs.addSelectionInput(
                'h_line_input',
                'Select H Line',
                'Select H Line'
                )
            h_line_input.setSelectionLimits(1,1)
            h_line_input.addSelectionFilter('SketchLines')

            d_line_input = cmd.commandInputs.addSelectionInput(
                'd_line_input',
                'Select D Line',
                'Select D Line'
                )
            d_line_input.setSelectionLimits(1,1)
            d_line_input.addSelectionFilter('SketchLines')

            t_line_input = cmd.commandInputs.addSelectionInput(
                't_line_input',
                'Select T Line',
                'Select T Line'
                )
            t_line_input.setSelectionLimits(1,1)
            t_line_input.addSelectionFilter('SketchLines')

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def main():
    try:
        commandId = 'BoxMaker'
        commandName = 'BoxMaker'
        commandDescription = 'Create boxes with notched box-joint panels.'
        cmdDef = ui.commandDefinitions.itemById(commandId)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(
                commandId,
                commandName,
                commandDescription,
                './resources'
            )

        onCommandCreated = BoxMakerCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)

        # keep the handler referenced globally
        handlers.append(onCommandCreated)

        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminated when the script returns,
        # because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

main()