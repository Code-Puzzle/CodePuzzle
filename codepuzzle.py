import random

import cocos
from cocos.director import director
from cocos.actions import *

from pyglet import gl


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

        # Перемешиваем строки и добавляем их к слою для отрисовки. Также добавляем позиции
        # TODO: Хардкод! Позиционировать строчки кода относительно игрового экрана
        i = 0
        strings = random.sample(strings, len(strings))
        for string in strings:
            self.lines.append(RectWithText(string, (0.3, 0.3, 1, 1), 50, director.get_window_size()[1]-100-20*i))
            self.positions.append(RectPosition(350, director.get_window_size()[1] - 100 - 20 * i))
            i += 1

        for line in self.lines:
            self.add(line, z=1)

        for pos in self.positions:
            self.add(pos, z=0)
        # Добавляем строку, сообщающую о выигрыше, в спрятанном состоянии
        # TODO: Переделать сообщение о победе во что-то няшное
        self.winning_line = cocos.text.Label("Поздравляю! Ты собрал правильный код!", (50, 100))
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
    """                          --------ТУТ Я ЗАКОНЧИЛ КОММЕНТИРОВАТЬ------                               """
    def on_mouse_release(self, x, y, buttons, modifiers):
        """This function is called when any mouse button is pressed

        (x, y) are the physical coordinates of the mouse
        'buttons' is a bitwise or of pyglet.window.mouse constants LEFT, MIDDLE, RIGHT
        'modifiers' is a bitwise or of pyglet.window.key modifier constants
           (values like 'SHIFT', 'OPTION', 'ALT')
        """

        if buttons == 1:
            x, y = director.get_virtual_coordinates(x, y)
            if self.is_dragged:
                pos = self.parent.is_line_in_unoccupied_position(x, y)
                if not pos:
                    self.is_dragged = False
                    self.do(MoveTo((self.startx, self.starty), 0.25))
                    self.parent.dragged_line = None
                    if self.in_position:
                        self.in_position.is_occupied = False
                        self.in_position.occupying_line = ""
                        self.in_position = None
                else:
                    self.is_dragged = False
                    self.do(MoveTo((pos.x, pos.y), 0.1))
                    self.parent.dragged_line = self
                    if self.in_position:
                        self.in_position.is_occupied = False
                        self.in_position.occupying_line = ""
                        self.in_position = None
                    pos.is_occupied = True
                    pos.occupying_line = self.line
                    self.in_position = pos
        if self.parent.goal():
            self.parent.winning_line.do(Show())
        else:
            self.parent.winning_line.do(Hide())

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.is_dragged:
            x, y = director.get_virtual_coordinates(x, y)
            self.do(Place((x - self.w/2, y - self.h/2)))


class RectPosition(cocos.layer.Layer):

    is_event_handler = True

    def __init__(self, x, y):
        super(RectPosition, self).__init__()

        self.is_occupied = False
        # self.is_hovered = False
        self.occupying_line = ""

        self.x = x
        self.y = y
        self.w = 250
        self.h = 18

        self.rectangle = Rectangle((1, 0.2, 0.2, 1), 0, 0, self.w, self.h)

        self.add(self.rectangle)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        x, y = director.get_virtual_coordinates(x, y)
        posx = self.x
        posy = self.y
        posx2 = self.x + self.w
        posy2 = self.y + self.h
        if (x >= posx) and (y >= posy) and (x <= posx2) and (y <= posy2) and not self.is_occupied:
            self.rectangle.layer_color = (0.2, 1, 0.2, 1)
        else:
            self.rectangle.layer_color = (1, 0.2, 0.2, 1)

    def on_mouse_release(self, x, y, buttons, modifiers):
        """This function is called when any mouse button is pressed

        (x, y) are the physical coordinates of the mouse
        'buttons' is a bitwise or of pyglet.window.mouse constants LEFT, MIDDLE, RIGHT
        'modifiers' is a bitwise or of pyglet.window.key modifier constants
           (values like 'SHIFT', 'OPTION', 'ALT')
        """
        self.rectangle.layer_color = (1, 0.2, 0.2, 1)


class Rectangle(cocos.layer.Layer):

    """Rectangle (color, x, y, w, h) : A layer drawing a rectangle at (x,y) of
    given color and w, h"""

    def __init__(self, color, x, y, w, h):
        super(Rectangle, self).__init__()

        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.layer_color = color

    def draw(self):
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

code = [line.strip() for line in open("code.txt", 'r')]

director.init(width=1024, height=768, caption="Code Puzzle", fullscreen=False)

sc = cocos.scene.Scene(DragDropStrings(code))

director.run(sc)
