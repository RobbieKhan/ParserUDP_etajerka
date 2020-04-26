import matplotlib.widgets as wdg
import matplotlib.pyplot as plt
import matplotlib.image as img
import matplotlib.backend_bases as bkndbs
from scipy.interpolate import interp1d
from scipy.signal import spectrogram
from zoomPan import *
from math import ceil
import os, struct
import numpy as np
from childWindows import *


class SamplesSpectrum:
    figure = None
    figureId = 2
    subplotMain = None
    subplotLeft = None
    fileName = ''
    pathName = ''
    startPacket = 0
    numberOfPackets = 0
    animationInProgress = False
    animationStartIcon = None
    animationStopIcon = None
    scrollLeftIcon = None
    scrollRightIcon = None
    isLogarithmicAxis = True
    # Settings
    nameEnding = ''
    isComplexSignal = True
    animationSpeed = 0.3
    numberOfPacketsToShow = 1
    yLimitHigh = 10
    yLimitLow = -150

    def __init__(self, master, file, filetype):
        self.master = master
        # Trying to access input file
        self.__class__.nameEnding = ''
        if filetype.__eq__('Amplified'):
            self.__class__.nameEnding = '_amplified.pcm'
        elif filetype.__eq__('Original'):
            self.__class__.nameEnding = '_nogain.pcm'
        elif filetype.__eq__('Current'):
            self.__class__.nameEnding = '.' + file.split('.')[1]
        self.__class__.fileName = file.split('.')[0] + self.__class__.nameEnding
        self.__class__.pathName = os.getcwd() + '/' + self.__class__.fileName
        try:
            self.__class__.numberOfPackets = os.path.getsize(self.__class__.pathName) // 8192
        except:
            Window_Error(self.master, 'Невозможно открыть файл с отсчетами.\nВозможно, он занят или удален.')
            return
        # CLosing the figure if it already exist before creating new one
        if self.__class__.figure is not None:
            plt.close()
        # Configuring figure's toolbar
        bkndbs.NavigationToolbar2.toolitems = {
            ('Save', 'Сохранить график', 'filesave', 'save_figure'),
        }
        #
        self.__class__.figure = plt.figure(self.__class__.figureId)
        self.__class__.figure.canvas.set_window_title(f'Спектрограмма файла \'{self.__class__.fileName}\'')
        self.__class__.subplotMain = self.__class__.figure.add_subplot(1, 1, 1)
        self.__class__.startPacket = 0
        # Getting icons
        self.__class__.animationStartIcon = img.imread('startIcon.png')
        self.__class__.animationStopIcon = img.imread('stopIcon.png')
        self.__class__.scrollLeftIcon = img.imread('scrollLeftIcon.png')
        self.__class__.scrollRightIcon = img.imread('scrollRightIcon.png')

    def configure(self):
        # Configuring y axes
        plt.setp(self.__class__.subplotMain, ylim=(self.__class__.yLimitLow, self.__class__.yLimitHigh))
        # Configuring x axes
        plt.xticks(rotation=45)
        # Adding zoom and pan control
        zp = ZoomPan()
        zp.zoom_factory(plt.gca(), base_scale=1.5)
        zp.pan_factory(plt.gca())
        # Adding buttons
        plt.subplots_adjust(bottom=0.25, left=0.2)
        # ___number of packet to show
        textboxPacketsToShowSubplot = plt.axes([0.85, 0.9, 0.05, 0.05])
        self.textboxPacketsToShow = wdg.TextBox(textboxPacketsToShowSubplot,
                                                'Число пакетов, данные которых\n отображаются одновременно',
                                                initial='1',
                                                label_pad=1)
        self.textboxPacketsToShow.on_submit(self.packetsToShowSet)
        # ___animation speed slider10
        sliderAnimationSpeedSubplot = plt.axes([0.07, 0.05, 0.03, 0.075])
        self.sliderAnimationSpeed = wdg.Slider(sliderAnimationSpeedSubplot,
                                               '',
                                               valmin=0.1,
                                               valinit=1,
                                               valmax=1,
                                               valfmt='%1.1f',
                                               orientation='vertical')

        self.sliderAnimationSpeed.set_val(1)
        self.sliderAnimationSpeed.on_changed(self.animationSpeedSet)
        # ___y axis high limit
        textboxLimitHighSubplot = plt.axes([0.02, 0.83, 0.08, 0.05])
        self.textboxLimitHigh = wdg.TextBox(textboxLimitHighSubplot,
                                            '',
                                            initial='10')
        self.textboxLimitHigh.on_submit(self.ylimSetHigh)
        # ___y axis low limit
        textboxLimitLowSubplot = plt.axes([0.02, 0.25, 0.08, 0.05])
        self.textboxLimitLow = wdg.TextBox(textboxLimitLowSubplot,
                                           '',
                                           initial='-150')
        self.textboxLimitLow.on_submit(self.ylimSetLow)
        # ___scroll buttons
        buttonScrollLeftSubplot = plt.axes([0.39, 0.05, 0.03, 0.075])
        buttonScrollLeft = wdg.Button(buttonScrollLeftSubplot,
                                      '',
                                      image=self.__class__.scrollLeftIcon)
        buttonScrollLeft.on_clicked(self.scrollLeft)
        buttonScrollRightSubplot = plt.axes([0.68, 0.05, 0.03, 0.075])
        buttonScrollRight = wdg.Button(buttonScrollRightSubplot,
                                       '',
                                       image=self.__class__.scrollRightIcon)
        buttonScrollRight.on_clicked(self.scrollRight)
        # ___animate button
        self.buttonAnimateSubplot = plt.axes([0.12, 0.05, 0.06, 0.075])
        buttonAnimate = wdg.Button(self.buttonAnimateSubplot,
                                   '',
                                   image=self.__class__.animationStartIcon)
        buttonAnimate.on_clicked(self.animate)
        # ___page buttons
        buttonNextSubplot = plt.axes([0.73, 0.05, 0.17, 0.075])
        buttonNext = wdg.Button(buttonNextSubplot,
                                'Следующие\nпакеты')
        buttonNext.on_clicked(self.buildNext)
        buttonPrevSubplot = plt.axes([0.2, 0.05, 0.17, 0.075])
        buttonPrevious = wdg.Button(buttonPrevSubplot,
                                    'Предыдущие\nпакеты')
        buttonPrevious.on_clicked(self.buildPrev)
        # Adding labels
        self.textPageTotalSubplot = plt.text(2.05, 0.0,
                                             f'{ceil(self.__class__.numberOfPackets / self.__class__.numberOfPacketsToShow)}',
                                             horizontalalignment='center',
                                             verticalalignment='center')
        plt.text(2.05, 0.5,
                 'из',
                 horizontalalignment='center',
                 verticalalignment='center')
        self.textPageCurrentubplot = plt.text(2.05, 1,
                                              f'{self.__class__.startPacket // self.__class__.numberOfPacketsToShow + 1}',
                                              horizontalalignment='center',
                                              verticalalignment='center')
        plt.show()

    def buildNext(self, event):
        self.__class__.subplotMain.cla()
        if self.__class__.startPacket.__ge__(self.__class__.numberOfPackets - self.__class__.numberOfPacketsToShow):
            self.__class__.startPacket = 0
        else:
            self.__class__.startPacket += self.__class__.numberOfPacketsToShow
        self.textPageCurrentubplot.set_text(
            f'{self.__class__.startPacket // self.__class__.numberOfPacketsToShow + 1}')
        self.updatePlot()
        self.__class__.figure.canvas.draw()

    def buildPrev(self, event):
        if self.__class__.startPacket.__lt__(self.__class__.numberOfPacketsToShow):
            self.__class__.startPacket = 0
        else:
            self.__class__.subplotMain.cla()
            self.__class__.startPacket -= self.__class__.numberOfPacketsToShow
            self.textPageCurrentubplot.set_text(
                f'{self.__class__.startPacket // self.__class__.numberOfPacketsToShow + 1}')
            self.updatePlot()
            self.__class__.figure.canvas.draw()

    def scrollLeft(self, event):
        self.__class__.subplotMain.cla()
        self.__class__.startPacket = 0
        self.textPageCurrentubplot.set_text(f'{self.__class__.startPacket // self.__class__.numberOfPacketsToShow + 1}')
        self.updatePlot()
        self.__class__.figure.canvas.draw()

    def scrollRight(self, event):
        self.__class__.subplotMain.cla()
        self.__class__.startPacket = self.__class__.numberOfPackets - self.__class__.numberOfPacketsToShow
        if self.__class__.startPacket < 0:
            self.__class__.startPacket = 0
        self.textPageCurrentubplot.set_text(f'{self.__class__.startPacket // self.__class__.numberOfPacketsToShow + 1}')
        self.updatePlot()
        self.__class__.figure.canvas.draw()

    def updatePlot(self):
        fileToOpen = self.__class__.fileName
        try:
            fileToRead = open(fileToOpen, 'rb')
        except:
            Window_Error(self.master, f'Невозможно открыть \'{self.__class__.fileName}\'.\nВозможно, он занят или удален.')
            return 404
        packetsPlotted = 0
        packetNumber = 0
        spectrumTotal = 0
        freq = 0

        samplesTotal = 0
        signalTotal = np.array([])
        while True:
            packet = fileToRead.read(8192 * 1)
            # Skipping processing of uninteresting packets
            if packetNumber.__lt__(self.__class__.startPacket):
                packetNumber += 1
                continue
            # Stop condition - if there is nothing more to read
            # or all the packets that need to be displayed are already plotted
            if packet.__eq__(b'') or packetsPlotted.__eq__(self.__class__.numberOfPacketsToShow):
                fileToRead.close()
                break
            formattedData = list(struct.unpack(f'{len(packet) // 2}h', bytearray(packet)))
            I = np.array([])
            Q = np.array([])
            if self.__class__.isComplexSignal.__eq__(True):
                I = np.append(I, formattedData[0::2])
                Q = np.append(Q, formattedData[1::2])
                # Calculating signal
                Y = I + 1j * Q
                samplesTotal += Y.size
                signalTotal = np.append(signalTotal, Y)
            else:
                I = np.append(I, formattedData)
                # Signal is equivalent to the read data
                Y = I
                samplesTotal += Y.size
                signalTotal = np.append(signalTotal, Y)
            packetsPlotted += 1
            # if self.__class__.isComplexSignal.__eq__(True):
            #     # print('Complex signal')
            #     I = np.append(I, formattedData[0::2])
            #     Q = np.append(Q, formattedData[1::2])
            #     # Calculating signal
            #     Y = I + 1j * Q
            #     # Calculating X axis values
            #     samplesNum = Y.size
            #     freq = np.fft.fftfreq(samplesNum, d=0.0002)
            #     freq = np.fft.fftshift(freq)
            #     # Getting window for FFT
            #     window = np.bartlett(samplesNum)
            #     # Calculating spectrum
            #     spectrum = np.fft.fft(Y * window)
            #     spectrum = np.fft.fftshift(spectrum)
            # else:
            #     # print('Real signal')
            #     I = np.append(I, formattedData)
            #     # Signal is equivalent to the read data
            #     Y = I
            #     # Calculating X axis values
            #     samplesNum = Y.size
            #     freq = np.fft.fftfreq(samplesNum // 2 + 1, d=0.0002)
            #     freq = np.fft.fftshift(freq)
            #     # Getting window for FFT
            #     window = np.bartlett(samplesNum)
            #     # Calculating spectrum
            #     spectrum = np.fft.rfft(Y * window) / samplesNum
            #     spectrum = np.fft.fftshift(spectrum)
            # spectrum = spectrum * 2 / (samplesNum * 32768)
            # spectrum = abs(spectrum)
            # spectrum = 20 * np.log10(spectrum)
            # spectrumTotal += spectrum
            # packetsPlotted += 1
        freq = np.fft.fftfreq(samplesTotal, d=0.0002)
        freq = np.fft.fftshift(freq)
        window = np.bartlett(samplesTotal)
        spectrum = np.fft.fft(signalTotal * window)
        spectrum = np.fft.fftshift(spectrum)
        spectrum = spectrum * 2 / (samplesTotal * 32768)
        spectrum = abs(spectrum)
        spectrum = 20 * np.log10(spectrum)

        self.__class__.subplotMain.plot(freq, spectrum, linewidth=1)
        # self.__class__.subplotMain.plot(freq, spectrumTotal / packetsPlotted, linewidth=1)
        # Configuring y axes
        plt.setp(self.__class__.subplotMain, ylim=(self.__class__.yLimitLow, self.__class__.yLimitHigh))
        return 0

    def ylimSetHigh(self, event):
        self.__class__.yLimitHigh = int(self.textboxLimitHigh.text)

    def ylimSetLow(self, event):
        self.__class__.yLimitLow = int(self.textboxLimitLow.text)

    def animationSpeedSet(self, event):
        self.__class__.animationSpeed = self.sliderAnimationSpeed.valmax + 0.1 - self.sliderAnimationSpeed.val

    def packetsToShowSet(self, event):
        self.textPageTotalSubplot.set_text(f'{ceil(self.__class__.numberOfPackets / self.__class__.numberOfPacketsToShow)}')
        self.textPageCurrentubplot.set_text(f'{self.__class__.startPacket // self.__class__.numberOfPacketsToShow + 1}')
        try:
            self.__class__.numberOfPacketsToShow = int(self.textboxPacketsToShow.text)
            if self.__class__.numberOfPacketsToShow.__eq__(0):
                raise Exception
        except:
            self.__class__.numberOfPacketsToShow = 1
            self.textboxPacketsToShow.set_val('1')


    def draw(self):
        result = self.updatePlot()
        if result.__eq__(404):
            return
        self.configure()

    def animate(self, event):
        if self.__class__.animationInProgress.__eq__(True):
            self.__class__.animationInProgress = False
            self.buttonAnimateSubplot.images[0].set_data(self.__class__.animationStartIcon)
        else:
            self.__class__.animationInProgress = True
            self.buttonAnimateSubplot.images[0].set_data(self.__class__.animationStopIcon)
        while True:
            try:
                self.buildNext(event)
                plt.pause(self.__class__.animationSpeed)
                if self.__class__.animationInProgress.__eq__(False):
                    break
            except:
                self.__class__.animationInProgress = False
                break
