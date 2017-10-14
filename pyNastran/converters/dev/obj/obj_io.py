"""
Defines the GUI IO file for OBJ.
"""
from __future__ import print_function

from numpy import arange
import vtk

from pyNastran.gui.gui_objects.gui_result import GuiResult
from pyNastran.gui.gui_utils.vtk_utils import numpy_to_vtk_points
from pyNastran.converters.dev.obj.obj import read_obj


class ObjIO(object):
    """
    Defines the GUI class for OBJ.
    """
    def __init__(self):
        pass

    def get_obj_wildcard_geometry_results_functions(self):
        """
        gets the OBJ wildcard loader used in the file load menu
        """
        data = ('OBJ',
                'OBJ (*.obj)', self.load_obj_geometry,
                None, None)
        return data

    def _remove_old_obj_geometry(self, filename):
        #return self._remove_old_geometry(filename)

        self.eid_map = {}
        self.nid_map = {}
        if filename is None:
            #self.emptyResult = vtk.vtkFloatArray()
            #self.vectorResult = vtk.vtkFloatArray()
            self.scalarBar.VisibilityOff()
            skip_reading = True
        else:
            self.turn_text_off()
            self.grid.Reset()
            #self.gridResult.Reset()
            #self.gridResult.Modified()

            self.result_cases = {}
            self.ncases = 0
            try:
                del self.case_keys
                del self.icase
                del self.isubcase_name_map
            except:
                # print("cant delete geo")
                pass

            #print(dir(self))
            skip_reading = False
        #self.scalarBar.VisibilityOff()
        self.scalarBar.Modified()
        return skip_reading

    def load_obj_geometry(self, obj_filename, name='main', plot=True):
        """
        The entry point for OBJ geometry loading.

        Parameters
        ----------
        obj_filename : str
            the obj filename to load
        name : str
            the name of the "main" actor for the GUI
        plot : bool; default=True
            should the model be generated or should we wait until
            after the results are loaded
        """
        skip_reading = self._remove_old_obj_geometry(obj_filename)
        if skip_reading:
            return

        self.eid_maps[name] = {}
        self.nid_maps[name] = {}
        model = read_obj(obj_filename, log=self.log, debug=False)
        self.model_type = 'obj'
        nodes = model.nodes
        nelements = model.nelements

        self.nnodes = model.nnodes
        self.nelements = nelements

        grid = self.grid
        grid.Allocate(self.nelements, 1000)

        assert nodes is not None
        #nnodes = nodes.shape[0]

        mmax = nodes.max(axis=0)
        mmin = nodes.min(axis=0)
        dim_max = (mmax - mmin).max()
        xmax, ymax, zmax = mmax
        xmin, ymin, zmin = mmin
        self.log_info("xmin=%s xmax=%s dx=%s" % (xmin, xmax, xmax-xmin))
        self.log_info("ymin=%s ymax=%s dy=%s" % (ymin, ymax, ymax-ymin))
        self.log_info("zmin=%s zmax=%s dz=%s" % (zmin, zmax, zmax-zmin))
        self.create_global_axes(dim_max)
        points = numpy_to_vtk_points(nodes)

        #assert elements.min() == 0, elements.min()

        tri_etype = 5 # vtkTriangle().GetCellType()
        #self.create_vtk_cells_of_constant_element_type(grid, elements, etype)
        quad_etype = 9 # vtk.vtkQuad().GetCellType()

        tris = model.tri_faces
        quads = model.quad_faces
        if len(tris):
            for eid, element in enumerate(tris):
                elem = vtk.vtkTriangle()
                elem.GetPointIds().SetId(0, element[0])
                elem.GetPointIds().SetId(1, element[1])
                elem.GetPointIds().SetId(2, element[2])
                self.grid.InsertNextCell(tri_etype, elem.GetPointIds())
        if len(quads):
            for eid, element in enumerate(quads):
                elem = vtk.vtkQuad()
                elem.GetPointIds().SetId(0, element[0])
                elem.GetPointIds().SetId(1, element[1])
                elem.GetPointIds().SetId(2, element[2])
                elem.GetPointIds().SetId(3, element[3])
                self.grid.InsertNextCell(quad_etype, elem.GetPointIds())

        grid.SetPoints(points)
        grid.Modified()
        if hasattr(grid, 'Update'):
            grid.Update()


        self.scalarBar.VisibilityOn()
        self.scalarBar.Modified()

        self.isubcase_name_map = {1: ['OBJ', '']}
        cases = {}
        ID = 1
        form, cases, icase = self._fill_obj_geometry_objects(
            cases, ID, nodes, nelements, model)
        self._finish_results_io2(form, cases)

    def clear_obj(self):
        pass

    def _fill_obj_geometry_objects(self, cases, ID, nodes, nelements, model):
        nnodes = nodes.shape[0]

        eids = arange(1, nelements + 1)
        nids = arange(1, nnodes + 1)

        subcase_id = 0
        nid_res = GuiResult(subcase_id, 'NodeID', 'NodeID', 'node', nids)
        eid_res = GuiResult(subcase_id, 'ElementID', 'ElementID', 'centroid', eids)

        cases = {
            0 : (nid_res, (0, 'NodeID')),
            1 : (eid_res, (0, 'ElementID')),
            #2 : (area_res, (0, 'Area')),
            #4 : (cart3d_geo, (0, 'NormalX')),
            #5 : (cart3d_geo, (0, 'NormalY')),
            #6 : (cart3d_geo, (0, 'NormalZ')),
        }
        geometry_form = [
            ('NodeID', 0, []),
            ('ElementID', 1, []),
            #('Area', 2, []),
            #('Normal X', 4, []),
            #('Normal Y', 5, []),
            #('Normal Z', 6, []),
        ]

        form = [
            ('Geometry', None, geometry_form),
        ]
        icase = 2
        return form, cases, icase

