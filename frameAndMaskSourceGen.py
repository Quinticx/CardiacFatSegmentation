import os
import openpyxl
import numpy as np
import nrrd
import imageio
import cv2


def offsetSegImageInOriginal(segImage, newWidth, newHeight, xOffset, yOffset):

    # get size of input image
    segImageSizeX, segImageSizeY = segImage.shape[1], segImage.shape[0]

    # create new np array for image data to return
    outImage = np.zeros((newHeight, newWidth))

    # # copy of the image data to the right locations
    # outImage[yOffset:yOffset + segImageSizeY, xOffset:xOffset + segImageSizeX] = segImage

    # copy data with for loops initially because that will be easier
    # TODO replace with python slicing approach
    for ii in range(0, segImageSizeY):

        # compute new location of this data from source image
        # if it's negative or past the height of the destination, just skip because this row is out of bounds
        newY = ii + yOffset
        if (newY < 0) or (newY >= newHeight):
            print('skipping row %d' % newY)
            continue

        for jj in range(0, segImageSizeX):

            # compute new column location from source image
            # if it's negative or past the width, skip because out of bounds
            newX = jj + xOffset
            if (newX < 0) or (newX >= newWidth):
                print('skipping col %d' % newX)
                continue

            # if we've made it to here, copy the value over
            # srcY = (segImageSizeY-1) - ii
            # srcX = (segImageSizeX-1) - jj
            srcY = ii
            srcX = jj
            if ii < 20 and jj < 20:
                outImage[newY, newX] = 255
            else:
                outImage[newY, newX] = segImage[srcY, srcX]

    # return the output image
    return outImage


# function to take in nrrd image and seg data and write out individual image filenames
# - checks to see how many files are already in the folder and uses that as the starting number
def writeImages(framePath, frameData, segPath, segData, segHeader,
                overlayPath, tissueChannel, offsetX, offsetY, debugImages):

    # check to see if path exists, and if not create it
    if not os.path.exists(framePath):
        os.mkdir(framePath)
    if not os.path.exists(segPath):
        os.mkdir(segPath)
    if not os.path.exists(overlayPath):
        os.mkdir(overlayPath)

    # skip this set if the image is not cropped - just do simple check on size (maybe around 150?)
    maxImageDim = max(frameData.shape)
    if maxImageDim > 150:
        print('Skipping %s' % framePath)
        return

    # count files in each path
    numFilesInFramePath = len(os.listdir(framePath))
    numFilesInMaskPath = len(os.listdir(segPath))
    startFileNum = numFilesInMaskPath

    # determine number of slices and tissue types
    numSlices = frameData.shape[2]
    numSegSlices = segData.shape[3]
    numTissueTypes = segData.shape[0]

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
            print('Skipping image %d' % indexFrame)
            continue

        # scale to 0-255, convert to int, and adjust orientation
        segFrame = np.flipud(np.rot90((segData[tissueChannel, :, :, indexMask] * 255).astype(np.uint8)))

        # check seg frame data also, if nothing present, skip this one
        maxSegVal = np.max(segFrame)
        if maxSegVal < 10:
            print('Skipping seg image %d' % indexMask)
            continue

        # now pad the image to make the seg the same size as the original iamge
        newSegFrame = offsetSegImageInOriginal(segFrame, imageFrame.shape[1], imageFrame.shape[0],
                                               offsetX, offsetY)

        # setup filenames based on how many images are already in the directory
        imageOutName = '%.3d.png' % (startFileNum + imagesWritten)
        overlayOutName = '%.3d_overlay.png' % (startFileNum + imagesWritten)
        segOutNameFullPath = segPath + '\\' + imageOutName
        imageOutNameFullPath = framePath + '\\' + imageOutName
        overlayOutNameFullPath = overlayPath + '\\' + overlayOutName

        # write out the images
        imageio.imwrite(segOutNameFullPath, newSegFrame)
        imageio.imwrite(imageOutNameFullPath, imageFrame)
        imagesWritten = imagesWritten + 1

        # for openCV blending, read back the PNGs, blend them, and rewrite overlay
        if debugImages:
            background = cv2.imread(imageOutNameFullPath)
            overlay = cv2.imread(segOutNameFullPath)
            combinedImage = cv2.addWeighted(background, 0.7, overlay, 0.3, 0)
            cv2.imwrite(overlayOutNameFullPath, combinedImage)


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
        overlayPath = outputPath + '\\NumberedOverlays' + whichTissueFileName
        frameData, frameHeader = nrrd.read(edFileName)
        segData, segHeader = nrrd.read(edSegName)

        # temp debug for only MF03PRE
        if subjectID == 'MF0303' and prePostString == 'PRE':

            # test offset values for this case
            xOffset, yOffset = 0, 0

            # get correct tissue "channel" number for this seg file based on which tissue type
            whichTissueChannel, extents = getTissueChannelAndExtents(segHeader, whichTissueFullName)

            writeImages(framePath, frameData, segPath, segData, segHeader, overlayPath, whichTissueChannel,
                        xOffset, yOffset, debugImages=True)
