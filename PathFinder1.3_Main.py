# features:
#
# 1: display image on screen
# 2: display grid on screen
# 3: draw lines between points by click order
# 4: save line coordinates in meters
import numpy as np
from math import atan2
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QPushButton, QCheckBox, QLineEdit
from PyQt5.QtGui import QPixmap, QPainterPath
import scipy.special
import json

from scipy.special.cython_special import binom


def Bernstein(n, k):
    """Bernstein polynomial.
    """
    coeff = binom(n, k)

    def _bpoly(x):
        return coeff * x ** k * (1 - x) ** (n - k)

    return _bpoly


def Bezier(calcPoints, num=100):
    """Build Bézier curve from points.
    """
    N = len(calcPoints)
    t = np.linspace(0, 1, num=num)
    curve = np.zeros((num, 2))
    for ii in range(N):
        curve += np.outer(Bernstein(N - 1, ii)(t), calcPoints[ii])
    return curve


points = []


def getDistTol(Arr, distArr):
    distTolArr = []
    tempval = 0
    pIndx = 0
    shiftVal = 0
    moreBezier = True
    pMin = None
    pMax = None

    while pIndx < len(Arr) - 1:
        if Arr[pIndx][2]:
            pMin = distArr[pIndx]
            tempval = pIndx

        elif not Arr[pIndx][2] and pMin is not None:
            pMax = distArr[pIndx]
            dist = pMax - pMin
            for i in range(pIndx - tempval):
                distTolArr.append(pMax - distArr[i])
                pIndx += 1

        else:
            distTolArr.append(0.1)
        pIndx += 1


def sortPointsIntoPathInfo(pointArr, ratios):  # fix later
    totalInfo = []
    printInfo = []
    printDist = []
    printDistTol = [0]
    distanceArr = [0]
    angleArr = [0]
    angTolArr = []
    distSum = 0
    distance = 0
    angle = 0

    pointArr = [[np.round(i[0] / ratios[0], 2), np.round(i[1] / ratios[1], 2), i[2]] for i in pointArr]

    for j in range(1, len(pointArr)):
        angle = np.round(atan2((pointArr[j][1] - pointArr[j - 1][1]), (pointArr[j][0] - pointArr[j - 1][0]))) * (
                180 / np.pi)
        if not pointArr[j][2]:  # if point is reverse (I don't know why it is False if pressed)
            lastAngle = angleArr[j - 1]
            angle = np.round(2 * lastAngle - 180 - angle, 2)  # angleArr[j - 1] --> lastAngle
            if abs(angle) > 180:
                angle = np.round(-180 + (angle % 180))
        angleArr.append(angle)

    for i in range(len(angleArr)):
        crrntAng = angleArr[i]  # current angle
        lstAng = angleArr[i - 1]  # last angle

    for i in range(1, len(pointArr)):
        crrntAng = angleArr[i]  # current angle
        lstAng = angleArr[i - 1]  # last angle
        increment = np.round(
            np.power(
                np.power(abs(pointArr[i][0] - pointArr[i - 1][0]), 2) + np.power(pointArr[i][1] - pointArr[i - 1][1],
                                                                                 2),
                0.5), 2)
        distSum += increment
        printDistTol.append(distSum)

    for i in range(1, len(pointArr)):
        crrntAng = angleArr[i]  # current angle
        lstAng = angleArr[i - 1]  # last angle
        increment = np.round(
            np.power(
                np.power(abs(pointArr[i][0] - pointArr[i - 1][0]), 2) + np.power(pointArr[i][1] - pointArr[i - 1][1],
                                                                                 2),
                0.5), 2)
        if pointArr[i][2]:
            distance += increment
        else:
            print("ducks")
            distance -= increment
        distTol = distSum - distance
        printDistTol.append(distTol)
        distanceArr.append(distance)

    # printDistTol = [distSum - printDistTol[i] for i in range(len(printDistTol))] implement only for curves later
    printDistTol = [0.3 for i in
                    range(len(pointArr))]  # still not working, fix statement after or (check point after if it exists)

    # printDistTol = [distanceArr[-i] for i in range(len(distanceArr))]
    angTolArr = [5 if pointArr[i][2] else 10 for i in
                 range(len(pointArr))]  # for some reason the number is divided by 100

    totalInfo.append(pointArr)
    totalInfo.append(distanceArr)
    totalInfo.append(angleArr)

    printInfo.append(distanceArr)
    printInfo.append(angleArr)
    printInfo.append(printDistTol)
    printInfo.append(angTolArr)

    # totalInfo: pointArr, distanceArr, angleArr
    # printInfo: printDistArr, angleArr, printDistTol

    return totalInfo, printInfo


class MainWindow(QtWidgets.QMainWindow):
    width = 1190  # 1600
    height = 508  # 650

    def __init__(self, widthInit=width, heightInit=height):
        super().__init__()

        self.destination = "PathFinder1.3_Data.json"
        self.clickPointArray = None
        self.dataDict = {}
        self.btnHeight = 50  # standard button Height
        self.btnWidth = 75  # standard button Width
        self.pixmap = QPixmap(
            'PathFinder1.3_2020-field.jpg'
        )  # image (and image path)
        realWidth = 22.71889  # m # 16.46
        realHeight = 9.533818  # m # 8.23
        self.PointNum = 7  # number of points whose values are calculated in the bezier curves
        self.last_x, self.last_y, self.ctrl_x, self.ctrl_y = None, None, None, None
        self.clickArr = []
        self.bezierPoints = []
        self.bPP = []  # bezier Points Print
        self.bSC = 5  # bezier Segment Count
        self.colorArr = ["purple", "blue", "green", "red", "cyan", "magenta", "yellow", "black", "white"]
        self.colornum = 0

        self.widthRatio = widthInit / realWidth
        self.heightRatio = heightInit / realHeight

        self.label1 = QtWidgets.QLabel()
        self.label2 = QtWidgets.QLabel(self.label1)

        # Buttons
        GetPathInfo = QPushButton('Get path info', self.label1)
        GetPathInfo.setStyleSheet("background-color: cyan")
        GetPathInfo.resize(self.btnWidth, self.btnHeight)
        GetPathInfo.move(0, heightInit)
        GetPathInfo.clicked.connect(self.PathInfoDef)

        saveCurrentPath = QPushButton('Save this path', self.label1)
        saveCurrentPath.setStyleSheet("background-color: orange")
        saveCurrentPath.resize(self.btnWidth, self.btnHeight - 25)
        saveCurrentPath.move(150, heightInit)
        saveCurrentPath.clicked.connect(self.SavePath)

        drawPath = QPushButton('draw this path', self.label1)
        drawPath.setStyleSheet("background-color: orange")
        drawPath.resize(self.btnWidth, self.btnHeight - 25)
        drawPath.move(225, heightInit)
        drawPath.clicked.connect(self.DrawPath)

        delPnt = QPushButton('delete point', self.label1)  # a button to delete points
        delPnt.setStyleSheet("background-color: green")
        delPnt.resize(self.btnWidth, self.btnHeight)
        delPnt.move(300, heightInit)
        delPnt.clicked.connect(self.DeletePoint)

        self.PathNameText = QLineEdit(self.label1)
        self.PathNameText.resize(150, 25)
        self.PathNameText.move(150, heightInit + 25)

        self.reverse = QCheckBox('reverse', self.label1)  # reverse button
        self.reverse.setStyleSheet("background-color: magenta")
        self.reverse.resize(self.btnWidth, self.btnHeight)
        self.reverse.move(75, heightInit)

        self.nextPathB = QPushButton('next path', self.label1)  # next path button
        self.nextPathB.setStyleSheet("background-color: yellow")
        self.nextPathB.resize(self.btnWidth, self.btnHeight)
        self.nextPathB.move(375, heightInit)
        self.nextPathB.clicked.connect(self.NewPath)

        canvas = QtGui.QPixmap(widthInit, heightInit + 50)
        canvas.fill(Qt.white)
        self.label1.setPixmap(canvas)
        self.label2.setPixmap(self.pixmap)
        self.setCentralWidget(self.label1)
        self.label2.show()
        self.draw_grid()

    def draw_grid(self, width_grid=width, height_grid=height):
        IntervalY = 65  # 185 = 1m
        IntervalX = 65  # 130 = 1m
        linesV = int(height_grid / IntervalY)
        linesH = int(width_grid / IntervalY)
        painter = QtGui.QPainter(self.label2.pixmap())
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor("gray"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLines(QtCore.QLineF(0, y * IntervalY, width_grid, y * IntervalY) for y in range(linesV * 2))
        painter.drawLines(QtCore.QLineF(x * IntervalX, 0, x * IntervalX, height_grid) for x in range(linesH * 2))
        painter.end()

    def mousePressEvent(self, e):
        b = not self.reverse.isChecked()

        if self.clickPointArray is None:
            self.clickPointArray = points
        pen = QtGui.QPen()
        path = QPainterPath()
        pen.setColor(QtGui.QColor(self.colorArr[self.colornum]))
        pen.setWidth(5)
        painter = QtGui.QPainter(self.label2.pixmap())
        painter.setPen(pen)

        if e.button() == QtCore.Qt.RightButton or self.clickPointArray is None:  # right click draws beziers
            center = QPoint(e.x(), e.y())
            if len(self.clickArr) < 1:
                self.clickPointArray.append([e.x(), e.y(), b])
            self.clickArr.append([e.x(), e.y()])
            self.bezierPoints = Bezier(self.clickArr)
            painter.drawEllipse(center, 2, 2)

        elif e.button() == QtCore.Qt.LeftButton:  # left button draws regular lines
            if self.last_x is None:  # First event.
                painter.drawEllipse(e.x(), e.y(), 2, 2)
                self.last_x = e.x()
                self.last_y = e.y()

            # add point coordinates to coordinate array
            if len(self.clickArr) > 1:
                bPP = Bezier(self.clickArr, self.PointNum)
                bPP = [[i[0], i[1]] for i in bPP]
                for i in range(len(bPP[1::])):
                    self.clickPointArray.append(
                        [bPP[i + 1][0], bPP[i + 1][1], b, self.colornum])  # doesn't work for 1st point of
                    # bezier, reason Unknown
            self.clickPointArray.append([e.x(), e.y(), b, self.colornum])

            self.clickArr = [[e.x(), e.y()]]

            # painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
            for i in range(1, len(self.clickPointArray)):
                pen.setColor(QtGui.QColor(self.colorArr[self.clickPointArray[i][3]]))
                painter.setPen(pen)
                if self.clickPointArray[i][2]:
                    painter.drawLine(self.clickPointArray[i - 1][0], self.clickPointArray[i - 1][1],
                                     self.clickPointArray[i][0], self.clickPointArray[i][1])
                else:
                    pen.setColor(QtGui.QColor(255, 100, 255))
                    painter.setPen(pen)
                    painter.drawLine(self.clickPointArray[i - 1][0], self.clickPointArray[i - 1][1],
                                     self.clickPointArray[i][0], self.clickPointArray[i][1])
        painter.end()
        self.update()

        # Update the origin for next time.
        self.last_x = e.x()
        self.last_y = e.y()

    # Button methods
    def PathInfoDef(self):
        infoArr, printArr = sortPointsIntoPathInfo(self.clickPointArray, [self.widthRatio, self.heightRatio])
        lines = [
            "new double[]{" + str(printArr[0][i])[:5] + ", " + str(printArr[1][i])[:6] + ", " + str(printArr[2][i])[
                                                                                                :5] + ", " + (
                "5" if not infoArr[0][i][2] else "10") + ", 0.3, 0.7}," for
            i in range(len(printArr[0]))]  # need to print 5 (for straight line) or 10 for Bezier (ToleranceAngle)
        lines[-1] = "new double[]{" + str(printArr[0][-1])[:5] + ", " + str(
            printArr[1][-1]) + ", " + "0.05" + ", 10, 0.3, 0.7}"

        for iLine in infoArr:
            print(iLine)

        for line in lines[1:]:
            print(line)
        print("\n")

    def SavePath(self):
        self.dataDict[self.PathNameText.text()] = self.clickPointArray.copy()

        try:
            with open(self.destination, "r") as json_data:
                dictData = json.load(json_data)
        except:
            dictData = {self.PathNameText.text(): self.clickPointArray.copy()}

        print(dictData)

        dictData[self.PathNameText.text()] = self.clickPointArray.copy()

        with open(self.destination, 'w') as json_data:
            json.dump(dictData, json_data)

    def DrawPath(self):
        with open(self.destination, 'r') as json_data:
            dictData = json.load(json_data)

        self.label2.setPixmap(self.pixmap)
        self.draw_grid()

        painter2 = QtGui.QPainter(self.label2.pixmap())
        pen2 = QtGui.QPen()
        pen2.setColor(QtGui.QColor(175, 175, 175))
        pen2.setWidth(5)
        pen2.setColor(QtGui.QColor('orange'))
        painter2.setPen(pen2)

        for i in range(1, len(dictData[self.PathNameText.text()])):
            painter2.drawLine(dictData[self.PathNameText.text()][i - 1][0],
                              dictData[self.PathNameText.text()][i - 1][1],
                              dictData[self.PathNameText.text()][i][0], dictData[self.PathNameText.text()][i][1])
        painter2.end()
        self.update()
        self.clickPointArray = dictData[self.PathNameText.text()].copy()  # change path array to new path array
        self.last_x, self.last_y = dictData[self.PathNameText.text()][-1][0], dictData[self.PathNameText.text()][-1][1]

    def NewPath(self):
        self.colornum += 1

    def DeletePoint(self):

        self.label2.setPixmap(self.pixmap)
        self.draw_grid()

        painter2 = QtGui.QPainter(self.label2.pixmap())
        pen2 = QtGui.QPen()
        pen2.setColor(QtGui.QColor(175, 175, 175))
        pen2.setWidth(5)
        pen2.setColor(QtGui.QColor('orange'))
        painter2.setPen(pen2)
        self.clickPointArray = self.clickPointArray[:-1]  # change path array to new path array

        for i in range(1, len(self.clickPointArray)):
            painter2.drawLine(self.clickPointArray[i - 1][0], self.clickPointArray[i - 1][1],
                              self.clickPointArray[i][0], self.clickPointArray[i][1])
            print(self.clickPointArray[i][0], self.clickPointArray[i][0])
        painter2.end()
        self.update()
        self.last_x, self.last_y = self.clickPointArray[-1][0], self.clickPointArray[-1][1]


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
