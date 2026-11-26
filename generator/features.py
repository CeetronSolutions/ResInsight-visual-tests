"""One regression case per rips feature.

Each feature builds a small project with rips on the smallest model that shows it.
Add a feature by writing a function decorated with @feature(name, model) and running
the nightly workflow; the first run reports missing_base until references are promoted.
"""

import math

import rips

FEATURES = {}

SPE1 = "spe1/SPE1CASE2.EGRID"
TEST10K = "TEST10K_FLT_LGR_NNC/TEST10K_FLT_LGR_NNC.EGRID"
TEST10K_WELLPATH = "TEST10K_FLT_LGR_NNC/wellpath_a.dev"
SUMMARY = "flow_diagnostics_test/SIMPLE_SUMMARY2.SMSPEC"


def feature(name, model=SPE1):
    """Register a feature."""

    def register(func):
        FEATURES[name] = (func, model)
        return func

    return register


def _show_pressure(view):
    # SOIL is zero at the first time step and shows nothing
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.update()


def _hide_cells(view):
    """Like Hide Cells in the toolbar: hide grid cells and faults."""
    view.set_grid_cells_visible(False)
    view.set_faults_visible(False)


Z_SCALE = 5.0


def _intersect_well(view, well_path):
    collection = view.descendants(rips.IntersectionCollection)[0]
    intersection = collection.add_new_object(rips.CurveIntersection)
    intersection.type = "CS_WELL_PATH"
    intersection.well_path = well_path
    intersection.update()


def _box_center(case):
    bbox = case.reservoir_boundingbox()
    return (
        (bbox.min_x + bbox.max_x) / 2,
        (bbox.min_y + bbox.max_y) / 2,
        (bbox.min_z + bbox.max_z) / 2,
        bbox,
    )


@feature("grid_default")
def grid_default(project, case, view, testmodels):
    """Unmodified default 3D view of the SPE1 grid."""
    pass


@feature("background_color")
def background_color(project, case, view, testmodels):
    """View background color set to #3388AA."""
    view.background_color = "#3388AA"
    view.update()


@feature("grid_box_hidden")
def grid_box_hidden(project, case, view, testmodels):
    """Grid box (axes) hidden with show_grid_box = False."""
    view.show_grid_box = False
    view.update()


@feature("z_scale")
def z_scale(project, case, view, testmodels):
    """Z scale set to 1 instead of the default 5."""
    view.grid_z_scale = Z_SCALE
    view.update()


@feature("disable_lighting")
def disable_lighting(project, case, view, testmodels):
    """Lighting disabled with disable_lighting = True."""
    view.disable_lighting = True
    view.update()


@feature("cell_result_dynamic", TEST10K)
def cell_result_dynamic(project, case, view, testmodels):
    """Dynamic cell result PRESSURE on the first time step."""
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.update()


@feature("cell_result_static", TEST10K)
def cell_result_static(project, case, view, testmodels):
    """Static cell result PORO."""
    view.apply_cell_result("STATIC_NATIVE", "PORO")
    view.update()


@feature("time_step", TEST10K)
def time_step(project, case, view, testmodels):
    """PRESSURE shown at time step 3 (current_time_step)."""
    view.apply_cell_result("DYNAMIC_NATIVE", "PRESSURE")
    view.current_time_step = 3
    view.update()


@feature("intersection_polyline", TEST10K)
def intersection_polyline(project, case, view, testmodels):
    """Polyline intersection through the middle of the grid, oblique camera."""
    _show_pressure(view)
    x, y, z, bbox = _box_center(case)
    collection = view.descendants(rips.IntersectionCollection)[0]
    intersection = collection.add_new_object(rips.CurveIntersection)
    intersection.type = "CS_POLYLINE"
    intersection.points = [
        [bbox.min_x, bbox.min_y, z],
        [x, y, z],
        [bbox.max_x, bbox.max_y, z],
    ]
    intersection.update()
    view.set_camera(azimuth=17.0, tilt=64.0, zoom=1.5)


@feature("regular_surface", TEST10K)
def regular_surface(project, case, view, testmodels):
    """Regular surface covering the central half of the grid, oblique camera."""
    _show_pressure(view)
    x, y, z, bbox = _box_center(case)
    nx, ny = 50, 50
    collection = project.descendants(rips.SurfaceCollection)[0]
    surface = collection.new_regular_surface(
        name="Wave surface",
        origin_x=bbox.min_x + (bbox.max_x - bbox.min_x) / 4,
        origin_y=bbox.min_y + (bbox.max_y - bbox.min_y) / 4,
        depth=z,
        nx=nx,
        ny=ny,
        increment_x=(bbox.max_x - bbox.min_x) / 2 / nx,
        increment_y=(bbox.max_y - bbox.min_y) / 2 / ny,
    )
    surface.rotation = 0.0
    surface.update()
    view.set_surface_visible(surface, True)
    view.set_camera(azimuth=0.0, tilt=59.0, zoom=1.5)


@feature("polygon", TEST10K)
def polygon(project, case, view, testmodels):
    """Red polygon outlining the grid bounding box."""
    _show_pressure(view)
    x, y, z, bbox = _box_center(case)
    coordinates = [
        [bbox.min_x, bbox.min_y, z],
        [bbox.max_x, bbox.min_y, z],
        [bbox.max_x, bbox.max_y, z],
        [bbox.min_x, bbox.max_y, z],
    ]
    collection = project.descendants(rips.PolygonCollection)[0]
    created = collection.create_polygon(name="Bounding box", coordinates=coordinates)
    appearance = created.appearance()
    appearance.line_color = "#ff0000"
    appearance.line_thickness = 5
    appearance.update()
    view.set_polygon_visible(created, True)


@feature("well_path_import", TEST10K)
def well_path_import(project, case, view, testmodels):
    """Well path imported from a .dev file with a well path intersection, oblique camera."""
    _show_pressure(view)
    project.import_well_paths([str(testmodels / TEST10K_WELLPATH)])
    well_path = project.well_paths()[0]
    _intersect_well(view, well_path)
    view.set_camera(azimuth=0.0, tilt=59.0)


@feature("modeled_well_path", TEST10K)
def modeled_well_path(project, case, view, testmodels):
    """Modeled well path with three targets; cells hidden, with a well path intersection."""
    _show_pressure(view)
    _hide_cells(view)
    collection = project.well_path_collection()
    well_path = collection.add_new_object(rips.ModeledWellPath)
    well_path.name = "Modeled well"
    well_path.update()
    geometry = well_path.well_path_geometry()
    reference = geometry.reference_point
    x, y, z, bbox = _box_center(case)
    reference[0], reference[1], reference[2] = x - 300, y - 200, -z - 20
    geometry.update()
    targets = [[0, 0, 0], [300, 200, 50], [600, 400, 120]]
    for target in targets:
        geometry.append_well_target(target)
    geometry.update()
    _intersect_well(view, well_path)
    view.set_camera(azimuth=0.0, tilt=59.0)


@feature("well_path_from_points", TEST10K)
def well_path_from_points(project, case, view, testmodels):
    """Well path imported from a list of points; cells hidden, with a well path intersection."""
    _show_pressure(view)
    _hide_cells(view)
    collection = project.well_path_collection()
    x, y, z, bbox = _box_center(case)
    points = [
        [x - 300 + 40 * i, y - 200 + 30 * i, z + 10 - 4 * i + math.sin(i) * 3]
        for i in range(15)
    ]
    well_path = collection.import_well_path_from_points(
        name="Point well", coordinates=points
    )
    _intersect_well(view, well_path)
    view.set_camera(azimuth=0.0, tilt=59.0)


def _import_summary_only(project, view, testmodels):
    view.delete()  # only the plot should be snapshotted
    return project.import_summary_case(str(testmodels / SUMMARY))


def _fit_multi_plots(project, columns, rows):
    """Use a page layout that matches the number of subplots, so the page has no empty cells."""
    for multi_plot in project.descendants(rips.MultiSummaryPlot):
        multi_plot.number_of_columns = columns
        multi_plot.rows_per_page = rows
        multi_plot.update()


@feature("summary_plot")
def summary_plot(project, case, view, testmodels):
    """Summary plot of the field oil production total (FOPT)."""
    summary_case = _import_summary_only(project, view, testmodels)
    collection = project.summary_plot_collection()
    collection.new_summary_plot(summary_cases=[summary_case], address="FOPT")
    _fit_multi_plots(project, rips.NumberOfColumns._1, rips.RowsPerPage._1)


@feature("summary_multi_plot")
def summary_multi_plot(project, case, view, testmodels):
    """Multi plot with one summary plot per vector (FOPT, FWPT)."""
    summary_case = _import_summary_only(project, view, testmodels)
    collection = project.summary_plot_collection()
    collection.new_summary_multi_plot(
        summary_cases=[summary_case], addresses=["FOPT", "FWPT"]
    )
    _fit_multi_plots(project, rips.NumberOfColumns._2, rips.RowsPerPage._1)


@feature("summary_plot_multi_vector")
def summary_plot_multi_vector(project, case, view, testmodels):
    """Two curves in the same summary plot (WOPR for wells P1 and P2)."""
    summary_case = _import_summary_only(project, view, testmodels)
    collection = project.summary_plot_collection()
    collection.new_summary_plot(
        summary_cases=[summary_case], address="WOPR:P1;WOPR:P2"
    )
    _fit_multi_plots(project, rips.NumberOfColumns._1, rips.RowsPerPage._1)


@feature("summary_plot_wildcard")
def summary_plot_wildcard(project, case, view, testmodels):
    """Summary plot with one curve per well from a wildcard address (WOPT:*)."""
    summary_case = _import_summary_only(project, view, testmodels)
    collection = project.summary_plot_collection()
    collection.new_summary_plot(summary_cases=[summary_case], address="WOPT:*")
    _fit_multi_plots(project, rips.NumberOfColumns._1, rips.RowsPerPage._1)


@feature("summary_plot_custom_title")
def summary_plot_custom_title(project, case, view, testmodels):
    """Summary plot with a custom title (is_using_auto_name = False)."""
    summary_case = _import_summary_only(project, view, testmodels)
    collection = project.summary_plot_collection()
    summary_plot = collection.new_summary_plot(
        summary_cases=[summary_case], address="FOPT"
    )
    summary_plot.is_using_auto_name = False
    summary_plot.plot_description = "Custom plot title"
    summary_plot.update()
    _fit_multi_plots(project, rips.NumberOfColumns._1, rips.RowsPerPage._1)


@feature("summary_multi_plot_grid")
def summary_multi_plot_grid(project, case, view, testmodels):
    """2x2 multi plot with three subplots created together and a fourth added with append_subplot."""
    summary_case = _import_summary_only(project, view, testmodels)
    collection = project.summary_plot_collection()
    multi_plot = collection.new_summary_multi_plot(
        summary_cases=[summary_case], addresses=["FOPT", "FWPT", "FOPR"]
    )
    multi_plot.append_subplot(summary_cases=[summary_case], address="FWPR")
    _fit_multi_plots(project, rips.NumberOfColumns._2, rips.RowsPerPage._2)


@feature("summary_multi_plot_common_legend")
def summary_multi_plot_common_legend(project, case, view, testmodels):
    """Multi plot with two subplots sharing one legend (use_common_legend = True)."""
    summary_case = _import_summary_only(project, view, testmodels)
    collection = project.summary_plot_collection()
    multi_plot = collection.new_summary_multi_plot(
        summary_cases=[summary_case], addresses=["WOPR:P1;WOPR:P2", "WWPR:P1;WWPR:P2"]
    )
    multi_plot.use_common_legend = True
    multi_plot.update()
    _fit_multi_plots(project, rips.NumberOfColumns._2, rips.RowsPerPage._1)


@feature("well_log_plot", TEST10K)
def well_log_plot(project, case, view, testmodels):
    """Well log plot with PORO and PRESSURE extraction curves along an imported well path."""
    # The 3D view stays: the case results are only loaded when a view is opened,
    # and without them the extraction curves are empty
    project.import_well_paths([str(testmodels / TEST10K_WELLPATH)])
    well_path = project.well_paths()[0]
    collection = project.descendants(rips.WellLogPlotCollection)[0]
    plot = collection.new_well_log_plot(case, well_path)
    for property_type, name in (
        (rips.PropertyType.STATIC_NATIVE, "PORO"),
        (rips.PropertyType.DYNAMIC_NATIVE, "PRESSURE"),
    ):
        track = plot.new_well_log_track(name, case, well_path)
        track.add_extraction_curve(case, well_path, property_type, name, 0)
