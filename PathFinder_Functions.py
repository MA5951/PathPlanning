import numpy as np
from math import atan2
import struct
import imghdr

def get_image_size(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0)  # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception:  # IGNORE:W0703
                return
        else:
            return
        return width, height


def binom(n, k):
    if not 0 <= k <= n: return 0
    b = 1
    for t in range(min(k, n - k)):
        b *= n
        b /= t + 1
        n -= 1
    return b


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
            angle = np.round(angle - 180, 2)  # angleArr[j - 1] --> lastAngle
            if abs(angle) > 180:
                angle = np.round((angle % 180), 2)
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