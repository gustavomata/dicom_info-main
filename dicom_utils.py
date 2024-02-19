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
    
import pydicom as dicom
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import CheckButtons
import os
import pyautogui
import pygetwindow as gw

import pydicom as dicom
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import CheckButtons
import os
import pyautogui
import pygetwindow as gw

def plot_slices(path):
    ct_images = os.listdir(path)

    # Extrair informações cruciais dos DICOMs
    slices = [dicom.read_file(os.path.join(path, s), force=True) for s in ct_images]
    slices = sorted(slices, key=lambda x: x.ImagePositionPatient[2])

    pixel_spacing = slices[0].PixelSpacing
    slices_thickness = slices[0].SliceThickness

    axial_aspect_ratio = pixel_spacing[1] / pixel_spacing[0]
    sagittal_aspect_ratio = pixel_spacing[1] / slices_thickness
    coronal_aspect_ratio = slices_thickness / pixel_spacing[0]

    img_shape = list(slices[0].pixel_array.shape)
    img_shape.append(len(slices))
    volume3d = np.zeros(img_shape)

    # Preencher o volume3d
    for i, s in enumerate(slices):
        array2D = s.pixel_array
        volume3d[:, :, i] = array2D

    # Configurar o tamanho da tela
    fig, axs = plt.subplots(2, 2, figsize=(15, 12))  # Ajuste o tamanho aqui

    axial_ax = axs[0, 0]
    sagittal_ax = axs[0, 1]
    coronal_ax = axs[1, 0]

    divider_axial = make_axes_locatable(axial_ax)
    cax_axial = divider_axial.append_axes("right", size="5%", pad=0.1)

    divider_sagittal = make_axes_locatable(sagittal_ax)
    cax_sagittal = divider_sagittal.append_axes("right", size="5%", pad=0.1)

    divider_coronal = make_axes_locatable(coronal_ax)
    cax_coronal = divider_coronal.append_axes("right", size="5%", pad=0.1)

    # Inicialização rápida da imagem
    im_axial = axial_ax.imshow(volume3d[:, :, img_shape[2] // 2], cmap='gray', picker=True, aspect='auto', extent=[0, img_shape[1], 1, img_shape[0]])
    axial_ax.set_title(f"Axial - Slice {img_shape[2] // 2}")
    axial_cbar = plt.colorbar(im_axial, cax=cax_axial)

    im_sagittal = sagittal_ax.imshow(volume3d[:, img_shape[1] // 2, :], cmap='gray', picker=True, aspect='auto', extent=[0, img_shape[1], 1, img_shape[0]])
    sagittal_ax.set_title(f"Sagittal - Slice {img_shape[1] // 2}")
    sagittal_cbar = plt.colorbar(im_sagittal, cax=cax_sagittal)

    im_coronal = coronal_ax.imshow(volume3d[img_shape[0] // 2, :, :].T, cmap='gray', picker=True, aspect='auto', extent=[0, img_shape[1], 1, img_shape[0]])
    coronal_ax.set_title(f"Coronal - Slice {img_shape[0] // 2}")
    coronal_cbar = plt.colorbar(im_coronal, cax=cax_coronal)

    # Adicionando widgets para medir e zoom
    rax = plt.axes([0.3, 0.95, 0.4, 0.04])
    check = CheckButtons(rax, ['Medir', 'Zoom'], [False, False])

    class ScrollSlices:
        def __init__(self, ax, slices, orientation):
            self.ax = ax
            self.slices = slices
            self.index = len(slices) // 2
            self.orientation = orientation
            self.measure_active = False
            self.zoom_active = False
            self.update()

        def update(self, *args):
            if self.orientation == 'vertical':
                self.ax.images[0].set_array(self.slices[:, :, self.index])
            elif self.orientation == 'sagittal':
                self.ax.images[0].set_array(self.slices[:, self.index, :].T)
            else:
                self.ax.images[0].set_array(self.slices[self.index, :, :].T)
            self.ax.set_title(f"{self.orientation.capitalize()} - Slice {self.index}")

        def toggle_measure(self, label):
            self.measure_active = not self.measure_active
            # Adicione a lógica de medição aqui se necessário

        def toggle_zoom(self, label):
            self.zoom_active = not self.zoom_active
            if self.zoom_active:
                self.ax.figure.canvas.mpl_connect('scroll_event', self.zoom)
            else:
                self.ax.figure.canvas.mpl_disconnect(self.zoom_id)

        def zoom(self, event):
            # Adicione a lógica de zoom aqui se necessário
            pass

        def on_scroll(self, event):
            if event.inaxes == self.ax:
                if event.button == 'up':
                    self.index = (self.index + 1) % len(self.slices)
                elif event.button == 'down':
                    self.index = (self.index - 1) % len(self.slices)
                self.update()
                plt.draw()

    axial_scroll = ScrollSlices(axial_ax, volume3d, 'vertical')
    sagittal_scroll = ScrollSlices(sagittal_ax, volume3d, 'sagittal')
    coronal_scroll = ScrollSlices(coronal_ax, volume3d, 'coronal')

    check.on_clicked(axial_scroll.toggle_measure)
    check.on_clicked(axial_scroll.toggle_zoom)

    fig.canvas.mpl_connect('scroll_event', axial_scroll.on_scroll)
    fig.canvas.mpl_connect('scroll_event', sagittal_scroll.on_scroll)
    fig.canvas.mpl_connect('scroll_event', coronal_scroll.on_scroll)

    plt.subplots_adjust(left=0.1, right=0.9, top=0.924, bottom=0.052, wspace=0.376, hspace=0.145)
    
    # Maximize a janela após a criação da figura
    # Maximize a janela após a criação da figura
    figure_title = plt.get_current_fig_manager().window.title()
    window = gw.getWindowsWithTitle(figure_title)
    if window:
        window[0].maximize()


plt.show()

# Exemplo de uso
# plot_slices(r"H:\DICOMS\Caso William\Silva_W_37288844")
    
    
