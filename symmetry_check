import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance as wrp
from functools import wraps
import re


def undo(func):
    """ Puts the wrapped `func` into a single Maya Undo action, then
        undoes it when the function enters the finally: block """
    @wraps(func)
    def _undofunc(*args, **kwargs):
        try:
            # start an undo chunk
            cmds.undoInfo(ock=True)
            return func(*args, **kwargs)
        except Exception:
            raise  # will raise original error
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.undoInfo(cck=True)

    return _undofunc


def get_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return wrp(long(ptr), QtWidgets.QMainWindow)


def my_combine(obj_list, out_mapping=None):
    sel_list = om.MSelectionList()
    for obj in obj_list:
        sel_list.add(obj)

    count_of_vertices_in_polys = om.MIntArray()
    polygon_connects = om.MIntArray()
    offset = 0

    if out_mapping is None:
        out_mapping = {}

    for i in range(sel_list.length()):
        dag_path = om.MDagPath()
        sel_list.getDagPath(i, dag_path)

        face_iterator = om.MItMeshPolygon(dag_path)

        offset = len(out_mapping)
        while not face_iterator.isDone():
            vertices_count = face_iterator.polygonVertexCount()
            count_of_vertices_in_polys.append(vertices_count)
            
            for j in range(vertices_count):
                index_in_obj = face_iterator.vertexIndex(j)
                index_in_combined = offset + index_in_obj
                polygon_connects.append(index_in_combined)
                out_mapping[index_in_combined] = {'obj_vtx': dag_path.partialPathName() + '.vtx[' + str(index_in_obj) + ']', 'coords': face_iterator.point(j, om.MSpace.kWorld), 'obj': dag_path.partialPathName()}
            face_iterator.next()
    num_vertices = len(out_mapping)
    num_polygons = len(count_of_vertices_in_polys)
    vertex_array = om.MPointArray()
    for mp in out_mapping.values():
        vertex_array.append(mp['coords'])

    mfn_mesh = om.MFnMesh()
    new_mobject = mfn_mesh.create(num_vertices,
                    num_polygons,
                    vertex_array,
                    count_of_vertices_in_polys,
                    polygon_connects)

    new_dag_path = om.MDagPath()
    om.MDagPath.getAPathTo(new_mobject, new_dag_path)
    return new_dag_path.partialPathName()


def check_object_sym(obj, inverse=False):
    if not obj:
        cmds.warning("Select object")
        return

    sel_list = om.MSelectionList()
    sel_list.add(obj)
    dag_path = om.MDagPath()
    sel_list.getDagPath(0, dag_path)

    vert_it = om.MItMeshVertex(dag_path)
    mtol = 0.001
    r_verts = []
    mid_verts = []
    while not vert_it.isDone():
        i = vert_it.index()
        thisPoint = vert_it.position(om.MSpace.kWorld)
        if inverse:
            condition = thisPoint.x < 0 - mtol
            condition2 = thisPoint.x < 0 + mtol
        else:
            condition = thisPoint.x > 0 + mtol
            condition2 = thisPoint.x > 0 - mtol
        if condition:
            r_verts.append(i)
        elif condition2:
            mid_verts.append(i)
        vert_it.next()

    cmds.select(["%s.vtx[%s]" % (obj, j) for j in r_verts], sym=True)
    selection_sym = set(cmds.ls(sl=True, fl=True))

    cmds.select("%s.vtx[*]" % (obj))
    selection_all = set(cmds.ls(sl=True, fl=True))

    selection_mid = set(["%s.vtx[%s]" % (obj, j) for j in mid_verts])

    final_set = selection_all - selection_sym - selection_mid
    cmds.select(cl=True)

    return list(final_set)


class Mywidget(QtWidgets.QWidget):
    def __init__(self):
        maya = get_maya_window()
        QtWidgets.QWidget.__init__(self, parent=maya)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle("World X Sym Tool")
        self.setFixedHeight(200)
        self.setFixedWidth(350)
        self.setStyleSheet("font:14px;")
        self.selection = []
        self.invert_side_flag = True
        self.idx = om.MEventMessage.addEventCallback("SelectionChanged", self.get_selected)
        vert_lo = QtWidgets.QVBoxLayout(self)
        vert_lo.setAlignment(QtCore.Qt.AlignTop)
        self.info = QtWidgets.QLabel()
        vert_lo.addWidget(self.info)
        self.info.setStyleSheet("color: black;background-color:#afaf4b;")
        self.info.setFixedHeight(30)
        self.info.setText("Select object(s)")
        hor_lo1 = QtWidgets.QHBoxLayout()
        self.btn0 = QtWidgets.QPushButton("New select")
        self.btn0.clicked.connect(self.btn0_click)
        self.btn0.setDisabled(True)
        hor_lo1.addWidget(self.btn0)
        self.line1 = QtWidgets.QLineEdit()
        hor_lo1.addWidget(self.line1)
        vert_lo.addLayout(hor_lo1)
        hor_lo2 = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Show asymmetry on: ")
        hor_lo2.addWidget(label)
        self.radio1 = QtWidgets.QRadioButton("LEFT SIDE")
        self.radio1.clicked.connect(self.radio1_click)
        self.radio1.setChecked(True)
        hor_lo2.addWidget(self.radio1)
        self.radio2 = QtWidgets.QRadioButton("RIGHT SIDE")
        self.radio2.clicked.connect(self.radio2_click)
        hor_lo2.addWidget(self.radio2)
        vert_lo.addLayout(hor_lo2)
        self.btn1 = QtWidgets.QPushButton("Check symmetry")
        self.btn1.clicked.connect(self.btn1_click)
        vert_lo.addWidget(self.btn1)
        self.btn1.setDisabled(True)

        self.btn2 = QtWidgets.QPushButton("Select objects")
        self.btn2.clicked.connect(self.btn2_click)
        self.btn2.setDisabled(True)
        vert_lo.addWidget(self.btn2)

        # self.btn3 = QtWidgets.QPushButton("Mirrorize")
        # self.btn3.clicked.connect(self.btn3_click)
        # self.btn3.setDisabled(True)
        # vert_lo.addWidget(self.btn3)

        self.get_selected()

    def do(self):
        lst = self.selection
        mapping = {}
        obj = my_combine(lst, mapping)

        soft_select_on = False
        if cmds.softSelect(q=True, sse=True):
            soft_select_on = True
            cmds.softSelect(sse=False)

        symmetry_modelling_on = False
        if cmds.symmetricModelling(q=True, symmetry=True):
            tol = cmds.symmetricModelling(q=True, t=True)
            ax = cmds.symmetricModelling(q=True, axis=True)
            ab = cmds.symmetricModelling(q=True, about=True)
            symmetry_modelling_on = True
        cmds.symmetricModelling(symmetry=True, t=0.0001, about='world', axis='x')

        res_list_dupl = check_object_sym(obj, inverse=self.invert_side_flag)
        self.res_list = []
        for x in res_list_dupl:
            num = int(x.split('[')[-1].strip(']'))
            self.res_list.append(mapping[num]['obj_vtx'])

        cmds.delete(obj)
        cmds.select(self.res_list)

        cmds.symmetricModelling(symmetry=False)
        if soft_select_on:
            cmds.softSelect(sse=True)
        if symmetry_modelling_on:
            cmds.symmetricModelling(symmetry=True, t=tol, about=ab, axis=ax)
        
        self.btn2.setDisabled(False)

    def only_objects(self):
        for x in self.selection:
            if '.' in x:
                return False
        return True

    def remove_callback(self):
        if self.idx:
            om.MMessage.removeCallback(self.idx)
            self.idx = None
            self.btn0.setDisabled(False)

    def get_selected(self, *args, **kwargs):
        self.selection = cmds.ls(sl=True)
        if not self.selection or not self.only_objects():
            self.info.setText('Select object(s)')
            self.info.setStyleSheet("color: black;background-color:#afaf4b;")
            self.line1.setText("")
            self.btn1.setDisabled(True)
        else:
            self.info.setText('Ready to process')
            self.info.setStyleSheet("color: black;background-color:#aaaaaa;")
            self.line1.setText(str(self.selection))
            self.btn1.setDisabled(False)

    def btn0_click(self):
        self.idx = om.MEventMessage.addEventCallback("SelectionChanged", self.get_selected)
        self.line1.setDisabled(False)
        self.get_selected()
        self.btn2.setDisabled(True)

    @undo
    def btn1_click(self):
        self.remove_callback()
        self.line1.setDisabled(True)
        self.do()
        if cmds.ls(sl=True):
            self.info.setText('Not symmetrical')
            self.info.setStyleSheet("color: black;background-color:#af4b4b;")
        else:
            self.info.setText('Symmetrical')
            self.info.setStyleSheet("color: black;background-color:#4baf4b;")

    def btn2_click(self):
        obj_res = set()
        for x in self.res_list:
            obj_res.add(x.split('.')[0])
        cmds.select(list(obj_res))
    
    def radio1_click(self):
        self.invert_side_flag = True

    def radio2_click(self):
        self.invert_side_flag = False
