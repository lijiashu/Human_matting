# -*- coding: utf-8 -*-
import os

 
filepath = "C:\\Users\\Administrator\\Desktop\\Human_matting\\portrait_matting\\\clip_img"  # 文件夹路径
 
if __name__ == "__main__":
 
    if not os.path.exists(filepath):
 
        print("目录不存在!!") 
        os._exit(1) 
    filenames = os.listdir(filepath) 
    name_1=[]
    for i in range(len(filenames)):
        name_1.append(i)
    print("文件数目为%i" %len(filenames)) 
    count=0

    for name in filenames:         
        # newname = 'data'+name  # 若想要在名字前面加字符段，可用此语句
        n=name_1[count]
        newname =str(n)+'.jpg'
        os.rename(filepath + '\\' + name, filepath + '\\' + newname)
        count+=1    
 

print('finish') 

 
