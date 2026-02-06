import numpy as np
import fastpelt
from BOCPD import bocd, GaussianUnknownMean
from RuLSIF import RuLSIF, DensityRatio, KernelInfo, to_numpy_matrix, search_sigma_and_lambda, compute_kernel_Gaussian, kernel_Gaussian
import ruptures as rpt
import matplotlib.pyplot as plt
import sys
import time

def BOCPD(data):
    hazard = 1/246#1/283#1/60#1/141#1/256#1/140#1/67  # Constant prior on changepoint probability.
    mean0  = -1.962#-4.246#-5.584#-4.148#9.674#8.483#1.82  # The prior mean on the mean parameter.
    var0   = 4.482#8.461#2.631#3.058#1.445#9.192#7.99  # The prior variance for mean parameter.
    varx   = 0.435#0.202#0.150#0.168#1.092#0.291#0.34  # The known variance of the data.

    model          = GaussianUnknownMean(mean0, var0, varx)
    max_R, R, pmean, pvar = bocd(data, model, hazard)
    cps = np.where(np.diff(max_R)<0)[0]
    return list(cps)#*10)

def RULSIF(data):
    alpha       = 0.796#0.62#0.12
    sig         = [8337.037]
    lam         = [110.945]
    thresh      = 0.338#0.35#0.2
    window_size = 2#5#8
    dens = []
    sum = 0
    data = np.array(data)
    for i in range(2*window_size, len(data)):
        dat1 = data[i-2*window_size:i-window_size]
        dat2 = data[i-window_size:i]
        res = RuLSIF( dat1, dat2, alpha, sig, lam)
        sum += res.compute_density_ratio(1)[0]
        if i%window_size == 0:
            dens.append(np.median(sum))
            sum = 0

    cps = [dens.index(np.max(dens))*window_size]#[dens.index(i)*window_size for i in dens if i >= np.max(dens)-np.max(dens)*thresh]
    return list(np.asarray(cps)*10)

def detectCP(data):
    #PELT
    # bt = time.perf_counter()
    mfast = fastpelt.Pelt(pen=10.680, loss="l1")
    pred = mfast.predict(data)
    pred.pop(-1)
    # at = time.perf_counter()
    # print(len(data), " in time: ", np.around(at-bt, 4))

    #BOCPD
    # bt = time.perf_counter()
    # pred = BOCPD(data)
    # at = time.perf_counter()
    # print(len(data), " in time: ", np.around(at-bt, 4))

    #RuLSIF
    # pred = RULSIF(data)
    # if 0 in pred:
    #     pred.remove(0)

    #BinSeg
    # model = "l2"  # "l1", "rbf", "linear", "normal", "ar",...
    # algo = rpt.Binseg(model=model).fit(np.asarray(data))
    # pred = algo.predict(pen=7)
    # pred.pop(-1)


    # print("Changepoint predicted at:", pred)
    return 1 if len(pred) > 0 else 0#pred #if len(pred) != 0 else 0
