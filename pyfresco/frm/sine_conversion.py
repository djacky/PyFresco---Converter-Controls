import json
import numpy as np
import pandas as pd
import pickle
import re
import os
from os import listdir
from os.path import isfile, join

path = '/afs/cern.ch/work/a/anicolet/private/fgc/sw/clients/python/' \
    + 'pyfresco/pyfresco/frm/Sine_fit/json_files'
os.chdir(path)
onlyfiles1 = [f for f in listdir(path) if isfile(join(path, f))]

onlyfiles = [x for x in onlyfiles1 if not 'DC' in x]

df = list()
freq = np.empty(len(onlyfiles))
for i in range(len(onlyfiles)):

    with open(onlyfiles[i]) as json_file:
        data = json.load(json_file)
    X = data['signals']
    Ts = data['period']
    for ii in range(len(X)):
        if X[ii]['name'] == 'I_REF_ADV':
            in_array = X[ii]['samples']
        if X[ii]['name'] == 'I_MEAS_REG':
            out_array = X[ii]['samples']

    t = np.arange(0, Ts * (len(in_array) - 1), Ts)
    in_array = in_array[0:len(t)]
    out_array = out_array[0:len(t)]

    arrays = [['I_REF_ADV', 'I_REF_ADV', 'I_MEAS_REG', 'I_MEAS_REG'],
           ['t_local', 'sample', 't_local', 'sample']]
    tuples = list(zip(*arrays))
    M1 = [t, in_array, t, out_array]
    index = pd.MultiIndex.from_tuples(tuples)
    d = pd.DataFrame(np.transpose(M1), columns=index)

    # d = {'t': t, 'I_REF_ADV': in_array, 'I_MEAS_REG': out_array}
    get_floats = re.findall(r'[-+]?\d*\.\d+|\d+', onlyfiles[i])
    freq[i] = float(get_floats[-1])

    df.append(d)
print(df[0])

# to store dataframe as pickle
with open('sine_data2.pickle', 'wb') as handle:
    pickle.dump(df, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('sine_freq.pickle', 'wb') as handle:
    pickle.dump(freq, handle, protocol=pickle.HIGHEST_PROTOCOL)

# load it back again
# df = pd.read_pickle('df.pkl')