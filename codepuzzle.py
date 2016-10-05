import random

import cocos
from cocos.director import director
from cocos.actions import *

from pyglet import gl

WIDTH = 1024
HEIGHT = 768


class DragDropStrings(cocos.layer.Layer):
    """
    DragDropStrings - слой, в котором происходит  перетаскивание строчек кода.
    Тут же и часть игровой логики
    """
    def __init__(self, strings):
        """ Конструктор"""
        super(DragDropStrings, self).__init__()

        self.dragged_line = None  # таскаемая в данный момент строчка кода (RectWithText)
        self.original_strings = strings[:]  # оригинальный код, который нужно собрать
        self.lines = []  # lines - список строк RectWithText
        self.positions = []  # positions - список позиций для строк RectPosition
        global background
        self.background = background
        self.add(self.background)
        # Перемешиваем строки и добавляем их к слою для отрисовки. Также добавляем позиции
        # TODO: Хардкод! Позиционировать строчки кода относительно игрового экрана
        i = 0
        strings = random.sample(strings, len(strings))
        for string in strings:
            self.lines.append(RectWithText(string, (0.3, 0.3, 1, 1), 100, HEIGHT-100-20*i))
            self.positions.append(RectPosition(WIDTH/2, HEIGHT - 100 - 20 * i))
            i += 1

        for line in self.lines:
            self.add(line, z=1)

        for pos in self.positions:
            self.add(pos, z=0)
        # Добавляем строку, сообщающую о выигрыше, в спрятанном состоянии
        # TODO: Переделать сообщение о победе во что-то няшное
        self.winning_line = cocos.text.Label("Поздравляю! Ты собрал правильный код!", (WIDTH/2 - 100, 100))
        self.winning_line.do(Hide())
        self.add(self.winning_line)

    def is_line_in_unoccupied_position(self, x, y):
        """ Функция для проверки, попадает ли строка в незанятую позицию
            Если попадает, возвращается ссылку на объект позиции (RectPosition)
            Если нет, возвращается False
        """
        for position in self.positions:
            posx = position.x
            posy = position.y
            posx2 = position.x + position.w
            posy2 = position.y + position.h
            if (x >= posx) and (y >= posy) and (x <= posx2) and (y <= posy2) and not position.is_occupied:
                return position
        return False

    def goal(self):
        """ Функция проверяет, собран ли правильно код. Составляется список занятых строк и сравнивается
            с оригинальным списком
            Возвращает True/False соответственно
        """
        attempt = []
        for pos in self.positions:
            attempt.append(pos.occupying_line)
        if attempt == self.original_strings:
            return True
        return False


class RectWithText(cocos.layer.Layer):
    """ RectWithText - слой, который содержит строчку собираемого кода, и всё для работы с ней.
        Является обработчиком событий
    """
    # TODO: запилить методы, которые буду управлять состояниями строки(находится/не находится в позиции и т д)

    is_event_handler = True

    def __init__(self, text, color, x, y):
        """ Конструктор"""
        super(RectWithText, self).__init__()

        self.is_dragged = False  # флаг, показывает, тащит ли юзер эту строчку мышкой в данный момент

        self.x = x  # x координата
        self.y = y  # y координата
        self.startx = x  # x координата стартовой позиции. Для возвращения строки на исходное место
        self.starty = y  # y координата стартовой позиции. Для возвращения строки на исходное место

        self.w = len(text)*10  # Длина прямоугольника со строкой. TODO: Хардкод! Более точно считать размер строки
        self.h = 18  # Высота прямоугольника со строкой. TODO: Хардкод! Переделать, если будет изменяться шрифт

        self.line = text  # Строковое значение - одна из строк кода. Используется для записи в соотв. поле позиции
        self.in_position = None  # ссылка на объект позиции (RectPosition) в которой находится строка

        self.rectangle = Rectangle(color, 0, 0, self.w, self.h)  # объект цветная подложка под текстом (Rectangle)
        self.text = cocos.text.Label(text, x=2, y=4)  # объект cocos.label.label с текстом строки кода
        # Добавляем в слой подложку и сам текст
        self.add(self.rectangle)
        self.add(self.text)

    def on_mouse_press(self, x, y, buttons, modifiers):
        """ Обработчик события  - нажатие кнопки мыши
        x, y - физические координаты курсора
        buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        # Если нажата левая кнопка, проверяем, попали ли в одну из таскаемых строчек, если да - начинаем таскать
        if buttons == 1:
            x, y = director.get_virtual_coordinates(x, y)  # перевод из физических координат в виртуальные
            posx = self.x
            posy = self.y
            posx2 = self.x + self.w
            posy2 = self.y + self.h
            if (x >= posx) and (y >= posy) and (x <= posx2) and (y <= posy2) and not(self.are_actions_running()):
                # TODO: что-то сделать с этим хаком
                # Тут для того, чтобы поменять z-уровень строки, она удаляется из списка, а потом добавляется заново
                self.is_dragged = True
                # hack:
                dragged = self
                par = self.parent
                self.kill()
                par.add(dragged, z=1)
                # /hack
                self.parent.dragged_line = self

    def on_mouse_release(self, x, y, buttons, modifiers):
        """ Обработчик события  - отпускание кнопки мыши
        x, y - физические координаты курсора
        buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        if buttons == 1:  # если нажата ЛКМ
            x, y = director.get_virtual_coordinates(x, y)  # перевод из физических координат в виртуальные
            if self.is_dragged:  # если строчку таскают
                pos = self.parent.is_line_in_unoccupied_position(x, y)
                if pos:  # проверяем, попали ли в незанятую позицию
                    self.is_dragged = False
                    self.do(MoveTo((pos.x, pos.y), 0.1))
                    self.parent.dragged_line = self
                    if self.in_position:  # если строка уже была в позиции, очищаем позицию
                        self.in_position.is_occupied = False
                        self.in_position.occupying_line = ""
                        self.in_position = None
                    pos.is_occupied = True
                    pos.occupying_line = self.line
                    self.in_position = pos
                else:  # если не попала - возвращаем строку на исходную
                    # TODO: сделать так, чтобы если строка была в какой-то позиции, она возвращалась на неё
                    self.is_dragged = False
                    self.do(MoveTo((self.startx, self.starty), 0.25))
                    self.parent.dragged_line = None
                    if self.in_position:
                        self.in_position.is_occupied = False
                        self.in_position.occupying_line = ""
                        self.in_position = None
        #  TODO: Заглушка! Возможно надо куда-нибудь это убрать - сделать обработчик события победы
        if self.parent.goal():  # проверяем, не достигнута ли цель
            self.parent.winning_line.do(Show())
            self.parent.parent.next_button.is_active = True
            self.parent.parent.next_button.do(Show())
        else:
            self.parent.winning_line.do(Hide())
            self.parent.parent.next_button.is_active = False
            self.parent.parent.next_button.do(Hide())

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """ Обработчик события  - таскание мышью
            x, y - физические координаты курсора
            buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        if self.is_dragged:  # если именно эту строчку таскают - таскаемся =)
            x, y = director.get_virtual_coordinates(x, y)
            self.do(Place((x - self.w/2, y - self.h/2)))  # за серединку


class Button(cocos.layer.Layer):
    """ Button - слой, который содержит кнопку.
        Является обработчиком событий
    """

    is_event_handler = True

    def __init__(self, text, color=(0, 0, 0, 0), color_pressed=(0.5, 0.5, 0.5, 1), x=0, y=0, w=1, h=1,
                 active=True, func=None, *args, **kwargs):
        """ Конструктор"""
        super(Button, self).__init__()
        self.is_active = active  # активна кнопка или нет
        self.x = x  # x координата
        self.y = y  # y координата
        self.w = w  # Длина кнопки
        self.h = h  # Высота кнопки
        self.line = text  # Надпись на кнопке
        self.func = func  # функция или метод, которая должна выполнится при нажатии на кнопку
        self.args = args
        self.kwargs = kwargs
        self.color = color
        self.color_pressed = color_pressed
        self.rectangle = Rectangle(color, 0, 0, self.w, self.h)  # объект цветная подложка под текстом (Rectangle)
        self.text = cocos.text.Label(text, x=2, y=4, font_size=16)  # объект cocos.label.label с текстом
        # Добавляем в слой подложку и сам текст
        self.add(self.rectangle)
        self.add(self.text)

    def on_mouse_press(self, x, y, buttons, modifiers):
        """ Обработчик события  - нажатие кнопки мыши
        x, y - физические координаты курсора
        buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        if buttons == 1:
            x, y = director.get_virtual_coordinates(x, y)  # перевод из физических координат в виртуальные
            posx = self.x
            posy = self.y
            posx2 = self.x + self.w
            posy2 = self.y + self.h
            if (x >= posx) and (y >= posy) and (x <= posx2) and (y <= posy2) and self.is_active:
                self.rectangle.layer_color = self.color_pressed

    def on_mouse_release(self, x, y, buttons, modifiers):
        """ Обработчик события  - отпускание кнопки мыши
        x, y - физические координаты курсора
        buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        if buttons == 1:
            x, y = director.get_virtual_coordinates(x, y)  # перевод из физических координат в виртуальные
            posx = self.x
            posy = self.y
            posx2 = self.x + self.w
            posy2 = self.y + self.h
            if (x >= posx) and (y >= posy) and (x <= posx2) and (y <= posy2) and self.is_active:
                if self.func:
                    self.func(*self.args, **self.kwargs)
            else:
                self.rectangle.layer_color = self.color

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """ Обработчик события  - таскание мышью
            x, y - физические координаты курсора
            buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        if buttons == 1:
            x, y = director.get_virtual_coordinates(x, y)  # перевод из физических координат в виртуальные
            posx = self.x
            posy = self.y
            posx2 = self.x + self.w
            posy2 = self.y + self.h
            # проверяем, попадает ли курсор, если да - изменяем цвет прямоугольника
            if (x >= posx) and (y >= posy) and (x <= posx2) and (y <= posy2) and self.is_active:
                self.rectangle.layer_color = self.color_pressed
            else:
                self.rectangle.layer_color = self.color


class RectPosition(cocos.layer.Layer):
    """ RectPosition - слой, который содержит позицию, в которой может находится строчка кода, и всё для работы с ней.
        Является обработчиком событий
    """
    # TODO: запилить методы, которые буду управлять состояниями позиции (в неё попала строка, очистить позицию и т д)

    is_event_handler = True

    def __init__(self, x, y):
        """ Конструктор """
        super(RectPosition, self).__init__()

        self.is_occupied = False  # флаг занятости позиции
        self.occupying_line = ""  # строка текста, если позиция занята. Из них собирается список для проверки

        self.x = x  # x - координата
        self.y = y  # y - координата
        self.w = 250  # ширина позиции TODO: Хардкод! Сделать ширину равной самой длинной строке исходного кода
        self.h = 18  # высота позиции TODO: Хардкод! Если будет меняться размер шрифта, нужно будет менять

        self.rectangle = Rectangle((1, 0.2, 0.2, 1), 0, 0, self.w, self.h)  # закрашений прямоугольник (Rectangle)

        self.add(self.rectangle)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """ Обработчик события  - таскание мышью
            x, y - физические координаты курсора
            buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        x, y = director.get_virtual_coordinates(x, y)  # перевод из физических координат в виртуальные
        posx = self.x
        posy = self.y
        posx2 = self.x + self.w
        posy2 = self.y + self.h
        # проверяем, попадает ли курсор в позицию, если да - изменяем цвет прямоугольника
        if (x >= posx) and (y >= posy) and (x <= posx2) and (y <= posy2) and not self.is_occupied:
            self.rectangle.layer_color = (0.2, 1, 0.2, 1)  # зелёненький
        else:
            self.rectangle.layer_color = (1, 0.2, 0.2, 1)  # красненький

    def on_mouse_release(self, x, y, buttons, modifiers):
        """ Обработчик события  - отпускание кнопки мыши
        x, y - физические координаты курсора
        buttons - нажатые кнопки. Опытным путем установлено: 1 - левая, 4 - правая, 2 - средняя
        """
        self.rectangle.layer_color = (1, 0.2, 0.2, 1)  # меняем цвет на красный в любом случае при отпускании мыши
        # TODO: убрать функционал в метод заполнения/очищения позиции. Сделать, чтобы цвет менялся для заполненной


class Rectangle(cocos.layer.Layer):

    """Rectangle (color, x, y, w, h) : слой, который рисует прямоугольник в (x,y) нужного цвета, ширины и высоты"""

    def __init__(self, color, x, y, w, h):
        """ Конструктор """
        super(Rectangle, self).__init__()

        self.x = x  # x - координата
        self.y = y  # y - координата
        self.w = w  # высота прямоугольника
        self.h = h  # ширина прямоугольника
        self.layer_color = color  # цвет прямоугольника (в формате OpenGL - (R<от 0 до 1>,G,B,A - альфа)  )

    def draw(self):
        """ Функция рисования прямоугольника, с использованием pyglet.gl """
        super(Rectangle, self).draw()

        gl.glColor4f(*self.layer_color)
        x, y = self.x, self.y
        w = x + self.w
        h = y + self.h
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(x, y)
        gl.glVertex2f(x, h)
        gl.glVertex2f(w, h)
        gl.glVertex2f(w, y)
        gl.glEnd()
        gl.glColor4f(1, 1, 1, 1)


class SceneTheory(cocos.scene.Scene):
    def __init__(self, picture_file, progress, prev_scene=None, next_scene=None):
        super(SceneTheory, self).__init__()
        self.progress = progress
        self.prev_scene = prev_scene
        self.next_scene = next_scene
        self.background = cocos.sprite.Sprite(image='code-1024x768.jpg', position=(WIDTH/2, HEIGHT/2))
        self.add(self.background)
        self.picture = cocos.sprite.Sprite(image=picture_file, position=(WIDTH/2, HEIGHT/2))
        self.add(self.picture)
        self.prev_button = Button('Назад', (0, 0.7, 0, 1), (0.5, 0.7, 0, 1), WIDTH / 5, 50, 100, 20, True,
                                  self.on_prev)
        self.add(self.prev_button)
        self.next_button = Button('Дальше', (0, 0.7, 0, 1), (0.5, 0.7, 0, 1), WIDTH / 5 * 3, 50, 100, 20, True,
                                  self.on_next)
        self.add(self.next_button)

    def on_next(self):
        global progress
        if progress < self.progress:
            progress = self.progress
        if self.next_scene == 'themes_menu':
            global background
            self.next_scene = cocos.scene.Scene(background, ThemesMenu())
        director.replace(self.next_scene)

    def on_prev(self):
        if self.prev_scene == 'themes_menu':
            global background
            self.prev_scene = cocos.scene.Scene(background, ThemesMenu())
        director.replace(self.prev_scene)


class SceneCode(cocos.scene.Scene):
    def __init__(self, code_file, task_file, progress, prev_scene=None, next_scene=None):
        super(SceneCode, self).__init__()
        self.progress = progress
        self.prev_scene = prev_scene
        self.next_scene = next_scene
        self.background = cocos.sprite.Sprite(image='code-1024x768.jpg', position=(WIDTH/2, HEIGHT/2))
        self.add(self.background)
        self.strings = DragDropStrings([line.strip() for line in open(code_file, 'r')])
        self.add(self.strings)
        self.prev_button = Button('Назад', (0, 0.7, 0, 1), (0.5, 0.7, 0, 1), WIDTH / 5, 50, 100, 20, True,
                                  self.on_prev)
        self.add(self.prev_button)
        self.next_button = Button('Дальше', (0, 0.7, 0, 1), (0.5, 0.7, 0, 1), WIDTH / 5 * 3, 50, 100, 20, True,
                                  self.on_next)
        self.next_button.is_active = False
        self.next_button.do(Hide())
        self.add(self.next_button)
        self.task = cocos.text.Label(''.join([line for line in open(task_file, 'r')]), (50, HEIGHT-20),
                                     multiline=True, width=WIDTH-100)
        self.add(self.task)

    def on_next(self):
        global progress
        if progress < self.progress:
            progress = self.progress
        if self.next_scene == 'themes_menu':
            global background
            self.next_scene = cocos.scene.Scene(background, ThemesMenu())
        director.replace(self.next_scene)

    def on_prev(self):
        if self.prev_scene == 'themes_menu':
            global background
            self.prev_scene = cocos.scene.Scene(background, ThemesMenu())
        director.replace(self.prev_scene)


class MainMenu(cocos.menu.Menu):
    def __init__(self):
        super(MainMenu, self).__init__('Конструктор программ Pascal')
        self.menu_valign = cocos.menu.CENTER
        self.menu_halign = cocos.menu.CENTER

        menu_items = [
            (cocos.menu.MenuItem("Задания", self.on_puzzles)),
            (cocos.menu.MenuItem("Сбросить прогресс", self.on_clear_progress)),
            (cocos.menu.MenuItem("Выход", self.on_quit))]
        self.create_menu(menu_items)

    def on_puzzles(self):
        global background
        director.run(cocos.scene.Scene(background, ThemesMenu()))

    def on_clear_progress(self):
        global progress
        progress = 0

    def on_quit(self):
        global progress
        open('progress', 'w').write(str(progress))
        exit()


class ThemesMenu(cocos.menu.Menu):
    def __init__(self):
        global progress
        super(ThemesMenu, self).__init__('Выбери тему')
        self.menu_valign = cocos.menu.CENTER
        self.menu_halign = cocos.menu.CENTER
        menu_items = []
        if progress >= 0:
            menu_items.append(cocos.menu.MenuItem("Общий вид программ на Паскале", self.on_theme, 1))
        if progress >= 1:
            menu_items.append(cocos.menu.MenuItem("Линейные программы", self.on_theme, 2))
        if progress >= 2:
            menu_items.append(cocos.menu.MenuItem("Условный переход", self.on_theme, 3))
        menu_items.append(cocos.menu.MenuItem("Назад", self.on_back))
        self.create_menu(menu_items)

    def on_theme(self, theme):
        global background
        if theme == 1:
            sc1 = SceneTheory('data/theme1pic1.jpg', 1, 'themes_menu', 'themes_menu')
            director.run(sc1)
        if theme == 2:
            sc1 = SceneTheory('data/theme2pic1.jpg', 0, 'themes_menu')
            sc2 = SceneCode('puzzles/theme2code1.txt', 'puzzles/theme2task1.txt', 0)
            sc3 = SceneCode('puzzles/theme2code2.txt', 'puzzles/theme2task2.txt', 2)
            sc1.next_scene = sc2
            sc2.prev_scene = sc1
            sc2.next_scene = sc3
            sc3.prev_scene = sc2
            sc3.next_scene = 'themes_menu'
            director.run(sc1)
        if theme == 3:
            sc1 = SceneTheory('data/theme3pic1.jpg', 0, 'themes_menu')
            sc2 = SceneCode('puzzles/theme3code1.txt', 'puzzles/theme3task1.txt', 0)
            sc3 = SceneCode('puzzles/theme3code2.txt', 'puzzles/theme3task2.txt', 3)
            sc1.next_scene = sc2
            sc2.prev_scene = sc1
            sc2.next_scene = sc3
            sc3.prev_scene = sc2
            sc3.next_scene = 'themes_menu'
            director.run(sc1)

    def on_back(self):
        global scene_main_menu
        director.run(scene_main_menu)

    def on_quit(self):
        global progress
        open('progress', 'w').write(str(progress))
        exit()

# Сначала запишем все сцены в нужном порядке по разделам в cocos.scene.sequence, и будем идти через них с помощью
# director.pop(), по пути записывая прогресс
# еще нужно сделать сцену (слой?) с картинкой и кнопками Назад Далее

# Тут начинается выполнение программы
try:
    progress = int(open('progress', 'r').read())
except FileNotFoundError:
    progress = 0
director.init(width=1024, height=768, caption="Code Puzzle", fullscreen=False)  # инициализация окна игры
background = cocos.sprite.Sprite(image='code-1024x768.jpg', position=(WIDTH/2, HEIGHT/2))
scene_main_menu = cocos.scene.Scene(background, MainMenu())
director.run(scene_main_menu)  # запускаем сцену
