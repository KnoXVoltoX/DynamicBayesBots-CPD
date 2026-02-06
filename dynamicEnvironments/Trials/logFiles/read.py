import numpy as np

dat = np.load("Dataset_01.npz")
raw = dat["arr_0"]
belive = dat["arr_1"]
time = dat["arr_2"]
print(dat["arr_0"][0],dat["arr_1"][0], dat["arr_2"])
#f = [float(d) for d in dat["arr_0"]]
#print(f)
