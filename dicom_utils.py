import os
import pydicom
import vtk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from datetime import datetime
from threading import Thread
from ttkthemes import ThemedTk
from PIL import Image, ImageTk

# ... (funções anteriores permanecem inalteradas)

def view_dicom_series(patient_key, dicom_files):
    viewer_window = tk.Toplevel(root)
    viewer_window.title(f"Visualização DICOM - {patient_key}")

    render_window = vtk.vtkRenderWindow()
    render_window.SetWindowName(f"Visualização DICOM - {patient_key}")
    render_window.SetSize(800, 600)

    renderer = vtk.vtkRenderer()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()

    viewer = vtk.vtkImageViewer2()
    viewer.SetupInteractor(render_window_interactor)
    viewer.SetRenderer(renderer)

    for dicom_file in dicom_files:
        dicom_path = os.path.join(main_directory, patient_key, dicom_file)
        try:
            ds = pydicom.dcmread(dicom_path, force=True)
            reader = vtk.vtkDICOMImageReader()
            reader.SetFileName(dicom_path)
            viewer.SetInputConnection(reader.GetOutputPort())
            viewer.Render()

            render_window.Render()

            render_window_interactor.Start()

        except pydicom.errors.InvalidDicomError:
            print(f"Aviso: Ignorando arquivo DICOM inválido: {dicom_path}")


def calculate_slice_thickness(ds):
    try:
        return "{:.2f} mm".format(float(getattr(ds, 'SliceThickness', "N/A")))
    except ValueError:
        return "N/A"
    
    
