import h5py
import argparse
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
                #print("HALLO: ", group[...])
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
    parser = argparse.ArgumentParser(
        description="Show the structure and content of an HDF5 file")
    parser.add_argument(
        'filename', type=str,
        help='HDF5 file to show'
    )
    parser.add_argument(
        '--section', type=str,
        help='Show only the contents of this group/dataset')

    parser.add_argument(
        '--show_attrs', dest='show_attrs', action='store_true',
        help='Show attributes of HDF5 datasets?')
    parser.set_defaults(show_attrs=False)
    parser.add_argument(
        '--show_data', dest='show_data', action='store_true',
        help='Show contents of HDF5 datasets? (Otherwise overview only)')
    parser.set_defaults(show_data=False)

    args = parser.parse_args()

    h5_file = h5py.File(args.filename, 'r')
    if args.section is not None:
        h5_in = h5_file[args.section]
    else:
        h5_in = h5_file
    h5_structure(h5_in, show_attrs=args.show_attrs, show_data=args.show_data)

    #costumized:
    for i in range(1,h5_in['trial_1/params/num_trials'][...]+1):
        #get the dataset of trial_1:
        data_set = h5_in['trial_'+str(i)]
        amount_intervals = 1+(data_set['params/num_envs'][...]-1)*3
        time_interval = (data_set['params/trial_duration'][...])/amount_intervals

        #plot the mean decision:
        fig, ax = plt.subplots( nrows=1, ncols=1 )
        ax.plot(data_set['time'][:], data_set['mean_robot_decision'][:])
        plt.ylim([-0.2, 1.2])
        ax.set_axisbelow(True)
        ax.axhline(0, linestyle='--', color='lightgray')
        ax.axhline(0.5, color='blue')
        ax.axhline(0.9, color='lime', label="mostly white")
        ax.axhline(0.1, color='red', label="mostly black")
        ax.legend();
        plt.title("Mean Decision of "+ str(data_set['params/num_robots'][...])+" Robots")
        plt.xlabel('Timestep [$t$]')
        plt.ylabel('Mean Decision [$d_f$]')
        ax.spines['left'].set_position(('data', 0))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.savefig('Trial_'+str(i)+' uPos: '+str(data_set['params/posFeedback'][...])+' pc: '+' tau: '+str(data_set['params/tau'][...])+' Mean Decision of Robots.png')
        plt.close(fig="all")

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
        # plt.savefig('Trial_'+str(i)+' uPos: '+str(data_set['params/posFeedback'][...])+' pc: '+' tau: '+str(data_set['params/tau'][...])+' Histogram of Decision.png')
        # plt.close(fig="all")
        #
        # #plot the reset histogram:
        # print("\n\nOf which Log-interval do you want to create the Reset-Histogram?\n(Please choose a number between 0 and ",data_set['robots_reset'].size-1,")")
        # num = int(input())
        # print("Data Hist",num,":\n", data_set['robots_reset'][num][:])
        # fig, ax = plt.subplots( nrows=1, ncols=1 )
        # plt.hist(data_set['robots_reset'][num][:], bins = 20)
        # plt.xlim([0, 5])
        # plt.ylim([0, 100])
        # plt.title("Histogram of Resets at Log-Interval "+str(num))
        # plt.xlabel('Resets [$CountR$]')
        # plt.ylabel('Amount of Robots [%]')
        # plt.savefig('Trial_'+str(i)+' uPos: '+str(data_set['params/posFeedback'][...])+' pc: '+' tau: '+str(data_set['params/tau'][...])+' Histogram of Reset.png')
        # plt.close(fig="all")

        #plot swarm mean belief:
        fig1, ax1 = plt.subplots( nrows=1, ncols=1 )
        ax1.plot(data_set['time'][:], 1-data_set['mean_believed_ratio'][:])
        plt.ylim([0, 1])
        ax1.axhline(0.5, color='blue')
        ax1.axhline(0.9, color='lime', label="threshold $p_c$ mostly white")
        ax1.axhline(0.1, color='red', label="threshold $p_c$ mostly black")
        new_interval = time_interval
        for j in range(1, data_set['params/num_envs'][...]):
            #if j == 0:
            ax1.axvline(data_set['params/time_to_reset'][...]*j, linestyle='--', color='lightgray', label="environment change")
            # elif j < (data_set['params/num_envs'][...]-1):
            #     new_interval += (data_set['params/trial_duration'][...]-time_interval)/(data_set['params/num_envs'][...]-1)
            #     ax1.axvline(new_interval, linestyle='--', color='lightgray')

        ax1.legend();
        plt.title("Believed Ratio of "+ str(data_set['params/num_robots'][...])+" Robots")
        plt.xlabel('Timestep [$t$]')
        plt.ylabel('Belived Ratio [$f$]')
        ax1.spines['left'].set_position(('data', 0))
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.set_axisbelow(True)

        # get accuracy and turnspeed
        # before change
        data = np.array(1-data_set['mean_believed_ratio'][:])
        time = np.array(data_set['time'][:])
        chng = int(data_set['params/time_to_reset'][...])
        print("data", chng)
        accu1_ind = np.where(data[np.where(time[:]<chng)[0]]>0.9)[0]
        accu1_max = np.max(data[np.where(time[:]<chng)[0]])
        if accu1_ind.size != 0:
            accu1_time = np.min(time[accu1_ind])
            a = str("First p_cred reached after "+str(accu1_time)+"s.\nMax Accuracy 1: "+str(np.around(accu1_max,3))+" reached after "+str(time[np.where(data[np.where(time[:]<chng)[0]]==accu1_max)[0][0]])+"s.")
        else:
            a = str("First Threshold not reached!\nMax Accuracy 1: "+str(np.around(accu1_max,3))+" reached after "+str(time[np.where(data[np.where(time[:]<chng)[0]]==accu1_max)[0][0]])+"s.")
        accu2_ind = np.where(data[np.where(time[:]>=chng)[0]]<0.1)[0]
        accu2_max = np.min(data[np.where(time[:]>=chng)[0]])
        print("HERE: ", np.min(data[np.where(time[:]>=chng)[0]]))
        if accu2_ind.size != 0:
            accu2_time = np.min(time[accu2_ind])
            b = str("Second p_cred reached after "+str(accu2_time)+"s.\nMax Accuracy 2: "+str(np.around(1-accu2_max,3))+" reached after "+str(time[np.where(data[np.where(time[:]>=chng)[0]]==accu2_max)[0][0]])+"s.")
        else:
            b = str("Second Threshold not reached!")

        gca().set_position((.1, .32, .8, .6))
        figtext(.05, .02, a+"\n\n"+b)
        plt.savefig('Trial_'+str(i)+' uPos: '+str(data_set['params/posFeedback'][...])+' pc: '+' tau: '+str(data_set['params/tau'][...])+' Believed Ratio of Robots.png')
        plt.close(fig="all")
    #plt.show()
    h5_file.close()
