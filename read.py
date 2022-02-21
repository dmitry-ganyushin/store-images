import numpy as np
import openslide
import sys
import os
import getopt
import time
from PIL import Image

NOADIOS = False
try:
    import adios2
except ImportError:
    NOADIOS = True


slide_name = sys.argv[2] + '/' + sys.argv[1]
output_folder = sys.argv[3] + '/' + sys.argv[1]
patch_size_20X = 1000

def main(input_type):
    print("slide name {}".format(slide_name))
    print("output folder {}".format(output_folder))
    fdone = '{}/extraction_done.txt'.format(output_folder)
    if os.path.isfile(fdone):
        print('fdone {} exist, skipping'.format(fdone))
        exit(0)

    print('extracting {}'.format(output_folder))

    if input_type is not "adios2":	
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

    try:
        oslide = openslide.OpenSlide(slide_name)
    #    mag = 10.0 / float(oslide.properties[openslide.PROPERTY_NAME_MPP_X]);
        if openslide.PROPERTY_NAME_MPP_X in oslide.properties:
           mag = 10.0 / float(oslide.properties[openslide.PROPERTY_NAME_MPP_X])
        elif "XResolution" in oslide.properties:
           mag = 10.0 / float(oslide.properties["XResolution"])
        elif 'tiff.XResolution' in oslide.properties:   # for Multiplex IHC WSIs, .tiff images
           mag = 10.0 / float(oslide.properties["tiff.XResolution"])
        else:
           mag = 10.0 / float(0.254)
        pw = int(patch_size_20X * mag / 20)
        width = oslide.dimensions[0]
        height = oslide.dimensions[1]
    except:
        print('{}: exception caught'.format(slide_name))
        exit(1)


    print(slide_name, width, height)

    if input_type is not "adios2":

        for x in range(1, width, pw):
            for y in range(1, height, pw):
                if x + pw > width:
                    pw_x = width - x
                else:
                    pw_x = pw
                if y + pw > height:
                    pw_y = height - y
                else:
                    pw_y = pw

                if (int(patch_size_20X * pw_x / pw) <= 0) or \
                   (int(patch_size_20X * pw_y / pw) <= 0) or \
                   (pw_x <= 0) or (pw_y <= 0):
                    continue

                patch = oslide.read_region((x, y), 0, (pw_x, pw_y))
                #shahira: skip where the alpha channel is zero
                patch_arr = np.array(patch)
                if(patch_arr[:,:,3].max() == 0):
                    continue

                # Resize into 20X.
                patch = patch.resize((int(patch_size_20X * pw_x / pw), int(patch_size_20X * pw_y / pw)), Image.ANTIALIAS)
                fname = '{}/{}_{}_{}_{}.png'.format(output_folder, x, y, pw, patch_size_20X)
                patch.save(fname)

        open(fdone, 'w').close()
    else:
        iotime = 0
        with adios2.open( output_folder + ".bp", "w") as fh:
            for x in range(1, width, pw):
                for y in range(1, height, pw):
                    if x + pw > width:
                        pw_x = width - x
                    else:
                        pw_x = pw
                    if y + pw > height:
                        pw_y = height - y
                    else:
                        pw_y = pw

                    if (int(patch_size_20X * pw_x / pw) <= 0) or \
                       (int(patch_size_20X * pw_y / pw) <= 0) or \
                       (pw_x <= 0) or (pw_y <= 0):
                        continue

                    patch = oslide.read_region((x, y), 0, (pw_x, pw_y))
                    #shahira: skip where the alpha channel is zero
                    patch_arr = np.array(patch)
                    if(patch_arr[:,:,3].max() == 0):
                        continue

                    # Resize into 20X.
                    patch = patch.resize((int(patch_size_20X * pw_x / pw), int(patch_size_20X * pw_y / pw)), Image.ANTIALIAS)
                    patch_arr = np.array(patch)
                    nx = patch_arr.shape[0]
                    ny = patch_arr.shape[1]
                    shape = [nx, ny, 3]
                    start = [0, 0, 0]
                    count = [nx, ny, 3]
                    fname = '{}_{}_{}_{}.png'.format(x, y, pw, patch_size_20X)
                    print("writing :" + fname)
                     
                    t0 = time.perf_counter()
                    fh.write(fname, patch_arr, shape, start, count)
                    iotime = iotime + time.perf_counter() -t0
        print("IO writing time = {} sec".format(iotime))


def printUsage():
    print("Options: --input=adios ")
    return

if __name__ == "__main__":
    INPUT_TYPE = None
    t0 = time.perf_counter()
    main("adios2")
    print('Execution time {} sec'.format(time.perf_counter() - t0 ))
    #TODODG exit codes for diagnostic
    sys.exit(0)
