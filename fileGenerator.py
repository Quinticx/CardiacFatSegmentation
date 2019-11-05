import os
import random
from PIL import Image
import numpy as np
import shutil
import scipy.ndimage as nd


def enhance1(img):
    laplacian = nd.gaussian_laplace(img, 2)
    newImage = laplacian + img
    data = newImage.astype(np.float) / newImage.max()  # normalize the data to 0 - 1
    data = 255 * data  # Now scale by 255
    final = data.astype(np.uint8)
    return final


def enhance2(img):
    sobel = nd.sobel(img)
    newImage = sobel + img
    data = newImage.astype(np.float) / newImage.max()  # normalize the data to 0 - 1
    data = 255 * data  # Now scale by 255
    final = data.astype(np.uint8)
    return final

def zeroCenter(image):
    avg = np.mean(image)
    normalized = image - avg
    return normalized


def openFile(curLocation, imageName):
    print(curLocation + imageName)
    img = Image.open(curLocation + imageName)
    return img


def writeFandMtofile(frames, masks, offset):
    for i in range(len(frames)):
        try:
            shutil.copy(FRAME_PATH + frames[i], FRAME_BLANK_PATH + str(i + offset) + '.png')
        except IOError:
            print('File: ' + frames[i] + ' already exists or had another problem')
        try:
            shutil.copy(MASK_PATH + masks[i], MASK_BLANK_PATH + str(i + offset) + '.bmp')
        except IOError:
            print('File: ' + masks[i] + ' already exists or had another problem')
        newOffset = i + offset
    return newOffset

def options(option, img):
    if option == 1:
        return enhance1(img)
    elif option == 2:
        return enhance2(img)
    else:
        return img

def add_frames(dir_name, image, option, num):
    img1 = Image.open(FRAME_BLANK_PATH + image)
    img = options(option, img1)
    img = np.array(img)
    visual = (img - img.min()) / (img.max() - img.min())
    result = Image.fromarray((visual * 255).astype(np.uint8))
    print(FRAME_BLANK_PATH + image)
    print(type(result))
    print(DATA_PATH + '/{}'.format(dir_name) + '/' + str(num) + '.png')
    result.save(DATA_PATH + '/{}'.format(dir_name) + '/' + str(num) + '.png')


def add_masks(dir_name, image, num):
    img = Image.open(MASK_BLANK_PATH + image)
    print(MASK_BLANK_PATH + image)
    print(type(img))
    img.save(DATA_PATH + '/{}'.format(dir_name) + '/' + str(num) + '.png')


DATA_PATH = './myData/'
FRAME_PATH = DATA_PATH + 'frames/'
MASK_PATH = DATA_PATH + 'masks/'

FRAME_UNIQUE_PATH = DATA_PATH + 'uniqueFrame/'
MASK_UNIQUE_PATH = DATA_PATH + 'uniqueMask/'

FRAME_BLANK_PATH = DATA_PATH + 'NumberedFrames/'
MASK_BLANK_PATH = DATA_PATH + 'NumberedMasks/'

frames = os.listdir(FRAME_PATH)
masks = os.listdir(MASK_PATH)

length1 = writeFandMtofile(frames, masks, 0)

frames = os.listdir(FRAME_BLANK_PATH)
masks = os.listdir(MASK_BLANK_PATH)

all_frames = os.listdir(FRAME_BLANK_PATH)
all_masks = os.listdir(MASK_BLANK_PATH)

random.seed(len(all_frames))
combined = list(zip(all_frames, all_masks))
random.shuffle(combined)

all_frames[:], all_masks[:] = zip(*combined)
# Generate train, val, and test sets for frames

train_split = int(0.7 * len(all_frames))
val_split = int(0.9 * len(all_frames))

train_frames = all_frames[:train_split]
val_frames = all_frames[train_split:val_split]
test_frames = all_frames[val_split:]

train_masks = all_masks[:train_split]
val_masks = all_masks[train_split:val_split]
test_masks = all_masks[val_split:]

folders1 = ['Original/', 'Sobel/', 'Laplacian/']
folders2 = ['Test/', 'Val/', 'Train/']
folders3 = ['Frames/', 'Masks/']

for folder1 in folders1:
    for folder2 in folders2:
        for folder3 in folders3:
            try:
                os.makedirs(DATA_PATH + folder1 + folder2 + folder3)
            except IOError:
                print('File: ' + DATA_PATH + folder1 + folder2 + folder3 + ' already exists or had another problem')

for i in range(len(folders1)):
    frame_folders = [(train_frames, str(folders1[i] + folders2[2] + folders3[0]), i),
                     (val_frames, str(folders1[i] + folders2[1] + folders3[0]), i),
                     (test_frames, str(folders1[i] + folders2[0] + folders3[0]), i)]

    mask_folders = [(train_masks, str(folders1[i] + folders2[2] + folders3[1])),
                    (val_masks, str(folders1[i] + folders2[1] + folders3[1])),
                    (test_masks, str(folders1[i] + folders2[0] + folders3[1]))]
    # Add frames
    for folder in mask_folders:
        array = folder[0]
        name = [folder[1]] * len(array)
        for index in range(0, len(name)):
            add_masks(name[index], array[index], index)

    for folder in frame_folders:
        array = folder[0]
        name = [folder[1]] * len(array)
        option = [folder[2]] * len(array)
        for index in range(0, len(name)):
            add_frames(name[index], array[index], option, index)
