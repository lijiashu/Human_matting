import torch
import torch.nn as nn
import torch.nn.functional as F
import time


def conv_bn_act(inp, oup, kernel_size=3, stride=1, padding=1):
    return nn.Sequential(
        nn.Conv2d(inp, oup, kernel_size, stride, padding, bias=False),
        nn.BatchNorm2d(oup),
        nn.PReLU(oup)
    )
def bn_act(inp):
    return nn.Sequential(
        nn.BatchNorm2d(inp),
        nn.PReLU(inp)
    )
class make_dense(nn.Module):
    def __init__(self, nChannels, growthRate):
        super(make_dense, self).__init__()
        
        self.conv = nn.Conv2d(nChannels, growthRate, kernel_size=3, padding=1, dilation=1, bias=False)#用了膨胀卷积 膨胀率为1相当于没用
        self.bn = nn.BatchNorm2d(growthRate)
        self.act = nn.ReLU(inplace=True)
    def forward(self, x):
        x_ = self.bn(self.conv(x))
        out = self.act(x_)
        out = torch.cat((x, out), 1)
        return out

class DenseBlock(nn.Module):
    def __init__(self, nChannels, nDenselayer, growthRate, reset_channel=False):#第一个参数为通道数  第二个是层数  第三个是每层通道数增加多少
        super(DenseBlock, self).__init__()
        nChannels_ = nChannels
        modules = []
        for i in range(nDenselayer):    
            modules.append(make_dense(nChannels_, growthRate))
            nChannels_ += growthRate 
        self.dense_layers = nn.Sequential(*modules)

    def forward(self, x):
        out = self.dense_layers(x)
        return out
 
# ResidualDenseBlock
class ResidualDenseBlock(nn.Module):
    def __init__(self, nIn, s=4, add=True):

        super(ResidualDenseBlock, self).__init__()

        n = int(nIn//s) 

        self.conv =  nn.Conv2d(nIn, n, 1, stride=1, padding=0, bias=False)#第三个参数是kernel_size
        self.dense_block = DenseBlock(n, nDenselayer=(s-1), growthRate=n)

        self.bn = nn.BatchNorm2d(nIn)  #里面的参数可以理解为通道数也就是特征数 也就通道数
        self.act = nn.PReLU(nIn)

        self.add = add

    def forward(self, input):

        # reduce
        inter = self.conv(input)
        combine =self.dense_block(inter)

        # if residual version
        if self.add:
            combine = input + combine

        output = self.act(self.bn(combine))
        return output
#这个是对图片进行几次下采样 一次两倍 
class InputProjection(nn.Module):

    def __init__(self, samplingTimes):
        '''
        :param samplingTimes: The rate at which you want to down-sample the image
        '''
        super().__init__()
        self.pool = nn.ModuleList()
        for i in range(0, samplingTimes):            
            #pyramid-based approach for down-sampling
            self.pool.append(nn.AvgPool2d(3, stride=2,padding=1))

    def forward(self, input):
        '''
        :param input: Input RGB Image
        :return: down-sampled image (pyramid-based approach)
        '''
        for pool in self.pool:
            input = nn.functional.avg_pool2d(input, 3, stride=2,padding=1)
        return input


# =========================================================================================
# 
# ESP  + Matting
# 
# =========================================================================================

class ERD_SegNet(nn.Module):

    def __init__(self, classes=2):

        super(ERD_SegNet, self).__init__()

        # -----------------------------------------------------------------
        # encoder 
        # ---------------------

        # input cascade
        self.cascade1 = InputProjection(1)    #一次下采样  参数表示二倍
        self.cascade2 = InputProjection(2)
        self.cascade3 = InputProjection(3)
        self.cascade4 = InputProjection(4)
        # 1/2
        self.head_conv = conv_bn_act(3, 12, kernel_size=3, stride=2, padding=1)#下采样通过stride来实现的
        self.stage_0 = ResidualDenseBlock(12, s=3, add=True)

        # 1/4
        self.ba_1 = bn_act(12+3)
        self.down_1 = conv_bn_act(12+3, 24, kernel_size=3, stride=2, padding=1)
        self.stage_1 = ResidualDenseBlock(24, s=3, add=True)
        # 1/8
        self.ba_2 = bn_act(48+3)
        self.down_2 = conv_bn_act(48+3, 48, kernel_size=3, stride=2, padding=1)
        self.stage_2 = ResidualDenseBlock(48, s=3, add=True)
        # 1/16
        self.ba_3 = bn_act(96+3)
        self.down_3 = conv_bn_act(96+3, 96, kernel_size=3, stride=2, padding=1)
        self.stage_3 = nn.Sequential(ResidualDenseBlock(96, s=6, add=True),
                                     ResidualDenseBlock(96, s=6, add=True))
        # 1/32
        self.ba_4 = bn_act(192+3)
        self.down_4 = conv_bn_act(192+3, 192, kernel_size=3, stride=2, padding=1)
        self.stage_4 = nn.Sequential(ResidualDenseBlock(192, s=6, add=True),
                                     ResidualDenseBlock(192, s=6, add=True)) 
     
        # -----------------------------------------------------------------
        # heatmap 
        # ---------------------
        self.classifier = nn.Conv2d(192, classes, 1, stride=1, padding=0, bias=False)

        # -----------------------------------------------------------------
        # decoder 
        # ---------------------

        self.up = nn.Upsample(scale_factor=2, mode='bilinear')#双线性插值每次两倍上采样
        self.prelu = nn.PReLU(classes)

        self.stage3_down = conv_bn_act(96, classes, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(classes)
        self.conv_3 = nn.Conv2d(classes, classes, kernel_size=3, stride=1, padding=1, bias=False)

        self.stage2_down = conv_bn_act(48, classes, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(classes)
        self.conv_2 = nn.Conv2d(classes, classes, kernel_size=3, stride=1, padding=1, bias=False)
 
        self.stage1_down = conv_bn_act(24, classes, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(classes)
        self.conv_1 = nn.Conv2d(classes, classes, kernel_size=3, stride=1, padding=1, bias=False)  

        self.stage0_down = conv_bn_act(12, classes, kernel_size=3, stride=1, padding=1)
        self.bn0 = nn.BatchNorm2d(classes)
        self.conv_0 = nn.Conv2d(classes, classes, kernel_size=3, stride=1, padding=1, bias=False)  
            
        self.last_up = nn.Upsample(scale_factor=2, mode='bilinear')
        
        # init weights
        self._init_weight()
        

    def _init_weight(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, input):
        input_cascade1 = self.cascade1(input)
        input_cascade2 = self.cascade2(input)
        input_cascade3 = self.cascade3(input)
        input_cascade4 = self.cascade4(input)
        
        x = self.head_conv(input)
        # 1/2
        s0 = self.stage_0(x)

        # ---------------
        s1_0 = self.down_1(self.ba_1(torch.cat((input_cascade1, s0),1)))
        s1 = self.stage_1(s1_0)

        # ---------------
        s2_0 = self.down_2(self.ba_2(torch.cat((input_cascade2, s1_0, s1),1)))
        s2 = self.stage_2(s2_0)

        # ---------------
        s3_0 = self.down_3(self.ba_3(torch.cat((input_cascade3, s2_0, s2),1)))
        s3 = self.stage_3(s3_0)

        # ---------------
        s4_0 = self.down_4(self.ba_4(torch.cat((input_cascade4, s3_0, s3),1)))
        s4 = self.stage_4(s4_0)
        # -------------------------------------------------------

        heatmap = self.classifier(s4)
        # -------------------------------------------------------


        heatmap_3 = self.up(heatmap)
        s3_heatmap = self.prelu(self.bn3(self.stage3_down(s3)))#此处用的跳跃结构skip技巧
        heatmap_3 = heatmap_3+ s3_heatmap   #这个是一个普通卷积后加到之前的上面去
        heatmap_3 = self.conv_3(heatmap_3)   
    
        heatmap_2 = self.up(heatmap_3)
        s2_heatmap = self.prelu(self.bn2(self.stage2_down(s2)))
        heatmap_2 = heatmap_2 + s2_heatmap
        heatmap_2 = self.conv_2(heatmap_2)

        heatmap_1 = self.up(heatmap_2)
        s1_heatmap = self.prelu(self.bn1(self.stage1_down(s1)))
        heatmap_1 = heatmap_1 + s1_heatmap
        heatmap_1 = self.conv_1(heatmap_1)        
        
        heatmap_0 = self.up(heatmap_1)
        s0_heatmap = self.prelu(self.bn0(self.stage0_down(s0))) 
        heatmap_0 = heatmap_0 + s0_heatmap
        heatmap_0 = self.conv_0(heatmap_0)   

        out = self.last_up(heatmap_0)

        return out

###################################################################################################
'''

      Segnet + Matting

feature extracter:
                    ERD_SegNet
                    ... ...

Matting:            filter  block

'''

class SegMattingNet(nn.Module):
    def __init__(self):
        super(SegMattingNet, self).__init__()
        self.seg_extract = ERD_SegNet(classes=2)
        # feather
        self.convF1 = nn.Conv2d(in_channels=11, out_channels=8, kernel_size=(3, 3), stride=1, padding=1, dilation=1, groups=1, bias=True)
        self.bn = nn.BatchNorm2d(num_features=8)
        self.ReLU = nn.ReLU(inplace=True)
        self.convF2 = nn.Conv2d(in_channels=8, out_channels=3, kernel_size=(3, 3), stride=1, padding=1, dilation=1, groups=1, bias=True)
        self.sigmoid = nn.Sigmoid()        
        # init weights
        self._init_weight()

    def _init_weight(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)


    def forward(self, x):      
        seg = self.seg_extract(x)   #先分割后matting
        # shape: n 1 h w
        seg_softmax = F.softmax(seg, dim=1)
        
        #seg_softmax[seg_softmax>0.5]=1
        
        bg, fg = torch.split(seg_softmax, 1, dim=1)
        
        # shape: n 3 h w
        imgSqr = x*x 
        imgMasked = x * (torch.cat((fg, fg, fg), 1))
        # shape: n 11 h w
        convIn = torch.cat((x, seg_softmax, imgSqr, imgMasked), 1)
        newconvF1 =  self.ReLU(self.bn(self.convF1(convIn)))
        newconvF2 = self.convF2(newconvF1)
        
        # fethering inputs:
        a, b, c = torch.split(newconvF2, 1, dim=1)

        #print("seg: {}".format(seg))
        alpha = a * fg + b * bg + c        
        alpha = self.sigmoid(alpha)        

        return seg, alpha
#model =SegMattingNet()
#print(model)
#net = SegMattingNet()
# 
#######################################
#params = list(net.parameters())
#k = 0
#for i in params:
#    l = 1
#    print("该层的结构：" + str(list(i.size())))
#    for j in i.size():
#        l *= j
#    print("该层参数和：" + str(l))
#    k = k + l
#print("总参数数量和：" + str(k))