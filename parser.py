from tkinter.filedialog import *
import tkinter.ttk as ttk
import os, struct
import matplotlib.pyplot as plot
import matplotlib.ticker as tck
import matplotlib.backend_bases as bkndbs
from math import ceil
from zoomPan import *
import time
import threading
from numba import njit

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

def ErrorWindow(__msg):
    window = Toplevel(mainWindow)
    window.title('Возникла ошибка')
    canvas = Canvas(window,
                    width=400,
                    height=50,
                    bg='skyblue',
                    cursor='arrow')
    window.resizable(False, False)
    window.attributes('-topmost', True, '-toolwindow', True)
    window.geometry("+%d+%d" % (mainWindow.winfo_x() + 470,
                                mainWindow.winfo_y()
                                )
                    )
    canvas.create_text(200, 25,
                       anchor=CENTER,
                       justify='center',
                       font="TimesNewRoman 12",
                       text=__msg)
    canvas.pack()

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
    zp.zoom_factory(plot.gca(), base_scale=1.1)
    zp.pan_factory(plot.gca())
    # Drawing
    plot.show()


def FastPower(a, n):
    if n == 0:
        return 1
    elif n == 1:
        return a
    elif n % 2 != 0:
        return a * FastPower(a, n - 1)
    elif n % 2 == 0:
        return FastPower(a * a, n / 2)

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
    buttonConvertObject.config(text='Выполнение',
                               state='disabled',
                               bg="whitesmoke")
    #
    dataType = var_DataType.get()
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
    canvas.itemconfig(textResult_1, text='')
    canvas.itemconfig(textResult_2, text='')
    #
    OUTPUT_FILENAME_NOGAIN = fileName.split('.')[0] + '_nogain.pcm'
    OUTPUT_FILENAME_AMPLIFIED = fileName.split('.')[0] + '_amplified.pcm'
    # Creating output files
    filetoWrite_nogain = None
    filetoWrite_amplified = None
    if var_BuildNoGain.get().__eq__(True):
        try:
            filetoWrite_nogain = open(OUTPUT_FILENAME_NOGAIN, 'wb')
        except:
            # Configuring button
            buttonConvertObject.config(text='Выполнить',
                                       state='normal',
                                       bg="white")
            ErrorWindow('Невозможно изменить итоговый файл!\nВозможно, он занят другой программой')
            return
    if var_BuildAmplified.get().__eq__(True):
        try:
            filetoWrite_amplified = open(OUTPUT_FILENAME_AMPLIFIED, 'wb')
        except:
            # Configuring button
            buttonConvertObject.config(text='Выполнить',
                                       state='normal',
                                       bg="white")
            ErrorWindow('Невозможно изменить итоговый файл!\nВозможно, он занят другой программой')
            return
    # Calculating steps for progress bar
    divider = 20
    if fileSize / __packet_size < divider:
        divider = fileSize // __packet_size
    stepsToProcess = fileSize // (__packet_size * divider)
    # Creating progress bar for scale drawing
    progressBar2 = ttk.Progressbar(mainWindow,
                                   mode='determinate',
                                   length=150)
    canvas.itemconfig(windowProgressBar2,
                      window=progressBar2,
                      state='normal')
    progressBar2['value'] = 0
    progressBar2.update()
    # Creating progress bar for calculations
    progressBar = ttk.Progressbar(mainWindow,
                                  mode='determinate',
                                  length=150)
    canvas.itemconfig(windowProgressBar,
                      window=progressBar,
                      state='normal')
    progressBar['value'] = 0
    progressBar.update()
    # Settings initial state for progress bar's count
    progressCounter = 0
    # Calculating scale
    minimalScale = 255
    scale = 10
    try:
        fileToRead = open(pathName, 'rb')
    except:
        # Configuring button
        buttonConvertObject.config(text='Выполнить',
                                   state='normal',
                                   bg="white")
        ErrorWindow('Невозможно открыть исходный файл!\nВозможно, он занят другой программой')
        return
    scaleList = []
    packetNumberCur = 0
    packetNumberOld = 0
    packetNumberErrors = 0
    while True:
        packet= fileToRead.read(__packet_size)
        if packet.__eq__(b''):
            fileToRead.close()
            break
        # Checking packets's order if we'e processing raw data
        if dataType.__eq__('Raw'):
            packetNumberCur = packet[3] << 24 | packet[2] << 16 | packet[1] << 8 | packet[0]
            if packetNumberOld.__eq__(0):
                packetNumberOld = packetNumberCur
            else:
                if (packetNumberCur-packetNumberOld).__ne__(1):
                    packetNumberErrors += 1
                packetNumberOld = packetNumberCur
        #
        if var_BuildGraph.get().__eq__(True):
            scaleList.append(packet[__scale_position])
            progressCounter += 1
            if (progressCounter % stepsToProcess).__eq__(0):
                progressBar2['value'] += 100/divider
                progressBar2.update()
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
        buttonConvertObject.config(text='Выполнить',
                                   state='normal',
                                   bg="white")
        ErrorWindow('Невозможно открыть исходный файл!\nВозможно, он занят другой программой')
        return
    #print(time.strftime('Start - %M %S', time.localtime()))
    if var_BuildNoGain.get().__eq__(True) or var_BuildAmplified.get().__eq__(True):
        if True:
            POWER_LIST = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]
            while True:
                packet = fileToRead.read(__packet_size)
                if packet.__eq__(b''):
                    break
                progressCounter += 1
                if (progressCounter % stepsToProcess).__eq__(0):
                    progressBar['value'] += 100/divider
                    progressBar.update()
                # Writing nogain file
                if var_BuildNoGain.get().__eq__(True):
                    filetoWrite_nogain.write(
                        bytearray(packet[__payload_position:__payload_position + PAYLOAD_SIZE]))
                # Writing amplified file
                if var_BuildAmplified.get().__eq__(True):
                    formattedData = list(
                        struct.unpack('4096h', bytearray(
                            packet[__payload_position:__payload_position + PAYLOAD_SIZE])))
                    finalScale = -scale + packet[__scale_position]
                    # Calculating new samples's value
                    formattedData = [Data_Amplify(sample, POWER_LIST[finalScale]) for sample in formattedData]
                    # Converting 16-bit data into 8-bit data
                    resultData = struct.pack('4096h', *formattedData)
                    filetoWrite_amplified.write(resultData)
        elif True:
            packet = fileToRead.read()
            # Writing nogain file
            if var_BuildNoGain.get().__eq__(True):
                packetToWrite = bytearray([])
                for step in range(__payload_position, len(packet), __packet_size):
                    packetToWrite += bytearray(packet[step:step+PAYLOAD_SIZE])
                filetoWrite_nogain.write(packetToWrite)
            pass
    #print(time.strftime('End - %M %S', time.localtime()))
    # Closing all files
    if var_BuildNoGain.get().__eq__(True) or var_BuildAmplified.get().__eq__(True):
        canvas.itemconfig(textResult_1, text='Создан файлы:')
    createdFiles = ''
    if var_BuildNoGain.get().__eq__(True):
        message = (fileName.split('.')[0] + '_nogain.pcm')
        createdFiles += message[0:25] + ('...\n' if len(message) > 26 else '\n')
        filetoWrite_nogain.close()
    if var_BuildAmplified.get().__eq__(True):
        message = (fileName.split('.')[0] + '_amplified.pcm\n')
        createdFiles += message[0:25] + ('...\n' if len(message) > 26 else '\n')
        filetoWrite_amplified.close()
    canvas.itemconfig(textResult_2, text=createdFiles)
    fileToRead.close()
    # Configuring button
    buttonConvertObject.config(text='Выполнить',
                               state='normal',
                               bg="white")
    # Drawing scale graph
    if packetNumberErrors.__gt__(0) and dataType.__eq__('Raw'):
        ErrorWindow(f'Некоторые пакеты идут не по порядку!\nЧисло зафиксированных ошибок - {packetNumberErrors}')
    if var_BuildGraph.get().__eq__(True):
        Scale_Draw(scaleList)



def GUI_OpenFile():
    global pathName, fileName, fileSize
    # Setting initial window state
    canvas.itemconfig(radio_8193Data, state='hidden')
    canvas.itemconfig(radio_RawData, state='hidden')
    canvas.itemconfig(buttonConvert, state='hidden')
    canvas.itemconfig(textResult_1, text='')
    canvas.itemconfig(textResult_2, text='')
    canvas.itemconfig(windowProgressBar, state='hidden')
    canvas.itemconfig(windowProgressBar2, state='hidden')
    canvas.itemconfig(check_ScaleGraph, state='hidden')
    canvas.itemconfig(check_CreateAmplified, state='hidden')
    canvas.itemconfig(check_CreateNoGain, state='hidden')
    #
    try:
        pathName = askopenfilename(title='Выберите файл для конвертации',
                                   parent=mainWindow,
                                   initialdir=os.path.dirname(os.path.abspath(__file__)))
        if pathName.__ne__(""):
            fileSize = os.path.getsize(pathName)
            fileName = pathName.split('/')[-1]
            if (fileSize % PACKET_SIZE_RAW).__eq__(0):
                canvas.itemconfig(textProjectName,
                                  text='Выбранный файл - ' + fileName + '\nКажется, это сырой файл.\nПоправьте, если ошибся:')
                var_DataType.set('Raw')
                canvas.itemconfig(radio_8193Data, state='normal')
                canvas.itemconfig(radio_RawData, state='normal')
                canvas.itemconfig(buttonConvert, state='normal')
                canvas.itemconfig(check_ScaleGraph, state='normal')
                canvas.itemconfig(check_CreateAmplified, state='normal')
                canvas.itemconfig(check_CreateNoGain, state='normal')
            elif (fileSize % PACKET_SIZE_WITH_SCALE).__eq__(0):
                canvas.itemconfig(textProjectName,
                                  text='Выбранный файл - ' + fileName + '\nКажется, это данные со скейлом.\nПоправьте, если ошибся:')
                var_DataType.set('Scale')
                canvas.itemconfig(radio_8193Data, state='normal')
                canvas.itemconfig(radio_RawData, state='normal')
                canvas.itemconfig(buttonConvert, state='normal')
                canvas.itemconfig(check_ScaleGraph, state='normal')
                canvas.itemconfig(check_CreateAmplified, state='normal')
                canvas.itemconfig(check_CreateNoGain, state='normal')
            else:
                canvas.itemconfig(textProjectName,
                                  text='Неизвестная структура файла')
        else:
            canvas.itemconfig(textProjectName,
                              text='Выберите файл для конвертации')
    except:
        pass


if __name__.__eq__('__main__'):
    mainWindow = Tk()
    mainWindow.title(GUI_TITLE)
    mainWindow.resizable(False, False)
    mainWindow.attributes('-topmost', True, '-toolwindow', True)
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
    textProjectName = canvas.create_text(20, 10,
                                         anchor=NW,
                                         text='Выберите файл для конвертации',
                                         font='TimesNewRoman 12')
    # Creating the opened file's type radiobuttons
    var_DataType = StringVar()
    var_DataType.set(None)
    radio_RawData = canvas.create_window(20, 77,
                                         anchor=W,
                                         window=Radiobutton(mainWindow,
                                                            variable=var_DataType,
                                                            value='Raw',
                                                            text='сырые данные',
                                                            font='TimesNewRoman 12',
                                                            bg="skyblue"),
                                         state='hidden')
    radio_8193Data = canvas.create_window(20, 100,
                                          anchor=W,
                                          window=Radiobutton(mainWindow,
                                                             variable=var_DataType,
                                                             value='Scale',
                                                             text='данные со скейлом',
                                                             font='TimesNewRoman 12',
                                                             bg="skyblue"),
                                          state='hidden')
    # Creating checkboxes and variables for them to choose the output files
    var_BuildGraph = BooleanVar()
    var_BuildAmplified = BooleanVar()
    var_BuildNoGain = BooleanVar()
    var_BuildGraph.set(True)
    var_BuildAmplified.set(False)
    var_BuildNoGain.set(False)
    check_CreateAmplified = canvas.create_window(180, 150,
                                                 anchor=NW,
                                                 window=Checkbutton(mainWindow,
                                                                    variable=var_BuildAmplified,
                                                                    text='получить усиленный сигнал',
                                                                    font='TimesNewRoman 12',
                                                                    bg="skyblue"),
                                                 state='hidden')
    check_CreateNoGain = canvas.create_window(180, 130,
                                              anchor=NW,
                                              window=Checkbutton(mainWindow,
                                                                 variable=var_BuildNoGain,
                                                                 text='получить исходный сигнал',
                                                                 font='TimesNewRoman 12',
                                                                 bg="skyblue"),
                                              state='hidden')
    check_ScaleGraph = canvas.create_window(180, 110,
                                            anchor=NW,
                                            window=Checkbutton(mainWindow,
                                                               variable=var_BuildGraph,
                                                               text='посмотреть динамику скейла',
                                                               font='TimesNewRoman 12',
                                                               bg="skyblue"),
                                            state='hidden')
    # Creating main button
    buttonConvertObject = Button(mainWindow,
                                 text="Выполнить",
                                 bd='0',
                                 bg="white",
                                 fg="dodgerblue",
                                 font=('Symbol', '12', 'bold'),
                                 command=Data_Convert_MemorySafe)
    buttonConvert = canvas.create_window(185, 195,
                                         anchor=W,
                                         width=150,
                                         window=buttonConvertObject,
                                         state='hidden')
    # Creating windows for progress bars
    windowProgressBar = canvas.create_window(20, 137,
                                             anchor=NW,
                                             height=35)
    windowProgressBar2 = canvas.create_window(20, 125,
                                              anchor=W)
    # Creating textboxes for final logs
    textResult_1 = canvas.create_text(20, 220,
                                      anchor=NW,
                                      text='',
                                      font='TimesNewRoman 12')
    textResult_2 = canvas.create_text(184, 220,
                                      anchor=NW,
                                      text='',
                                      font='TimesNewRoman 12')
    # Creating the result window
    canvas.pack()
    mainWindow.config(menu=guiMenuBar)
    mainWindow.mainloop()
