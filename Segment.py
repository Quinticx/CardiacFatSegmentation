from model import *
from PIL import Image
import numpy as np
from data import *

def loadModel(modelName):
    model = unet()
    model.load_weights(modelName)
    return model

def runModel(image, model):
    image = image.reshape((-1, 256, 256, 1))
    results = model.predict(image)
    return 255 * results

modelName = 'unetOriginal.hdf5'

FRAME_PATH = "MyData/Original/Test/Frames"
frames = os.listdir(FRAME_PATH)
j = []
r = []



for i in frames:
    img1 = Image.open(FRAME_PATH + '/' + i)
    img3 = img1.resize((256, 256), Image.ANTIALIAS)
    img = np.asarray(img3)
    model = loadModel(modelName)
    g = runModel(img, model)
    plt.imshow(g[0, :, :, 0])
    plt.show()
    plt.pause(0.5)

    r.append(g)
    j.append(img)


#results = model.predict_generator(testGene, 30, verbose=1)

#saveResult("MyData/Original/Test/label2", r.astype('uint8'))

#img1 = Image.open(FRAME_BLANK_PATH + image)

