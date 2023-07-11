from vtk.web import protocols as vtk_protocols
from wslink import register as exportRpc

import vtk
from model.colormap import CUSTOM_COLORMAP
from model.presets import *

# -------------------------------------------------------------------------
# ViewManager
# -------------------------------------------------------------------------

class Dicom3D(vtk_protocols.vtkWebProtocol):
    def __init__(self):
        self._dicomDataPath = None
        self.colors = vtk.vtkNamedColors()

        # Pipeline
        self.reader = vtk.vtkDICOMImageReader()
        self.mapper = vtk.vtkSmartVolumeMapper()
        self.volProperty = vtk.vtkVolumeProperty()
        self.volume = vtk.vtkVolume()
        self.color = vtk.vtkColorTransferFunction()
        self.scalarOpacity = vtk.vtkPiecewiseFunction()

        self.checkLight = True
        self.checkBox = True

        # Cropping By Box
        self.boxRep = vtk.vtkBoxRepresentation()
        self.widget = vtk.vtkBoxWidget2()
        self.planes = vtk.vtkPlanes()

    @property
    def dicomDataPath(self):
        return self._dicomDataPath
    
    @dicomDataPath.setter
    def dicomDataPath(self, path):
        self._dicomDataPath = path

    @exportRpc("vtk.initialize")
    def createVisualization(self):
        interactor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        path = self.dataPath if self.dicomDataPath is not None else "./data/Ankle"

        # Reader
        self.reader.SetDirectoryName(path)
        self.reader.Update()

        # Mapper
        self.mapper.SetInputData(self.reader.GetOutput())

        # Volume Property
        self.volProperty.ShadeOn()
        self.volProperty.SetAmbient(0.1)
        self.volProperty.SetDiffuse(0.9)
        self.volProperty.SetSpecular(0.2)

        self.color.RemoveAllPoints()
        rgbPoints = CUSTOM_COLORMAP.get("STANDARD_CT").get("rgbPoints")
        for point in rgbPoints:
            self.color.AddRGBPoint(point[0], point[1], point[2], point[3])
        self.volProperty.SetColor(self.color)

        # Muscle CT
        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)
        self.volProperty.SetScalarOpacity(self.scalarOpacity)

        # Volume
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volProperty)

        # Cropping By Box
        self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
        self.boxRep.SetInsideOut(True)

        self.widget.SetRepresentation(self.boxRep)
        self.widget.SetInteractor(interactor)
        self.widget.GetRepresentation().SetPlaceFactor(1)
        self.widget.GetRepresentation().PlaceWidget(self.reader.GetOutput().GetBounds())
        self.widget.SetEnabled(True)

        ipwcallback = IPWCallback(self.planes, self.mapper)
        self.widget.AddObserver(vtk.vtkCommand.InteractionEvent, ipwcallback)
        self.widget.Off()

        # Render
        renderer.AddVolume(self.volume)
        renderer.ResetCamera()

        # Render Window
        renderWindow.Render()
        return self.resetCamera()

    @exportRpc("vtk.camera.reset")
    def resetCamera(self):
        renderWindow = self.getView('-1')

        renderWindow.GetRenderers().GetFirstRenderer().ResetCamera()
        renderWindow.Render()

        self.getApplication().InvalidateCache(renderWindow)
        self.getApplication().InvokeEvent('UpdateEvent')

        return -1

    @exportRpc("viewport.mouse.zoom.wheel")
    def updateZoomFromWheel(self, event):
        if 'Start' in event["type"]:
            self.getApplication().InvokeEvent('StartInteractionEvent')

        renderWindow = self.getView(event['view'])
        if renderWindow and 'spinY' in event:
            zoomFactor = 1.0 - event['spinY'] / 10.0

            camera = renderWindow.GetRenderers().GetFirstRenderer().GetActiveCamera()
            fp = camera.GetFocalPoint()
            pos = camera.GetPosition()
            delta = [fp[i] - pos[i] for i in range(3)]
            camera.Zoom(zoomFactor)

            pos2 = camera.GetPosition()
            camera.SetFocalPoint([pos2[i] + delta[i] for i in range(3)])
            renderWindow.Modified()

        if 'End' in event["type"]:
            self.getApplication().InvokeEvent('EndInteractionEvent')

    @exportRpc("vtk.dicom3d.light")
    def light(self):
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        if self.checkLight:
            renderer.SetBackground(self.colors.GetColor3d("Black"))
            self.boxRep.GetOutlineProperty().SetColor(1, 1, 1)
            self.checkLight = False
        else:
            renderer.SetBackground(self.colors.GetColor3d("White"))
            self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
            self.checkLight = True

        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')
        
    @exportRpc("vtk.dicom3d.presets.bone.ct")
    def showBoneCT(self):
        self.color.RemoveAllPoints()
        rgbPoints = BONE_CT.get("colorMap").get("rgbPoints")
        for point in rgbPoints:
            self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = BONE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow = self.getView('-1')
        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')
      
    @exportRpc("vtk.dicom3d.presets.angio.ct")
    def showAngioCT(self):
        self.color.RemoveAllPoints()
        rgbPoints = ANGIO_CT.get("colorMap").get("rgbPoints")
        for point in rgbPoints:
            self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = ANGIO_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow = self.getView('-1')
        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("vtk.dicom3d.presets.muscle.ct")
    def showMuscleCT(self):
        self.color.RemoveAllPoints()
        rgbPoints = MUSCLE_CT.get("colorMap").get("rgbPoints")
        for point in rgbPoints:
            self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow = self.getView('-1')
        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("vtk.dicom3d.presets.mip")
    def showMip(self):
        self.color.RemoveAllPoints()
        rgbPoints = MIP.get("colorMap").get("rgbPoints")
        if len(rgbPoints):
            for point in rgbPoints:
                self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MIP.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow = self.getView('-1')
        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("vtk.dicom3d.crop")
    def crop3d(self):
        # self.getApplication() -> vtkWebApplication()
        renderWindow = self.getView('-1')

        if self.checkBox:
            self.widget.On()
            self.checkBox = False
        else:
            self.widget.Off()
            self.checkBox = True

        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')

class IPWCallback():
    def __init__(self, planes: vtk.vtkPlanes, mapper: vtk.vtkSmartVolumeMapper):
        self.planes = planes
        self.mapper = mapper

    def __call__(self, obj: vtk.vtkBoxWidget2, event: str) -> None:
        obj.GetRepresentation().GetPlanes(self.planes)
        self.mapper.SetClippingPlanes(self.planes)