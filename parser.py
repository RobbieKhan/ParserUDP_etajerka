from tkinter.filedialog import *
import tkinter.ttk as ttk
from tkinter import PhotoImage
import os, struct
import matplotlib.widgets as wdg
import matplotlib.pyplot as plot
import matplotlib.ticker as tck
import matplotlib.backend_bases as bkndbs
from math import ceil
from zoomPan import *
from childWindows import *
import time
import threading
from numba import njit
import numpy as np
import plotly.graph_objects as go
from OscillogramGraph import *
from SpectrumGraph import *

GUI_TITLE = 'Конвертер'
GUI_WIDTH = 450
GUI_HEIGHT = 450

PACKET_SIZE_RAW = 8208
PACKET_SIZE_WITH_SCALE = 8193
PAYLOAD_SIZE = 8192
PAYLOAD_POSITION_RAW = 16
PAYLOAD_POSITION_WITH_SCALE = 1
SCALE_POSITION_RAW = 4
SCALE_POSITION_WITH_SCALE = 0


def Scale_Draw(list):
    global fileName
    # Configuring figure's toolbar
    bkndbs.NavigationToolbar2.toolitems = {
        ('Save', 'Сохранить график', 'filesave', 'save_figure'),
    }
    #
    plot.figure().canvas.set_window_title(f'Динамика скейла файла \'{fileName}\'')
    plot.plot(list, ':', label='Скейл')
    plot.legend()
    plot.gca().xaxis.set_major_locator(tck.MultipleLocator(base=ceil(len(list) / 5)))
    plot.xticks(rotation=45)
    # Adding zoom and pan control
    zp = ZoomPan()
    zp.zoom_factory(plot.gca(), base_scale=1.5)
    zp.pan_factory(plot.gca())
    # Drawing
    plot.show()


def GUI_Spectrum():
    samplesSpectrum = SamplesSpectrum(mainWindow, fileName, varFileToBuildGraph.get())
    samplesSpectrum.draw()


def GUI_SpectrumSettings():
    Window_Settings(mainWindow, 'spectrum')


def GUI_Oscillogram():
    samplesOscilloram = SamplesOscillogram(mainWindow, fileName, varFileToBuildGraph.get())
    samplesOscilloram.draw()


def GUI_OscillogramSettings():
    Window_Settings(mainWindow, 'oscillogram')


@njit
def Data_Amplify(data, power):
    data //= power
    if data < -32766 or data > 32767:
        if data > 0:
            data = 32767
        else:
            data = -32766
    return data


def Data_Convert_MemorySafe():
    # Configuring button
    buttonExecute_POINTER.config(text='Выполнение',
                                 state='disabled',
                                 bg="whitesmoke")
    #
    dataType = varFileType.get()
    __packet_size = 0
    __scale_position = 0
    __payload_position = 0
    if dataType.__eq__('Raw'):
        __packet_size = PACKET_SIZE_RAW
        __payload_position = PAYLOAD_POSITION_RAW
        __scale_position = SCALE_POSITION_RAW
    elif dataType.__eq__('Scale'):
        __packet_size = PACKET_SIZE_WITH_SCALE
        __payload_position = PAYLOAD_POSITION_WITH_SCALE
        __scale_position = SCALE_POSITION_WITH_SCALE
    # Setting initial window state
    canvas.itemconfig(textFinalLogLeft, text='')
    canvas.itemconfig(textFinalLogRight, text='')
    #
    OUTPUT_FILENAME_NOGAIN = fileName.split('.')[0] + '_nogain.pcm'
    OUTPUT_FILENAME_AMPLIFIED = fileName.split('.')[0] + '_amplified.pcm'
    # Creating output files
    filetoWrite_nogain = None
    filetoWrite_amplified = None
    if varBuildOriginalFile.get().__eq__(True):
        try:
            filetoWrite_nogain = open(OUTPUT_FILENAME_NOGAIN, 'wb')
        except:
            # Configuring button
            buttonExecute_POINTER.config(text='Выполнить',
                                         state='normal',
                                         bg="white")
            Window_Error(mainWindow, 'Невозможно изменить итоговый файл!\nВозможно, он занят другой программой')
            return
    if varBuildAmplifiedFile.get().__eq__(True):
        try:
            filetoWrite_amplified = open(OUTPUT_FILENAME_AMPLIFIED, 'wb')
        except:
            # Configuring button
            buttonExecute_POINTER.config(text='Выполнить',
                                         state='normal',
                                         bg="white")
            Window_Error(mainWindow, 'Невозможно изменить итоговый файл!\nВозможно, он занят другой программой')
            return
    # Calculating steps for progress bar
    divider = 20
    if fileSize / __packet_size < divider:
        divider = fileSize // __packet_size
    stepsToProcess = fileSize // (__packet_size * divider)
    # Creating progress bar for scale drawing
    progressbarScaleGraph_POINTER = ttk.Progressbar(mainWindow,
                                                    mode='determinate',
                                                    length=150)
    canvas.itemconfig(progressbarScaleGraph,
                      window=progressbarScaleGraph_POINTER,
                      state='normal')
    progressbarScaleGraph_POINTER['value'] = 0
    progressbarScaleGraph_POINTER.update()
    # Creating progress bar for calculations
    progressbarFiles_POINTER = ttk.Progressbar(mainWindow,
                                               mode='determinate',
                                               length=150)
    canvas.itemconfig(progressbarFiles,
                      window=progressbarFiles_POINTER,
                      state='normal')
    progressbarFiles_POINTER['value'] = 0
    progressbarFiles_POINTER.update()
    # Settings initial state for progress bar's count
    progressCounter = 0
    # Calculating scale
    minimalScale = 255
    scale = 10
    try:
        fileToRead = open(pathName, 'rb')
    except:
        # Configuring button
        buttonExecute_POINTER.config(text='Выполнить',
                                     state='normal',
                                     bg="white")
        Window_Error(mainWindow, 'Невозможно открыть исходный файл!\nВозможно, он занят другой программой')
        return
    scaleList = []
    packetNumberCur = 0
    packetNumberOld = 0
    packetNumberErrors = 0
    while True:
        packet = fileToRead.read(__packet_size)
        if packet.__eq__(b''):
            fileToRead.close()
            break
        # Checking packets's order if we'e processing raw data
        if dataType.__eq__('Raw'):
            packetNumberCur = packet[3] << 24 | packet[2] << 16 | packet[1] << 8 | packet[0]
            if packetNumberOld.__eq__(0):
                packetNumberOld = packetNumberCur
            else:
                if (packetNumberCur - packetNumberOld).__ne__(1):
                    packetNumberErrors += 1
                packetNumberOld = packetNumberCur
        #
        if varBuildScaleGraph.get().__eq__(True):
            scaleList.append(packet[__scale_position])
            progressCounter += 1
            if (progressCounter % stepsToProcess).__eq__(0):
                progressbarScaleGraph_POINTER['value'] += 100 / divider
                progressbarScaleGraph_POINTER.update()
        minimalScale = packet[__scale_position] if packet[__scale_position].__lt__(
            minimalScale) else minimalScale
        scale = scale if scale < minimalScale else minimalScale
    # Settings initial state for progress bar's count
    progressCounter = 0
    # Processing each packet
    try:
        fileToRead = open(pathName, 'rb')
    except:
        # Configuring button
        buttonExecute_POINTER.config(text='Выполнить',
                                     state='normal',
                                     bg="white")
        Window_Error(mainWindow, 'Невозможно открыть исходный файл!\nВозможно, он занят другой программой')
        return
    # print(time.strftime('Start - %M %S', time.localtime()))
    if varBuildOriginalFile.get().__eq__(True) or varBuildAmplifiedFile.get().__eq__(True):
        POWER_LIST = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]
        while True:
            packet = fileToRead.read(__packet_size)
            if packet.__eq__(b''):
                break
            progressCounter += 1
            if (progressCounter % stepsToProcess).__eq__(0):
                progressbarFiles_POINTER['value'] += 100 / divider
                progressbarFiles_POINTER.update()
            # Writing nogain file
            if varBuildOriginalFile.get().__eq__(True):
                filetoWrite_nogain.write(
                    bytearray(packet[__payload_position:__payload_position + PAYLOAD_SIZE]))
            # Writing amplified file
            if varBuildAmplifiedFile.get().__eq__(True):
                formattedData = list(
                    struct.unpack('4096h', bytearray(
                        packet[__payload_position:__payload_position + PAYLOAD_SIZE])))
                finalScale = -scale + packet[__scale_position]
                # Calculating new samples's value
                formattedData = [Data_Amplify(sample, POWER_LIST[finalScale]) for sample in formattedData]
                # Converting 16-bit data into 8-bit data
                resultData = struct.pack('4096h', *formattedData)
                filetoWrite_amplified.write(resultData)
    # print(time.strftime('End - %M %S', time.localtime()))
    # Closing all files
    if varBuildOriginalFile.get().__eq__(True) or varBuildAmplifiedFile.get().__eq__(True):
        canvas.itemconfig(textFinalLogLeft, text='Созданы файлы:')
    createdFiles = ''
    if varBuildOriginalFile.get().__eq__(True):
        message = (fileName.split('.')[0] + '_nogain.pcm')
        createdFiles += message[0:25] + ('...\n' if len(message) > 26 else '\n')
        filetoWrite_nogain.close()
    if varBuildAmplifiedFile.get().__eq__(True):
        message = (fileName.split('.')[0] + '_amplified.pcm\n')
        createdFiles += message[0:25] + ('...\n' if len(message) > 26 else '\n')
        filetoWrite_amplified.close()
    canvas.itemconfig(textFinalLogRight, text=createdFiles)
    fileToRead.close()
    # Configuring button
    buttonExecute_POINTER.config(text='Выполнить',
                                 state='normal',
                                 bg="white")
    # Drawing scale graph
    if packetNumberErrors.__gt__(0) and dataType.__eq__('Raw'):
        Window_Error(mainWindow,
                     f'Некоторые пакеты идут не по порядку!\nЧисло зафиксированных ошибок - {packetNumberErrors}')
    if varBuildScaleGraph.get().__eq__(True):
        Scale_Draw(scaleList)


def GUI_Convert():
    # th = threading.Thread(target=Data_Convert_MemorySafe)
    # th.start()
    Data_Convert_MemorySafe()


def GUI_OpenFile():
    global pathName, fileName, fileSize
    # Setting initial window state
    canvas.itemconfig(textUpperLabel,
                      text='Выберите файл')
    canvas.itemconfig(radioTypeProcessed, state='hidden')
    canvas.itemconfig(radioTypeRaw, state='hidden')
    canvas.itemconfig(buttonExecute, state='hidden')
    canvas.itemconfig(textFinalLogLeft, text='')
    canvas.itemconfig(textFinalLogRight, text='')
    canvas.itemconfig(progressbarFiles, state='hidden')
    canvas.itemconfig(progressbarScaleGraph, state='hidden')
    canvas.itemconfig(checkbuttonBuildScaleGraph, state='hidden')
    canvas.itemconfig(checkbuttonBuildOriginalFile, state='hidden')
    canvas.itemconfig(checkbuttonBuildAmplifiedFile, state='hidden')
    canvas.itemconfig(buttonOscilloscope, state='hidden')
    canvas.itemconfig(buttonSpectrum, state='hidden')
    canvas.itemconfig(textFinalTypeChoosing, state='hidden')
    canvas.itemconfig(radioFileTypeAmplified, state='hidden')
    canvas.itemconfig(radioFileTypeOriginal, state='hidden')
    canvas.itemconfig(radioFileTypeCurrent, state='hidden')
    #
    try:
        pathName = askopenfilename(title='Выберите файл для конвертации',
                                   parent=mainWindow,
                                   initialdir=os.path.dirname(os.path.abspath(__file__)))
        if pathName.__ne__(""):
            fileSize = os.path.getsize(pathName)
            fileName = pathName.split('/')[-1]
            if (fileSize % PACKET_SIZE_RAW).__eq__(0):
                canvas.itemconfig(textUpperLabel,
                                  text='Выбранный файл - \"' + fileName + '\".\nКажется, это сырые данные.\nПоправьте, если ошибся:')
                varFileType.set('Raw')
                canvas.itemconfig(radioTypeProcessed, state='normal')
                canvas.itemconfig(radioTypeRaw, state='normal')
                canvas.itemconfig(buttonExecute, state='normal')
                canvas.itemconfig(checkbuttonBuildScaleGraph, state='normal')
                canvas.itemconfig(checkbuttonBuildOriginalFile, state='normal')
                canvas.itemconfig(checkbuttonBuildAmplifiedFile, state='normal')
                canvas.itemconfig(buttonOscilloscope, state='normal')
                canvas.itemconfig(buttonSpectrum, state='normal')
                canvas.itemconfig(textFinalTypeChoosing, state='normal')
                varFileToBuildGraph.set('Amplified')
                canvas.itemconfig(radioFileTypeAmplified, state='normal')
                canvas.itemconfig(radioFileTypeOriginal, state='normal')
                canvas.itemconfig(radioFileTypeCurrent, state='normal')
                radioFileTypeAmplified_POINTER['state'] = NORMAL
                radioFileTypeOriginal_POINTER['state'] = NORMAL
                radioFileTypeCurrent_POINTER['state'] = DISABLED
            elif (fileSize % PACKET_SIZE_WITH_SCALE).__eq__(0):
                canvas.itemconfig(textUpperLabel,
                                  text='Выбранный файл - \"' + fileName + '\".\nКажется, это данные со скейлом.\nПоправьте, если ошибся:')
                varFileType.set('Scale')
                canvas.itemconfig(radioTypeProcessed, state='normal')
                canvas.itemconfig(radioTypeRaw, state='normal')
                canvas.itemconfig(buttonExecute, state='normal')
                canvas.itemconfig(checkbuttonBuildScaleGraph, state='normal')
                canvas.itemconfig(checkbuttonBuildOriginalFile, state='normal')
                canvas.itemconfig(checkbuttonBuildAmplifiedFile, state='normal')
                canvas.itemconfig(buttonOscilloscope, state='normal')
                canvas.itemconfig(buttonSpectrum, state='normal')
                canvas.itemconfig(textFinalTypeChoosing, state='normal')
                varFileToBuildGraph.set('Amplified')
                canvas.itemconfig(radioFileTypeAmplified, state='normal')
                canvas.itemconfig(radioFileTypeOriginal, state='normal')
                canvas.itemconfig(radioFileTypeCurrent, state='normal')
                radioFileTypeAmplified_POINTER['state'] = NORMAL
                radioFileTypeOriginal_POINTER['state'] = NORMAL
                radioFileTypeCurrent_POINTER['state'] = DISABLED
            elif (fileSize % PAYLOAD_SIZE).__eq__(0):
                canvas.itemconfig(textUpperLabel,
                                  text='Выбранный файл - \"' + fileName + '\".\nФайл был распознан, как чистые данные.')
                canvas.itemconfig(buttonOscilloscope, state='normal')
                canvas.itemconfig(buttonSpectrum, state='normal')
                canvas.itemconfig(textFinalTypeChoosing, state='normal')
                varFileToBuildGraph.set('Current')
                canvas.itemconfig(radioFileTypeAmplified, state='normal')
                canvas.itemconfig(radioFileTypeOriginal, state='normal')
                canvas.itemconfig(radioFileTypeCurrent, state='normal')
                radioFileTypeAmplified_POINTER['state'] = DISABLED
                radioFileTypeOriginal_POINTER['state'] = DISABLED
                radioFileTypeCurrent_POINTER['state'] = NORMAL
                pass
            else:
                canvas.itemconfig(textUpperLabel,
                                  text='Неизвестная структура файла!')
        else:
            canvas.itemconfig(textUpperLabel,
                              text='Выберите файл')
    except:
        pass


if __name__.__eq__('__main__'):
    mainWindow = Tk()
    mainWindow.title(GUI_TITLE)
    mainWindow.resizable(False, False)
    mainWindow.attributes('-topmost', True, '-toolwindow', False)
    guiMenuBar = Menu(mainWindow)
    guiFileMenu = Menu(guiMenuBar, tearoff=0)
    guiFileMenu.add_command(label='Выбрать файл',
                            command=GUI_OpenFile)
    guiFileMenu.add_separator()
    guiFileMenu.add_command(label='Выход',
                            command=mainWindow.quit)
    guiMenuBar.add_cascade(label='Файл',
                           menu=guiFileMenu)
    canvas = Canvas(mainWindow,
                    width=GUI_WIDTH,
                    height=GUI_HEIGHT,
                    bg='skyblue',
                    cursor='arrow')
    # ============
    # Creating GUI
    # ============
    # Creating textbox that contains the opened file data
    textUpperLabel = canvas.create_text(20, 10,
                                        anchor=NW,
                                        text='Выберите файл',
                                        font='TimesNewRoman 12')
    # Creating the opened file's type radiobuttons
    varFileType = StringVar()
    varFileType.set(None)
    radioTypeRaw = canvas.create_window(16, 77,
                                        anchor=W,
                                        window=Radiobutton(mainWindow,
                                                           variable=varFileType,
                                                           value='Raw',
                                                           text='сырые данные',
                                                           font='TimesNewRoman 12',
                                                           bg="skyblue"),
                                        state='hidden')
    radioTypeProcessed = canvas.create_window(16, 100,
                                              anchor=W,
                                              window=Radiobutton(mainWindow,
                                                                 variable=varFileType,
                                                                 value='Scale',
                                                                 text='данные со скейлом',
                                                                 font='TimesNewRoman 12',
                                                                 bg="skyblue"),
                                              state='hidden')
    # Creating checkboxes and variables for them to choose the output files
    varBuildScaleGraph = BooleanVar()
    varBuildAmplifiedFile = BooleanVar()
    varBuildOriginalFile = BooleanVar()
    varBuildScaleGraph.set(True)
    varBuildAmplifiedFile.set(False)
    varBuildOriginalFile.set(False)
    checkbuttonBuildAmplifiedFile = canvas.create_window(16, 160,
                                                         anchor=NW,
                                                         window=Checkbutton(mainWindow,
                                                                            variable=varBuildAmplifiedFile,
                                                                            text='получить усиленный сигнал',
                                                                            font='TimesNewRoman 12',
                                                                            bg="skyblue"),
                                                         state='hidden')
    checkbuttonBuildOriginalFile = canvas.create_window(16, 135,
                                                        anchor=NW,
                                                        window=Checkbutton(mainWindow,
                                                                           variable=varBuildOriginalFile,
                                                                           text='получить исходный сигнал',
                                                                           font='TimesNewRoman 12',
                                                                           bg="skyblue"),
                                                        state='hidden')
    checkbuttonBuildScaleGraph = canvas.create_window(16, 110,
                                                      anchor=NW,
                                                      window=Checkbutton(mainWindow,
                                                                         variable=varBuildScaleGraph,
                                                                         text='посмотреть динамику скейла',
                                                                         font='TimesNewRoman 12',
                                                                         bg="skyblue"),
                                                      state='hidden')
    # Creating "Execute" button
    buttonExecute_POINTER = Button(mainWindow,
                                   text="Выполнить",
                                   bd='0',
                                   bg="white",
                                   fg="dodgerblue",
                                   font=('Symbol', '12', 'bold'),
                                   command=GUI_Convert)
    buttonExecute = canvas.create_window(20, 205,
                                         anchor=W,
                                         width=150,
                                         window=buttonExecute_POINTER,
                                         state='hidden')
    # Creating "Spectrum" button
    buttonSpectrum_POINTER = Button(mainWindow,
                                    text="Спектр",
                                    bd='0',
                                    bg="white",
                                    fg="dodgerblue",
                                    font=('Symbol', '12', 'bold'),
                                    command=GUI_Spectrum)
    buttonSpectrum = canvas.create_window(20, 305,
                                          anchor=W,
                                          width=150,
                                          window=buttonSpectrum_POINTER,
                                          state='hidden')
    # Creating "Oscilloscope" button
    buttonOscilloscope_POINTER = Button(mainWindow,
                                        text="Осциллограмма",
                                        bd='0',
                                        bg="white",
                                        fg="dodgerblue",
                                        font=('Symbol', '12', 'bold'),
                                        command=GUI_Oscillogram)
    buttonOscilloscope = canvas.create_window(20, 345,
                                              anchor=W,
                                              width=150,
                                              window=buttonOscilloscope_POINTER,
                                              state='hidden')
    # Creating windows for progress bars
    progressbarFiles = canvas.create_window(270, 140,
                                            anchor=NW,
                                            height=45)
    progressbarScaleGraph = canvas.create_window(270, 125,
                                                 anchor=W)
    # Creating textboxes for final logs
    textFinalLogLeft = canvas.create_text(20, 230,
                                          anchor=NW,
                                          text='',
                                          font='TimesNewRoman 12')
    textFinalLogRight = canvas.create_text(184, 230,
                                           anchor=NW,
                                           text='',
                                           font='TimesNewRoman 12')
    # Radiobuttons to select the type of file whose graphics will be built
    textFinalTypeChoosing = canvas.create_text(184, 290,
                                               anchor=NW,
                                               text='Тип файла для отстройки',
                                               font='TimesNewRoman 12',
                                               state='hidden')
    varFileToBuildGraph = StringVar()
    varFileToBuildGraph.set('None')
    radioFileTypeAmplified_POINTER = Radiobutton(mainWindow,
                                                 variable=varFileToBuildGraph,
                                                 value='Amplified',
                                                 text='усиленный сигнал',
                                                 font='TimesNewRoman 12',
                                                 bg="skyblue")
    radioFileTypeAmplified = canvas.create_window(184, 323,
                                                  anchor=W,
                                                  window=radioFileTypeAmplified_POINTER,
                                                  state='hidden')
    radioFileTypeOriginal_POINTER = Radiobutton(mainWindow,
                                                variable=varFileToBuildGraph,
                                                value='Original',
                                                text='оригинальный сигнал',
                                                font='TimesNewRoman 12',
                                                bg="skyblue")
    radioFileTypeOriginal = canvas.create_window(184, 348,
                                                 anchor=W,
                                                 window=radioFileTypeOriginal_POINTER,
                                                 state='hidden')
    radioFileTypeCurrent_POINTER = Radiobutton(mainWindow,
                                               variable=varFileToBuildGraph,
                                               value='Current',
                                               text='текущий выбранный файл',
                                               font='TimesNewRoman 12',
                                               bg="skyblue")
    radioFileTypeCurrent = canvas.create_window(184, 373,
                                                anchor=W,
                                                window=radioFileTypeCurrent_POINTER,
                                                state='hidden')
    # Creating the result window
    canvas.pack()
    mainWindow.config(menu=guiMenuBar)
    mainWindow.mainloop()
