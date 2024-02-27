# -*- coding: utf-8 -*-
'''
# Created on Dec-31-19 19:46 
# plot.py
# @author: 
'''
import sys
import numpy as np
import pyqtgraph as pg
import time
import random
import pyqtgraph.opengl as gl
import numpy, array
import threading, time


# import pybullet for physics simulation
import pybullet as p

# load some utility functions
# bullet2pyqtgraph is a function to convert objects from bullet to 
# pyqtgraph, when using this function for meshes of 3D CAD models 
# make sure you have the python module trimesh as well
# install it using the command: pip install trimesh
# quaternion2axis_angle and quaternion2rotation_matrix are two
# functions to convert a quaternion to an axis-angle and a rotation 
# matrix, which are all different ways to describe an orientation.
from lib.util import bullet2pyqtgraph, quaternion2axis_angle, quaternion2rotation_matrix

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import * 
from PyQt5.QtGui import QFont

line_width = 1
line_color = [
    pg.mkPen((72, 209, 204), width = line_width),  #  medium turquoise
    pg.mkPen((255,105,180), width = line_width),  #  hot pink
    pg.mkPen((255, 255, 0), width = line_width),  #  yellow
    pg.mkPen((255, 0, 255), width = line_width),   # magenta 
    pg.mkPen((30, 144, 255), width = line_width),  # dodger blue
    pg.mkPen((255, 69, 0), width = line_width),  # orange red
    pg.mkPen((50, 205, 50), width = line_width),   # lime green
    pg.mkPen((255, 140, 0), width = line_width),  # dark orange
    pg.mkPen((169, 169, 169), width = line_width),  # dark gray
    pg.mkPen((240,255,255), width = line_width),  #  azure
]

error_str_c = [
    'ERR_NONE',
    'ERR_IMU',
    'ERR_MAG',
    'ERR_BARO',
    'ERR_GPS',
    'ERR_ATT',
    'ERR_ALT',
    'ERR_POS',
    'ERR_VEL',
    'ERR_RC',
    'ERR_BATT',
]

event_str_c = [
    'EV_ARMED',
    'EV_DISARMED',
    'EV_LAND',
    'EV_MAY_LAND',
    'EV_CRASHED',
    'EV_FREEFALL',
    'EV_FLIGHT',
]

mode_str_c = [
    'ATTCTL',
    'ALTCTL',
    'POSCTL',
    'SPORTS',
    'AUTO_MISSION',
    'AUTO_POSCTL',
    'AUTO_RTL',
    'AUTO_LANDENGFAIL',
    'AUTO_LANDGPSFAIL',
    'AUTO_TAKEOFF',
    'AUTO_LAND',
    'AUTO_FOLLOW',
    'AUTO_PRECLAND',
]

# 绘图线程 0.1s调用一次 graph.updateLine
class graphThread(QThread):
    _signal = pyqtSignal()
    def __init__(self, graph):
        self.graph = graph
        self.pause = False
        super(graphThread, self).__init__()
        self._signal.connect(self.graph.updateLine)

    def run(self):
        while True:
            if self.pause is False:
                self._signal.emit()
            time.sleep(0.1)


class graph:
    def __init__(self, y_axis_dict=None, x_axis_dict=None):
        self.x_axis_dict = x_axis_dict
        self.y_axis_dict = y_axis_dict

        self.p = pg.PlotWidget(background = pg.mkColor(28,31,38))
        self.p.setRange(QtCore.QRectF(0, -100, 5000, 200))
        # self.p.setLabel('bottom', 'Time', '')
        self.p.setDownsampling(mode='mean')
        self.p.setClipToView(True)
        self.p.setRange(xRange=[-5000, 0])
        self.p.setLimits(xMax=0)
        self.p.plotItem.showGrid(True, True)
        self.legend = pg.LegendItem(offset=(70,30))
        self.legend.setParentItem(self.p.graphicsItem())
        # 绘图曲线
        self.curves = {}
        # 绘图数据缓存
        self.curves_data = {}
        # 指向数据长度
        self.ptr = 0

        # self.text = pg.TextItem("", anchor=(0.5, 1), color=(255,105,180))
        self.text = pg.TextItem("", anchor=(0.5, 1), color=(7, 154, 125))
        font = QFont()
        font.setFamily('Consolas')
        self.text.setFont(font)        
        self.p.plotItem.addItem(self.text)
        self.p.plotItem.setFont(font)

        self.y_min = 1e10
        self.y_max = -1e10

    def addMouseLine(self):
        # 鼠标移动
        self.vb = self.p.plotItem.vb
        self.p.scene().sigMouseMoved.connect(self.mouseMoved)
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen=(7, 154, 125))
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen=(7, 154, 125))
        self.p.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.p.plotItem.addItem(self.hLine, ignoreBounds=True)

    def updateLine(self):
        # 依次从 y_axis_dict 中获取数据
        for label_i, lines_i in self.curves.items():
            if label_i in self.y_axis_dict:
                self.curves_data[label_i] = self.y_axis_dict[label_i]
                # 获取数据长度
                self.ptr = len(self.curves_data[label_i])
                data = self.curves_data[label_i]
                # 绘制曲线
                if self.x_axis_dict == None:
                    self.curves[label_i].setData(data[:self.ptr])
                    self.curves[label_i].setPos(-self.ptr, 0)
                else:
                    self.curves[label_i].setData(self.x_axis_dict[label_i], data[:self.ptr])
                    if len(self.x_axis_dict[label_i]) == 0:
                        return
                    self.curves[label_i].setPos(-self.x_axis_dict[label_i][-1], 0)

    def removeLine(self, label):
        if label in self.curves:
            self.legend.removeItem(label)
            self.p.removeItem(self.curves[label])
            self.curves.pop(label)

    def addLine(self, label):
        # c = self.p.plot(pen=color)
        color = [random.randint(80, 255) for _ in range(3)]
        c = self.p.plot(pen = pg.mkPen(color, width = line_width))

        # 手动设置y轴最大值和最小值
        # if min(self.y_axis_dict[label]) < self.y_min:
        #     self.y_min = min(self.y_axis_dict[label])
        # if max(self.y_axis_dict[label]) > self.y_max:
        #     self.y_max = max(self.y_axis_dict[label])

        self.y_min = min(self.y_axis_dict[label])
        self.y_max = max(self.y_axis_dict[label])
        self.p.setYRange(self.y_min, self.y_max)

        self.p.addItem(c)
        self.curves[label] = c 
        self.legend.addItem(self.curves[label], label)
        self.curves_data[label] = [0]

    def mouseMoved(self, evt):
        pos = evt
        if self.p.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)

            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

            self.text.setText('x:%0.5f  y:%0.5f' % (mousePoint.x(), mousePoint.y()))
            self.text.setPos(mousePoint.x(), mousePoint.y())


# 静态绘图，添加曲线时和动态的不一样，没有update_line
class graphStatic(graph):
    def __init__(self, y_axis_dict=None, x_axis_dict=None):
        graph.__init__(self, y_axis_dict=None, x_axis_dict=None)
        self.p = pg.PlotWidget(background = pg.mkColor(28,31,38))
        # self.p = pg.PlotWidget(background = pg.mkColor(100,100,100))
        self.p.setDownsampling(mode='peak')
        self.p.setLabel('bottom', 'Time')
        self.p.setClipToView(True)
        self.legend = pg.LegendItem(offset=(70,30))
        self.legend.setParentItem(self.p.graphicsItem())   # Note we do NOT call plt.addItem in this case
        self.p.autoRange(False)

        self.text = pg.TextItem("", anchor=(0.5, 1), color=(7, 154, 125))
        font = QFont()
        font.setFamily('Consolas')
        self.text.setFont(font)
        self.p.plotItem.addItem(self.text)

        self.addMouseLine()

        self.curves = {}
        self.curves_data = {}
        self.x_min = self.x_max = self.y_min = self.y_max = 0
        self.mode_mark_list = []
        self.error_mark_list = []
        self.event_mark_list = []

    def addLine(self, label, x, y):
        color = [random.randint(80, 255) for _ in range(3)]
        c = self.p.plot(pen = pg.mkPen(color, width = line_width))
        self.p.addItem(c)
        self.curves[label] = c
        self.legend.addItem(self.curves[label], label)
        self.curves_data[label] = y
        self.data_len = len(y)
        # 手动设置y轴最大值和最小值
        # if min(y) < self.y_min:
        #     self.y_min = min(y)
        # if max(y) > self.y_max:
        #     self.y_max = max(y)
        # self.p.setYRange(self.y_min, self.y_max)
        self.p.setYRange(min(y), max(y))
        if x == 0:
            self.p.setXRange(0,self.data_len)
            # 绘图
            self.curves[label].setData(self.curves_data[label][:self.data_len])
        else:
            self.p.setXRange(0,max(x))
            self.curves[label].setData(x,self.curves_data[label][:self.data_len])
    
    def addMark(self, type, x_data, info):
        for i,i_item in enumerate(x_data):
            if i_item > 8640:
                continue
            if type == 1:
                t_up = pg.TextItem(error_str_c[info[i]], color=(255, 0, 0), anchor=(0, 0))
                t_up.setPos(i_item, 0)
                self.error_mark_list.append(t_up)
                self.p.addItem(t_up)
            elif type == 2:
                t_up = pg.TextItem(mode_str_c[info[i]], color=(0, 255, 0), anchor=(0, 0))
                t_up.setPos(i_item, 0)
                self.mode_mark_list.append(t_up)
                self.p.addItem(t_up)
            else:
                t_up = pg.TextItem(event_str_c[info[i]], color=(255, 255, 255), anchor=(0, 0))
                t_up.setPos(i_item, 0)
                self.event_mark_list.append(t_up)
                self.p.addItem(t_up)

    def removeMark(self, type):
        if type == 1:
            for item in self.error_mark_list:
                self.p.removeItem(item)
        elif type == 2:
            for item in self.mode_mark_list:
                self.p.removeItem(item)
        else:
            for item in self.event_mark_list:
                self.p.removeItem(item)
        
    def remove_all_line(self):
        labels = []
        for label in self.curves:
            labels.append(label)
        for i in range(len(labels)):
            self.removeLine(labels[i])

class graph_sim:
    def __init__(self):
        self.window = gl.GLViewWidget()
        self.window.setCameraPosition(distance=5)
        self.gaxis = gl.GLAxisItem()
        self.gaxis.setSize(x=2,y=2,z=2)
        self.window.addItem(self.gaxis)
        self.grid = gl.GLGridItem(size = QtGui.QVector3D(60,60,1))
        self.window.addItem(self.grid)
        self.window.update()

        # configure pybullet and load plane.urdf and quadcopter.urdf
        self.physicsClient = p.connect(p.DIRECT)  # pybullet only for computations no visualisation
        p.setGravity(0,0,-9.8)
        p.setRealTimeSimulation(0)
        self.quadcopterId = p.loadURDF("models/quadrotor.urdf",[0,0,1],p.getQuaternionFromEuler([0,0,0]))
        self.quadcopterMesh = bullet2pyqtgraph(self.quadcopterId)[0]
        self.window.addItem(self.quadcopterMesh)
        self.window.update()

        self.attitude = [0,0,0,1]
        self.position = [0,0,0]

    def update(self,pos_meas,quat_meas):
        self.attitude = quat_meas
        self.position = pos_meas
        transform = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        angle,x,y,z = quaternion2axis_angle(self.attitude)
        self.quadcopterMesh.setTransform(transform)
        self.quadcopterMesh.rotate(np.degrees(angle),x,y,z,local=True)
        self.quadcopterMesh.translate(self.position[0],self.position[1],self.position[2])
        self.window.update()

class graph_3d:
    def __init__(self):
        self.w = gl.GLViewWidget()
        
        self.w.setCameraPosition(distance=25)
        self.gaxis = gl.GLAxisItem()
        self.gaxis.setSize(x=5,y=5,z=5)
        self.w.addItem(self.gaxis)

        self.w.setBackgroundColor(pg.mkColor(32,33,38))

        self.gz = gl.GLGridItem()
        self.gz.translate(0, 0, -0)
        self.w.addItem(self.gz)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        self.items = {}
        self.itemsData = {}

        # dots color
        # self.bluecolor  = ( 30/255,144/255,    1.0,      1)
        self.pinkcolor  = (144/255,      0,144/255,255/255)
        self.yellowcolor= (255/255,255/255,0      ,255/255)
        self.whilecolor = (255/255,255/255,255/255,255/255)
        self.blackcolor = (0      ,0      ,0      ,255/255)
        self.redcolor   = (255/255,0      ,0      ,255/255)
        self.greencolor = (0      ,255/255,0      ,255/255)
        self.bluecolor  = (0      ,0      ,255/255,255/255)
        self.Cyancolor  = (0      ,255/255,255/255,255/255)
        self.Purplecolor= (255/255,0      ,255/255,255/255)

        self.size = 3

    def update(self):
        # self.w.orbit(0.5, 0)
        pass

    def addItem(self, itemLable, color):
        # p = gl.GLScatterPlotItem(pos = np.zeros(3), size=self.size, color=self.color, pxMode=True)
        p = gl.GLScatterPlotItem(pos = np.zeros(3), size=self.size, color=color, pxMode=True)
        self.items.setdefault(itemLable, p)
        self.itemsData.setdefault(itemLable, np.empty((1, 3)))
        self.w.addItem(self.items[itemLable])

    def setItemData(self, itemLable, dataArray):
        if itemLable in self.items:
            self.itemsData[itemLable] = np.vstack((self.itemsData[itemLable], dataArray))
            self.items[itemLable].setData(pos=self.itemsData[itemLable])

    def plotSphere(self, transform_mat = None, translate_mat = None, rows = 30, cols = 50, radius = 1):
        if transform_mat is None:
            kk = gl.MeshData.sphere(rows=rows, cols=cols, radius=radius)
            colors = np.ones((kk.faceCount(), 4), dtype=float)
            colors[:,0] = 0.1
            # colors[:,1] = np.linspace(0, 0.5, colors.shape[0])
            colors[:,1] = 0.1
            colors[:,2] = 0 
            colors[:,3] = 0.4
            # colors[:,2] = 0
            kk.setFaceColors(colors)
            # m2 = gl.GLMeshItem(meshdata=kk, smooth=True,shader='balloon', glOptions='additive')
            # m2 = gl.GLMeshItem(meshdata=kk, smooth=False,shader='shaded')
            m2 = gl.GLMeshItem(meshdata=kk, smooth=False,shader='edgeHilight', glOptions='additive')
            m2.translate(4,0,0)
            self.w.addItem(m2)
            return
        offset = True
        verts = np.empty((rows+1, cols, 3), dtype=float)
        ## compute vertexes
        phi = (np.arange(rows+1) * np.pi / rows).reshape(rows+1, 1)
        s = radius * np.sin(phi)
        verts[...,2] = radius * np.cos(phi)
        th = ((np.arange(cols) * 2 * np.pi / cols).reshape(1, cols)) 
        if offset:
            th = th + ((np.pi / cols) * np.arange(rows+1).reshape(rows+1,1))  ## rotate each row by 1/2 column
        verts[...,0] = s * np.cos(th)
        verts[...,1] = s * np.sin(th)
        verts = verts.reshape((rows+1)*cols, 3)[cols-1:-(cols-1)]  ## remove redundant vertexes from top and bottom

        xx = verts[...,0]
        yy = verts[...,1]
        zz = verts[...,2]
        P = [xx,yy,zz]
        # B = np.array([  [1.0359     ,-0.0194    ,0.0667 ],
        #                 [-0.0194    ,0.9685     ,-0.0068],
        #                 [0.0667     ,-0.0068    ,0.9631 ]   ])
        B = transform_mat
        B1 = np.transpose(B)
        P1 = np.transpose(P)
        pp = np.dot(P1,B1)

        ## compute faces
        faces = np.empty((rows*cols*2, 3), dtype=np.uint)
        rowtemplate1 = ((np.arange(cols).reshape(cols, 1) + np.array([[0, 1, 0]])) % cols) + np.array([[0, 0, cols]])
        rowtemplate2 = ((np.arange(cols).reshape(cols, 1) + np.array([[0, 1, 1]])) % cols) + np.array([[cols, 0, cols]])
        for row in range(rows):
            start = row * cols * 2 
            faces[start:start+cols] = rowtemplate1 + row * cols
            faces[start+cols:start+(cols*2)] = rowtemplate2 + row * cols
        faces = faces[cols:-cols]  ## cut off zero-area triangles at top and bottom

        # adjust for redundant vertexes that were removed from top and bottom
        vmin = cols-1
        faces[faces<vmin] = vmin
        faces -= vmin  
        vmax = verts.shape[0]-1
        faces[faces>vmax] = vmax
        md = gl.MeshData(vertexes=pp, faces=faces)
        colors = np.ones((md.faceCount(), 4), dtype=float)
        colors[:,0] = 0.1
        # colors[:,1] = np.linspace(0, 0.5, colors.shape[0])
        colors[:,1] = 0.1
        colors[:,2] = 0 
        colors[:,3] = 0.4
        md.setFaceColors(colors)
        # mm = gl.GLMeshItem(meshdata=md, smooth=True,shader='balloon', glOptions='additive')
        mm = gl.GLMeshItem(meshdata=md, smooth=False,shader='edgeHilight', glOptions='additive')
        mm.translate(-translate_mat[0,0],-translate_mat[1,0],-translate_mat[2,0])
        self.w.addItem(mm)

    def removeItem(self, itemLable):
        if itemLable in self.items:
            self.w.removeItem(self.items[itemLable])
            self.items.pop(itemLable)
            self.itemsData.pop(itemLable)

    def removeAllItem(self):
        for itemLable in self.items:
            self.w.removeItem(self.items[itemLable])
        self.items.clear()
        self.itemsData.clear()
        
def samplemat(dims):
    """Make a matrix with all zeros and increasing elements on the diagonal"""
    aa = np.zeros(dims)
    for i in range(min(dims)):
        aa[i, i] = i
    return aa

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    wgt = QtWidgets.QWidget()
    wgtLayout = QtWidgets.QHBoxLayout(wgt)

    #graph = graph_3d()
    #wgtLayout.addWidget(graph.w)

    # graph.size = 10
    #graph.addItem('ad', graph.yellowcolor)
    #graph.setItemData('ad', (10, 10, 10))

    
    wgt.show()
    wgt.setFixedSize(480, 640)

    sys.exit(app.exec_())
