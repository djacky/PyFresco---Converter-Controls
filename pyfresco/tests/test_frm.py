import pyfresco
import pickle
import numpy as np
from pkg_resources import resource_string
import os
import pytest
from .plot import Plot
from .fgc_funcs import frm_prbs_vals

host = os.uname().nodename
requires_root_cert = pytest.mark.skipif(host not in ('cs-ccr-teepc2.cern.ch'),
        reason="no grid root certificate inside CI")

df_sine = pickle.loads(resource_string(__name__, 'test_data/sine_data2.pickle'))
freq = pickle.loads(resource_string(__name__, 'test_data/sine_freq2.pickle'))

# device = "RFNA.866.01.ETH2"
device = "RPAAO.866.02.ETH8"


class Params:

    @staticmethod
    def prbs_pars():
        default = Params()
        prbs_pars, df_prbs = frm_prbs_vals(device)
        # props_prbs = {'reg_mode': 'V', 'ref_mode': 'V_REF_(V)', 'meas_mode': 'I_MEAS_(A)',
        # 'period_iters': int(2), 'amplitude_pp': 1, 'k_order': int(11), 'num_sequences': int(12)}
        props_prbs = {'reg_mode': 'V', 'ref_mode': 'V_REF_(V)', 'meas_mode': 'I_MEAS_(A)',
        'period_iters': prbs_pars['period_iters'], 'amplitude_pp': prbs_pars['amp_pp'],
        'k_order': prbs_pars['k'], 'num_sequences': prbs_pars['num_seq']}
        for prop in props_prbs:
            setattr(default, prop, props_prbs[prop])
        return default, df_prbs

    @staticmethod
    def sine_pars():
        default = Params()
        props_sine = {'reg_mode': 'V', 'ref_mode': 'I_REF_ADV', 'meas_mode': 'I_MEAS_REG',
                    'num_freq': 10}
        for prop in props_sine:
            setattr(default, prop, props_sine[prop])
        return default


@requires_root_cert
def test_prbs():
    F = pyfresco.frm.Frm_methods(device)
    P = Params()
    prbs_pars, df_prbs = P.prbs_pars()
    df, df_gd = F.prbs(df_prbs, prbs_pars)
    Plot.plot_gen(df_gd['f'].values, df_gd['group_delay'].values,
                  df_gd['f'].values, df_gd['group_delay_ma'].values, device=device)
    assert df.isnull().values.any() == False


@requires_root_cert
def test_sine():
    F = pyfresco.frm.Frm_methods(device)
    P = Params()
    sine_pars = P.sine_pars()
    df, _ = F.sine_fit(freq, df_sine, sine_pars)
    freq_array = F.sine_freq_array(0.2, 283, 10, sine_pars)
    assert df.isnull().values.any() == False
    np.testing.assert_array_equal(np.sort(freq), df['f'].values)


@requires_root_cert
def test_prbs_params():
    F = pyfresco.frm.Frm_methods(device)
    f1 = 2
    f2 = 5000
    prbs_c = F.prbs_params_calc(f1, f2, 1, 12, 'V')

