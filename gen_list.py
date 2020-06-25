# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 17:04:42 2019

@author: Administrator
"""
import os

color_img_path = 'D:\\Human_matting\\portrait_matting\\\images\\'
label_img_path = 'D:\\Human_matting\\portrait_matting\\masks\\'
alpha_imag_paht = 'D:\\Human_matting\\portrait_matting\\alphas\\'

imgs = os.listdir(color_img_path)
limgs = os.listdir(label_img_path)
alphas = os.listdir(alpha_imag_paht)

f = open('D:\\Human_matting\\portrait_matting\\train.txt', 'w')

       
imgs.sort(key=str.lower)
limgs.sort(key=str.lower)
alphas.sort(key=str.lower)
for img, limg,alph in zip(imgs, limgs,alphas):
     f.write('portrait_matting/images/' + img + ' ' + 'portrait_matting/masks/' + limg +' '+'portrait_matting/alphas/'+alph+ '\n')
   

f.close()
print('finish!!!')
