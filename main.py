from model import *

from data import *


data_gen_args = dict(rotation_range=0.2,
                    width_shift_range=0.05,
                    height_shift_range=0.05,
                    shear_range=0.05,
                    zoom_range=0.05,
                    horizontal_flip=True,
                    fill_mode='nearest')

myGene = trainGenerator(2, 'C:/Users/vdinh/Desktop/CardiacFatSegmentation/myData/Sobel/Train', 'Frames', 'Masks', data_gen_args, save_to_dir=None)
model = unet()
model_checkpoint = ModelCheckpoint('unetOriginal_ED_LM.hdf5', monitor='loss', verbose=1, save_best_only=True)

model.fit_generator(myGene, steps_per_epoch=300, epochs=5, callbacks=[model_checkpoint], verbose=2)

testPath = "C:/Users/vdinh/Desktop/CardiacFatSegmentation/myData/Sobel/Test/Frames"
numTestFrames = len(os.listdir(testPath))
testGene = testGenerator(testPath, numTestFrames)

numTestFrames = len(os.listdir(testPath))

results = model.predict_generator(testGene, numTestFrames, verbose=1)
r = results*255

labelPath = "C:/Users/vdinh/Desktop/CardiacFatSegmentation/myData/Sobel/Label"
if not os.path.exists(labelPath):
    os.mkdir(labelPath)

saveResult(labelPath, r.astype('uint8'))

