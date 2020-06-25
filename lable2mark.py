# -*- coding: utf-8 -*-
import os
import cv2
path  = "D:\\Human_matting\\portrait_matting\\matts"
os.chdir(path) 
imgList = os.listdir(path)
for img in imgList:
    img_name = img
    img = cv2.imread(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#    ret, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
#    ret, img = cv2.threshold(img, 127, 1,cv2.THRESH_BINARY_INV)
    img = 1-img/225  

    cv2.imwrite("D:\\Human_matting\\portrait_matting\\alphas\\" + img_name[0:-3] + "png", img)	

print ("done!")


