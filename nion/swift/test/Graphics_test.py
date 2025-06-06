# standard libraries
import copy
import logging
import math
import typing
import unittest

# third party libraries
import numpy

# local libraries
from nion.data import Calibration
from nion.swift import Application
from nion.swift import DisplayPanel
from nion.swift import Facade
from nion.swift import ImageCanvasItem
from nion.swift.model import DataItem
from nion.swift.model import Graphics
from nion.swift.test import TestContext
from nion.ui import CanvasItem
from nion.ui import TestUI
from nion.utils import Geometry


Facade.initialize()


class TestGraphicsClass(unittest.TestCase):

    def setUp(self):
        TestContext.begin_leaks()
        self._test_setup = TestContext.TestSetup()

    def tearDown(self):
        self._test_setup = typing.cast(typing.Any, None)
        TestContext.end_leaks(self)

    def __get_mapping(self):
        return ImageCanvasItem.ImageCanvasItemMapping((1000, 1000), Geometry.FloatRect.from_tlbr(0, 0, 1000, 1000),
                                                      [Calibration.Calibration(-0.5, 1 / 1000),
                                                       Calibration.Calibration(-0.5, 1 / 1000)])

    def test_copy_graphic(self):
        rect_graphic = Graphics.RectangleGraphic()
        copy.deepcopy(rect_graphic).close()
        rect_graphic.close()
        ellipse_graphic = Graphics.EllipseGraphic()
        copy.deepcopy(ellipse_graphic).close()
        ellipse_graphic.close()
        line_graphic = Graphics.LineGraphic()
        copy.deepcopy(line_graphic).close()
        line_graphic.close()

    def test_rect_test(self):
        mapping = self.__get_mapping()
        rect_graphic = Graphics.RectangleGraphic()
        rect_graphic.bounds = (0.25, 0.25), (0.5, 0.5)
        ui_settings = DisplayPanel.FixedUISettings()
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((500, 500)), move_only=False), ("all", False))
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250, 250)), move_only=False)[0], "top-left")
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((750, 750)), move_only=False)[0], "bottom-right")
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250, 750)), move_only=False)[0], "top-right")
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((750, 250)), move_only=False)[0], "bottom-left")
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250, 500)), move_only=False), ("all", True))
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((750, 500)), move_only=False), ("all", True))
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((500, 250)), move_only=False), ("all", True))
        self.assertEqual(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((500, 750)), move_only=False), ("all", True))
        self.assertIsNone(rect_graphic.test(mapping, ui_settings, Geometry.FloatPoint(), move_only=False)[0])
        rect_graphic.close()

    def test_line_test(self):
        mapping = self.__get_mapping()
        line_graphic = Graphics.LineGraphic()
        line_graphic.start = (0.25,0.25)
        line_graphic.end = (0.75,0.75)
        ui_settings = DisplayPanel.FixedUISettings()
        self.assertEqual(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((500, 500)), move_only=True)[0], "all")
        self.assertEqual(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250, 250)), move_only=True)[0], "start")
        self.assertEqual(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((750, 750)), move_only=True)[0], "end")
        self.assertEqual(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250, 250)), move_only=False)[0], "start")
        self.assertEqual(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((750, 750)), move_only=False)[0], "end")
        self.assertIsNone(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((240, 240)), move_only=False)[0])
        self.assertIsNone(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((760, 760)), move_only=False)[0])
        self.assertIsNone(line_graphic.test(mapping, ui_settings, Geometry.FloatPoint(), move_only=False)[0])
        line_graphic.close()

    def test_line_dragging(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            data_item = DataItem.DataItem(numpy.zeros((1000, 1000)))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            mapping = self.__get_mapping()
            line_graphic = Graphics.LineGraphic()
            line_graphic.start = (0.25, 0.25)
            line_graphic.end = (0.75, 0.75)
            ui_settings = DisplayPanel.FixedUISettings()
            display_item.add_graphic(line_graphic)

            display_panel.display_canvas_item.simulate_click((250, 250))
            document_controller.periodic()

            # Test 1.1 - Drag start point, no modifiers
            display_panel.display_canvas_item.simulate_drag((250, 250), (300, 300))
            document_controller.periodic()
            self.assertEqual(line_graphic.start.x, 0.3)
            self.assertEqual(line_graphic.start.y, 0.3)
            self.assertEqual(line_graphic.end.x, 0.75)
            # Test 1.2 - Drag end point, no modifiers
            display_panel.display_canvas_item.simulate_drag((750, 750), (600, 600))
            document_controller.periodic()
            self.assertEqual(line_graphic.end.x, 0.6)
            self.assertEqual(line_graphic.end.y, 0.6)
            self.assertEqual(line_graphic.start.x, 0.3)
            # Test 2 - Drag start point, Alt pressed
            display_panel.display_canvas_item.simulate_drag((300, 300), (200, 200), CanvasItem.KeyboardModifiers(alt=True))
            document_controller.periodic()
            self.assertEqual(line_graphic.start.x, 0.2)
            self.assertEqual(line_graphic.start.y, 0.2)
            self.assertEqual(line_graphic.end.x, 0.7)
            self.assertEqual(line_graphic.end.y, 0.7)
            # Test 3 - Drag start point, Shift pressed
            display_panel.display_canvas_item.simulate_drag((200, 200), (200, 680), CanvasItem.KeyboardModifiers(shift=True)) # Almost vertical
            document_controller.periodic()
            self.assertEqual(line_graphic.start.x, 0.7)
            self.assertEqual(line_graphic.start.y, 0.2)
            self.assertEqual(line_graphic.end.x, 0.7)
            self.assertEqual(line_graphic.end.y, 0.7)
            # Test 4 - Drag end point, Alt pressed part way through. Ensure original mid-point is used.
            midpoint = Geometry.midpoint(line_graphic.start, line_graphic.end)
            display_panel.display_canvas_item.simulate_press((700, 700))
            display_panel.display_canvas_item.simulate_move((800, 700))
            document_controller.periodic()
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.2, 0.7), line_graphic.start)
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.8, 0.7), line_graphic.end)
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.5, 0.7), Geometry.midpoint(line_graphic.start, line_graphic.end))
            display_panel.display_canvas_item.simulate_move((800, 700), CanvasItem.KeyboardModifiers(alt=True))
            document_controller.periodic()
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.1, 0.7), line_graphic.start)
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.8, 0.7), line_graphic.end)
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.45, 0.7), Geometry.midpoint(line_graphic.start, line_graphic.end))
            self.assertAlmostEqualPoint(midpoint, Geometry.midpoint(line_graphic.start, line_graphic.end))
            display_panel.display_canvas_item.simulate_release((700, 800))
            document_controller.periodic()

    def test_point_test(self):
        mapping = self.__get_mapping()
        point_graphic = Graphics.PointGraphic()
        point_graphic.position = (0.25,0.25)
        ui_settings = DisplayPanel.FixedUISettings()
        self.assertEqual(point_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250, 250)), move_only=True)[0], "all")
        self.assertEqual(point_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250 - 18, 250)), move_only=True)[0], None)
        point_graphic.label = "Test"
        self.assertEqual(point_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((250 - 18 - 6, 250)), move_only=True)[0], "all")
        point_graphic.close()

    def test_spot_test(self):
        mapping = self.__get_mapping()
        spot_graphic = Graphics.SpotGraphic()
        spot_graphic.bounds = (0.2 - 0.5, 0.2 - 0.5), (0.1, 0.1)
        ui_settings = DisplayPanel.FixedUISettings()
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((200, 200)), move_only=False), ("top-left", True))
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((300, 200)), move_only=False), ("bottom-left", True))
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((300, 300)), move_only=False), ("bottom-right", True))
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((200, 300)), move_only=False), ("top-right", True))
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((800, 800)), move_only=False), ("inverted-top-left", True))
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((700, 800)), move_only=False), ("inverted-bottom-left", True))
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((700, 700)), move_only=False), ("inverted-bottom-right", True))
        self.assertEqual(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint.make((800, 700)), move_only=False), ("inverted-top-right", True))
        self.assertIsNone(spot_graphic.test(mapping, ui_settings, Geometry.FloatPoint(), move_only=False)[0])
        spot_graphic.close()

    def test_create_all_graphic_by_dragging(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            t = [
                ("line", Graphics.LineGraphic),
                ("rectangle", Graphics.RectangleGraphic),
                ("ellipse", Graphics.EllipseGraphic),
                ("point", Graphics.PointGraphic),
                ("spot", Graphics.SpotGraphic),
                ("wedge", Graphics.WedgeGraphic),
                ("ring", Graphics.RingGraphic),
                ("lattice", Graphics.LatticeGraphic),
            ]
            display_panel = document_controller.selected_display_panel
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            for tool_mode, graphic_type in t:
                document_controller.tool_mode = tool_mode
                self.assertEqual(0, len(display_item.graphics))
                display_panel.display_canvas_item.simulate_drag((500, 500), (600, 600))
                document_controller.periodic()
                self.assertEqual(1, len(display_item.graphics))
                graphic = display_item.graphics[0]
                self.assertIsInstance(graphic, graphic_type)
                display_item.remove_graphic(graphic).close()

    def test_drag_spot_mask(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller_with_application()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            # create data item with origin at center
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            data_item.set_dimensional_calibration(0, Calibration.Calibration(-5, 0))
            data_item.set_dimensional_calibration(1, Calibration.Calibration(-5, 0))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            # set up display to be 1000x1000
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            # set up mask graphic
            spot_graphic = Graphics.SpotGraphic()
            display_item.add_graphic(spot_graphic)
            initial_bounds = Geometry.FloatRect.from_center_and_size((0.10, 0.25), (0.1, 0.1))
            spot_graphic.bounds = initial_bounds
            origin = Geometry.FloatPoint(500, 500)
            # activate display panel
            display_panel.display_canvas_item.simulate_click(origin)
            document_controller.periodic()
            # move primary spot
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.FloatPoint(100, 250), origin + Geometry.FloatPoint(50, 200))
            document_controller.periodic()
            self.assertAlmostEqualRect(Geometry.FloatRect.from_center_and_size((0.05, 0.20), (0.1, 0.1)), spot_graphic.bounds)
            # move secondary spot
            display_panel.display_canvas_item.simulate_drag(origin - Geometry.FloatPoint(50, 200), origin - Geometry.FloatPoint(100, 250))
            document_controller.periodic()
            self.assertAlmostEqualRect(Geometry.FloatRect.from_center_and_size((0.10, 0.25), (0.1, 0.1)), spot_graphic.bounds)
            # move top-right
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.FloatPoint(50, 300), origin + Geometry.FloatPoint(60, 310))
            document_controller.periodic()
            self.assertAlmostEqualRect(Geometry.FloatRect.from_center_and_size((0.10, 0.25), (0.08, 0.12)), spot_graphic.bounds)

    def test_drag_wedge_mask(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller_with_application()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            # create data item with origin at center
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            data_item.set_dimensional_calibration(0, Calibration.Calibration(-5, 0))
            data_item.set_dimensional_calibration(1, Calibration.Calibration(-5, 0))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            # set up display to be 1000x1000
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            # set up mask graphic
            wedge_graphic = Graphics.WedgeGraphic()
            display_item.add_graphic(wedge_graphic)
            wedge_graphic.start_angle = math.radians(30)
            wedge_graphic.end_angle = math.radians(60)
            origin = Geometry.IntPoint(500, 500)
            # activate display panel
            display_panel.display_canvas_item.simulate_click(origin)
            # drag start angle
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.IntPoint(250 * -math.sin(math.radians(30)), 250 * math.cos(math.radians(30))),
                                                            origin + Geometry.IntPoint(250 * -math.sin(math.radians(20)), 250 * math.cos(math.radians(20))))
            document_controller.periodic()
            self.assertAlmostEqual(20, math.degrees(wedge_graphic.start_angle), delta=1.0)
            self.assertAlmostEqual(60, math.degrees(wedge_graphic.end_angle), delta=1.0)
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.IntPoint(250 * -math.sin(math.radians(60)), 250 * math.cos(math.radians(60))),
                                                            origin + Geometry.IntPoint(250 * -math.sin(math.radians(50)), 250 * math.cos(math.radians(50))))
            document_controller.periodic()
            self.assertAlmostEqual(20, math.degrees(wedge_graphic.start_angle), delta=1.0)
            self.assertAlmostEqual(50, math.degrees(wedge_graphic.end_angle), delta=1.0)
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.IntPoint(250 * -math.sin(math.radians(35)), 250 * math.cos(math.radians(35))),
                                                            origin + Geometry.IntPoint(250 * -math.sin(math.radians(45)), 250 * math.cos(math.radians(45))))
            document_controller.periodic()
            self.assertAlmostEqual(30, math.degrees(wedge_graphic.start_angle), delta=1.0)
            self.assertAlmostEqual(60, math.degrees(wedge_graphic.end_angle), delta=1.0)

    def test_drag_ring_mask(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller_with_application()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            # create data item with origin at center
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            data_item.set_dimensional_calibration(0, Calibration.Calibration(-5, 0))
            data_item.set_dimensional_calibration(1, Calibration.Calibration(-5, 0))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            # set up display to be 1000x1000
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            # set up mask graphic
            ring_graphic = Graphics.RingGraphic()
            display_item.add_graphic(ring_graphic)
            ring_graphic.radius_1 = 0.2
            ring_graphic.radius_2 = 0.3
            origin = Geometry.FloatPoint(500, 500)
            # activate display panel
            display_panel.display_canvas_item.simulate_click(origin)
            document_controller.periodic()
            display_panel.display_canvas_item.simulate_click(origin + Geometry.FloatPoint(250, 0))
            document_controller.periodic()
            # move rings
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.FloatPoint(200, 0), origin + Geometry.FloatPoint(100, 0))
            document_controller.periodic()
            self.assertAlmostEqual(0.1, ring_graphic.radius_1)
            self.assertAlmostEqual(0.3, ring_graphic.radius_2)
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.FloatPoint(300, 0), origin + Geometry.FloatPoint(350, 0))
            document_controller.periodic()
            self.assertAlmostEqual(0.1, ring_graphic.radius_1)
            self.assertAlmostEqual(0.35, ring_graphic.radius_2)

    def test_drag_ring_lattice(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller_with_application()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            # create data item with origin at center
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            data_item.set_dimensional_calibration(0, Calibration.Calibration(-5, 0))
            data_item.set_dimensional_calibration(1, Calibration.Calibration(-5, 0))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            # set up display to be 1000x1000
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            # set up mask graphic
            lattice_graphic = Graphics.LatticeGraphic()
            display_item.add_graphic(lattice_graphic)
            lattice_graphic.u_pos = Geometry.FloatPoint(0.1, 0.3)
            lattice_graphic.v_pos = Geometry.FloatPoint(-0.2, -0.2)
            lattice_graphic.radius = 0.05
            origin = Geometry.FloatPoint(500, 500)
            # activate display panel
            display_panel.display_canvas_item.simulate_click(origin)
            document_controller.periodic()
            # move vectors
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.FloatPoint(100, 300), origin + Geometry.FloatPoint(150, 250))
            document_controller.periodic()
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.15, 0.25), lattice_graphic.u_pos)
            self.assertAlmostEqualPoint(Geometry.FloatPoint(-0.20, -0.20), lattice_graphic.v_pos)
            self.assertAlmostEqual(0.05, lattice_graphic.radius)
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.FloatPoint(-200, -200), origin + Geometry.FloatPoint(-250, -150))
            document_controller.periodic()
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.15, 0.25), lattice_graphic.u_pos)
            self.assertAlmostEqualPoint(Geometry.FloatPoint(-0.25, -0.15), lattice_graphic.v_pos)
            self.assertAlmostEqual(0.05, lattice_graphic.radius)
            display_panel.display_canvas_item.simulate_drag(origin + Geometry.FloatPoint(-300, -100), origin + Geometry.FloatPoint(-350, -50))
            document_controller.periodic()
            self.assertAlmostEqualPoint(Geometry.FloatPoint(0.15, 0.25), lattice_graphic.u_pos)
            self.assertAlmostEqualPoint(Geometry.FloatPoint(-0.25, -0.15), lattice_graphic.v_pos)
            self.assertAlmostEqual(0.10, lattice_graphic.radius)

    def test_spot_mask_inverted(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller_with_application()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            spot_graphic = Graphics.SpotGraphic()
            display_item.add_graphic(spot_graphic)
            initial_bounds = Geometry.FloatRect.from_center_and_size((0.25, 0.25), (0.25, 0.25))
            spot_graphic.bounds = initial_bounds
            display_panel.display_canvas_item.simulate_drag((250, 250), (250, 500))
            document_controller.periodic()
            self.assertNotEqual(initial_bounds, Geometry.FloatRect.make(spot_graphic.bounds))
            display_panel.display_canvas_item.simulate_drag((-250, -500), (-250, -250))
            document_controller.periodic()
            self.assertEqual(initial_bounds, Geometry.FloatRect.make(spot_graphic.bounds))

    def test_spot_mask_is_sensible_when_smaller_than_one_pixel(self):
        spot_graphic = Graphics.SpotGraphic()
        spot_graphic.bounds = (0.0, 0.0), (0.05, 0.05)
        mask_data = spot_graphic.get_mask((10, 10), Geometry.FloatPoint(y=5.5, x=5.5))
        self.assertEqual(mask_data.shape, (10, 10))
        self.assertTrue(numpy.array_equal(mask_data, numpy.zeros((10, 10))))
        spot_graphic.close()

    def test_spot_mask_is_sensible_when_outside_bounds(self):
        spot_graphic = Graphics.SpotGraphic()
        spot_graphic.bounds = (1.5, 1.5), (0.1, 0.1)
        mask_data = spot_graphic.get_mask((10, 10))
        self.assertEqual(mask_data.shape, (10, 10))
        self.assertTrue(numpy.array_equal(mask_data, numpy.zeros((10, 10))))
        mask_data = spot_graphic.get_mask((10, 10))
        spot_graphic.bounds = (-0.5, -0.5), (0.1, 0.1)
        self.assertEqual(mask_data.shape, (10, 10))
        self.assertTrue(numpy.array_equal(mask_data, numpy.zeros((10, 10))))
        spot_graphic.close()

    def test_spot_mask_is_sensible_when_partially_outside_bounds(self):
        spot_graphic = Graphics.SpotGraphic()
        spot_graphic.bounds = (0.25, 0.25), (0.5, 0.5)
        mask_data = spot_graphic.get_mask((10, 10))
        self.assertEqual(mask_data.shape, (10, 10))
        self.assertFalse(numpy.array_equal(mask_data, numpy.zeros((10, 10))))
        spot_graphic.bounds = (-0.75, -0.75), (0.5, 0.5)
        mask_data = spot_graphic.get_mask((10, 10))
        self.assertEqual(mask_data.shape, (10, 10))
        self.assertFalse(numpy.array_equal(mask_data, numpy.zeros((10, 10))))
        spot_graphic.close()

    def assertAlmostEqualPoint(self, p1, p2, e=0.00001):
        if not(Geometry.distance(p1, p2) < e):
            logging.debug("%s != %s", p1, p2)
        self.assertTrue(Geometry.distance(p1, p2) < e)

    def assertAlmostEqualSize(self, s1, s2, e=0.00001):
        if not(abs(s2.height - s1.height) < e) or not(abs(s2.width - s1.width) < e):
            logging.debug("%s != %s", s1, s2)
        self.assertTrue(abs(s2.height - s1.height) < e and abs(s2.width - s1.width) < e)

    def assertAlmostEqualRect(self, r1, r2, e=0.00001):
        if not(Geometry.distance(r1[0], r2[0]) < e and Geometry.distance(r1[1], r2[1]) < e):
            logging.debug("%s != %s", r1, r2)
        self.assertTrue(Geometry.distance(r1[0], r2[0]) < e and Geometry.distance(r1[1], r2[1]) < e)

    def test_dragging_regions(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller_with_application()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))

            def get_extended_attr(object, extended_name):
                initial_value = object
                for sub_property in extended_name.split("."):
                    initial_value = getattr(initial_value, sub_property)
                return initial_value

            def map_string(s, m1, m2):
                for k, v in m1.items():
                    s = s.replace(k, v)
                for k, v in m2.items():
                    s = s.replace(k, v)
                return s

            class ScalarCoordinate(object):

                def __init__(self, v_value=None, h_value=None):
                    self.v_value = v_value
                    self.h_value = h_value

                @property
                def value(self):
                    return self.v_value if self.v_value is not None else self.h_value

            def reflect_rect(r, v, h):
                if v and not h:
                    return Geometry.FloatRect(Geometry.FloatPoint(1.0 - r.bottom, r.left), r.size)
                elif v and h:
                    return Geometry.FloatRect(Geometry.FloatPoint(1.0 - r.bottom, 1.0 - r.right), r.size)
                elif not v and h:
                    return Geometry.FloatRect(Geometry.FloatPoint(r.top, 1.0 - r.right), r.size)
                else:
                    return r

            def reflect_point(p, v, h):
                y = 1.0 - p.y if v else p.y
                x = 1.0 - p.x if h else p.x
                return Geometry.FloatPoint(y, x)

            def reflect_size(s, v, h):
                height = 1.0 - s.height if v else s.height
                width = 1.0 - s.width if h else s.width
                return Geometry.FloatSize(height, width)

            def reflect_scalar(s, v, h):
                v_value = 1.0 - s.v_value if s.v_value is not None and v else s.v_value
                h_value = 1.0 - s.h_value if s.h_value is not None and h else s.h_value
                return ScalarCoordinate(v_value, h_value)

            def reflect_value(value, v, h, mapping_v1, mapping_v2, mapping_h1, mapping_h2):
                if isinstance(value, Geometry.FloatRect):
                    return reflect_rect(value, v, h)
                elif isinstance(value, Geometry.FloatPoint):
                    return reflect_point(value, v, h)
                elif isinstance(value, Geometry.FloatSize):
                    return reflect_size(value, v, h)
                elif isinstance(value, ScalarCoordinate):
                    return reflect_scalar(value, v, h)
                elif isinstance(value, str):
                    if v:
                        value = map_string(value, mapping_v1, mapping_v2)
                    if h:
                        value = map_string(value, mapping_h1, mapping_h2)
                    return value
                elif isinstance(value, float):
                    return value
                raise Exception("Unknown value type %s", type(value))
                return None

            def reflect(d, v, h):
                d = copy.deepcopy(d)
                mapping_v1 = {"top": "was_top", "bottom": "was_bottom"}
                mapping_v2 = {"was_top": "bottom", "was_bottom": "top"}
                mapping_h1 = {"left": "was_left", "right": "was_right"}
                mapping_h2 = {"was_left": "right", "was_right": "left"}
                # name
                if v:
                    d["name"] = map_string(d["name"], mapping_v1, mapping_v2)
                if h:
                    d["name"] = map_string(d["name"], mapping_h1, mapping_h2)
                # input
                old_input = d["input"]["properties"]
                new_input = dict()
                for property, expected_value in old_input.items():
                    if v:
                        property = map_string(property, mapping_v1, mapping_v2)
                    if h:
                        property = map_string(property, mapping_h1, mapping_h2)
                    new_input[property] = reflect_value(expected_value, v, h, mapping_v1, mapping_v2, mapping_h1, mapping_h2)
                d["input"]["properties"] = new_input
                # drag
                drag = d["drag"]
                c0, c1 = drag[0:2]
                if v:
                    c0 = 1000 - c0[0], c0[1]
                    c1 = 1000 - c1[0], c1[1]
                if h:
                    c0 = c0[0], 1000 - c0[1]
                    c1 = c1[0], 1000 - c1[1]
                new_drag = list((c0, c1))
                new_drag.extend(drag[2:])
                d["drag"] = tuple(new_drag)
                # output
                old_output = d["output"]["properties"]
                new_output = dict()
                for property, expected_value in old_output.items():
                    if v:
                        property = map_string(property, mapping_v1, mapping_v2)
                    if h:
                        property = map_string(property, mapping_h1, mapping_h2)
                    new_output[property] = reflect_value(expected_value, v, h, mapping_v1, mapping_v2, mapping_h1, mapping_h2)
                d["output"]["properties"] = new_output
                return d

            def do_drag_test(d, e=0.00001):
                # logging.debug("test %s", d["name"])
                region = Graphics.factory(lambda t: d["input"]["type"])
                for property, initial_value in d["input"]["properties"].items():
                    setattr(region, property, initial_value)
                initial_values = dict()
                for property, expected_value in d["output"]["properties"].items():
                    if isinstance(expected_value, str):
                        initial_values[expected_value] = get_extended_attr(region, expected_value)
                for constraint in d["input"].get("constraints", list()):
                    if constraint == "bounds":
                        region.is_bounds_constrained = True
                    elif constraint == "shape":
                        region.is_shape_locked = True
                    elif constraint == "position":
                        region.is_position_locked = True
                display_item.add_graphic(region)
                display_item.graphic_selection.set(0)
                display_panel.display_canvas_item.simulate_drag(*d["drag"])
                document_controller.periodic()
                for property, expected_value in d["output"]["properties"].items():
                    actual_value = get_extended_attr(region, property)
                    # logging.debug("%s: %s == %s ?", property, actual_value, expected_value)
                    if isinstance(expected_value, str):
                        if isinstance(actual_value, Geometry.FloatRect):
                            self.assertAlmostEqualRect(actual_value, initial_values[expected_value], e)
                        elif isinstance(actual_value, Geometry.FloatPoint):
                            self.assertAlmostEqualPoint(actual_value, initial_values[expected_value], e)
                        elif isinstance(actual_value, Geometry.FloatSize):
                            self.assertAlmostEqualSize(actual_value, initial_values[expected_value], e)
                        elif isinstance(actual_value, ScalarCoordinate):
                            self.assertAlmostEqual(actual_value.value, initial_values[expected_value])
                        else:
                            raise Exception("Unknown value type %s", type(actual_value))
                    else:
                        if isinstance(actual_value, Geometry.FloatRect):
                            self.assertAlmostEqualRect(actual_value, expected_value, e)
                        elif isinstance(actual_value, Geometry.FloatPoint):
                            self.assertAlmostEqualPoint(actual_value, expected_value, e)
                        elif isinstance(actual_value, Geometry.FloatSize):
                            self.assertAlmostEqualSize(actual_value, expected_value, e)
                        elif isinstance(actual_value, float):
                            self.assertAlmostEqual(actual_value, expected_value.value)
                        else:
                            raise Exception("Unknown value type %s", type(actual_value))
                display_item.remove_graphic(region).close()

            def rotate(p, o, angle):
                origin = Geometry.FloatPoint.make(o)
                point = Geometry.FloatPoint.make(p)
                delta = point - origin
                angle_sin = math.sin(angle)
                angle_cos = math.cos(angle)
                return origin + Geometry.FloatPoint(x=delta.x * angle_cos + delta.y * angle_sin, y=delta.y * angle_cos - delta.x * angle_sin)

            def round1000(p):
                return Geometry.FloatPoint(y=int(p.y * 1000) / 1000, x=int(p.x * 1000) / 1000)

            # rectangle top-left

            d = {
                "name": "drag top-left corner outside of bounds with no constraints",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect(origin=(0.21, 0.22), size=(0.31, 0.32)) }
                },
                "drag": [(210, 220), (-190, -180)],
                "output": {
                    "properties": {
                        "_bounds.top_left": Geometry.FloatPoint(y=-0.19, x=-0.18),
                        "_bounds.bottom_right": "_bounds.bottom_right"
                    },
                }
            }

            # for v in (False, True):
            #     for h in (False, True):
            #         do_drag_test(reflect(d, v, h))

            for rotation in (-2 * math.pi / 8, -2 * math.pi / 8):

                d = {
                    "name": "drag rotated top-left corner outside of bounds with no constraints",
                    "input": {
                        "type": "rect-graphic",
                        "properties": { "_bounds": Geometry.FloatRect(origin=(0.4, 0.3), size=(0.2, 0.4)), "rotation": rotation }
                    },
                    "drag": [rotate((400, 300), (500, 500), rotation), rotate((450, 250), (500, 500), rotation)],
                    "output": {
                        "properties": {
                            "_rotated_top_left": rotate((0.45, 0.25), (0.5, 0.5), rotation),
                            "_rotated_bottom_right": "_rotated_bottom_right"
                        },
                    }
                }

                # rotation odd reflections are not valid
                do_drag_test(reflect(d, False, False), e=0.001)
                do_drag_test(reflect(d, True, True), e=0.001)

                d = {
                    "name": "drag rotated top-right corner outside of bounds with no constraints",
                    "input": {
                        "type": "rect-graphic",
                        "properties": { "_bounds": Geometry.FloatRect(origin=(0.4, 0.3), size=(0.2, 0.4)), "rotation": rotation }
                    },
                    "drag": [rotate((400, 700), (500, 500), rotation), rotate((450, 750), (500, 500), rotation)],
                    "output": {
                        "properties": {
                            "_rotated_top_right": rotate((0.45, 0.75), (0.5, 0.5), rotation),
                            "_rotated_bottom_left": "_rotated_bottom_left"
                        },
                    }
                }

                # rotation odd reflections are not valid
                do_drag_test(reflect(d, False, False), e=0.001)
                do_drag_test(reflect(d, True, True), e=0.001)

                d = {
                    "name": "drag rotated top-left corner outside of bounds from center",
                    "input": {
                        "type": "rect-graphic",
                        "properties": { "_bounds": Geometry.FloatRect(origin=(0.4, 0.3), size=(0.2, 0.4)), "rotation": rotation }
                    },
                    "drag": [rotate((400, 300), (500, 500), rotation), rotate((450, 250), (500, 500), rotation), CanvasItem.KeyboardModifiers(alt=True)],
                    "output": {
                        "properties": {
                            "_rotated_top_left": rotate((0.45, 0.25), (0.5, 0.5), rotation),
                            "_bounds.center": "_bounds.center"
                        },
                    }
                }

                # rotation odd reflections are not valid
                do_drag_test(reflect(d, False, False), e=0.001)
                do_drag_test(reflect(d, True, True), e=0.001)

                d = {
                    "name": "drag rotated top-right corner outside of bounds from center",
                    "input": {
                        "type": "rect-graphic",
                        "properties": { "_bounds": Geometry.FloatRect(origin=(0.4, 0.3), size=(0.2, 0.4)), "rotation": rotation }
                    },
                    "drag": [rotate((400, 700), (500, 500), rotation), rotate((450, 750), (500, 500), rotation), CanvasItem.KeyboardModifiers(alt=True)],
                    "output": {
                        "properties": {
                            "_rotated_top_right": rotate((0.45, 0.75), (0.5, 0.5), rotation),
                            "_bounds.center": "_bounds.center"
                        },
                    }
                }

                # rotation odd reflections are not valid
                do_drag_test(reflect(d, False, False), e=0.001)
                do_drag_test(reflect(d, True, True), e=0.001)

            d = {
                "name": "drag top-left corner outside of bounds with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.21, 0.22), (0.31, 0.32)) },
                    "constraints": ["bounds"]
                },
                "drag": [(210, 220), (-190, -180)],
                "output": {
                    "properties": {
                        "_bounds.top_left": Geometry.FloatPoint(),
                        "_bounds.bottom_right": "_bounds.bottom_right"
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag top-left corner from center towards top left with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.25, 0.25), (0.5, 0.5)) },
                    "constraints": ["bounds"]
                },
                "drag": [(250, 250), (150, 140), CanvasItem.KeyboardModifiers(alt=True)],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.top_left": Geometry.FloatPoint(0.15, 0.14),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag top-left corner from center towards top left with position constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.25, 0.25), (0.5, 0.5)) },
                    "constraints": ["position"]
                },
                "drag": [(250, 250), (150, 140), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.top_left": Geometry.FloatPoint(0.15, 0.14),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag top-left corner from center outside of bounds to the top left with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.21, 0.22), (0.31, 0.32)) },
                    "constraints": ["bounds"]
                },
                "drag": [(210, 220), (-190, -180), CanvasItem.KeyboardModifiers(alt=True)],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.top_left": Geometry.FloatPoint(),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag top-left corner from center outside of bounds to the bottom with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.21, 0.22), (0.31, 0.32)) },
                    "constraints": ["bounds"]
                },
                "drag": [(210, 220), (1500, 220), CanvasItem.KeyboardModifiers(alt=True)],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.top": ScalarCoordinate(v_value=0.0),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag top-left corner from center outside of bounds to the right with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.21, 0.22), (0.31, 0.32)) },
                    "constraints": ["bounds"]
                },
                "drag": [(210, 220), (210, 1500), CanvasItem.KeyboardModifiers(alt=True)],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.left": ScalarCoordinate(h_value=0.0),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag squared top-left corner from outside of bounds to the bottom right with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.2, 0.3), (0.4, 0.5)) },
                    "constraints": ["bounds"]
                },
                "drag": [(200, 300), (1500, 1500), CanvasItem.KeyboardModifiers(shift=True)],
                "output": {
                    "properties": {
                        "_bounds.top_left": "_bounds.bottom_right",
                        "_bounds.bottom": ScalarCoordinate(v_value=0.8),
                        "_bounds.right": ScalarCoordinate(h_value=1.0),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag squared top-left corner from in one direction",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.4, 0.4), (0.2, 0.2)) },  # center 0.5, 0.5
                    "constraints": ["bounds"]
                },
                "drag": [(400, 400), (200, 400), CanvasItem.KeyboardModifiers(shift=True)],
                "output": {
                    "properties": {
                        "_bounds.bottom_right": "_bounds.bottom_right",
                        "_bounds.top_left": Geometry.FloatPoint(0.2, 0.2),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag squared top-left corner from outside of bounds to the bottom right with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.1, 0.3), (0.2, 0.2)) },  # center 0.2, 0.4
                    "constraints": ["bounds"]
                },
                "drag": [(100, 300), (-200, -200), CanvasItem.KeyboardModifiers(shift=True, alt=True)],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.left": ScalarCoordinate(h_value=0.2),
                        "_bounds.top": ScalarCoordinate(v_value=0.0),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag squared top-left corner with bounds, center, square constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.4, 0.4), (0.2, 0.2)) },  # center 0.5, 0.5
                    "constraints": ["bounds"]
                },
                "drag": [(400, 400), (300, 200), CanvasItem.KeyboardModifiers(shift=True, alt=True)],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.top_left": Geometry.FloatPoint(0.3, 0.3),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag squared top-left corner with bounds, center, square constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.7, 0.7), (0.2, 0.2)) },  # center 0.8, 0.8
                    "constraints": ["bounds"]
                },
                "drag": [(700, 700), (0, 0), CanvasItem.KeyboardModifiers(shift=True, alt=True)],
                "output": {
                    "properties": {
                        "_bounds.center": "_bounds.center",
                        "_bounds.right": ScalarCoordinate(h_value=1.0),
                        "_bounds.bottom": ScalarCoordinate(v_value=1.0),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag top-left to top-left with shape constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.3, 0.2), (0.2, 0.2)) },  # center 0.4, 0.3
                    "constraints": ["shape"]
                },
                "drag": [(300, 200), (-100, -100), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_bounds.center": Geometry.FloatPoint(),
                        "_bounds.size": "_bounds.size",
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag all to top-left with no constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.3, 0.2), (0.2, 0.2)) },  # center 0.4, 0.3
                },
                "drag": [(400, 300), (0, 0), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_bounds.center": Geometry.FloatPoint(),
                        "_bounds.size": "_bounds.size",
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag all top-left with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.3, 0.2), (0.2, 0.2)) },  # center 0.4, 0.3
                    "constraints": ["bounds"]
                },
                "drag": [(400, 300), (0, 0), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_bounds.center": Geometry.FloatPoint(0.1, 0.1),
                        "_bounds.size": "_bounds.size",
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag all bottom-right with bounds constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.3, 0.2), (0.2, 0.2)) },  # center 0.4, 0.3
                    "constraints": ["bounds"]
                },
                "drag": [(400, 300), (1000, 1000), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_bounds.center": Geometry.FloatPoint(0.9, 0.9),
                        "_bounds.size": "_bounds.size",
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "drag all with restrict constraint",
                "input": {
                    "type": "rect-graphic",
                    "properties": { "_bounds": Geometry.FloatRect((0.4, 0.4), (0.2, 0.2)) },  # center 0.5, 0.5
                },
                "drag": [(500, 500), (800, 600), CanvasItem.KeyboardModifiers(shift=True)],
                "output": {
                    "properties": {
                        "_bounds.center": Geometry.FloatPoint(0.8, 0.5),
                        "_bounds.size": "_bounds.size",
                    }
                }
            }

            # vertical reflections not valid
            for h in (False, True):
                do_drag_test(reflect(d, False, h))

            # point

            d = {
                "name": "point drag with no constraint",
                "input": {
                    "type": "point-graphic",
                    "properties": { "_position": Geometry.FloatPoint(0.2, 0.3) },
                    # "constraints": ["bounds"]
                },
                "drag": [(200, 300), (-100, -100), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_position": Geometry.FloatPoint(-0.1, -0.1),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "point drag with bounds constraint",
                "input": {
                    "type": "point-graphic",
                    "properties": { "_position": Geometry.FloatPoint(0.2, 0.3) },
                    "constraints": ["bounds"]
                },
                "drag": [(200, 300), (-100, -100), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_position": Geometry.FloatPoint(),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "point drag with restrict",
                "input": {
                    "type": "point-graphic",
                    "properties": { "_position": Geometry.FloatPoint(0.2, 0.3) },
                    "constraints": ["bounds"]
                },
                "drag": [(200, 300), (100, 100), CanvasItem.KeyboardModifiers(shift=True)],
                "output": {
                    "properties": {
                        "_position": Geometry.FloatPoint(0.2, 0.1),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            # line regions

            d = {
                "name": "line drag with no constraints",
                "input": {
                    "type": "line-graphic",
                    "properties": {
                        "_start": Geometry.FloatPoint(0.2, 0.3),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    },
                    # "constraints": ["bounds"]
                },
                "drag": [(400, 400), (600, 700), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_start": Geometry.FloatPoint(0.4, 0.6),
                        "_end": Geometry.FloatPoint(0.8, 0.8),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "line start drag with restrict",
                "input": {
                    "type": "line-graphic",
                    "properties": {
                        "_start": Geometry.FloatPoint(0.2, 0.3),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    },
                    "constraints": ["shape"]
                },
                "drag": [(200, 300), (400, 600), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_start": Geometry.FloatPoint(0.4, 0.6),
                        "_end": Geometry.FloatPoint(0.8, 0.8),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "line drag with bounds constraint",
                "input": {
                    "type": "line-graphic",
                    "properties": {
                        "_start": Geometry.FloatPoint(0.2, 0.3),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    },
                    "constraints": ["bounds"]
                },
                "drag": [(400, 400), (1000, 1000), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_start": Geometry.FloatPoint(0.6, 0.8),
                        "_end": Geometry.FloatPoint(1.0, 1.0),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "line start drag with no constraints",
                "input": {
                    "type": "line-graphic",
                    "properties": {
                        "_start": Geometry.FloatPoint(0.2, 0.3),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    },
                    # "constraints": ["bounds"]
                },
                "drag": [(200, 300), (600, 700), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_start": Geometry.FloatPoint(0.6, 0.7),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "line start drag with bounds constraint",
                "input": {
                    "type": "line-graphic",
                    "properties": {
                        "_start": Geometry.FloatPoint(0.2, 0.3),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    },
                    "constraints": ["bounds"]
                },
                "drag": [(200, 300), (-100, 300), CanvasItem.KeyboardModifiers()],
                "output": {
                    "properties": {
                        "_start": Geometry.FloatPoint(0.0, 0.3),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

            d = {
                "name": "line start drag with shape constraint",
                "input": {
                    "type": "line-graphic",
                    "properties": {
                        "_start": Geometry.FloatPoint(0.2, 0.3),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    },
                    "constraints": ["bounds"]
                },
                "drag": [(200, 300), (500, 500), CanvasItem.KeyboardModifiers(shift=True)],
                "output": {
                    "properties": {
                        "_start": Geometry.FloatPoint(0.5, 0.5),
                        "_end": Geometry.FloatPoint(0.6, 0.5),
                    }
                }
            }

            for v in (False, True):
                for h in (False, True):
                    do_drag_test(reflect(d, v, h))

    def test_selected_graphics_get_priority_when_dragging_middles(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            display_panel.set_display_panel_display_item(display_item)
            header_height = display_panel.header_canvas_item.header_height
            display_panel.root_container.layout_immediate((1000 + header_height, 1000))
            rect_graphic1 = Graphics.RectangleGraphic()
            rect_graphic2 = Graphics.RectangleGraphic()
            rect_graphic1.bounds = (0.4, 0.4), (0.2, 0.2)
            rect_graphic2.bounds = (0.25, 0.25), (0.5, 0.5)
            display_item.add_graphic(rect_graphic1)
            display_item.add_graphic(rect_graphic2)
            display_item.graphic_selection.set(0)
            # now the smaller rectangle (selected) is behind the larger one
            display_panel.display_canvas_item.simulate_drag((500, 500), (600, 600))
            document_controller.periodic()
            # make sure the smaller one gets dragged
            self.assertAlmostEqualPoint(Geometry.FloatRect.make(rect_graphic1.bounds).center, Geometry.FloatPoint(y=0.6, x=0.6))
            self.assertAlmostEqualPoint(Geometry.FloatRect.make(rect_graphic2.bounds).center, Geometry.FloatPoint(y=0.5, x=0.5))

    def test_removing_graphic_from_display_closes_it(self):
        # make the document controller
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            display_panel.set_display_panel_display_item(display_item)
            graphic = Graphics.PointGraphic()
            display_item.add_graphic(graphic)
            self.assertFalse(graphic._closed)
            display_item.remove_graphic(graphic).close()
            self.assertTrue(graphic._closed)

    def test_removing_data_item_closes_graphic_attached_to_display(self):
        # make the document controller
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            display_panel = document_controller.selected_display_panel
            data_item = DataItem.DataItem(numpy.zeros((10, 10)))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            display_panel.set_display_panel_display_item(display_item)
            graphic = Graphics.PointGraphic()
            display_item.add_graphic(graphic)
            self.assertFalse(graphic._closed)
            document_model.remove_data_item(data_item)
            self.assertTrue(graphic._closed)

    def test_removing_region_closes_associated_drawn_graphic(self):
        with TestContext.create_memory_context() as test_context:
            document_model = test_context.create_document_model()
            data_item = DataItem.DataItem(numpy.zeros((8, 8), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            point_region = Graphics.PointGraphic()
            display_item.add_graphic(point_region)
            drawn_graphic = display_item.graphics[0]
            self.assertFalse(drawn_graphic._closed)
            display_item.remove_graphic(point_region).close()
            self.assertTrue(drawn_graphic._closed)

    def test_removing_data_item_closes_associated_drawn_graphic(self):
        with TestContext.create_memory_context() as test_context:
            document_model = test_context.create_document_model()
            data_item = DataItem.DataItem(numpy.zeros((8, 8), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            point_region = Graphics.PointGraphic()
            display_item.add_graphic(point_region)
            drawn_graphic = display_item.graphics[0]
            self.assertFalse(drawn_graphic._closed)
            document_model.remove_data_item(data_item)
            self.assertTrue(drawn_graphic._closed)

    def test_removing_graphic_with_dependent_data_removes_dependent_data(self):
        with TestContext.create_memory_context() as test_context:
            document_model = test_context.create_document_model()
            data_item = DataItem.DataItem(numpy.zeros((8, 8), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            crop_region = Graphics.RectangleGraphic()
            display_item.add_graphic(crop_region)
            cropped_data_item = document_model.get_crop_new(display_item, display_item.data_item, crop_region)
            self.assertIn(cropped_data_item, document_model.data_items)
            display_item.remove_graphic(crop_region).close()
            self.assertNotIn(cropped_data_item, document_model.data_items)

    def test_removing_one_of_two_graphics_with_dependent_data_only_removes_the_one(self):
        with TestContext.create_memory_context() as test_context:
            document_model = test_context.create_document_model()
            data_item = DataItem.DataItem(numpy.zeros((8, 8), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            crop_region1 = Graphics.RectangleGraphic()
            display_item.add_graphic(crop_region1)
            crop_region2 = Graphics.RectangleGraphic()
            display_item.add_graphic(crop_region2)
            document_model.get_crop_new(display_item, display_item.data_item, crop_region1)
            document_model.get_crop_new(display_item, display_item.data_item, crop_region2)
            self.assertIn(crop_region1, display_item.graphics)
            self.assertIn(crop_region2, display_item.graphics)
            display_item.remove_graphic(crop_region1).close()
            self.assertIn(crop_region2, display_item.graphics)

    def test_changing_data_length_does_not_update_graphics(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item = DataItem.DataItem(numpy.zeros((100, ), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            interval_graphic = Graphics.IntervalGraphic()
            interval_graphic.interval = (0.25, 0.75)
            display_item.add_graphic(interval_graphic)
            self.assertEqual(display_item.displayed_dimensional_scales[-1], 100)
            data_item.set_data(numpy.zeros((50, ), numpy.uint32))
            self.assertEqual(interval_graphic.interval, (0.25, 0.75))

    def test_changing_data_scale_does_not_update_graphics(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item = DataItem.DataItem(numpy.zeros((100, ), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            interval_graphic = Graphics.IntervalGraphic()
            interval_graphic.interval = (0.25, 0.75)
            display_item.add_graphic(interval_graphic)
            self.assertEqual(display_item.displayed_dimensional_scales[-1], 100)
            display_item.dimensional_scales = (1,)
            self.assertEqual(interval_graphic.interval, (0.25, 0.75))

    def test_setting_interval_to_non_floats_throws_execption(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item = DataItem.DataItem(numpy.zeros((100, ), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            interval_graphic = Graphics.IntervalGraphic()
            interval_graphic.interval = (0.25, 0.75)
            display_item.add_graphic(interval_graphic)
            with self.assertRaises(Exception):
                interval_graphic.interval = (numpy.array([1, 2]), numpy.array([3, 4]))
            with self.assertRaises(Exception):
                interval_graphic.start = numpy.array([1, 2])
            with self.assertRaises(Exception):
                interval_graphic.end = numpy.array([3, 4])

    def test_copy_paste_graphics(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item = DataItem.DataItem(numpy.zeros((100, ), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            document_controller.show_display_item(document_model.get_display_item_for_data_item(data_item))
            t = [
                ("line", Graphics.LineGraphic),
                ("rectangle", Graphics.RectangleGraphic),
                ("ellipse", Graphics.EllipseGraphic),
                ("point", Graphics.PointGraphic),
                ("spot", Graphics.SpotGraphic),
                ("wedge", Graphics.WedgeGraphic),
                ("ring", Graphics.RingGraphic),
                ("lattice", Graphics.LatticeGraphic),
            ]
            for name, c in t:
                graphic = c()
                display_item.add_graphic(graphic)
                display_item.graphic_selection.set(0)
                document_controller.handle_copy()
                self.assertEqual(1, len(display_item.graphics))
                document_controller.handle_paste()
                self.assertEqual(2, len(display_item.graphics))
                display_item.remove_graphic(display_item.graphics[0]).close()
                display_item.remove_graphic(display_item.graphics[0]).close()

    def test_copy_paste_line_profile_generates_secondary_data_item(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item1 = DataItem.DataItem(numpy.zeros((100, 100), numpy.uint32))
            data_item2 = DataItem.DataItem(numpy.zeros((100, 100), numpy.uint32))
            document_model.append_data_item(data_item1)
            document_model.append_data_item(data_item2)
            display_item1 = document_model.get_display_item_for_data_item(data_item1)
            display_item2 = document_model.get_display_item_for_data_item(data_item2)
            document_controller.show_display_item(display_item1)
            target_data_item = document_model.get_line_profile_new(display_item1, display_item1.data_item)
            document_model.recompute_all()
            self.assertEqual(1, len(display_item1.graphics))
            self.assertEqual(0, len(display_item2.graphics))
            self.assertEqual(3, len(document_model.data_items))
            self.assertEqual(2, len(document_model.data_items[0].data_shape))
            self.assertEqual(2, len(document_model.data_items[1].data_shape))
            self.assertEqual(1, len(document_model.data_items[2].data_shape))
            display_item1.graphic_selection.set(0)
            document_controller.handle_copy()
            document_controller.selected_display_panel.set_display_item(display_item2)
            document_controller.handle_paste()
            document_model.recompute_all()
            self.assertEqual(4, len(document_model.data_items))
            self.assertEqual(1, len(display_item1.graphics))
            self.assertEqual(1, len(display_item2.graphics))
            self.assertEqual(1, len(document_model.data_items[-1].data_shape))

    def test_high_pass_mask(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item = DataItem.DataItem(numpy.zeros((10,10), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            document_controller.show_display_item(document_model.get_display_item_for_data_item(data_item))
            # set up mask graphic
            ring_graphic = Graphics.RingGraphic()
            display_item.add_graphic(ring_graphic)
            ring_graphic.radius_1 = 0.2
            ring_graphic.radius_2 = 0.4
            ring_graphic.mode = "high-pass"

            # high pass should use radius 1 meaning only the innermost region is set to 0
            mask = ring_graphic.get_mask((10,10), Geometry.FloatPoint(4.5,4.5))
            self.assertEqual(mask[5,5], 0.0) # inside inner
            self.assertEqual(mask[5, 2], 1.0) # inbetween radius
            self.assertEqual(mask[0, 0], 1.0) # outside outer

            # check for radius_1 larger than radius 2
            ring_graphic.radius_1 = 0.4
            ring_graphic.radius_2 = 0.2

            # high pass should use radius 1 meaning only the outermost region is set to 1
            mask = ring_graphic.get_mask((10,10), Geometry.FloatPoint(4.5, 4.5))
            self.assertEqual(mask[5,5], 0.0) # inside inner
            self.assertEqual(mask[5, 2], 0.0) # inbetween radius
            self.assertEqual(mask[0, 0], 1.0) # outside outer

            display_item.remove_graphic(display_item.graphics[0]).close()

    def test_low_pass_mask(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item = DataItem.DataItem(numpy.zeros((10, 10), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            document_controller.show_display_item(document_model.get_display_item_for_data_item(data_item))

            # set up mask graphic
            ring_graphic = Graphics.RingGraphic()
            display_item.add_graphic(ring_graphic)
            ring_graphic.radius_1 = 0.2
            ring_graphic.radius_2 = 0.4
            ring_graphic.mode = "low-pass"

            # low-pass should use radius 2 so only the outermost region is set to 0
            mask = ring_graphic.get_mask((10,10), Geometry.FloatPoint(4.5,4.5))
            self.assertEqual(mask[5,5], 1.0) # inside inner
            self.assertEqual(mask[5, 2], 1.0) # inbetween radius
            self.assertEqual(mask[0, 0], 0.0) # outside outer

            # check for radius_1 larger than radius 2
            ring_graphic.radius_1 = 0.4
            ring_graphic.radius_2 = 0.2

            # low-pass should use radius 2 so only the innermost region should be set to 1
            mask = ring_graphic.get_mask((10,10), Geometry.FloatPoint(4.5,4.5))
            self.assertEqual(mask[5,5], 1.0) # inside inner
            self.assertEqual(mask[5, 2], 0.0) # inbetween radius
            self.assertEqual(mask[0, 0], 0.0) # outside outer

            display_item.remove_graphic(display_item.graphics[0]).close()

    def test_band_pass_mask(self):
        with TestContext.create_memory_context() as test_context:
            document_controller = test_context.create_document_controller()
            document_model = document_controller.document_model
            data_item = DataItem.DataItem(numpy.zeros((10, 10), numpy.uint32))
            document_model.append_data_item(data_item)
            display_item = document_model.get_display_item_for_data_item(data_item)
            document_controller.show_display_item(document_model.get_display_item_for_data_item(data_item))

            # set up mask graphic
            ring_graphic = Graphics.RingGraphic()
            display_item.add_graphic(ring_graphic)
            ring_graphic.radius_1 = 0.2
            ring_graphic.radius_2 = 0.4
            ring_graphic.mode = "band-pass"

            # band-pass uses both radii so only the region between the 2 should be set to 1
            mask = ring_graphic.get_mask((10,10), Geometry.FloatPoint(4.5,4.5))
            self.assertEqual(mask[5,5], 0.0) # inside inner
            self.assertEqual(mask[5, 2], 1.0) # inbetween radius
            self.assertEqual(mask[0, 0], 0.0) # outside outer

            # check for radius_1 larger than radius 2
            ring_graphic.radius_1 = 0.4
            ring_graphic.radius_2 = 0.2

            # band-pass uses both radii so only the region between the 2 should be set to 1
            mask = ring_graphic.get_mask((10,10), Geometry.FloatPoint(4.5,4.5))
            self.assertEqual(mask[5,5], 0.0) # inside inner
            self.assertEqual(mask[5, 2], 1.0) # inbetween radius
            self.assertEqual(mask[0, 0], 0.0) # outside outer

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
