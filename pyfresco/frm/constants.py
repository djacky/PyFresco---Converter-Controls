
dl = 1e-5
limits_prbs = {'reg_mode': 'V', 'ref_mode': 'V_REF_(V)', 'meas_mode': 'I_MEAS_(A)',
        'num_sequences': [6, 50], 'amplitude_pp': [dl, 10**6],
        'period_iters': [1, 10], 'k_order': [8, 20]}

limits_sine = {'reg_mode': 'V', 'ref_mode': 'V_REF_(V)', 'meas_mode': 'I_MEAS_(A)',
        'num_freq': [2, 10**4]}