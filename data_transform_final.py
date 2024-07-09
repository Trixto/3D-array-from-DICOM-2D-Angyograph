import numpy as np
import pydicom
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from skimage.transform import iradon
from matplotlib.colors import ListedColormap
import pandas as pd
import napari
import cv2 as cv
from pathlib import Path
import threading
import time


def openDICOMFileDialog():
		
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename()
        root.destroy()

        return path


def levels_with_gamma(input_image, black_input, white_input, black_output, white_output, gamma):
    # Aplikácia vzorca
    output_image = ((input_image - black_input) / (white_input - black_input)) ** gamma
    output_image = output_image * (white_output - black_output) + black_output

    # Obmedzenie hodnôt do rozsahu 0-255
    output_image = np.clip(output_image, 0, 1)

    return output_image

def worker (ii,barrier,rozlisenie):
    
    print(f"Thread {ii} is waiting at the barrier")
    barrier.wait()  # Wait for all threads to reach the barrier
    print(f"Thread {ii} is now performing calculations")
    
    tmp = np.array(img1[:,ii,:]).T
    reconstruction_img = iradon(tmp[:,:], theta=thetas, filter_name='ramp')
    
    k=np.min(reconstruction_img[160:850,160:850])*-1
    normal_image =(reconstruction_img[160:850,160:850]+k)/np.max(reconstruction_img[160:850,160:850])
    # Predpokladajme, že máme vstupný obrázok `input_image` a hodnoty pre levels sú:
    black_input = 0
    white_input = 1
    black_output = 1-155/255
    white_output = 200/255
    gamma = 0.5
    
    # Aplikujeme funkciu na vstupný obrázok
    output_image = levels_with_gamma(normal_image, black_input, white_input, black_output, white_output, gamma)
    invert_image =1-output_image
    
    resized_image = cv.resize(invert_image, (rozlisenie, rozlisenie),interpolation = cv.INTER_AREA)
    full3D[ii]=resized_image






dicomFile = openDICOMFileDialog()
ds = pydicom.read_file(dicomFile)
img1 = ds.pixel_array
theta = ds.PositionerPrimaryAngleIncrement._list
thetas=[]
rozlisenie=128
full3D=np.empty(shape=(1024, rozlisenie,rozlisenie), dtype='object')
novySinogram=[]

for k in range (122):
    temp=theta[k]+(0.19*k)
    thetas.append(temp)

for start in range(4):
    barrier = threading.Barrier(256)        
    threads = [threading.Thread(target=worker, args=(i,barrier,rozlisenie)) for i in range(start*256,(start+1)*256,1)]
    [thread.start() for thread in threads]
    
     # Waiting for all threads to finish
    [thread.join() for thread in threads]

full3D_notscale = full3D.astype(np.float32)  

scaled_data_avg = np.mean(np.array(full3D).T.reshape(rozlisenie, rozlisenie, rozlisenie, 8), axis=3)
scaled_data_avg = scaled_data_avg.astype(np.float32)

scaled_data_maxpool = np.max(np.array(full3D).T.reshape(rozlisenie, rozlisenie, rozlisenie, 8), axis=3)
scaled_data_maxpool = scaled_data_maxpool.astype(np.float32)
# Reshape the array to the new shape


bez=np.max(np.array(full3D[:384]).T.reshape(rozlisenie, rozlisenie, rozlisenie, 3), axis=3)
z=np.max(np.array(full3D[384:]).T.reshape(rozlisenie, rozlisenie, rozlisenie, 5), axis=3)



# np.save("bez", bez)
# np.save("z", z)

# bez=bez.astype(np.float32)
# z=z.astype(np.float32)
# # Open a Napari viewer
viewer = napari.Viewer() 

# # Add your scaled data to the viewer
viewer.add_image(bez)  # or scaled_data_maxpool

# Run the Napari viewer
napari.run()