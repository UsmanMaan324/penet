"""Create HDF5 file for PE project."""
import argparse
import h5py
import numpy as np
import os
import pickle
import re
import util
import pandas as pd

from ct import CTPE, CONTRAST_HU_MIN, CONTRAST_HU_MAX
from tqdm import tqdm


def main(args):
    study_re = re.compile(r'(\d+)_(\d\.\d)')
    study_paths = []
    ctpes = []
    
    # TODO read in csv
    df = pd.read_csv(args.csv_path)
    
    acc = set(df.ACCESSION_NO)
    df.set_index("ACCESSION_NO", inplace=True)


    #num_positive = 0
    #num_negative = 0

    # Read slice-wise labels
    with open(args.slice_list, 'r') as slice_fh:
        slice_lines = [l.strip() for l in slice_fh.readlines() if l.strip()]
    name2slices = {}
    name2info = {}
    print(len(slice_lines))
    for slice_line in slice_lines:
        try:
            info, slices = slice_line.split(':')
        except:
            print("exception")
            print(slice_line)
            continue
        slices = slices.strip()
        info = info.split(',')
        studynum, thicc, label, num_slices, phase, dataset = int(info[0]), float(info[1]), int(info[2]), int(info[3]), info[4], info[5]
        if phase != "test": 
            #print(phase)
            continue
        #if dataset != "central":
            #print("CENTRAL")
            #continue

        #TODO filter out subseg

        #if (df.loc[int(studynum)].SUBSEGMENTAL == 1 and df.loc[int(studynum)].POSITIVE_CTPA == 1) or int(studynum) in [1725465, 1990158, 2178280]:
            #print(studynum)
            #continue

        if (int(studynum) in [1725465, 1990158, 2178280, 2723621,2539770,1714879, 1714887, 1716610,1717870, 1722054, 1722949, 1727117, 1731412, 1731704, 1735808, 1735973, 1736262, 1741715, 1742266,1742356, 1743808]): continue
        """

        if int(studynum) in acc:
            if df.loc[int(studynum)]["subsegmental_only"] == 1: continue
        if num_positive >= 83 and num_negative >= 84: break
        if label == 1:
            if num_positive >=83: continue
            num_positive +=1
        if label == 0:
            if num_negative >=84: continue
            print(studynum)
            num_negative +=1

        if np.isnan(df.loc[int(studynum)]["START"]): continue

        if studynum in acc:
            if df.loc[int(studynum)]["SUBSEGMENTAL"] == 1: 
                print("*",studynum)
                continue
        """

        name2info[studynum] = [thicc, label, num_slices, phase, dataset]
        if slices: 
            name2slices[studynum] = [int(n) for n in slices.split(',')]
        else:
            name2slices[studynum] = []
    # Collect list of paths to studies to convert
    voxel_means = []
    voxel_stds = []
    for base_path, _, file_names in os.walk(args.data_dir):
        npy_names = [f for f in file_names if f.endswith('.npy')]
        for name in npy_names:
            match = study_re.match(name)
            if not match:
                print(name)
                continue
            study_num, slice_thickness = int(match.group(1)), float(match.group(2))
            if study_num in name2slices:
                if slice_thickness in args.use_thicknesses:
                    # Add to list of studies
                    study_paths.append(os.path.join(base_path, name))
                    pe_slice_nums = name2slices.get(study_num, [])
                    thicc, label, num_slices, phase, dataset = name2info[study_num]
                    print (study_num, label, phase, num_slices)
                    if thicc != slice_thickness:
                        print("Thickness issue with file ", name)
                    ctpes.append(CTPE(study_num, slice_thickness, pe_slice_nums, num_slices, dataset, is_positive=label, phase=phase))

    with open(os.path.join(args.output_dir, 'series_list.pkl'), 'wb') as pkl_fh:
        pickle.dump(ctpes, pkl_fh)

    print('Wrote {} studies'.format(len(study_paths)))
    print('Mean {}'.format(np.mean(voxel_means)))
    print('Std {}'.format(np.mean(voxel_stds)))


def get_mean_std(scan, means, stds):
    scan = scan.astype(np.float32)
    scan = (scan - CONTRAST_HU_MIN) / (CONTRAST_HU_MAX - CONTRAST_HU_MIN)
    scan = np.clip(scan, 0., 1.)
    means.append(np.mean(scan))
    stds.append(np.std(scan))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create HDF5 file for PE')

    parser.add_argument('--data_dir', type=str,
                        default='/deep/group/aihc-bootcamp-winter2018/medical-imaging/ct_chest_pe/data-final/images',
                        help='Base directory for loading 3D volumes.')
    parser.add_argument('--slice_list', type=str,
                        default='/deep/group/aihc-bootcamp-winter2018/medical-imaging/ct_chest_pe/tanay_data_12_4_clean/slice_list_12_4_clean.txt')
    parser.add_argument('--use_thicknesses', default='1.25', type=str,
                        help='Comma-separated list of thicknesses to use.')
    parser.add_argument('--hu_intercept', type=float, default=-1024,
                        help='Intercept for converting from original numpy files to HDF5 (probably -1024).')
    parser.add_argument('--output_dir', type=str,
                        default='/deep/group/aihc-bootcamp-winter2018/medical-imaging/ct_chest_pe/tanay_data_12_4_clean',
                        help='Output directory for HDF5 file and pickle file.')

    # TODO csv to filter subseg
    parser.add_argument('--csv_path', type=str)

    args_ = parser.parse_args()
    args_.use_thicknesses = util.args_to_list(args_.use_thicknesses, arg_type=float, allow_empty=False)

    main(args_)
