# features:
#
# 1: display selected image on screen
# 2: display grid on screen
# 3: draw lines between points by pressing left click
# 4: draw segmented (using the bezier function) by pressing right click
# 4: save line coordinates in meters
# 5: mirror path in horizontal or vertical orientation
# 6: save and load path by name
# 7: divide path into color coded segments
# 8: change position of selected point
# 9: clear path from screen
# 10: delete last point from path
# draw
import pyperclip
import copy
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtWidgets import QPushButton, QCheckBox, QTextEdit
from PyQt5.QtGui import QPixmap
import tkinter as tk
from tkinter import filedialog
import json
from PathFinder_Functions import *

root = tk.Tk()
root.withdraw()

filePath = filedialog.askopenfilename()


class MainWindow(QtWidgets.QMainWindow):
    if filePath != "":
        rawFieldImg = get_image_size(filePath)  # image (and image path)
    else:
        rawFieldImg = get_image_size("PathFinder_2020-field.jpg")
    width = rawFieldImg[0] + 85  # application width
    height = rawFieldImg[1] - 50  # application height

    def __init__(self, widthInit=width, heightInit=height):
        super().__init__()

        self.destination = "PathFinder1.3_Data.json"
        self.clickPointArray = None
        self.dataDict = {}
        self.btnHeight = 50  # standard button Height
        self.btnWidth = 75  # standard button Width
        self.btnPosX = self.width - 80
        self.mirrorMode = 2
        self.mirrorP_Num = 0
        if filePath != "":
            self.pixmap = QPixmap(filePath)  # image (and image path)
        else:
            self.pixmap = QPixmap("PathFinder_2020-field.jpg")
        realWidth = 22.71889  # m # 16.46
        realHeight = 9.533818  # m # 8.23
        self.PointNum = 7  # number of points whose values are calculated in the bezier curves
        self.last_x, self.last_y, self.ctrl_x, self.ctrl_y = None, None, None, None
        self.clickArr = []
        self.bezierPoints = []
        self.bPP = []  # bezier Points Print
        self.bSC = 5  # bezier Segment Count
        self.colorArr = ["pink", "blue", "green", "red", "cyan", "magenta", "yellow", "black", "white"]
        self.colornum = 0

        self.widthRatio = widthInit / realWidth
        self.heightRatio = heightInit / realHeight

        self.label1 = QtWidgets.QLabel()
        self.label2 = QtWidgets.QLabel(self.label1)

        # Buttons
        GetPathInfo = QPushButton('Get path info', self.label1)
        GetPathInfo.setStyleSheet("background-color: light gray")
        GetPathInfo.resize(self.btnWidth, self.btnHeight)
        GetPathInfo.move(self.btnPosX, 0)
        GetPathInfo.clicked.connect(self.PathInfoDef)

        self.reverse = QCheckBox('reverse', self.label1)  # reverse button
        self.reverse.resize(self.btnWidth, self.btnHeight)
        self.reverse.move(self.btnPosX + 10, 35)

        delPnt = QPushButton('delete point', self.label1)  # a button to delete points
        delPnt.setStyleSheet("background-color: light gray")
        delPnt.resize(self.btnWidth, self.btnHeight + 5)
        delPnt.move(self.btnPosX, 70)
        delPnt.clicked.connect(self.DeletePoint)

        self.nextPathB = QPushButton('next path', self.label1)  # next path button
        self.nextPathB.setStyleSheet("background-color: light gray")
        self.nextPathB.resize(self.btnWidth, self.btnHeight)
        self.nextPathB.move(self.btnPosX, 125)
        self.nextPathB.clicked.connect(self.NewPath)

        self.PathNameText = QTextEdit(self.label1)  # 'Save this path' and 'draw this path' textbox configuration
        self.PathNameText.setFixedSize(QSize(75, 50))
        self.PathNameText.setLineWrapMode(True)
        self.PathNameText.move(self.btnPosX, 200)

        saveCurrentPath = QPushButton('Save this path', self.label1)  # button to save path by written name
        saveCurrentPath.setStyleSheet("background-color: light gray")
        saveCurrentPath.resize(self.btnWidth + 4, self.btnHeight - 25)
        saveCurrentPath.move(self.btnPosX - 2, 175)
        saveCurrentPath.clicked.connect(self.SavePath)

        drawPath = QPushButton('Draw this path', self.label1)  # button to draw path selected by name
        drawPath.setStyleSheet("background-color: light gray")
        drawPath.resize(self.btnWidth + 4, self.btnHeight - 25)
        drawPath.move(self.btnPosX - 2, 250)
        drawPath.clicked.connect(self.DrawPath)

        self.mirrorBtn = QPushButton('Mirror', self.label1)  # button to change the orientation of the mirror
        self.mirrorBtn.setStyleSheet("background-color: light gray")
        self.mirrorBtn.resize(self.btnWidth, self.btnHeight)
        self.mirrorBtn.move(self.btnPosX, 275)
        self.mirrorBtn.clicked.connect(self.mirror)

        self.mirrorAllBtn = QPushButton('Mirror All', self.label1)  # button to mirror the whole path.
        self.mirrorAllBtn.setStyleSheet("background-color: light gray")
        self.mirrorAllBtn.resize(self.btnWidth, self.btnHeight)
        self.mirrorAllBtn.move(self.btnPosX, 325)
        self.mirrorAllBtn.clicked.connect(self.mirrorAll)

        self.clearBtn = QPushButton('Clear', self.label1)  # button to clear the entire path
        self.clearBtn.setStyleSheet("background-color: light gray")
        self.clearBtn.resize(self.btnWidth, self.btnHeight)
        self.clearBtn.move(self.btnPosX, 375)
        self.clearBtn.clicked.connect(self.clear)

        self.dragPointBtn = QCheckBox('Move Point', self.label1)  # button to move closest point to click
        self.dragPointBtn.resize(self.btnWidth, self.btnHeight)
        self.dragPointBtn.move(self.btnPosX, 410)

        canvas = QtGui.QPixmap(int(widthInit), int(heightInit + 50))
        canvas.fill(Qt.lightGray)
        self.label1.setPixmap(canvas)
        self.label2.setPixmap(self.pixmap)
        self.setCentralWidget(self.label1)
        self.label2.show()
        self.draw_grid()

    def draw_grid(self, width_grid=width, height_grid=height):
        IntervalY = 50  # 185 = 1m
        IntervalX = 50  # 130 = 1m
        linesV = int(height_grid / IntervalY)
        linesH = int(width_grid / IntervalY)
        painter = QtGui.QPainter(self.label2.pixmap())
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor("gray"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLines(
            QtCore.QLineF(0, y * IntervalY, width_grid + IntervalX, y * IntervalY) for y in range(linesV * 2))
        painter.drawLines(
            QtCore.QLineF(x * IntervalX, 0, x * IntervalX, height_grid + IntervalY) for x in range(linesH * 2))
        painter.end()

    def paint_path(self, pointArr, colorArr):
        painter = QtGui.QPainter(self.label2.pixmap())
        pen = QtGui.QPen()
        for i in range(1, len(pointArr)):
            pen.setColor(QtGui.QColor(colorArr[pointArr[i][3]]))
            painter.setPen(pen)
            painter.drawLine(pointArr[i - 1][0], pointArr[i - 1][1],
                             pointArr[i][0], pointArr[i][1])

            painter.end()

    def mousePressEvent(self, e):
        isReverse = not self.reverse.isChecked()

        if self.mirrorMode == 2:
            self.label2.setPixmap(self.pixmap)
            self.draw_grid()

        if self.clickPointArray is None:
            self.clickPointArray = []
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor("pink"))
        pen.setWidth(5)
        painter = QtGui.QPainter(self.label2.pixmap())
        painter.setPen(pen)
        if self.dragPointBtn.isChecked():
            minSumNum = (
            ((self.clickPointArray[0][0] - e.x()) ** 2 + (self.clickPointArray[0][1] - e.y()) ** 2) ** 0.5, 0)
            for n, i in enumerate(self.clickPointArray):
                if ((i[0] - e.x()) ** 2 + (i[1] - e.y()) ** 2) ** 0.5 <= minSumNum[0]:
                    minSumNum = (((i[0] - e.x()) ** 2 + (i[1] - e.y()) ** 2) ** 0.5, n)
            self.clickPointArray[minSumNum[1]][0], self.clickPointArray[minSumNum[1]][1] = e.x(), e.y()
        elif e.button() == QtCore.Qt.RightButton:  # right click draws beziers
            if len(self.clickArr) < 1:
                self.clickPointArray.insert(len(self.clickPointArray), [e.x(), e.y(), isReverse, self.colornum])
            self.clickArr.insert(len(self.clickArr), [e.x(), e.y()])
            self.bezierPoints = Bezier(self.clickArr)
            for i in range(len(self.clickArr)):
                painter.drawEllipse(QPoint(self.clickArr[i][0], self.clickArr[i][1]), 2, 2)

        elif e.button() == QtCore.Qt.LeftButton:  # left button draws regular lines
            if self.last_x is None:  # First event.
                painter.drawEllipse(e.x(), e.y(), 2, 2)
                self.last_x = e.x()
                self.last_y = e.y()

            # add point coordinates to coordinate array
            if len(self.clickArr) > 1:
                bPP = Bezier(self.clickArr, self.PointNum)
                bPP = [[i[0], i[1]] for i in bPP]
            else:
                bPP = [[e.x(), e.y()]]
            for i in range(len(bPP)):
                self.clickPointArray.insert(len(self.clickPointArray),
                                            [bPP[i][0], bPP[i][1], isReverse,
                                             self.colornum])  # doesn't work for 1st point of
                # bezier, reason Unknown
            self.clickArr = [[e.x(), e.y()]]

        #  swap with draw_path function later
        for i in range(1, len(self.clickPointArray)):
            pen.setColor(QtGui.QColor(self.colorArr[self.clickPointArray[i][3]]))
            painter.setPen(pen)
            painter.drawLine(self.clickPointArray[i - 1][0], self.clickPointArray[i - 1][1],
                             self.clickPointArray[i][0], self.clickPointArray[i][1])

        painter.end()
        self.update()

        # Update the origin for next time.
        self.last_x = e.x()
        self.last_y = e.y()

    # Button methods
    def draw_mirror(self, mirrorType, labelWidth=width, labelHeight=height):
        painter = QtGui.QPainter(self.label2.pixmap())
        pen = QtGui.QPen()

        pen.setColor(QtGui.QColor("cyan"))
        pen.setWidth(5)
        painter.setPen(pen)

        if mirrorType == 0:
            painter.drawLine(int(labelWidth / 2) - 50, 0, int(labelWidth / 2) - 50, labelHeight + 50)
        elif mirrorType == 1:
            painter.drawLine(0, int(labelHeight / 2), labelWidth, int(labelHeight / 2))

        painter.end()

    def mirror(self):
        self.label2.setPixmap(self.pixmap)
        self.draw_grid()

        self.mirrorMode = (self.mirrorMode + 1) % 3

        self.draw_mirror(self.mirrorMode)
        painter2 = QtGui.QPainter(self.label2.pixmap())
        pen2 = QtGui.QPen()
        pen2.setWidth(5)
        pen2.setColor(QtGui.QColor('cyan'))
        painter2.setPen(pen2)
        # painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        pen2.setColor(QtGui.QColor('pink'))
        painter2.setPen(pen2)
        if self.clickPointArray is not None:
            for i in range(1, len(self.clickPointArray)):
                pen2.setColor(QtGui.QColor(self.colorArr[self.clickPointArray[i][3]]))
                painter2.setPen(pen2)
                painter2.drawLine(self.clickPointArray[i - 1][0], self.clickPointArray[i - 1][1],
                                  self.clickPointArray[i][0], self.clickPointArray[i][1])

        painter2.end()
        self.update()

    def mirrorAll(self):
        try:
            if self.clickPointArray is not None and len(self.clickPointArray) != 1:
                self.label2.setPixmap(self.pixmap)
                self.draw_grid()

                painter2 = QtGui.QPainter(self.label2.pixmap())
                pen2 = QtGui.QPen()
                pen2.setColor(QtGui.QColor(175, 175, 175))
                pen2.setWidth(5)
                pen2.setColor(QtGui.QColor('orange'))
                painter2.setPen(pen2)
                clickPointArrayMirrored = copy.deepcopy(self.clickPointArray)[::-1]
                if self.mirrorMode == 0:
                    for i in clickPointArrayMirrored: i[0] -= 2 * (i[0] - int(self.width / 2)) + 100
                    self.clickPointArray += clickPointArrayMirrored  # change path array to new path array
                elif self.mirrorMode == 1:
                    for i in clickPointArrayMirrored: i[1] -= 2 * (i[1] - int(self.height / 2))
                    #  clickPointArrayMirrored[0][0] = 0
                    self.clickPointArray += clickPointArrayMirrored  # change path array to new path array
                self.clickArr = [[self.clickPointArray[-1][0], self.clickPointArray[-1][1]]]  # updates bezier points
                # starting point if it is deleted

                for i in range(1, len(self.clickPointArray)):
                    pen2.setColor(QtGui.QColor(self.colorArr[self.clickPointArray[i][3]]))
                    painter2.setPen(pen2)
                    painter2.drawLine(self.clickPointArray[i - 1][0], self.clickPointArray[i - 1][1],
                                      self.clickPointArray[i][0], self.clickPointArray[i][1])
                painter2.end()
                self.update()
                self.last_x, self.last_y = self.clickPointArray[-1][0], self.clickPointArray[-1][1]
        except:
            pass

    def PathInfoDef(self):
        infoArr, printArr = sortPointsIntoPathInfo(self.clickPointArray, [self.widthRatio, self.heightRatio])
        lines = [
            "new double[]{" + str(printArr[0][i])[:5] + ", " + str(printArr[1][i])[:6] + ", " + str(printArr[2][i])[
                                                                                                :5] + ", " + (
                "5" if not infoArr[0][i][2] else "10") + ", 0.3, 0.7}," for
            i in range(len(printArr[0]))]  # need to print 5 (for straight line) or 10 for Bezier (ToleranceAngle)
        lines[-1] = "new double[]{" + str(printArr[0][-1])[:5] + ", " + str(
            printArr[1][-1]) + ", " + "0.05" + ", 10, 0.3, 0.7}"

        #  for iLine in infoArr:
        #      print(iLine)

        for line in lines[1:]:
            print(line)
        print("\n")
        #  print(self.clickPointArray)

        pyperclip.copy('\n'.join(lines))

    def SavePath(self):
        self.dataDict[self.PathNameText.toPlainText()] = self.clickPointArray.copy()

        # noinspection PyBroadException
        try:
            with open(self.destination, "r") as json_data:
                dictData = json.load(json_data)
        except:
            dictData = {self.PathNameText.toPlainText(): self.clickPointArray.copy()}

        dictData[self.PathNameText.toPlainText()] = self.clickPointArray.copy()

        with open(self.destination, 'w') as json_data:
            json.dump(dictData, json_data)

    def DrawPath(self):
        with open(self.destination, 'r') as json_data:
            dictData = json.load(json_data)

        self.label2.setPixmap(self.pixmap)
        self.draw_grid()
        self.draw_mirror(self.mirrorMode)

        painter2 = QtGui.QPainter(self.label2.pixmap())
        pen2 = QtGui.QPen()
        pen2.setWidth(5)
        pen2.setColor(QtGui.QColor('orange'))
        painter2.setPen(pen2)

        for i in range(1, len(dictData[self.PathNameText.toPlainText()])):
            painter2.drawLine(dictData[self.PathNameText.toPlainText()][i - 1][0],
                              dictData[self.PathNameText.toPlainText()][i - 1][1],
                              dictData[self.PathNameText.toPlainText()][i][0],
                              dictData[self.PathNameText.toPlainText()][i][1])
        painter2.end()
        self.update()
        self.clickPointArray = dictData[self.PathNameText.toPlainText()].copy()  # change path array to new path array
        self.last_x, self.last_y = dictData[self.PathNameText.toPlainText()][-1][0], \
                                   dictData[self.PathNameText.toPlainText()][-1][1]

    def clear(self):
        self.clickArr = []
        self.clickPointArray = []
        self.bezierPoints = []

        self.label2.setPixmap(self.pixmap)
        self.draw_grid()
        self.draw_mirror(self.mirrorMode)
        self.update()

    def NewPath(self):
        self.colornum += 1

    def DeletePoint(self):
        if self.clickPointArray is not None and len(self.clickPointArray) != 1:
            self.label2.setPixmap(self.pixmap)
            self.draw_grid()

            painter2 = QtGui.QPainter(self.label2.pixmap())
            pen2 = QtGui.QPen()
            pen2.setColor(QtGui.QColor(175, 175, 175))
            pen2.setWidth(5)
            pen2.setColor(QtGui.QColor('orange'))
            painter2.setPen(pen2)
            self.clickPointArray = self.clickPointArray[:-1]  # change path array to new path array

            self.clickArr = [[self.clickPointArray[-1][0], self.clickPointArray[-1][1]]]  # updates bezier points
            # starting point if it is deleted

            for i in range(1, len(self.clickPointArray)):
                pen2.setColor(QtGui.QColor(self.colorArr[self.clickPointArray[i][3]]))
                painter2.setPen(pen2)
                painter2.drawLine(self.clickPointArray[i - 1][0], self.clickPointArray[i - 1][1],
                                  self.clickPointArray[i][0], self.clickPointArray[i][1])
            painter2.end()
            self.update()
            self.last_x, self.last_y = self.clickPointArray[-1][0], self.clickPointArray[-1][1]


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
