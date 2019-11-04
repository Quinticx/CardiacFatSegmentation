from scipy.spatial import distance
import os
from PIL import Image
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import morphology
import time

def read_in_label(path, list, threshold, erosion, holes):
    img = []
    thresh = []
    kernal = np.ones((5, 5), np.uint8)
    for i in list:
        #print(i)
        image = Image.open(path + '/' + i)
        img1 = np.asarray(image)
        s, th0 = cv2.threshold(img1, threshold, 255, cv2.THRESH_BINARY)
        th1 = cv2.erode(th0, kernal, iterations=erosion)
        th2 = morphology.remove_small_objects(th1, holes)
        th3 = th2.astype('bool')
        img.append(img1)
        thresh.append(th3.astype('int'))
    return img, thresh
def read_in_mask(path, list):
    img = []
    for i in list:
        #print(i)
        image = Image.open(path + '/' + i)
        img0 = image.resize((256, 256))
        img1 = np.asarray(img0)
        img2 = img1.astype('bool')
        img.append(img2.astype('int'))
    return img

def processData(img, thresh):
    dice = []
    crossTruth = []
    crossLabel = []
    for i in range(0,len(img)):
        # plt.subplot(2, 2, 1)
        # plt.imshow(img[i])
        # plt.title('original Mask')
        # plt.subplot(2, 2, 2)
        # plt.imshow(thresh[i])
        # plt.title('New Mask')
        # plt.subplot(2, 2, 3)
        # plt.imshow(2 * img[i] + thresh[i])
        # plt.title('Overlap')
        # plt.pause(3)

        gt = img[i]
        seg = thresh[i]
        diceSim = np.sum(seg[gt == 1]) * 2.0 / (np.sum(seg) + np.sum(gt))
        dice.append(diceSim)
        crossLabel.append(seg.sum())
        crossTruth.append(gt.sum())
    diceTotal = np.asarray(dice).sum()/len(dice)
    CrossLabelTotal = np.asarray(crossLabel).sum() / len(crossLabel)
    CrossTruthTotal = np.asarray(crossTruth).sum() / len(crossTruth)
    return diceTotal, CrossTruthTotal, CrossLabelTotal

DATA_PATH = 'C:/Users/mfulton/Documents/GitHub/unet/myData/'
Original_Label_path = DATA_PATH + 'Original/Test/label'
Sobel_Label_path = DATA_PATH + 'Sobel/Test/label'
Laplacian_Label_path = DATA_PATH + 'Laplacian/Test/label'

Original_Mask_path = DATA_PATH + 'Original/Test/Masks'
Sobel_Mask_path = DATA_PATH + 'Sobel/Test/Masks'
Laplacian_Mask_path = DATA_PATH + 'Laplacian/Test/Masks'

Original_Label_list = os.listdir(Original_Label_path)
Original_Mask_list = os.listdir(Original_Mask_path)

Original_Mask_list.sort(key=lambda item: (-len(item), item))
Original_Label_list.sort(key=lambda item: (-len(item), item))

Sobel_Label_list = os.listdir(Sobel_Label_path)
Sobel_Mask_list = os.listdir(Sobel_Mask_path)

Sobel_Label_list.sort(key=lambda item: (-len(item), item))
Sobel_Mask_list.sort(key=lambda item: (-len(item), item))

Laplacian_Label_list = os.listdir(Laplacian_Label_path)
Laplacian_Mask_list = os.listdir(Laplacian_Mask_path)

Laplacian_Label_list.sort(key=lambda item: (-len(item), item))
Laplacian_Mask_list.sort(key=lambda item: (-len(item), item))

imgOL = []
imgOM = []
imgSL = []
imgSM = []
imgLL = []
imgLM = []
maxDice = 0
BestThresh = 0
BestErosion = 0
BestArea = 0
str = ''
clear = lambda : os.system('cls')
for threshold in range(1, 255):
    for erosion in range(1, 10):
        for j in range(1,10):
            holes = 100*j
            print('Threshold - ', threshold)
            print('Erosion -', erosion)
            print('holes -', holes)
            imgOL, threshOL = read_in_label(Original_Label_path, Original_Label_list, threshold, erosion, holes)
            imgOM = read_in_mask(Original_Mask_path, Original_Mask_list)

            imgSL, threshSL = read_in_label(Sobel_Label_path, Sobel_Label_list, threshold, erosion, holes)
            imgSM = read_in_mask(Sobel_Mask_path, Sobel_Mask_list)

            imgLL, threshLL = read_in_label(Laplacian_Label_path, Laplacian_Label_list, threshold, erosion, holes)
            imgLM = read_in_mask(Laplacian_Mask_path, Laplacian_Mask_list)

            diceOrig, crossTruthOrig, crossLabelOrig = processData(imgOM, threshOL)
            diceSob, crossTruthSob, crossLabelSob = processData(imgSM, threshSL)
            diceLap, crossTruthLap, crossLabelLap = processData(imgLM, threshLL)

            if maxDice < diceOrig:
                str = 'Original'
                maxDice = diceOrig
                BestThresh = threshold
                BestErosion = erosion
                BestArea = holes
            if maxDice < diceSob:
                str = 'Sobel'
                maxDice = diceSob
                BestThresh = threshold
                BestErosion = erosion
                BestArea = holes
            if maxDice < diceLap:
                str = 'Laplacian'
                maxDice = diceLap
                BestThresh = threshold
                BestErosion = erosion
                BestArea = holes
            print(maxDice)

print('Best Dice ', maxDice)
print('Best Type', str)
print('Best Threshold ', BestThresh)
print('Best Erosion ', BestErosion)
print('Best Area ', BestArea)

# print('Original: Dice - ', diceOrig, 'Cross Truth - ', crossTruthOrig, 'Cross Label - ', crossLabelOrig)
# print('Sobel: Dice - ', diceSob, 'Cross Truth - ', crossTruthSob, 'Cross Label - ', crossLabelSob)
# print('Laplacian: Dice - ', diceLap, 'Cross Truth - ', crossTruthLap, 'Cross Label - ', crossLabelLap)
