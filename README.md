# DICOM INFO Analysis Application

The DICOM INFO Analysis Application is a tool developed in Python with a graphical interface using Tkinter. It allows users to analyze and visualize medical image information in DICOM format present in a specific directory.

## Features

- **Directory Analysis**: Users can select a directory containing DICOM images for analysis. The application recursively scans the selected directory, extracts relevant information from each DICOM file, and displays this information in a table in the graphical interface.

- **Information Visualization**: The extracted information from each DICOM file includes data such as patient's birthdate, gender, age, exam date, study description, equipment manufacturer, exam type, number of slices, and slice thickness. This information is displayed clearly and organized in the application interface.

- **PDF Report Generation**: Users can generate a report in PDF format containing the extracted analysis information. The PDF report can be easily shared and archived for future reference.

## System Requirements

- Python 3.x installed on the system
- Required Python packages installed (PyDicom, Tkinter, ThemedTk, Pillow, ReportLab)

## How to Use

1. Run the Python application.
2. Choose the directory containing the DICOM images you want to analyze.
3. Click the "Analyze" button to start the analysis.
4. View the information of the DICOM images in the table displayed in the interface.
5. If desired, filter the information by patient name using the search box.
6. Generate a PDF report by clicking the "Generate PDF Report" button.
7. The PDF report will be generated and automatically opened for viewing.

## Notes

- Ensure that the selected directory contains only files in DICOM format for accurate analysis.
- The graphical interface allows customization of light and dark themes to meet user preferences.

This application offers an efficient and convenient way to analyze and manage medical images in DICOM format, providing valuable insights for healthcare professionals and researchers.


SOFTWARE.

![image](https://github.com/gustavomata/dicom_info-main/assets/47390349/951a0379-c671-4b4d-bca4-f846c4b21e41)

