import openpyxl

# column numbers for the filenames - 1-based indexing as in excel
edFileNameCol = 5
edSegNameCol = 6
esFileNameCol = 7
esSegNameCol = 8

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
for row in worksheet.iter_rows(min_row=2, min_col=edFileNameCol, max_col=esSegNameCol):

    # grab the filenames for this scan
    edFileName = row[0].value
    edSegName = row[1].value
    esFileName = row[2].value
    esSegName = row[3].value

    # open each of the NRRD files and "explode" them into separate image files

