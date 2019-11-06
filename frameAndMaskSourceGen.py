import os
import openpyxl
import numpy as np
import nrrd
import imageio

# function to take in nrrd image and seg data and write out individual image filenames
# - checks to see how many files are already in the folder and uses that as the starting number
def writeImages(framePath, frameData, segPath, segData, segHeader, tissueChannel):

    # check to see if path exists, and if not create it
    if not os.path.exists(framePath):
        os.mkdir(framePath)
    if not os.path.exists(segPath):
        os.mkdir(segPath)

    # TODO skip this set if the image is not cropped - just do simple check on size (maybe around 150?)
    # TODO skip this set if all the image slice data is black - check max value below a certain point

    # count files in each path
    namesFramePath = os.listdir(framePath)
    numFilesInFramePath = len(namesFramePath)
    # numFilesInFramePath = len([name for name in os.listdir(framePath) if os.path.isfile(name)])
    namesMaskPath = os.listdir(segPath)
    numFilesInMaskPath = len(namesMaskPath)
    # numFilesInMaskPath = len([name for name in os.listdir(segPath) if os.path.isfile(name)])
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
    for ii in range(0, numSegSlices):

        # compute index values to use for grabbing data from both regular image volume for frames
        # and segmented volume for masks
        indexMask = ii
        indexFrame = indexMask + segOffsetFrameIndex

        # extract out the image data for each slice to write to file
        # imageFrame = frameData[:, :, ii].astype(np.uint8)
        imageFrame = frameData[:, :, ii]
        segFrame = (segData[tissueChannel, :, :, ii] * 255).astype(np.uint8)  # scale to 0-255

        # setup filenames based on how many images are already in the directory
        imageOutName = '%.3d.png' % (startFileNum + ii)
        segOutNameFullPath = segPath + '\\' + imageOutName
        imageOutNameFullPath = framePath + '\\' + imageOutName

        # write out the images
        imageio.imwrite(segOutNameFullPath, segFrame)
        imageio.imwrite(imageOutNameFullPath, imageFrame)


# parses each channel in seg.nrrd and returns the zero-based number of the channel based on matching
# the name string
def getTissueChannel(segHeader, whichTissueFullName):

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

    return numSeg


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

        # get correct tissue "channel" number for this seg file based on which tissue type
        whichTissueChannel = getTissueChannel(segHeader, whichTissueFullName)

        writeImages(framePath, frameData, segPath, segData, segHeader, whichTissueChannel)
