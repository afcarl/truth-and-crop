import cv2  # Tested with opencv version 3.0.0.
import os.path
import numpy as np
import argparse
import matplotlib.pyplot as plt
from colorama import Fore, Back, Style
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries

import sys
from PyQt4 import QtCore, QtGui, uic

qtCreatorFile = "truth_and_crop.ui"

#  Constants
APP_NAME = 'Truth and Crop'
IMAGES_OUT_DIR = 'images/'
MASKS_OUT_DIR = 'masks/'
IMAGE_EXT = '.jpg'
MASK_EXT = '_mask.jpg'
PX_INTENSITY = 0.4
N_CHANNELS = 2

#  Globals
drawing = False  # Set to True if not cropping.
cropping = False  # Press 'm' to toggle, if True, draw rectangle.
ix, iy = -1, -1
w = 0

crop_list = []
class_label = 0
drawing_list = []


def color_superpixel_by_class(x, y, class_label):
    """Color superpixel according to class_label

    Keyword arguments:
    x,y -- pixel coordinates from MouseCallback
    class_label -- determines channel (B,G,R) whose intensity to set
    """
    global segments
    img[:, :, N_CHANNELS - class_label][segments == segments[y, x]] = PX_INTENSITY


def handle_mouse_events(event, x, y, flags, param):
    """Perform ground truthing, and select areas to crop via MouseCallback

    Keyword arguments:
    event -- mouse event type, (e.g moving, left/right click)
    x,y -- current mouse coordinates
    """
    global w, drawing, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        # If we are cropping, we are not truthing.
        if cropping == True:
            drawing = False
            cv2.rectangle(img, (x - w, y - w), (x + w, y + w), (0, 255, 0), 3)
            crop_list.append((x, y))

        # We are ground truthing.
        else:
            drawing = True
            drawing_list.append((x, y, class_label))
            color_superpixel_by_class(x, y, class_label)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            drawing_list.append((x, y, class_label))
            color_superpixel_by_class(x, y, class_label)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False


Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
 
class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        #self.calc_tax_button.clicked.connect(self.CalculateTax)
        self.dial.setMinimum=0
        self.dial.setMaximum=10
        self.lcdNumber.setDecMode()
        self.dial.valueChanged.connect(self.getDial)
            

    def getDial(self):
        #price = int(self.price_box.toPlainText())
        #tax = (self.tax_rate.value())
        self.lcdNumber.display(self.dial.value())   
 
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

'''
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('img_path', help="path to image to be ground-truthed")
    parser.add_argument(
        'img_name', help="name of image to be ground-truthed")
    parser.add_argument(
        'out_path', help="root path to save resulting cropped image/mask pairs")
    parser.add_argument('--wnd', type=int,
                        help="square crop size / 2 in pixels", default=112)
    parser.add_argument(
        '--ds', type=int, help="image down-sampling factor", default=1)
    parser.add_argument(
        '--nseg', type=int, help="number of superpixel segments for SLIC", default=1000)
    parser.add_argument('--sigma', type=int,
                        help="gaussian smoothing parameter for SLIC", default=3)
    args = parser.parse_args()
    w = args.wnd

    input_file = os.path.join(args.img_path, args.img_name)

    img = cv2.imread(input_file)[::args.ds, ::args.ds, :].astype(np.uint8)

    # Copy original so we don't capture box outlines in cropped images.
    original = img.copy()

    # Initialize segmentation mask as "other" class.
    segmentation_mask = np.zeros(img[:, :, 0].shape)

    segments = slic(img, n_segments=200, sigma=3, \
    	enforce_connectivity=True, compactness=20)
    img = mark_boundaries(img, segments, color=(0, 0, 0))

    cv2.namedWindow(APP_NAME)
    cv2.setMouseCallback(APP_NAME, handle_mouse_events)

    while(1):

        cv2.imshow(APP_NAME, img)
        key = cv2.waitKey(1) & 0xFF

        # 'm' - Change mode from cropping to drawing.
        if key == ord('m'):
            cropping = not cropping
            if cropping == True:
                print('Currently cropping.')
            else:
                print('Currently ground-truthing, use number keys to choose class.')

        # 'w' - Write all cropped regions and their segmentation masks'.
        elif key == ord('w'):

            for px, py, p_class in drawing_list:

                # Find superpixel that coord belongs to.
                super_px = segments[py, px]

                # Set all pixels in super_px to p_class.
                segmentation_mask[segments == super_px] = p_class

            i = 0
            for x, y in crop_list:

                # Detailed cropped image suffix.
                details = args.img_name[:-4] + '_nseg' + str(args.nseg) + '_sig' + str(args.sigma) \
                    + '_ds' + str(args.ds) + '_' + str(i) + \
                    "_x" + str(x) + "_y" + str(y)

                height, width, _ = original.shape

                if y - w > 0 and y + w < height and x - w > 0 and x + w < width:

                    cropped_image = original[y - w:y + w, x - w:x + w, :]
                    cropped_mask = segmentation_mask[y - w:y + w, x - w:x + w]

                    image_path = os.path.join(args.out_path, IMAGES_OUT_DIR)
                    mask_path = os.path.join(args.out_path, MASKS_OUT_DIR)

                    if not os.path.exists(image_path):
                        os.makedirs(image_path)

                    if not os.path.exists(mask_path):
                        os.makedirs(mask_path)

                    cv2.imwrite(os.path.join(
                        image_path, details + IMAGE_EXT), cropped_image)
                    cv2.imwrite(os.path.join(
                        mask_path, details + IMAGE_EXT), cropped_mask)

                    print('Success: cropped image at x=%d,y=%d with wnd=%d' %
                          (x, y, w))

                else:
                    print(Fore.RED + 'Error: exceeded image dimensions, could not crop at x=%d,y=%d with wnd=%d' % (
                        x, y, w))
                    print(Style.RESET_ALL)

                i += 1

        elif key == 's':
            plt.close('all')
            cv2.destroyAllWindows()
            fig = plt.figure()
            plt.imshow(segmentation_mask)
            plt.show()
            print("Showing segmentation mask.")

        # '0' - Change to class 0.
        elif key == ord('0'):
            class_label = 0
            print("Selected class 0.")

        # '1' - Change to class 1.
        elif key == ord('1'):
            class_label = 1
            print("Selected class 1.")

        # '2' - Change to class 2.
        elif key == ord('2'):
            class_label = 2
            print("Selected class 2.")

        # 'q' - Quit, potentially without writing.
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()
'''