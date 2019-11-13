from model import *

from data import *


data_gen_args = dict(rotation_range=0.2,
                    width_shift_range=0.05,
                    height_shift_range=0.05,
                    shear_range=0.05,
                    zoom_range=0.05,
                    horizontal_flip=True,
                    fill_mode='nearest')

myGene = trainGenerator(2, 'myData/Original/Train', 'Frames', 'Masks', data_gen_args, save_to_dir=None)
model = unet()
model_checkpoint = ModelCheckpoint('unetOriginal_ED_LM.hdf5', monitor='loss', verbose=1, save_best_only=True)

model.fit_generator(myGene, steps_per_epoch=75, epochs=2, callbacks=[model_checkpoint])

testPath = "MyData/Original/Test/Frames"
testGene = testGenerator(testPath)

numTestFrames = len(os.listdir(testPath))

results = model.predict_generator(testGene, numTestFrames, verbose=1)
r = results*255

labelPath = "MyData/Original/Test/Label"
if not os.path.exists(labelPath):
    os.mkdir(labelPath)

saveResult(labelPath, r.astype('uint8'))

