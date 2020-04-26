import tkinter as tk


class Window_Error:
    window = None

    def __init__(self, master, errorMessage):
        if self.__class__.window is not None:
            self.__class__.window.destroy()
        self.__class__.window = tk.Toplevel(master)
        self.__class__.window.title('Возникла ошибка')
        self.canvas = tk.Canvas(self.__class__.window,
                                width=400,
                                height=50,
                                bg='#ee9086',
                                cursor='arrow')
        self.__class__.window.resizable(False, False)
        self.__class__.window.attributes('-topmost', True, '-toolwindow', True)
        self.__class__.window.geometry("+%d+%d" % (master.winfo_x() + 470,
                                                   master.winfo_y()
                                                   )
                                       )
        self.canvas.create_text(200, 25,
                                anchor=tk.CENTER,
                                justify='center',
                                font="TimesNewRoman 12",
                                text=errorMessage)
        self.canvas.pack()


class Window_Settings:
    window = None

    def __init__(self, master, type=None):
        if self.__class__.window is not None:
            self.__class__.window.destroy()
        self.type = type
        self.master = master
        self.__class__.window = tk.Toplevel(self.master)
        windowType = 'осциллограммы' if self.type.__eq__('oscillogram') else 'спектрограммы'
        self.__class__.window.title(f'Настройки {windowType}')
        self.canvas = tk.Canvas(self.__class__.window,
                                width=400,
                                height=250,
                                bg='skyblue',
                                cursor='arrow')
        self.__class__.window.resizable(False, False)
        self.__class__.window.attributes('-topmost', True, '-toolwindow', True)
        self.__class__.window.geometry("+%d+%d" % (self.master.winfo_x() + 470,
                                                   self.master.winfo_y()
                                                   )
                                       )
        self.configure()
        self.canvas.pack()

    def configure(self):
        # Number of packets
        self.canvas.create_text(20, 20,
                                anchor=tk.NW,
                                font="TimesNewRoman 12",
                                text='Отрисовать пакетов:')
        self.canvas.create_window(380, 20,
                                  anchor=tk.NE,
                                  window=tk.Spinbox(self.__class__.window,
                                                    width=5,
                                                    justify='right',
                                                    fg="dodgerblue",
                                                    font=('Symbol', '10', 'bold')))
        # Animation speed
        self.canvas.create_text(20, 50,
                                anchor=tk.NW,
                                font="TimesNewRoman 12",
                                text='Скорость анимации:')
        self.canvas.create_window(380, 50,
                                  anchor=tk.NE,
                                  window=tk.Spinbox(self.__class__.window,
                                                    width=5,
                                                    justify='right',
                                                    fg="dodgerblue",
                                                    font=('Symbol', '10', 'bold')))
        # Signal type - complex or real
        self.canvas.create_text(20, 80,
                                anchor=tk.NW,
                                font="TimesNewRoman 12",
                                text='Тип сигнала:')
        self.varSignalType = tk.StringVar()
        self.varSignalType.set('complex')
        self.canvas.create_window(200, 80,
                                  anchor=tk.NW,
                                  window=tk.Radiobutton(self.__class__.window,
                                                        variable=self.varSignalType,
                                                        text='действительный',
                                                        font='TimesNewRoman 12',
                                                        bg="skyblue",
                                                        value='real'))
        self.canvas.create_window(200, 110,
                                  anchor=tk.NW,
                                  window=tk.Radiobutton(self.__class__.window,
                                                        variable=self.varSignalType,
                                                        text='комплексный',
                                                        font='TimesNewRoman 12',
                                                        bg="skyblue",
                                                        value='complex'))
        # Signal file type
        self.canvas.create_text(20, 140,
                                anchor=tk.NW,
                                font="TimesNewRoman 12",
                                text='Сигнал для построения:')
        self.varFileType = tk.StringVar()
        self.varFileType.set('amplified')
        self.canvas.create_window(200, 140,
                                  anchor=tk.NW,
                                  window=tk.Radiobutton(self.__class__.window,
                                                        variable=self.varFileType,
                                                        text='исходный',
                                                        font='TimesNewRoman 12',
                                                        bg="skyblue",
                                                        value='original'))
        self.canvas.create_window(200, 170,
                                  anchor=tk.NW,
                                  window=tk.Radiobutton(self.__class__.window,
                                                        variable=self.varFileType,
                                                        text='усиленный',
                                                        font='TimesNewRoman 12',
                                                        bg="skyblue",
                                                        value='amplified'))
        # Control buttons
        self.canvas.create_window(20, 235,
                                  anchor=tk.SW,
                                  window=tk.Button(self.__class__.window,
                                                   bd='0',
                                                   bg="white",
                                                   width=10,
                                                   compound='top',
                                                   fg="dodgerblue",
                                                   font=('Symbol', '12', 'bold'),
                                                   text='Применить'))
        self.canvas.create_window(380, 235,
                                  anchor=tk.SE,
                                  window=tk.Button(self.__class__.window,
                                                   bd='0',
                                                   bg="white",
                                                   width=10,
                                                   compound='top',
                                                   fg="dodgerblue",
                                                   font=('Symbol', '12', 'bold'),
                                                   text='Закрыть',
                                                   command=self.close))

    def close(self):
        self.__class__.window.destroy()

    def accept(self):
        if self.varFileType.get().__eq__('amplified'):
            pass
