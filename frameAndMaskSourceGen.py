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
            srcY = ii
            srcX = jj
            outImage[newY, newX] = segImage[srcY, srcX]

    # return the output image
    return outImage

# function to take in nrrd image data and do two successive operations (rotate, flip, etc.) to orient
# it correctly compared to the image data - this is just determined empirically and stored in a spreadsheet
# that is read in
def orientImage(image, firstOperation, secondOperation):

    # check string and perform first operation
    if firstOperation == 'rot90':
        image = np.rot90(image)
    elif firstOperation == 'fliplr':
        image = np.fliplr(image)
    elif firstOperation == 'flipud':
        image = np.flipud(image)

    # check string and perform second operation
    if secondOperation == 'rot90':
        image = np.rot90(image)
    elif secondOperation == 'fliplr':
        image = np.fliplr(image)
    elif secondOperation == 'flipud':
        image = np.flipud(image)

    # return data
    return image

# function to take in nrrd image and seg data and write out individual image filenames
# - checks to see how many files are already in the folder and uses that as the starting number
def writeImages(framePath, frameData, segPath, segData, segHeader,
                overlayPath, fileNameAppend, tissueChannel, firstImageOperation, secondImageOperation,
                firstSegOperation, secondSegOperation, offsetX, offsetY, debugImages):

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
        imageFrame = orientImage(frameData[:, :, indexFrame], firstImageOperation, secondImageOperation)

        # skip this image if all the image slice data is black - check max value below a certain point
        maxImageVal = np.max(imageFrame)
        if maxImageVal < 10:
            print('Skipping image %d' % indexFrame)
            continue

        # scale to 0-255, convert to int, and adjust orientation using operations passed in
        segFrame = orientImage((segData[tissueChannel, :, :, indexMask] * 255).astype(np.uint8),
            firstSegOperation, secondSegOperation)

        # check seg frame data also, if nothing present, skip this one
        maxSegVal = np.max(segFrame)
        if maxSegVal < 10:
            print('Skipping seg image %d' % indexMask)
            continue

        # now pad the image to make the seg the same size as the original iamge
        newSegFrame = offsetSegImageInOriginal(segFrame, imageFrame.shape[1], imageFrame.shape[0],
                                               offsetX, offsetY)

        # setup filenames based on how many images are already in the directory
        imageOutName = '%.3d_%s.png' % ((startFileNum + imagesWritten), fileNameAppend)
        overlayOutName = '%.3d_overlay_%s.png' % ((startFileNum + imagesWritten), fileNameAppend)
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
spreadSheetName = 'C:\\Users\\vdinh\\Documents\\MF03_WashU_CCIR_MRIData\\MRI-Table.xlsx'

# top level location of data
topLevelDataPath = 'C:\\Users\\vdinh\\Documents\\MF03_WashU_CCIR_MRIData'

# output path for all the numbered image files
outputPath = 'C:\\Users\\vdinh\\Desktop\\CardiacFatSegmentation\\myData'

# output path for the text file with data orientation/space information
spaceOutputPath = 'C:\\Users\\vdinh\\Desktop\\CardiacFatSegmentation\\myData\\spaceOrientation.txt'

# open the output spacing file
spaceFile = open(spaceOutputPath, 'w')

# lead in the spreadsheet that has the list of names
workbook = openpyxl.load_workbook(spreadSheetName)
worksheet = next(iter(workbook))

# loop through each row and grab out the filenames that are required for both the image data (for the "frames") and
# the segmentations (for the "masks") - min row is 2 as in excel, to start at first scan
for row in worksheet.iter_rows(min_row=2, min_col=1, max_col=26):  # min 1 max 18 for correct column data

    # read the subject ID, prepost string, and offsets for this scan
    subjectID = row[0].value
    prePostString = row[3].value
    edXOffset, edYOffset = row[18].value, row[19].value
    esXOffset, esYOffset = row[20].value, row[21].value

    # read the  image operations from the spreadsheet
    edFirstSegOperation = row[22].value
    edSecondSegOperation = row[23].value
    esFirstSegOperation = row[24].value
    esSecondSegOperation = row[25].value
    edFirstImageOperation = row[14].value
    edSecondImageOperation = row[15].value
    esFirstImageOperation = row[16].value
    esSecondImageOperation = row[17].value

    # blank pre/post string means skip this file
    if prePostString is not None:

        # make the strings to append to filenames for ED and ES images
        appendED = subjectID + '_' + prePostString + '_ED'
        appendES = subjectID + '_' + prePostString + '_ES'

        # if only writing one case
        # SWITCHES FOR END-DIASTOLIC AND END-SYSTOLIC IMAGES HERE, ALONG WITH SUBJECT AND SCAN INFO
        writeES = True
        writeED = True
        whichSubject = 'MF0312'
        whichScan = 'POST'

        # turn this on if only want to handle subject listed above, if false it will do all scans
        # SWITCH TO USE FOR ONLY CHECKING CURRENT SCAN - FOR FINDING OFFSET VALUES AND IMAGE OPERATIONS TO ALIGN
        # IF THIS IS FALSE, EVERYTHING BELOW WITH TEST VALUES SHOULD BE COMMENTED OUT
        checkSubject = False

        # test offset values for this case - from top/left corner origin
        # IF FINDING OFFSET VALUES AND SEG IMAGE OPERATIONS, RESET HERE FOR THIS CASE, OTHERWISE, IT WILL
        # USE WHAT'S READ FROM SPREADSHEET
        # edXOffset, edYOffset = 4, 8
        # esXOffset, esYOffset = 8, 9
        # edFirstSegOperation = 'rot90'
        # edSecondSegOperation = 'fliplr'
        # edFirstImageOperation = 'rot90'
        # edSecondImageOperation = 'fliplr'
        # esFirstSegOperation = 'rot90'
        # esSecondSegOperation = 'fliplr'
        # esFirstImageOperation = 'rot90'
        # esSecondImageOperation = 'fliplr'

        # only proceed if it's the selected scan (use this to determine offsets), or if not checking subjects
        # then proceed always unless there are no offset values in the spreadsheet (checking ed x offset)
        if ((subjectID == whichSubject) and (prePostString == whichScan) and (checkSubject)) or \
                ((not checkSubject) and (edXOffset is not None)):

            # grab the filenames for this scan
            edFileName = topLevelDataPath + '\\' + subjectID + '-' + prePostString + '\\' + row[edFileNameCol].value
            edSegName = topLevelDataPath + '\\' + subjectID + '-' + prePostString + '\\' + row[edSegNameCol].value
            esFileName = topLevelDataPath + '\\' + subjectID + '-' + prePostString + '\\' + row[esFileNameCol].value
            esSegName = topLevelDataPath + '\\' + subjectID + '-' + prePostString + '\\' + row[esSegNameCol].value

            # open each of the image NRRD files and "explode" them into separate image files
            # end-diastole
            edFramePath = outputPath + '\\NumberedFramesED_' + whichTissueFileName
            edSegPath = outputPath + '\\NumberedMasksED_' + whichTissueFileName
            edOverlayPath = outputPath + '\\NumberedOverlaysED_' + whichTissueFileName
            if checkSubject:  # if only finding image ops and offsets, use other directory
                edFramePath = edFramePath + '_test'
                edSegPath = edSegPath + '_test'
                edOverlayPath = edOverlayPath + '_test'
            edFrameData, edFrameHeader = nrrd.read(edFileName)
            edSegData, edSegHeader = nrrd.read(edSegName)

            # end-systole
            esFramePath = outputPath + '\\NumberedFramesES_' + whichTissueFileName
            esSegPath = outputPath + '\\NumberedMasksES_' + whichTissueFileName
            esOverlayPath = outputPath + '\\NumberedOverlaysES_' + whichTissueFileName
            if checkSubject:  # if only finding image ops and offsets, use other directory
                esFramePath = esFramePath + '_test'
                esSegPath = esSegPath + '_test'
                esOverlayPath = esOverlayPath + '_test'
            esFrameData, esFrameHeader = nrrd.read(esFileName)
            esSegData, esSegHeader = nrrd.read(esSegName)

            # read the spacing information from the headers
            edFrameSpace = edFrameHeader.get('space')
            edSegSpace = edSegHeader.get('space')
            esFrameSpace = edFrameHeader.get('space')
            esSegSpace = edSegHeader.get('space')

            # format text line for writing space information
            spaceOutputString = subjectID + ', ' + prePostString +\
                                ', ED image, ' + edFrameSpace + ', ED seg, ' + edSegSpace + '\n'

            # write the output line to space text file
            spaceFile.write(spaceOutputString)

            # write images
            if writeED:
                # get correct tissue "channel" number for this seg file based on which tissue type
                edWhichTissueChannel, edExtents = getTissueChannelAndExtents(edSegHeader, whichTissueFullName)
                writeImages(edFramePath, edFrameData, edSegPath, edSegData, edSegHeader, edOverlayPath,
                            appendED, edWhichTissueChannel, edFirstImageOperation, edSecondImageOperation,
                            edFirstSegOperation, edSecondSegOperation, edXOffset, edYOffset, debugImages=True)
            if writeES:
                # get correct tissue "channel" number for this seg file based on which tissue type
                esWhichTissueChannel, esExtents = getTissueChannelAndExtents(esSegHeader, whichTissueFullName)
                writeImages(esFramePath, esFrameData, esSegPath, esSegData, esSegHeader, esOverlayPath,
                            appendES, esWhichTissueChannel, esFirstImageOperation, esSecondImageOperation,
                            esFirstSegOperation, esSecondSegOperation, esXOffset, esYOffset, debugImages=True)

# close the spacing/orientation output text file
spaceFile.close()
