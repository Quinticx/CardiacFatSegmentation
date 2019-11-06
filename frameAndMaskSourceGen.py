import os
import openpyxl
import numpy as np
import math
import nrrd
import imageio
import matplotlib.pyplot as plt


# take the seg.nrrd input image and pad it based on the extents read from the file for this tissue type
def padSegImage(inImage, padXLeft, padYTop, padXRight, padYBottom):

    # get size of input image
    sizeInputX, sizeInputY = inImage.shape[1], inImage.shape[0]
    newSizeX = inImage.shape[1] + padXLeft + padXRight
    newSizeY = inImage.shape[0] + padYTop + padYBottom

    # create new np array for image data to return
    outImage = np.zeros((newSizeY, newSizeX))

    # copy of the image data to the right locations
    outImage[padYTop:padYTop + sizeInputY, padXLeft:padXLeft + sizeInputX] = inImage
    return outImage


# takes the headers of both the regular image data and the seg data and computes the padding needed
# for the alignment of the two volumes - padding will be
def computeImageAlignment(frameHeader, segHeader):

    # get origin and space directions for each input header
    frameOrigin = frameHeader.get('space origin')
    frameSpaceDirections = frameHeader.get('space directions')
    print(frameSpaceDirections)
    segOrigin = segHeader.get('space origin')
    segSpaceDirections = segHeader.get('space directions')

    # Remove the channel row from the space directions (it is all NaNs)
    segSpaceDirections = np.delete(segSpaceDirections, 0, axis=0)
    print(segSpaceDirections)

    # get spacing for both datasets as single array
    frameSpacing = np.linalg.norm(frameSpaceDirections, axis=1)
    print(frameSpacing)
    segSpacing = np.linalg.norm(segSpaceDirections, axis=1)
    print(segSpacing)

    # # get the dimensions of the seg volume and the image volume
    # sizeSegVolumeString = segHeader.get('sizes')
    # sizeImageVolumeString = frameHeader.get('sizes')
    # sizeSegVolume = [int(i) for i in sizeSegVolumeString]
    # sizeImageVolume = [int(i) for i in sizeImageVolumeString]
    # imWidth, imHeight = sizeImageVolume[0], sizeImageVolume[1]
    # segWidth, segHeight = sizeSegVolume[0], sizeSegVolume[1]
    #
    # print(imWidth, imHeight)
    # print(segWidth, segHeight)

    # # Handle the space the NRRD files are in
    # spaceFrame = frameHeader.get('space')
    # if spaceFrame in ['right-anterior-superior', 'RAS']:
    #     worldSpaceMatrixImage = np.diag([1, 1, 1])
    # elif spaceFrame in ['left-anterior-superior', 'LAS']:
    #     worldSpaceMatrixImage = np.diag([-1, 1, 1])
    # elif spaceFrame in ['left-posterior-superior', 'LPS']:
    #     worldSpaceMatrixImage = np.diag([-1, -1, 1])
    # spaceSeg = segHeader.get('space')
    # if spaceSeg in ['right-anterior-superior', 'RAS']:
    #     worldSpaceMatrixSeg = np.diag([1, 1, 1])
    # elif spaceSeg in ['left-anterior-superior', 'LAS']:
    #     worldSpaceMatrixSeg = np.diag([-1, 1, 1])
    # elif spaceSeg in ['left-posterior-superior', 'LPS']:
    #     worldSpaceMatrixSeg = np.diag([-1, -1, 1])
    #
    # # transform the origins accordingly
    # print(frameOrigin)
    # print(segOrigin)
    # frameOrigin = worldSpaceMatrixImage @ frameOrigin
    # segOrigin = worldSpaceMatrixSeg @ segOrigin
    # print(frameOrigin)
    # print(segOrigin)
    #
    # # compute location of origin of the segmentation compared to the image data - i.e. do this
    # # by subtracting so we get the diff between seg and image data, this would be the origin
    # # of the segmentation in the 3D coordinate system of the image volume
    # originDiff = segOrigin - frameOrigin
    # print(originDiff)



# function to take in nrrd image and seg data and write out individual image filenames
# - checks to see how many files are already in the folder and uses that as the starting number
def writeImages(framePath, frameData, segPath, segData, segHeader, tissueChannel, extents, debugImages):

    # check to see if path exists, and if not create it
    if not os.path.exists(framePath):
        os.mkdir(framePath)
    if not os.path.exists(segPath):
        os.mkdir(segPath)

    # skip this set if the image is not cropped - just do simple check on size (maybe around 150?)
    maxImageDim = max(frameData.shape)
    if maxImageDim > 150:
        return

    # count files in each path
    numFilesInFramePath = len(os.listdir(framePath))
    numFilesInMaskPath = len(os.listdir(segPath))
    print(numFilesInFramePath)
    print(numFilesInMaskPath)
    startFileNum = numFilesInMaskPath

    # determine number of slices
    numSlices = frameData.shape[2]
    print(numSlices)

    numSegSlices = segData.shape[3]
    numTissueTypes = segData.shape[0]
    print(numSegSlices)
    print(numTissueTypes)

    # get offset value from seg nrrd
    segOffsetString = segHeader.get('Segmentation_ReferenceImageExtentOffset')
    segOffsetList = segOffsetString.split(' ')
    segOffsetFrameIndex = int(segOffsetList[2])
    print('offset frame: %d' % segOffsetFrameIndex)

    # loop through each seg slice and write the image file
    imagesWritten = 0
    for ii in range(0, numSegSlices):

        # compute index values to use for grabbing data from both regular image volume for frames
        # and segmented volume for masks
        indexMask = ii
        indexFrame = indexMask + segOffsetFrameIndex

        # extract out the image data for each slice to write to file and
        # adjust orientation to match display in slicer (for debugging)
        imageFrame = np.fliplr(np.rot90(frameData[:, :, indexFrame]))

        # skip this image if all the image slice data is black - check max value below a certain point
        maxImageVal = np.max(imageFrame)
        if maxImageVal < 10:
            continue

        # scale to 0-255, convert to int, and adjust orientation
        segFrame = np.flipud(np.rot90((segData[tissueChannel, :, :, indexMask] * 255).astype(np.uint8)))

        # check seg frame data also, if nothing present, skip this one
        maxSegVal = np.max(segFrame)
        if maxSegVal < 10:
            continue

        # now pad the image to make the seg the same size as the original iamge
        sizeImY, sizeImX = imageFrame.shape
        sizeSegY, sizeSegX = segFrame.shape
        offsetX = sizeImX - sizeSegX
        offsetY = sizeImY - sizeSegY
        padX_left, padY_top = int(math.ceil(offsetX/2)), 0  # put offset on bottom left
        padX_right, padY_bottom = 0, int(math.ceil(offsetY/2))
        newSegFrame = padSegImage(segFrame, padX_left, padY_top, padX_right, padY_bottom)

        # setup filenames based on how many images are already in the directory
        imageOutName = '%.3d.png' % (startFileNum + imagesWritten)
        segOutNameFullPath = segPath + '\\' + imageOutName
        imageOutNameFullPath = framePath + '\\' + imageOutName

        if debugImages:
            plt.figure()
            plt.imshow(imageFrame, 'gray', interpolation='none')
            plt.imshow(newSegFrame, 'gray', interpolation='none', alpha=0.3)
            plt.show()

        # write out the images
        imageio.imwrite(segOutNameFullPath, newSegFrame)
        imageio.imwrite(imageOutNameFullPath, imageFrame)
        imagesWritten = imagesWritten + 1


# parses each channel in seg.nrrd and returns the zero-based number of the channel based on matching
# the name string
def getTissueChannelAndExtents(segHeader, whichTissueFullName):

    # loop through header information and grab out the number of the tissue type based on the string passed in
    segExists = True
    numSeg = 0

    while segExists:

        # check for the correct field name
        fieldNameToCheckLower = 'segment%.1d_name' % numSeg
        fieldNameToCheckCap = 'Segment%.1d_Name' % numSeg

        if segHeader.get(fieldNameToCheckLower):
            fieldNameToCheck = fieldNameToCheckLower
        else:
            if segHeader.get(fieldNameToCheckCap):
                fieldNameToCheck = fieldNameToCheckCap
            else:
                segExists = False
                break

        # get current name
        segName = segHeader.get(fieldNameToCheck)
        if segName == whichTissueFullName:
            break
        else:
            numSeg = numSeg + 1

    # use the resulting tissue type to grab the extents and return them
    extentFieldName = 'Segment%.1d_Extent' % numSeg
    extentString = segHeader.get(extentFieldName).split(' ')

    return numSeg, extentString


# column numbers for the filenames - 1-based indexing as in excel
edFileNameCol = 4
edSegNameCol = 5
esFileNameCol = 6
esSegNameCol = 7

# which tissue type for this pass?
whichTissueFileName = 'LM'  # left myocardium
whichTissueFullName = 'LeftMyocardium'

# top level location of spreadsheet
spreadSheetName = 'C:\\Users\\jokling\\Documents\\WashU_CCIR_MRIData\\MRI-Table.xlsx'

# top level location of data
topLevelDataPath = 'C:\\Users\\jokling\\Documents\\WashU_CCIR_MRIData\\OriginalDICOM'

outputPath = 'C:\\Users\\jokling\\Documents\\Projects\\CardiacFatSegmentation\\myData'

# lead in the spreadsheet that has the list of names
workbook = openpyxl.load_workbook(spreadSheetName)
worksheet = next(iter(workbook))

# loop through each row and grab out the filenames that are required for both the image data (for the "frames") and
# the segmentations (for the "masks") - min row is 2 as in excel, to start at first scan
for row in worksheet.iter_rows(min_row=2, min_col=1, max_col=8):  # min 1 max 8 for correct column data

    # read the subject ID for this scan
    subjectID = row[0].value
    prePostString = row[3].value

    # blank pre/post string means skip this file
    if prePostString is not None:

        # grab the filenames for this scan
        edFileName = topLevelDataPath + '\\' + subjectID + '_' + prePostString + '\\' + row[edFileNameCol].value
        edSegName = topLevelDataPath + '\\' + subjectID + '_' + prePostString + '\\' + row[edSegNameCol].value
        esFileName = topLevelDataPath + '\\' + subjectID + '_' + prePostString + '\\' + row[esFileNameCol].value
        esSegName = topLevelDataPath + '\\' + subjectID + '_' + prePostString + '\\' + row[esSegNameCol].value

        # open each of the image NRRD files and "explode" them into separate image files
        framePath = outputPath + '\\NumberedFrames' + whichTissueFileName
        segPath = outputPath + '\\NumberedMasks' + whichTissueFileName
        frameData, frameHeader = nrrd.read(edFileName)
        segData, segHeader = nrrd.read(edSegName)

        # temp debug for only MF03PRE
        if subjectID == 'MF0303' and prePostString == 'PRE':

            # # compute the alignment based on image and seg header
            # computeImageAlignment(frameHeader, segHeader)

            # get correct tissue "channel" number for this seg file based on which tissue type
            whichTissueChannel, extents = getTissueChannelAndExtents(segHeader, whichTissueFullName)

            writeImages(framePath, frameData, segPath, segData, segHeader, whichTissueChannel,
                        extents, debugImages=True)
