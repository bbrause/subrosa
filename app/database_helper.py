# SUB ROSA v0.1
# 2019
#
# author:  Jan Luhmann
# license: GNU General Public License v3.0

import numpy as np

def dense_to_sparse(arr):
    # Compresses sparse vector (numpy array) by using Compressed Row Storage
    # OBSOLETE since decompression to slow
    sparse = []
    sparse.append((0, arr[0]))
    index = 1
    for value in arr[1:-1]:
        if value > 0:
            sparse.append((index, value))
            index += 1
    sparse.append((len(arr) - 1, arr[-1]))
    return np.array(sparse)


def sparse_to_dense(arr):
    # Decompresses CRS compressed sparse vector (numpy array) 
    # OBSOLETE since too slow
    dense = (int(arr[-2]) + 1) * [0]
    for i in range(0,len(arr),2):
        index = int(arr[i])
        value = arr[i+1]
        dense[index] = value
    return np.array(dense)