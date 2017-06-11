import adsk.core
import adsk.fusion
import traceback

import os
import sys
sys.path.append(os.path.dirname(__file__))
from BMLib import (
    genFrontPoints,
    genBackPoints,
    genLeftPoints,
    genRightPoints,
    genBottomPoints,
    genTopPoints,
)

# global set of event handlers to keep them referenced for the duration of the command
handlers = []

app = adsk.core.Application.get()
if app:
    ui = app.userInterface

DEFAULT_WIDTH = '500 mm'
DEFAULT_HEIGHT = '300 mm'
DEFAULT_DEPTH = '400 mm'
DEFAULT_THICKNESS = '6 mm'

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

def buildAll(component, w, h, d, thickness):
    buildFront(component, w, h, d, thickness)
    # buildBack(component, w, h, d, thickness)
    # buildLeft(component, w, h, d, thickness)
    # buildRight(component, w, h, d, thickness)
    # buildBottom(component, w, h, d, thickness)
    # buildTop(component, w, h, d, thickness)

def buildFront(component, w, h, d, thickness):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketchPoints(sketch, genFrontPoints(w, h, d, thickness))
    # e = extrudeSketch(component, sketch, thickness)
    # e.faces[0].body.name = "Front"
    # moveExt(component, e, 'z', d - thickness)

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

def sketchPoints(sketch, points):
    lines = sketch.sketchCurves.sketchLines
    points = list(points)

    lastX, lastY = points[-1]
    for (x, y) in points:
        lines.addByTwoPoints(
            adsk.core.Point3D.create(lastX, lastY, 0),
            adsk.core.Point3D.create(x, y, 0),
        )
        lastX, lastY = x, y

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
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            design = app.activeProduct
            if not design:
                ui.messageBox('No active Fusion design', 'No Design')
                return
            component = design.rootComponent

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
                        w_input_obj = w_input_objs[0] # width_input_obj.length
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

            if (w_input_obj == None or h_input_obj == None or d_input_obj == None or t_input_obj == None):
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

            cmd.commandInputs.addValueInput(
                'widthInput',
                'Width (mm)',
                'mm',
                adsk.core.ValueInput.createByString(DEFAULT_WIDTH)
            )

            cmd.commandInputs.addValueInput(
                'heightInput',
                'Height (mm)',
                'mm',
                adsk.core.ValueInput.createByString(DEFAULT_HEIGHT)
            )

            cmd.commandInputs.addValueInput(
                'depthInput',
                'Depth (mm)',
                'mm',
                adsk.core.ValueInput.createByString(DEFAULT_DEPTH)
            )

            cmd.commandInputs.addValueInput(
                'thicknessInput',
                'Wall Thickness',
                'mm',
                adsk.core.ValueInput.createByString(DEFAULT_THICKNESS)
            )

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