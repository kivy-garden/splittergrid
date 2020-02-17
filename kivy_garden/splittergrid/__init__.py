"""
Demo flower
============

Defines the Kivy garden :class:`FlowerLabel` class which is the widget provided
by the demo flower.
"""

from ._version import __version__

from kivy.core.window import Window
from kivy.uix.layout import Layout
from kivy.properties import (
    ListProperty, NumericProperty, OptionProperty, BooleanProperty
)

from math import ceil

__all__ = ['SplitterGrid']


class SplitterGrid(Layout):
    """A grid where you can manually resize rows and columns using
    touch, supports all possible filling order (see `orientation`), and
    constraining the number of cols or rows (the other will be
    automatically computed).
    """
    cols = NumericProperty(0)
    ':attr:cols is a NumericProperty and allows setting the number of columns'
    rows = NumericProperty(0)
    ':attr:rows is a NumericProperty and allows setting the number of rows'
    margin = NumericProperty(10)
    ':attr:margin is a NumericProperty and allows setting the space between each column/row.'

    col_ratios = ListProperty()
    ':attr:col_ratios is a ListProperty containing the current list of relative sizes in the order of columns'
    row_ratios = ListProperty()
    ':attr:row_ratios is a ListProperty containing the current list of relative sizes in the order of rows'

    min_col_width = NumericProperty(40)
    ':attr:min_col_width is a NumericProperty and sets the minimum width of any column'
    min_row_height = NumericProperty(40)
    ':attr:min_row_height is a NumericProperty and sets the minimum height of any row'

    orientation = OptionProperty(
        'lr-tb',
        options=[
            'tb-lr', 'bt-lr', 'tb-rl', 'bt-rl',
            'lr-tb', 'lr-bt', 'rl-tb', 'rl-bt'
        ]
    )
    ':attr:orientation is an OptionProperty and sets the filling order of the grid.'

    override_cursor = BooleanProperty(True)

    __events__ = ('on_resize_start', 'on_resize_complete')

    def __init__(self, **kwargs):
        super(SplitterGrid, self).__init__(**kwargs)
        self._resize_count = 0
        self.bind(
            pos=self.do_layout,
            size=self.do_layout,
            cols=self.do_layout,
            rows=self.do_layout,
            col_ratios=self.do_layout,
            row_ratios=self.do_layout,
            orientation=self.do_layout,
        )
        self.bind(
            cols=self.on_children,
            rows=self.on_children,
        )

        Window.bind(mouse_pos=self.update_cursor)

    def get_rows_cols(self, *args):
        if self.cols:
            cols = float(self.cols)
            rows = ceil(len(self.children) / cols)

        elif self.rows:
            rows = float(self.rows)
            cols = ceil(len(self.children) / rows)

        else:
            return 0, 0

        return rows, cols

    def update_cursor(self, win, pos):
        if not self.override_cursor:
            return

        if self._resize_count > 0:
            return

        col_row = self.match_col_row(self.to_widget(*pos))
        col = 'col' in col_row
        row = 'row' in col_row

        cursor = (
            'size_all'
            if col and row else
            'size_ns'
            if row else
            'size_we'
            if col else
            'arrow'
        )
        Window.set_system_cursor(cursor)

    def on_children(self, *args):
        rows, cols = self.get_rows_cols()

        while rows > len(self.row_ratios):
            self.row_ratios.append(1)
        while rows < len(self.row_ratios):
            self.row_ratios.pop()

        while cols > len(self.col_ratios):
            self.col_ratios.append(1)
        while cols < len(self.col_ratios):
            self.col_ratios.pop()

    def on_touch_down(self, touch):
        if super(SplitterGrid, self).on_touch_down(touch):
            return True

        result = self.match_col_row(touch.pos)
        if result:
            touch.ud['{}_col'.format(id(self))] = result.get('col')
            touch.ud['{}_row'.format(id(self))] = result.get('row')
            touch.grab(self)
            self.dispatch('on_resize_start', touch)
        return result

    def match_col_row(self, pos):
        result = {}
        if self.collide_point(*pos):
            rows, cols = self.get_rows_cols()
            margin = self.margin
            width = self.internal_width
            height = self.internal_height

            x, y = self.pos

            sum_col_ratios = sum(self.col_ratios)
            sum_row_ratios = sum(self.row_ratios)

            col_ratios = self.col_ratios
            for i, col in enumerate(col_ratios):
                x += width * col / sum_col_ratios
                if x < pos[0] < x + margin:
                    result['col'] = i
                    break
                x += margin

            row_ratios = self.row_ratios
            for i, row in enumerate(row_ratios):
                y += height * row / sum_row_ratios
                if y < pos[1] < y + margin:
                    result['row'] = i
                    break
                y += margin
        return result

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super(SplitterGrid, self).on_touch_move(touch)

        col = touch.ud.get('{}_col'.format(id(self)))
        row = touch.ud.get('{}_row'.format(id(self)))
        width = self.internal_width
        height = self.internal_height

        min_col_width = self.min_col_width
        min_row_height = self.min_row_height

        orientation = self.orientation.split('-')

        col_ratios = self.col_ratios
        row_ratios = self.row_ratios

        sum_col_ratios = sum(col_ratios)
        sum_row_ratios = sum(row_ratios)

        result = False

        if col is not None:
            dx = touch.dx
            col_pos = (
                self.x
                + self.margin * col
                + sum(
                    (width * c / sum_col_ratios)
                    for c in col_ratios[:col + 1]
                )
            )

            if (dx < 0 and touch.x < col_pos) or (dx > 0 and touch.x > col_pos):

                width_1 = width * (col_ratios[col] / sum_col_ratios) + dx
                width_2 = width * (col_ratios[col + 1] / sum_col_ratios) - dx

                total_width = width_1 + width_2
                width_1 = max(min_col_width, width_1)
                width_2 = total_width - width_1

                width_2 = max(min_col_width, width_2)
                width_1 = total_width - width_2

                # assume the sum of ratios didn't change
                col_ratios[col] = sum_col_ratios * width_1 / width
                col_ratios[col + 1] = sum_col_ratios * width_2 / width
                self.col_ratios = col_ratios

            result = True

        if row is not None:
            dy = touch.dy
            row_pos = self.y + self.margin * row + sum((height * r / sum_row_ratios) for r in row_ratios[:row + 1])
            if (dy < 0 and touch.y < row_pos) or (dy > 0 and touch.y > row_pos):
                height_1 = height * (row_ratios[row] / sum_row_ratios) + dy
                height_2 = height * (row_ratios[row + 1] / sum_row_ratios) - dy

                total_height = height_1 + height_2
                height_1 = max(min_row_height, height_1)
                height_2 = total_height - height_1

                height_2 = max(min_row_height, height_2)
                height_1 = total_height - height_2

                # assume the sum of ratios didn't change
                row_ratios[row] = sum_row_ratios * height_1 / height
                row_ratios[row + 1] = sum_row_ratios * height_2 / height
                self.row_ratios = row_ratios
            result = True

        if result:
            return True

        return super(SplitterGrid, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(SplitterGrid, self).on_touch_up(touch)

        col = touch.ud.get('{}_col'.format(id(self)))
        row = touch.ud.get('{}_row'.format(id(self)))
        if col is not None or row is not None:
            touch.ungrab(self)
            self.dispatch('on_resize_complete', touch)
            return True
        return super(SplitterGrid, self).on_touch_up(touch)

    @property
    def internal_width(self):
        rows, cols = self.get_rows_cols()
        sum_cols = sum(self.col_ratios)
        sum_margins_cols = self.margin * (cols - 1)
        return self.width - sum_margins_cols

    @property
    def internal_height(self):
        rows, cols = self.get_rows_cols()
        sum_rows = sum(self.row_ratios)
        sum_margins_rows = self.margin * (rows - 1)
        return self.height - sum_margins_rows

    def do_layout(self, *args):
        if not (self.cols or self.rows) or not (self.row_ratios and self.col_ratios):
            return

        i = 0
        children = self.children[::-1]

        sum_col_ratios = sum(self.col_ratios)
        sum_row_ratios = sum(self.row_ratios)

        y = self.y
        width = self.internal_width
        height = self.internal_height

        margin = self.margin

        orientation = self.orientation.split('-')
        if 'tb' in orientation:
            row_ratios = self.row_ratios[::-1]
        else:
            row_ratios = self.row_ratios

        if 'rl' in orientation:
            col_ratios = self.col_ratios[::-1]
        else:
            col_ratios = self.col_ratios

        if orientation[0] in ('bt', 'tb'):
            ratios_d1 = col_ratios
            ratios_d2 = row_ratios
            d1, d2 = 'yx'

        elif orientation[0] in ('lr', 'rl'):
            ratios_d1 = row_ratios
            ratios_d2 = col_ratios
            d1, d2 = 'xy'

        initial_pos = {
            'x': self.x if 'lr' in orientation else self.right,
            'y': self.y if 'bt' in orientation else self.top
        }
        pos = {k: v for k, v in initial_pos.items()}
        for r1 in ratios_d1:
            pos[d1] = initial_pos[d1]
            if not ratios_d2:
                continue
            for r2 in ratios_d2:
                w = children[i]
                i += 1
                w.width = width * (r2 if d1 == 'x' else r1)  / sum_col_ratios
                w.height = height * (r1 if d1 == 'x' else r2) / sum_row_ratios
                w.pos = (
                    pos['x'] - (w.width if 'rl' in orientation else 0),
                    pos['y'] - (w.height if 'tb' in orientation else 0)
                )
                pos[d1] += (
                    (margin + w.width) * (-1 if 'rl' in orientation else 1)
                    if d1 == 'x' else
                    (margin + w.height) * (-1 if 'tb' in orientation else 1)
                )
                if i >= len(children):
                    return
            pos[d2] += (
                (margin + w.height) * (-1 if 'tb' in orientation else 1)
                if d2 == 'y' else
                (margin + w.width) * (-1 if 'rl' in orientation else 1)
            )

    def on_resize_start(self, touch):
        self._resize_count += 1

    def on_resize_complete(self, touch):
        self._resize_count -= 1


EXAMPLE = '''
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        Spinner:
            id: spinner
            text: 'lr-tb'
            values:
                [
                'tb-lr', 'bt-lr', 'tb-rl', 'bt-rl',
                'lr-tb', 'lr-bt', 'rl-tb', 'rl-bt'
                ]
        
    SplitterGrid:
        id: grid
        cols: 5
        orientation: spinner.text or 'lr-tb'
'''


if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.factory import Factory as F
    from kivy.lang import Builder

    root = Builder.load_string(EXAMPLE)
    for i in range(25):
        root.ids.grid.add_widget(F.Button(text=f'{i}'))

    runTouchApp(root)
