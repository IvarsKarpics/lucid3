#! /usr/bin/env python
import os
import cv2
import shutil
import tempfile
import scipy.misc
import numpy as np
import matplotlib.pyplot as plt

# import matplotlib
# matplotlib.use('Qt4Agg')
# import matplotlib.pyplot as plt

# import sys

# definition des variables Global :

MICRON_PER_PIXEL = 2
# Relative area criteria
AIRE_MIN_REL = 0.02
# Minimal lengh of detected contour (used when contour are still opened)
LENGH_MIN = 125
# global YSize # Size of white border
(XSize, YSize) = (10, 10)  # White border applied to image in order to avoid border effect
# (XSize, YSize) = (5, 5)  # White border applied to image in order to avoid border effect
Offset = (4, 4)  # Offset applied to image in order to avoid border effect
SeuilMode = False  # computing threshold mode
Area_Point_rel = 0.005
# This parameter indicate the number of iteration on closing algorithme (upper value could lead to dust agglomeration with support)
NiteClosing = 6
# Possible Criteron mod
CRIT_MOD_NOVALUE = 0
CRIT_MOD_SUP = 1
CRIT_MOD_LOOP = 2
CRIT_MOD_NARROW = 3
# Definition of value used for criterion depending on MICRON_PER_PIXEL value
CRITERON_DY_LOOP_SUP = 280 / MICRON_PER_PIXEL
CRITERON_DEFAULT3 = 110 / MICRON_PER_PIXEL
CRITERON_DX_LINEARITY = 140 / MICRON_PER_PIXEL
CRITERON_DY_LINEARITY = 90 / MICRON_PER_PIXEL
CRITERON_DY_NARROW = 50 / MICRON_PER_PIXEL
CRITERON_DX_NARROW = 50 / MICRON_PER_PIXEL
CRITERON_DY_LOOP_SUP2 = 150 / MICRON_PER_PIXEL
def find_loop(input_data, IterationClosing=1, rotation=None, debug=False):
    """
      This function detect support (or loop) and return the coordinates if there is a detection,
      and -1 if not.
      in : filename : string image Filename / Format accepted :
      in : IterationClosing : int : Number of iteration for closing contour procedure
      Out : tupple of coordiante : (string, coordinate X, coordinate Y) where string take value
          'Coord' or 'No loop detected depending if loop was detected or not. If no loop was
           detected coordinate X and coordinate y take the value -1.
    """
# Archive the image
    if debug:
        archiveDir = "/scisoft/users/svensson/tmp"
        (file_descriptor, fileBase) = tempfile.mkstemp(prefix="lucid_id29_", dir=archiveDir)
        os.close(file_descriptor)
        suffix = os.path.splitext(input_data)[1]
        shutil.copy(input_data, fileBase + suffix)
        os.remove(os.path.join(archiveDir, fileBase))
# Definition variable Global
    global AIRE_MIN_REL
    global AIRE_MIN
    global NORM_IMG
    global NiteClosing
    global pointRef
# Chargement image
    try :
        if type(input_data) == str:
            # Image filename is passed
            img_ipl = cv2.imread(input_data)
            img_ipl = cv2.cvtColor(img_ipl, cv2.COLOR_RGB2GRAY);
            if rotation is not None:
                if debug:
                    plt.imshow(img_ipl)
                    plt.title("Not rotated")
                    plt.show()
                # rows, cols, layers = img0.shape
                print(img_ipl.shape)
                # M = cv2.getRotationMatrix2D((cols / 2, rows / 2), rotation, 1)
                # imgRotated = cv2.warpAffine(img0, M, (cols, rows))
                imgRotated = np.rot90(img_ipl, k=3)
                print(imgRotated.shape)
                if debug:
                    plt.imshow(imgRotated)
                    plt.title("Rotated")
                    plt.show()
                # cv2.imshow("Test", dst)
                # cv2.waitKey(0)
                img_ipl = imgRotated
        elif type(input_data) == np.ndarray:
            # img_ipl = cv2.cv.fromarray(input_data)
            img_ipl = input_data
        else:
            print("ERROR : Input image could not be opened, check format or path")
            return ("ERROR : Input image could not be opened, check format or path", -10, -10)
    except:
        raise
        print("ERROR : Input image could not be opened, check format or path")
        return ("ERROR : Input image could not be opened, check format or path", -10, -10)
    rows, cols = img_ipl.shape
    NORM_IMG = rows * cols
    AIRE_MIN = NORM_IMG * AIRE_MIN_REL
    print("AIRE_MIN: {0}".format(AIRE_MIN))
# traitement

    # Converting input image in Grey scale image
    # img_gray_ini = cv2.cvtColor(img_ipl, cv2.COLOR_RGB2GRAY);
    img_gray_ini = img_ipl
    # Removing Offset from image
    img_gray_resize = img_gray_ini[Offset[0]:rows - 2 * Offset[0], Offset[1]:cols - 2 * Offset[1]]
    if debug:
        plt.imshow(img_gray_resize)
        plt.title("Original")
        plt.show()
#    #creat image used for treatment
    img_gray = cv2.GaussianBlur(img_gray_resize, ksize=(11, 9), sigmaX=0)
    if debug:
        plt.imshow(img_gray)
        plt.title("Gaussian Blur")
        plt.show()
#   Cutoff for very smooth images
    rows, cols = img_gray.shape
    center = [int(cols / 2), int(rows / 2)]
    radius = min(center[0], center[1])
    Y, X = np.ogrid[:rows, :cols]
    dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
    if debug:
        plt.imshow(dist_from_center)
        plt.title("Mask")
        plt.show()

    mask1 = dist_from_center <= radius
    mask2 = np.ones((rows, cols), dtype=img_gray.dtype) - mask1
    img_gray_masked = img_gray * mask1 + mask2 * 100
    img_gray[ np.where(img_gray_masked < 20) ] = 0
    if debug:
        plt.imshow(img_gray)
        plt.title("Cutoff")
        plt.show()
    img_trait = cv2.Canny(img_gray, 40, 60)
    # Computing laplacian
    img_lap_ini = cv2.Laplacian(img_gray, cv2.CV_64F, ksize=5)
    if debug:
        plt.imshow(img_lap_ini)
        plt.title("Laplacian")
        plt.show()
    # Applying Offset to avoid border effect
    img_lap = img_lap_ini[Offset[0]:rows - 2 * Offset[0], Offset[1]:cols - 2 * Offset[1]]
    # Apply an asymetrique  smoothing
    img_lap = cv2.GaussianBlur(img_lap, ksize=(21, 11), sigmaX=0)
    # img_lap = cv2.GaussianBlur(img_lap, ksize=(17, 9), sigmaX=0)
    # Define the Kernel for closing algorythme
    MKernel = cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(5, 3), anchor=(3, 1))
    # MKernel = cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(7, 3), anchor=(3, 1))
    img_lap = cv2.morphologyEx(img_lap, cv2.MORPH_CLOSE, MKernel, iterations=NiteClosing)
    if debug:
        plt.imshow(img_lap)
        plt.title("Morphology")
        plt.show()

    img_lap[ np.where(img_lap < 0) ] = 0
    img_lap[ np.where(img_lap >= 255) ] = 0

    img_lap8_ini = np.uint8(img_lap)

    if debug:
        plt.imshow(img_lap8_ini)
        plt.title("Cutoff")
        plt.show()

    # Add white border to image
    img_lap8 = WhiteBorder(img_lap8_ini[:], XSize, YSize)

    # Compute threshold
    seuil_tmp = Seuil_var(img_lap8)
    # If Seuil_tmp is not null
    if seuil_tmp != 0:
        seuil = seuil_tmp
    # Else seuil is fixed to 20, which prevent from wrong positiv detection
    else :
        seuil = 20
    print("Seuil: {0}".format(seuil))

    # Compute thresholded image
    ret, img_lap_bi = cv2.threshold(img_lap8, seuil, 255, 0)
    if debug:
        plt.imshow(img_lap_bi)
        plt.title("Threshold")
        plt.show()
    # Gaussian smoothing on laplacian
    img_lap_bi = cv2.GaussianBlur(img_lap_bi, ksize=(11, 11), sigmaX=0)
    # img_lap_bi = cv2.GaussianBlur(img_lap_bi, ksize=(15, 15), sigmaX=0)
    # Convert grayscale laplacian image to binarie image using "seuil" as threshold value
    ret, img_lap_bi = cv2.threshold(img_lap_bi, seuil, 255, cv2.THRESH_BINARY_INV)
    if debug:
        plt.imshow(img_lap_bi)
        plt.title("Gaussian blur")
        plt.show()
    img_lap_color = img_lap_bi
    img_trait_lap = cv2.Canny(img_lap_bi, 0, 2)
    kernel = np.ones((3, 3), np.uint8)
    img_trait_lap = cv2.dilate(img_trait_lap, kernel, iterations=1)
    if debug:
        plt.imshow(img_trait_lap)
        plt.title("Contours")
        plt.show()
# img_lap[ np.where(img_lap < 0) ] = 0
#         cv2.imshow("Canny", img_trait_lap)
#     cv2.waitKey(0)

    # Find contour
    contours, hierarchy = cv2.findContours(img_trait_lap, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_SIMPLE)
    # contour is filtered
    try :
        contour_list = parcourt_contour(contours, img_lap_color)
    except :
        raise
#     If error is traped then there is no loop detected
        return (0, 0, ("No loop detected", -1, -1))

#    If there contours's list is not empty
    NCont = len(contour_list)
    if(NCont > 0):
        #     The CvSeq is inversed : X(i) became i(X)
        rows, cols = img_lap_color.shape
        indice = MapCont(contour_list[0], cols, rows)
        #     The coordinate of target is computed in the traited image
        point_shift = integreCont(indice, contour_list[0])
        #     The coordinate in original image are computed taken into account Offset and white bordure
        point = (point_shift[0], point_shift[1] + 2 * Offset[0] - XSize, point_shift[2] + 2 * Offset[1] - YSize)
        # Mask the lower and upper right corners
        if point_shift[1] < cols * 0.2:
            if point_shift[2] < rows * 0.2 or \
               (rows - point_shift[2]) < rows * 0.2:
                # No loop is detected
                point = ("No loop detected", -1, -1)
        else:
            if rotation is not None:
                # centX = cols / 2
                # centY = rows
                # distX = centX - point[1]
                # distY = centY - point[2]
                # point = (point[0], centX - distY, centY + distX)
                point = (point[0], point[2], cols - point[1])
            if debug:
                image = scipy.misc.imread(input_data, flatten=True)
                imgshape = image.shape
                extent = (0, imgshape[1], 0, imgshape[0])
                implot = plt.imshow(image, extent=extent, cmap='gray')
                plt.title(fileBase)
                if point[0] == 'Coord':
                    xPos = point[1]
                    yPos = imgshape[0] - point[2]
                    plt.plot(xPos, yPos, marker='+', markeredgewidth=2,
                             markersize=20, color='red')
                newFileName = os.path.join(archiveDir, fileBase + "_marked.png")
                print("Saving image to " + newFileName)
                plt.savefig(newFileName)
                plt.close()

    else:
        # Else no loop is detected
        point = ("No loop detected", -1, -1)

    return point

def parcourt_contour(_contours, img):
    """
    This fonction is a seq contours filter. Contours are selectionned by applying AIRE and lengh critera.
       
    In : contours : List of contours  
    In : Image : Image where was extract seq
    Out : list of contour
    """
    # Global Variable Definition
    global AIRE_MIN_REL
    global AIRE_MIN
    global NORM_IMG
    global LENGH_MIN
    contours = list(_contours)
    # Local Variable definition
    Still_Contour = True  # Booleen Used for check if all contour seq is checked
    Contour_Keep = []  # List of contour selectionned
    AireMem = 0  # Aire buffer
    remonte = False  # used for check the vertical cover side (upward : True ; DownWard : False)
    gauche = True  # used for check the horizontal cover side (Right to Left : True ; Left to Right False)
    niveau = 0  # used for keep in memory the current level in the tree seq
    count = 0  # used in order to count the number of kept contour

    if len(contours) > 0:
        seq = contours.pop(0)
        Still_Contour = True
        lengh = len(seq)
        Area = cv2.contourArea(seq)
    else:
        seq = None
        Still_Contour = False
        lengh = 0
        Area = 0

    # Compute lengh of Contour
    print(lengh)

    # if Current contour lengh or Aire is upper than reference
    if(lengh > LENGH_MIN or Area > AIRE_MIN):
        # increament contour kept counter
        count = count + 1
        # Seq is put in buffer
        Seq_triee = seq
        if(count == 1):
            color = (255, 0, 0)
        elif(count == 2):
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)
        # Kept contour are ordered in decreasing Area critera
        if(Area > AireMem):
            Contour_Keep.insert(0, Seq_triee)
            AireMem = Area
        else:
            Contour_Keep.append(Seq_triee)
    # While there is contour to check
    while Still_Contour :
        # print("AireMem: {0}".format(AireMem))
        # New sequence is the next in horizontal.
        seq = contours.pop(0)
        if len(contours) > 0:
            Still_Contour = True
        else:
            Still_Contour = False
        # compute Area of contour
        Area = cv2.contourArea(seq)
        # Compute lengh of contour
        lengh = len(seq)
        # If lengh or Area is upper limit value contour is kept
        if(lengh > LENGH_MIN or Area > AIRE_MIN):
            count = count + 1
            Seq_triee = seq
            # If contour have the maximal area
            if(Area > AireMem):
                # Contour is save in the first indexe
                Contour_Keep.insert(0, Seq_triee)
                AireMem = Area
            # Else contour is save in last position
            else:
                Contour_Keep.append(Seq_triee)
        # Else if there is upper contours
    return Contour_Keep
def WhiteBorder(img, XSize, YSize):
    """
    This fonction add white border to an image

    In : img : numpy array : input image
    In : XSize : int: width of white border
    In : YSize : int: heigh of white border
    Out : ouput_mat : numpy array : Output image copy of input one added of white border 
    """
    s0, s1 = img.shape
    dtypeI = img.dtype
    output_mat = np.zeros((s0, s1), dtype=dtypeI)
    output_mat[XSize:s0 - XSize, YSize:s1] = img[XSize:s0 - XSize, 0:s1 - YSize]
    # Clear corners
    cutoff_size = 50
    output_mat[0:cutoff_size, 0:cutoff_size] = 0
    output_mat[s0 - cutoff_size:s0, 0:cutoff_size] = 0
    return output_mat
def Seuil_var(img):
    """
    This fonction compute threshold value. In first the image's histogram is calculated. The threshold value is set to the first indexe of histogram wich respect the following criterion : DH > 0, DH(i)/H(i) > 0.1 , H(i) < 0.01 % of the Norm. 

    In : img : ipl Image : image to treated
    Out: seuil : Int : Value of the threshold 
    """
    dim = 255
    MaxValue = np.amax(np.asarray(img[:]))
    Norm = np.asarray(img[:]).shape[0] * np.asarray(img[:]).shape[1]
    scale = MaxValue / dim
    MaxValue = np.amax(np.asarray(img[:]))
    bins = [float(x) for x in range(dim)]
    hist, bin_edges = np.histogram(np.asarray(img[:]), bins)
    Norm = Norm - hist[0]
    i = 1
    som = 0
    while (som < 0.8 * Norm and i < len(hist) - 1):
        som = som + hist[i]
        i = i + 1
    while ((hist[i] - hist[i - 1] < 0 or (hist[i] - hist[i - 1]) / hist[i - 1] > 0.1 or hist[i] > 0.01 * Norm) and i < len(hist) - 1):
        i = i + 1
        if hist[i - 1] == 0:
            return 0

    if(i == len(hist) - 1):
        seuil = 0
    else:
        seuil = i

    return seuil

# Draw contour from list of tuples.
def MapCont(Cont, s0, s1):
    """
    This function transform a list of coordinate X(i) intoa function of coordinate i(X)

    In : Cont : CvSeq : Contour represented by a sequence of point
    In : s0 :
    In : s1 :
    Out : ListInd : List : function indexe(abscissa)

    """
    listInd = []

    for i in range(0, s0):
        result = [index for index, item in enumerate(Cont) if _filter(item, i)]
        listInd.append(result)
    return listInd
def FindPointMax(listInd):
    """
    This function return the maximal not null value in a list
    
    In : list : List of index
    Out : maximal indexe
    """
    i = len(listInd) - 1
    while((listInd[i] == [] or listInd[i] == None) and i >= 0):
        i = i - 1
    if i == 0:
        return None
    else:
        return listInd[i][0]
def _filter(tuple, x):
    """
    This function is a filter which return true if the first value of tuple is equal to x
    In : tuple : tuple to be tested
    In : x : float, The test value
    Out : Bool : Result of test 
    """
    if(tuple[0][0] == x):
        return True
    else:
        return False
def integreCont(listInd, seq):
    """
    This fonction integrate contour, in order to extract target coordinates
    In : listInd : list : list of indexe contour i(X) where x is the abscissa of contour point
    In : seq : list of int tuple (X,Y) : list of point of contour
    Out : tuple : Coordinate of the target
    """
    # Global variable declaration
    global Crit_Mod
    global CRIT_MOD_SUP
    global CRIT_MOD_LOOP
    global CRIT_MOD_NARROW
    global CRIT_MOD_NOVALUE
    global Area_Point_rel
    # Initialize both cover indexe to the one of the maximal abscissa point of contour
    indMax = FindPointMax(listInd)
    indMin = FindPointMax(listInd)
    # buffer initialisation
    seq_tmp = []
    # iteration number initialisation
    Xcib = None
    Ycib = None
    Nite = 0
    search = True
    # Y initialisation
    Y = seq[indMax][0][1]
    # if sequence is not empty
    if indMax != None:
        # Get the lengh of the sequence
        s0 = len(seq)
        # The maximum iteration is arbitrary fixed to the half of the sequence lengh
        NInd = s0 / 2
        # Initialize both cover indexe to the one of the maximal abscissa point of contour
        indp = indMax
        indm = indMax
        # Initialize refrence distance to zero
        distRef = 0
        # Initialize the maximal value of abscissa
        Xtot = seq[indMax][0][0]
        # Get the criter for extract coordinate point
        Area = GetCriter(listInd, seq, indMax)
        Area10 = Area * Area_Point_rel
        Nmax = s0 / 2.
        # While coordinates point are not found and iteration max is not reached
        while(search and Nite < Nmax):
            Nite = Nite + 1
            # Only one is decrease between upper index and lower index, it's the one with the lower value. Bounding condition are applied on indexes
            if(seq[indp][0][0] > seq[indm][0][0]):
                if(indp < s0 - 2):
                    indp = indp + 1
                else :
                    indp = 0
            else:
                if(indm > 1):
                    indm = indm - 1
                else :
                    indm = s0 - 1
            poids = float(abs(seq[indp][0][0] - seq[indm][0][0])) / float(Xtot)
            dist = abs(seq[indp][0][1] - seq[indm][0][1])
            distRef = distRef + dist * poids
            # Partial Area of contour is calculated
            if(indm < indp):
                AreaTmp = cv2.contourArea(seq[indm:indp])
            else :
                AreaTmp = cv2.contourArea(seq) - cv2.contourArea(seq[indp:indm])
            AreaTmp = abs(AreaTmp)
            # if Partial area is lower than area criteron and the criteron mod is not Narrow or support
            if(AreaTmp < Area10 and Crit_Mod != CRIT_MOD_NARROW and Crit_Mod != CRIT_MOD_SUP):
                # Coordinates are saved
                Xcib = (seq[indm][0][0] + seq[indp][0][0]) * 0.5
                Ycib = (seq[indm][0][1] + seq[indp][0][1]) * 0.5
            # else if criteron mod is narrow or support and distance between current point and maximal abscissa is lower than 80 microns
            elif((Crit_Mod == CRIT_MOD_NARROW or Crit_Mod == CRIT_MOD_SUP)and (Xtot - (seq[indm][0][0] + seq[indp][0][0]) * 0.5) < 40):
                # Coordinates are saved
                Xcib = (seq[indm][0][0] + seq[indp][0][0]) * 0.5
                Ycib = (seq[indm][0][1] + seq[indp][0][1]) * 0.5
            # else if coordinate point already found and criteron mod is not narrow nor support
            elif(AreaTmp > Area10 and Crit_Mod != CRIT_MOD_NARROW and Crit_Mod != CRIT_MOD_SUP):
                # the loop is ended in order to avoid minimal contous abscissa interference
                search = False
            if Xcib is not None and Ycib is not None:
                Xcib = int(Xcib)
                Ycib = int(Ycib)
    if Xcib is None or Ycib is None:
        return ("No loop detected", -1, -1)
    else:
        return ("Coord", Xcib, Ycib)
def GetCriter(listInd, seq, indMax):
    """ 
    This fonction use contour to determine the type of support and the type of criter to use for get point coord. The determination is based on the shape of counter, specialy the width of counter versus abscissa. There is 4 different Type. Narrow, wich is for Narrow support. SUP wich for support. Loop for     loop, all loop are not detected in this categorie, only one wich have a principal support. And defaut value wich is for all not detected support.
    In[1] List of indice depenting of value of X 
    In[2] CvSeq of main contour
    In[3] Indice of the point of CvSeq having the Max X
    Out [1] : Area of interrest wich will be used as reference Area
      
    Area critere and Detected Type are global variable
    """

    #  Global variable declaration
    global Crit_Mod
    global CRIT_MOD_SUP
    global CRIT_MOD_LOOP
    global CRIT_MOD_NARROW
    global CRIT_MOD_NOVALUE
    Crit_Mod = CRIT_MOD_NOVALUE
    global Area_Point_rel
    Area_Point_rel = 0.008
    #  Local variable declaration
    Crit_Mod_opt = CRIT_MOD_NOVALUE  # Used when a possible support is detected, but loop could still be detected also.
    # If there is a Maximum in X
    if indMax != None:
        # Get the lengh of contours to analyse
        s0 = len(seq)
        indp = indMax  # Initialisation of indice
        indm = indMax  # Initialisation of indice
        Xtot = seq[indMax][0][0]  # Set Maximal value
        DeltaY = [0]  # List of width of contour versus X
        Xmax = [Xtot]  # List of X linked to previous list of DeltaY
        Ymax = 0
        Xmem = 12000
        Xmin = 0
        XminMem = Xtot
        Xm = 600
        XM = Xtot
        Nite = 0
        # Indexes of contours are cover on 600 micron or until abscissa 15 is reach or maximal iteration or a final criteron is foun
        while (Xtot - XM) < 300 and Xm > 15 and Nite < 500 and Crit_Mod == CRIT_MOD_NOVALUE :
            Nite = Nite + 1
            X1 = seq[indp][0][0]  # Upper Abscissa
            Y1 = seq[indp][0][1]  # Upper Ordinate
            X2 = seq[indm][0][0]  # Lower Abscissa
            Y2 = seq[indm][0][1]  # Lower Ordinate
            Xm = (X1 + X2) * 0.5  # Mean Abscissa
            Ym = (Y1 + Y2) * 0.5  # Mean Ordinate
            Xd = (X1 - X2)  # Abscissa difference
            Yd = abs(Y2 - Y1)  # Ordinate difference
            XM = max(X1, X2)  # Abscissa Maximal
            Xmin = min(X1, X2)  # Abscissa Minimal
            if(Yd > Ymax) :
                Ymax = Yd
            # If the minimal Abscissa strongly increase during one iteration, the shape should be lineare
            # Witch is a caracteristic of a kind of support
            if(abs(Xmin - XminMem) > CRITERON_DX_LINEARITY and Crit_Mod_opt != CRIT_MOD_SUP) :
                # If the step in Y corresponding is upper than 90 Micron
                if((Ymax - Yd) > CRITERON_DY_LINEARITY) :
                    Crit_Mod = CRIT_MOD_LOOP
                    Area_Point_rel = 0.4
                else :
                    # An option is took to Support type, but not definitly cause some loop can present this kind of shape too
                    Crit_Mod_opt = CRIT_MOD_SUP
            # If Yd is upside the narrow limit and dx is downside the x narrow limit then it s not a narrow type
            if(Yd > CRITERON_DY_NARROW and (Xtot - XM) < CRITERON_DX_NARROW):
                Area_Point_rel = 0.05
            # If the CRITERON_DX_NARROW has been cover and area_point_rel is still to the default value and no support option has been detected
            if((Xtot - XM) > CRITERON_DX_NARROW and Area_Point_rel < 0.04 and Crit_Mod_opt != CRIT_MOD_SUP) :
                # Then criteron is set to narrow mod
                Crit_Mod = CRIT_MOD_NARROW
            # If a step in Dy superior to 140 micron is detected then default value for relative area is set to 0.15
            if(Yd > CRITERON_DEFAULT3 and Area_Point_rel < 0.1 and Crit_Mod_opt != CRIT_MOD_SUP):
                 Area_Point_rel = 0.15
            # If a loop support is detected for the fist time
            if(Yd > CRITERON_DY_LOOP_SUP and Crit_Mod != CRIT_MOD_LOOP):
                Xint = 0
                iint = 0
                sumD = 0
                # Search back the Dy value 50 micron back
                while(Xint < CRITERON_DX_NARROW and iint < len(DeltaY)):
                    Xint = Xmax[iint] - XM
                    iint = iint + 1
                DY25 = Yd - DeltaY[iint - 1]
                # if the step is taller than 140 micron then mod is loop and relative area is set to 0.2
                if(DY25 > CRITERON_DY_LOOP_SUP2) :
                    Crit_Mod = CRIT_MOD_LOOP
                    Area_Point_rel = 0.2
                    indBord1 = indm
                    indBord2 = indp
                # Else criteron mode is set to support
                else :
                    Crit_Mod = CRIT_MOD_SUP
            # The calculations made on previous indexe ar keep in memory if contour do not present irregularity
            # if abscissa is decreasing
            if((XM - Xmem) < 0) :
                Xmax.insert(0, XM)
                Xmem = XM
                DeltaY.insert(0, Yd)
            # else the yd value is test and keep if it's highter than saved one
            else :
                i = 0
                if(Yd > DeltaY[0]):
                    while(Xmax[0] < XM):
                        i = i + 1
                        Xmax.pop(0)
                        DeltaY.pop(0)
            # Only one is decrease between upper index and lower index, it's the one with the lower value. Bounding condition are applied on indexes
            if(seq[indp][0][0] > seq[indm][0][0]):
                if(indp < s0 - 2):
                    indp = indp + 1
                else :
                    indp = 0
            else:
                if(indm > 1):
                    indm = indm - 1
                else :
                    indm = s0 - 1
    # Depending on criteron mode the reference area is computed
    if(Crit_Mod == CRIT_MOD_LOOP) :
        if(indm < indp):
            Norm = cv2.contourArea(seq[indm:indp])
        else :
            Norm = cv2.contourArea(seq) - cv2.contourArea(seq[indp:indm])
    elif(Crit_Mod_opt == CRIT_MOD_SUP):
        Crit_Mod = CRIT_MOD_SUP
        Norm = cv2.contourArea(seq)
    else :
        Norm = cv2.contourArea(seq)
    return Norm
