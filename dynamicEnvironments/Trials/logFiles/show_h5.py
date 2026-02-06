import h5py
import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
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
    path = os.getcwd()
    h5files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if(file.endswith(".h5")):
                h5files.append(os.path.join(root,file))
                print(root)#os.path.join(root,file))

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

    name = str(h5_in['trial_1/params/log_filename'][...])
    name = name.split("'")[1]


    #costumized:
    boxPlt = []
    belDat = []
    rawDat = []
    for i in range(0,h5_in['trial_1/params/num_trials'][...]):
        labelsize = 22
        data_set = h5_in['trial_'+str(i+1)]
        amount_intervals = 1+(data_set['params/num_environments'][...]-1)*3
        time_interval = (data_set['params/trial_duration'][...])/amount_intervals

        #plot the mean decision:
        fig, ax = plt.subplots( nrows=1, ncols=1 )
        ax.bar(data_set['time'][:], data_set['mean_robot_decision'][:][:,0], 4, label="Undecided", color="gray")
        ax.bar(data_set['time'][:], data_set['mean_robot_decision'][:][:,2], 4, bottom=data_set['mean_robot_decision'][:][:,0], label="Black", color="red")
        ax.bar(data_set['time'][:], data_set['mean_robot_decision'][:][:,1], 4, bottom=(data_set['mean_robot_decision'][:][:,0]+data_set['mean_robot_decision'][:][:,2]), label="White", color="blue")
        # ax.legend();
        ax.tick_params(axis='x', labelsize=labelsize)
        ax.tick_params(axis='y', labelsize=labelsize)
        plt.xlabel('time [$s$]', fontsize=labelsize)
        plt.ylabel('number of agents', fontsize=labelsize)
        plt.tight_layout()
        plt.savefig(name+'_trial_'+str(i)+'_swarm_decision_dist.pdf')
        plt.close(fig="all")

        # #reset histogram:
        change = int(data_set['params/environmentChange'][...]/10)
        num = [change-10,change+40]
        res_data = [np.array(data_set['robots_reset'][n][:]).astype(int) for n in num]
        figHis = plt.figure()
        his1 = figHis.add_subplot(2,1,1)
        his2 = figHis.add_subplot(2,1,2)

        b = [0,1,2,3,4,5,1000]
        labelos = ["0", "1", "2", "3", "4", ">5"]

        hisso, _ = np.histogram(res_data[0], bins = b)
        o = his1.bar(labelos,hisso, color ="#002b49")
        his1.bar_label(o, fontsize=(labelsize*0.75))
        his1.set_ylim([0, 120])
        his1.tick_params(axis='x', labelsize=labelsize)
        his1.tick_params(axis='y', labelsize=labelsize)
        his1.set_ylabel('agents', fontsize=labelsize)
        his1.set_xlabel('resets at '+str(num[0]*10)+" s", fontsize=labelsize)

        hisso, _ = np.histogram(res_data[1], bins = b)
        o = his2.bar(labelos,hisso, color ="#002b49")
        his2.bar_label(o, fontsize=(labelsize*0.75))
        his2.set_ylim([0, 120])
        his2.tick_params(axis='x', labelsize=labelsize)
        his2.tick_params(axis='y', labelsize=labelsize)
        his2.set_ylabel('agents', fontsize=labelsize)
        his2.set_xlabel('resets at '+str(num[1]*10)+" s", fontsize=labelsize)

        plt.tight_layout(pad=0.4, h_pad=1.5)
        plt.savefig(name+'_trial_'+str(i)+'_resets_hist.pdf')

        #plot swarm mean belief:
        fig1, ax1 = plt.subplots( nrows=1, ncols=1 )
        ax1.plot(data_set['time'][:], 1-data_set['mean_believed_ratio'][:])
        plt.ylim([0, 1])
        ax1.axhline(0.5, color='gray')
        new_interval = time_interval
        for j in range(1, data_set['params/num_environments'][...]):
            ax1.axvline(data_set['params/environmentChange'][...]*j, linestyle='--', color='lightgray', label="environment change")

        #ax1.legend();
        plt.xlabel('time [$s$]', fontsize=labelsize)
        plt.ylabel('swarm belief', fontsize=labelsize)
        ax1.spines['left'].set_position(('data', 0))
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.set_axisbelow(True)
        ax1.tick_params(axis='x', labelsize=labelsize)
        ax1.tick_params(axis='y', labelsize=labelsize)

        data = np.array(1-data_set['mean_believed_ratio'][:])
        time = np.array(data_set['time'][:])


        plt.tight_layout()
        plt.savefig(name+'_trial_'+str(i)+'_swarm_belief.pdf')
        plt.close(fig="all")

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
        dataBox = np.array(ones(h5_in['trial_1/params/num_trials'][...]))
        boxTime.append(int(i*(data_set['params/trial_duration'][...]/40)))
        for j in range(0,len(boxPlt)):
            dataBox[j] = boxPlt[j][i]
        boxData.append(dataBox)
    boxTime.append(int(data_set['params/trial_duration'][...]))


    fig3, ax3 = plt.subplots( nrows=1, ncols=1 )
    ax3.boxplot(boxData)
    plt.xticks(np.arange(41),boxTime, rotation=-35)
    c = 0
    for label in ax3.xaxis.get_ticklabels()[::]:
        if c%4==0:
            label.set_visible(True)
        else:
            label.set_visible(False)
        c += 1

    plt.ylim([0, 1])
    ax3.axhline(0.5, color='gray')
    for j in range(1, data_set['params/num_environments'][...]):
        ax3.axvline((len(boxData)/data_set['params/num_environments'][...])*j, linestyle='--', color='gray', label="environment change")

    ax3.tick_params(axis='x', labelsize=labelsize)
    ax3.tick_params(axis='y', labelsize=labelsize)
    plt.xlabel('time [$s$]', fontsize=labelsize)
    plt.ylabel('swarm belief', fontsize=labelsize)
    plt.tight_layout()
    plt.savefig(name+".pdf")

    print("Data read done!")
    h5_file.close()
