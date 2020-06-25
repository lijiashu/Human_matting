t# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 15:38:04 2019

@author: leilei
"""

import os
#遍历文件夹   
def recurrence(path,file_list):
    for file in os.listdir(path):
        fs = os.path.join(path, file)
        if os.path.isfile(fs):
            file_list.append(fs)
        elif os.path.isdir(fs):
            recurrence(fs, file_list)                    
def main():   
    path_1 = 'D:\\Human_matting\\SImple_segmentation'
    path_2 = 'D:\\EG2000\\test_masks'
    filenames_1 = []  # 带路径的文件名存入列表
    filenames_2 = []
    recurrence(path_1, filenames_1)
    recurrence(path_2, filenames_2)   
    f1 = open("D:\Human_matting\\evalue_accurate.txt", "w")
    for filename_1, filename_2 in zip(filenames_1, filenames_2):  
        newname_1=str(filename_1).replace('\\','/')
        newname_2=str(filename_2).replace('\\','/')
        f1.write(newname_1+' '+newname_2+'\n')
    f1.close() # 要记得关闭！
#    f2 = open("C:\\Users\\Administrator\\Desktop\\Datas\\matting.txt", "w")
#    for filename in filenames_2:
#        f2.write(filename+'\n')
#    f2.close() # 要记得关闭！
#    print(len(filenames_1))
#    print(len(filenames_2))
if __name__ == "__main__":
    main()
    print('finish!!!!')