import h5py
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
from pylab import *

def h5_structure(h5_group, show_attrs=True, show_data=False):
    """
    Recursively print the tree structure of an HDF5 file or group
    """
    sep = '| '

    def print_group_structure(h5_group, str_prefix):
        for name, group in h5_group.items():
            if isinstance(group, h5py.Dataset):
                if show_data:
                    print(str_prefix + name + ": " + str(group[...]))
                else:
                    print(str_prefix + str(group))
                if show_attrs:
                    print_attributes(group, str_prefix + sep)
            else:
                print(str_prefix + name)
                print_group_structure(group, str_prefix+sep)

    def print_attributes(dset, str_prefix):
        for k, v in dset.attrs.items():
            print(str_prefix, k, ':', v)

    print_group_structure(h5_group, '')


if __name__ == "__main__":
    h5_in = []
    filenames = []
    filename = "init"
    print("!!!Be careful to combine only logfiles with the same trial duration and logintervals!!!")
    while filename != "":
        if filename == "init":
            print("\nPlease enter h5-data filename:")
        else:
            print("\nPlease enter the next h5-data filename to evaluate with:")
        filename = str(input())
        if filename != "":
            h5_in.append(h5py.File(filename, 'r'))
            filenames.append(str(filename))

    ParamsName = ""
    boxPltParams = []                                         # parameter sets an x-axis
    boxPltMaxAcc = []                                         # boxplot the max accuracy of each trial new box for each parameter set
    boxPltMaxSpeed = []                                       # count how often threshold is reached in each environment
    boxPltThreshCount = []

    for file in h5_in:
        name = (filenames[h5_in.index(file)][:-3])            # logfile name without data type
        os.mkdir("DATA_READ/"+name)
        ParamsName = name.split("_")[3].split("=")[0]
        boxPltParams.append(name.split("_")[3].split("=")[1]) # splits the string into param names logfile names have to be named uniformly split with "_"
        h5_structure(file, show_attrs=False, show_data=False)
        data_set = np.zeros((10,6))
        boxPlt = []
        MaxAccData = []
        MaxSpeedData = []
        ThreshReachData = []
        for i in range(0,file['trial_1/params/num_trials'][...]):
            # Get the dataset of trial:
            data_set = file['trial_'+str(i+1)]
            amount_intervals = 1+(data_set['params/num_environments'][...]-1)*3
            time_interval = (data_set['params/trial_duration'][...])/amount_intervals

            # Plot the mean decision:
            fig, ax = plt.subplots( nrows=1, ncols=1 )
            ax.bar(data_set['time'][:], data_set['mean_robot_decision'][:][:,0], 4, label="Undecided", color='gray')
            ax.bar(data_set['time'][:], data_set['mean_robot_decision'][:][:,2], 4, bottom=data_set['mean_robot_decision'][:][:,0], label="Black", color="red")
            ax.bar(data_set['time'][:], data_set['mean_robot_decision'][:][:,1], 4, bottom=(data_set['mean_robot_decision'][:][:,0]+data_set['mean_robot_decision'][:][:,2]), label="White", color='blue')
            # ax.legend();
            # plt.title("Decision of "+ str(data_set['params/num_robots'][...])+" Robots")
            plt.xlabel('timestep [$t$]')
            plt.ylabel('decision [$d_f$]')
            plt.savefig("DATA_READ/"+name+'/Trial_'+str(i)+' Mean Decision of Robots.pdf')
            plt.close(fig="all")

            # Histograms
            # #plot the belief histogram:
            # print("\n\nOf which Log-interval do you want to create the Decision-Histogram?\n(Please choose a number between 0 and ",data_set['robots_decision'].size-1,")")
            # num = int(input())
            # print("Data Hist",num,":\n", data_set['robots_decision'][num][:])
            # fig, ax = plt.subplots( nrows=1, ncols=1 )
            # plt.hist(data_set['robots_decision'][num][:], bins = 20)
            # plt.xlim([0, 1])
            # plt.ylim([0, 100])
            # plt.title("Histogram of Beliefs at Log-Interval "+str(num))
            # plt.xlabel('Beliefed Ratio of Tiles')
            # plt.ylabel('Amount of Robots [%]')
            # plt.tight_layout()
            # plt.savefig("DATA_READ/"+name+'/Trial_'+str(i)+' Histogram of Decision.pdf')
            # plt.close(fig="all")
            #
            # #plot the reset histogram:
            # print("\n\nOf which Log-interval do you want to create the Reset-Histogram?\n(Please choose a number between 0 and ",data_set['robots_reset'].size-1,")")
            # num = int(input())
            # res_data = np.array(data_set['robots_reset'][num][:]).astype(int)
            # print("Data Hist",num,":\n", data_set['robots_reset'][num][:])
            # fig, ax = plt.subplots( nrows=1, ncols=1 )
            # plt.hist(res_data, bins = 20)
            # plt.xlim([0, 5])
            # plt.ylim([0, 100])
            # plt.title("Histogram of Resets at Log-Interval "+str(num))
            # plt.xlabel('Resets [$CountR$]')
            # plt.ylabel('Amount of Robots [%]')
            # plt.tight_layout()
            # plt.savefig("DATA_READ/"+name+'/Trial_'+str(i)+' Histogram of Reset.pdf')
            # plt.close(fig="all")

            # Plot mean belief of the swarm:
            fig1, ax1 = plt.subplots( nrows=1, ncols=1 )
            ax1.plot(data_set['time'][:], 1-data_set['mean_believed_ratio'][:])
            plt.ylim([0, 1])
            ax1.axhline(0.5, color='gray')
            ax1.axhline(data_set['params/credibleThreshold'][...], color='blue', label="threshold $p_c$ mostly white")
            ax1.axhline((1-data_set['params/credibleThreshold'][...]), color='red', label="threshold $p_c$ mostly black")
            new_interval = time_interval
            for j in range(1, data_set['params/num_environments'][...]):
                ax1.axvline(data_set['params/environmentChange'][...]*j, linestyle='--', color='lightgray', label="environment change")
            #ax1.legend();
            # plt.title("Believed Ratio of "+ str(data_set['params/num_robots'][...])+" Robots")
            plt.xlabel('timestep [$t$]')
            plt.ylabel('belived fill ratio [$f$]')
            ax1.spines['left'].set_position(('data', 0))
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.set_axisbelow(True)
            plt.tight_layout()

            # Get speed and accuracy
            data = np.array(1-data_set['mean_believed_ratio'][:])
            time = np.array(data_set['time'][:])
            change = int(data_set['params/environmentChange'][...])

            accuracy_thresh = []
            accuracy_best = []
            accuracy_time = []

            for c in range(0, data_set['params/num_environments'][...]):

                if c%2 == 0:
                    ind_control = np.where((time[:]>change*c)&(time[:]<change*(c+1))&(data[:]>0.95))[0]                 # could be adapted with the p_cred thresold data
                    if ind_control.size != 0:
                        accuracy_thresh.append(ind_control[0])
                    else:
                        accuracy_thresh.append(-1)
                    accuracy_best.append(np.max(data[np.where((time[:]>change*c)&(time[:]<change*(c+1)))[0]]))

                    if accuracy_thresh[c] != -1:
                        accuracy_time.append(time[int(accuracy_thresh[c])]-data_set['params/environmentChange'][...]*c)
                        a = str(str(c+1)+". Threshold reached after "+str(accuracy_time[c])+"s.\nMax Accuracy"+str(c+1)+": "+str(np.around(accuracy_best[c],3))+" reached after "+str(time[np.where((time[:]>change*c)&(time[:]<change*(c+1))&(data[:]==accuracy_best[c]))[0]][0])+"s.")
                    else:
                        accuracy_time.append(-1)
                        a = str(str(c+1)+". Threshold not reached!\nMax Accuracy"+str(c+1)+": "+str(np.around(accuracy_best[c],3))+" reached after "+str(time[np.where((time[:]>change*c)&(time[:]<change*(c+1))&(data[:]==accuracy_best[c]))[0]][0])+"s.")

                # If odd we search for the lowest value instead of the highest
                else:
                    ind_control = np.where((time[:]>change*c)&(time[:]<change*(c+1))&(data[:]<0.05))[0]
                    if ind_control.size != 0:
                        accuracy_thresh.append(ind_control[0])
                    else:
                        accuracy_thresh.append(-1)
                    accuracy_best.append(np.min(data[np.where((time[:]>change*c)&(time[:]<change*(c+1)))[0]]))

                    if accuracy_thresh[c] != -1:
                        accuracy_time.append(time[int(accuracy_thresh[c])]-data_set['params/environmentChange'][...]*c)
                        a = str(str(c+1)+". Threshold reached after "+str(accuracy_time[c])+"s.\nMax Accuracy"+str(c+1)+": "+str(np.around(accuracy_best[c],3))+" reached after "+str(time[np.where((time[:]>change*c)&(time[:]<change*(c+1))&(data[:]==accuracy_best[c]))[0]][0])+"s.")
                    else:
                        accuracy_time.append(-1)
                        a = str(str(c+1)+". Threshold not reached!\nMax Accuracy"+str(c+1)+": "+str(np.around(1-accuracy_best[c],3))+" reached after "+str(time[np.where((time[:]>change*c)&(time[:]<change*(c+1))&(data[:]==accuracy_best[c]))[0]][0])+"s.")

                gca().set_position((.12, .32, .8, .6))
                figtext(.05, .19-(c*0.08), a)
            MaxAccData.append(accuracy_best)
            ThreshReachData.append(accuracy_thresh)
            MaxSpeedData.append(accuracy_time)
            plt.savefig("DATA_READ/"+name+'/Trial_'+str(i)+' Believed Ratio of Robots.pdf')
            plt.close(fig="all")

        #create Boxplot of the trial believes
            n=0
            dataBox = np.array(ones(40))
            for l in range(0,len(data)):
                if l%(int(len(data)/40)) == 0:
                    dataBox[n]= data[l]
                    n+=1
            boxPlt.append(dataBox)

        boxData = []
        boxTime = []
        for i in range(0,40):
            dataBox = np.array(ones(file['trial_1/params/num_trials'][...]))
            boxTime.append(int(i*(data_set['params/trial_duration'][...]/40)))
            for j in range(0,len(boxPlt)):
                dataBox[j] = boxPlt[j][i]
            boxData.append(dataBox)
        boxTime.append(int(data_set['params/trial_duration'][...]))


        fig3, ax3 = plt.subplots(nrows=1, ncols=1 )
        ax3.boxplot(boxData)
        plt.xticks(np.arange(41),boxTime, rotation=-45)
        for label in ax3.xaxis.get_ticklabels()[1::2]:
            label.set_visible(False)
        plt.ylim([0, 1])
        ax3.axhline(0.5, color='gray')
        ax3.axhline(data_set['params/credibleThreshold'][...], color='blue', label="threshold $p_c$ mostly white")
        ax3.axhline((1-data_set['params/credibleThreshold'][...]), color='red', label="threshold $p_c$ mostly black")
        for j in range(1, data_set['params/num_environments'][...]):
            ax3.axvline((len(boxData)/data_set['params/num_environments'][...])*j, linestyle='--', color='lightgray', label="environment change")
        plt.xlabel("time in [$s$]")
        plt.ylabel("belived fill ratio [$f$]")
        plt.tight_layout()
        plt.savefig("DATA_READ/"+name+'/Boxplot_of_Trials.pdf')

        file.close()

        # evaluate here the multiple logfiles
        boxPltMaxAcc.append(MaxAccData)
        boxPltThreshCount.append(ThreshReachData)
        boxPltMaxSpeed.append(MaxSpeedData)

    fig4, ax4 = plt.subplots(nrows=1, ncols=1 )
    temp3 = []
    for x in boxPltMaxAcc:
        temp1 = []
        temp2 = []
        for y in x:
            temp1.append(y[0])
            temp2.append(1-y[1])
        temp3.append([temp1,temp2])

    space = 0.15
    for x in range(0,len(temp3)):
        bp1=ax4.boxplot(temp3[x][0], positions=[x-space], widths=0.2, patch_artist=True,
                    boxprops=dict(facecolor='gold'), medianprops = dict(color='black'))
        bp2=ax4.boxplot(temp3[x][1], positions=[x+space], widths=0.2, patch_artist=True,
                    boxprops=dict(facecolor='orange'), medianprops = dict(color='black'))

    labelsize = 12
    plt.xticks(rotation="horizontal")
    ax4.set_xticks(np.arange(len(temp3)))
    ax4.set_xticklabels([f'{label}' for label in boxPltParams])
    plt.xlabel("sample limit [$p_{lim}$]" if ParamsName == "sampleLimit" else ParamsName)
    ax4.tick_params(axis='x', labelsize=labelsize)
    ax4.legend([bp1["boxes"][0], bp2["boxes"][0]], ['Environment 1', 'Environment 2'], loc='lower right')
    plt.ylabel("maximal accuracy")
    #ax4.set_ylim(top=1)
    ax4.set_ylim([0.5,1])
    plt.tight_layout()
    plt.savefig('DATA_READ/Boxplot_max_Accuracy_over'+ParamsName+'.pdf')


    fig5, ax5 = plt.subplots(nrows=1, ncols=1 )
    temp3 = []
    temp4 = []
    for x, z in zip(boxPltMaxSpeed,boxPltThreshCount):
        temp1 = []
        temp2 = []
        tempcount1 = 0
        tempcount2 = 0
        for y, t in zip(x,z):
            if y[0] !=-1:
                temp1.append(y[0])
            if y[1] !=-1:
                temp2.append(y[1])
            if t[0] !=-1:
                tempcount1 += 1
            if t[1] !=-1:
                tempcount2 += 1
        temp3.append([temp1,temp2])
        temp4.append([int(tempcount1), int(tempcount2)])

    space = 0.15
    width = 0.2
    ax6 = ax5.twinx()
    for x in range(0,len(temp3)):
        rects1 = ax6.bar(x - width, temp4[x][0], width, color='gold', alpha=0.6)
        rects2 = ax6.bar(x + width, temp4[x][1], width, color='orange', alpha=0.6)

        bp1 = ax5.boxplot(temp3[x][0], positions=[x-space], widths=0.2, patch_artist=True,
                    boxprops=dict(facecolor='gold'), medianprops = dict(color='black'))
        bp2 = ax5.boxplot(temp3[x][1], positions=[x+space], widths=0.2, patch_artist=True,
                    boxprops=dict(facecolor='orange'), medianprops = dict(color='black'))

    labelsize = 12
    ax6.set_ylabel("$p_c$ reached out of "+str(len(MaxAccData))+" runs")
    ax6.set_ylim([0,len(MaxAccData)])
    ax5.set_xticks(np.arange(len(temp4)))
    ax5.set_xticklabels([f'{label}' if label != "1.02" else "NaN" for label in boxPltParams], rotation="horizontal")
    ax5.tick_params(axis='x', labelsize=labelsize)
    ax5.legend([bp1["boxes"][0], bp2["boxes"][0]], ['Environment 1', 'Environment 2'], loc='lower right')
    ax5.set_xlabel("sample limit [$p_{lim}$]" if ParamsName == "sampleLimit" else ParamsName)
    ax5.set_ylabel("speed [$s$]")
    ax5.set_ylim(bottom=0)
    plt.tight_layout()
    ax5.set_zorder(ax6.get_zorder()+1)
    ax5.patch.set_visible(False)
    plt.savefig('DATA_READ/Boxplot_'+ParamsName+'_of_Max_Speeds.pdf')


    print("Data read done!")
