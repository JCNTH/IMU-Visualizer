# name: alignment.py


import quaternion   
import numpy as np
from scipy.spatial.transform import Rotation as R



def get_ja_alignment(ja, alignment_id):

    aligned_ja = {}

    sequence = 'ZXY'
    # sequence = 'zxy'

    for side in ['r', 'l']:

        for joint in ['hip', 'knee', 'ankle']:

            euler_ja = np.array([ja[joint + '_flexion_' + side], 
                                 ja[joint + '_adduction_' + side], 
                                 ja[joint + '_rotation_' + side]]).T
            rot_ja   = R.from_euler(sequence, euler_ja, degrees = True).as_matrix()

            static_euler_ja = np.array([ja[joint + '_flexion_' + side][alignment_id[0]:alignment_id[1]].mean(),
                                        ja[joint + '_adduction_' + side][alignment_id[0]:alignment_id[1]].mean(),
                                        ja[joint + '_rotation_' + side][alignment_id[0]:alignment_id[1]].mean()]).T
            static_rot_ja   = R.from_euler(sequence, static_euler_ja, degrees = True).as_matrix()
            static_rot_ref  = R.from_euler(sequence, [0, 0, 0], degrees = True).as_matrix()  # identity matrix

            correction = static_rot_ja.T @ static_rot_ref

            rot_aligned_ja = np.zeros(rot_ja.shape)
            for i in range(rot_ja.shape[0]):
                rot_aligned_ja[i] = rot_ja[i] @ correction

            euler_aligned_ja = R.from_matrix(rot_aligned_ja).as_euler(sequence, degrees = True)
            aligned_ja[joint + '_flexion_' + side] = euler_aligned_ja[:, 0]
            aligned_ja[joint + '_adduction_' + side] = euler_aligned_ja[:, 1]
            aligned_ja[joint + '_rotation_' + side] = euler_aligned_ja[:, 2]

    try:
        # aligned_ja['pelvis_tilt'] = ja['pelvis_tilt']  # no need to align the pelvis tilt
        # aligned_ja['pelvis_list'] = ja['pelvis_list']
        # aligned_ja['pelvis_rot'] = ja['pelvis_rot']

        euler_pelvis = np.array([ja['pelvis_tilt'], ja['pelvis_list'], ja['pelvis_rot']]).T
        rot_pelvis   = R.from_euler(sequence, euler_pelvis, degrees = True).as_matrix()

        static_euler_pelvis = np.array([ja['pelvis_tilt'][alignment_id[0]:alignment_id[1]].mean(),
                                       ja['pelvis_list'][alignment_id[0]:alignment_id[1]].mean(),
                                       ja['pelvis_rot'][alignment_id[0]:alignment_id[1]].mean()]).T
        static_rot_pelvis   = R.from_euler(sequence, static_euler_pelvis, degrees = True).as_matrix()

        correction = static_rot_pelvis.T @ static_rot_ref

        rot_aligned_pelvis = np.zeros(rot_pelvis.shape)
        for i in range(rot_pelvis.shape[0]):
            rot_aligned_pelvis[i] = rot_pelvis[i] @ correction

        euler_aligned_pelvis = R.from_matrix(rot_aligned_pelvis).as_euler(sequence, degrees = True)
        aligned_ja['pelvis_tilt'] = euler_aligned_pelvis[:, 0] + 90 # these numbers to align with the simulation coordinate system
        aligned_ja['pelvis_list'] = euler_aligned_pelvis[:, 1] - 90
        aligned_ja['pelvis_rot'] = euler_aligned_pelvis[:, 2] + 90


    except:
        pass

    return aligned_ja













