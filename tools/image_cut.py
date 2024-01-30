import cv2
import os

def crop_image(image_path, start_x, start_y, end_x, end_y):
    imagepath, imagename = os.path.split(image_path)
    imageid, suffix = imagename.split('.')
    img = cv2.imread(image_path)
    cropped_img = img[start_y:end_y, start_x:end_x]
    cv2.imwrite('/home/tianyi/project/ByteTrack/visio/word/'+'{}.jpg'.format(imageid), cropped_img)

if __name__ == '__main__':
    for i in range(76):
        imageid=90+i
        crop_image('/home/tianyi/project/ByteTrack/visio/'+'{:06d}.jpg'.format(imageid), 660,10,1850,940)

