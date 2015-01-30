# -*- coding: utf-8 -*-

from threading import Thread
from numpy import concatenate

class Modelo(Thread):
    result = 0
    def __init__(self,param,x,args):
        Thread.__init__(self)
        self.param = param
        self.x     = x

        self.args  = args

    def run(self):
        
        x = self.x

        alpha = self.param[0]
        beta  = self.param[1]
        #gama  = self.param[2]
        #eta   = self.param[3]
        y1 = alpha*(x**beta)
        #y1 = alpha*x/(1+beta*x)
        #y2 = gama*x2  + eta

        self.result = y1