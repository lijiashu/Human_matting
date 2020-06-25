# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 15:43:36 2019

@author: Administrator
"""

import numpy as np
import cv2 as cv

def compute_iou(gt, pt):
    gt = cv.imread(gt)/255
    pt = cv.imread(pt)/255
    intersection = np.sum(gt * pt)
    u = gt + pt
    u[u > 1] = 1
    union = np.sum(u)
    return intersection / union



# coding:utf-8
iou = 0.0
with open("D:\Human_matting\\evalue_accurate.txt", "r") as f:
    for line in f.readlines():
        data = line.split('\n\t')
        path = data[0].split(' ')
        pt = path[0]
        gt = path[1].split('\n')
        gt = gt[0]     
        img = cv.imread(pt)
        iou += compute_iou(pt,gt)
        
miou = iou /300

print(miou)




#iou = compute_iou(pt,gt)


    
