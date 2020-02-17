import pytest


def test_flower():
    from kivy_garden.splittergrid import SplitterGrid
    grid = SplitterGrid(cols=5)
    assert grid.cols = 5
    assert grid.orientation ='lr-tb'
