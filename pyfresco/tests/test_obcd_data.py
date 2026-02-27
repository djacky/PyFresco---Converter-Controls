import pyfresco.obcd as cd
import pyfresco.frm as frm
import numpy as np
import os
import pytest
from .fgc_funcs import obcd_data_vals
from .plot import Plot


host = os.uname().nodename
requires_root_cert = pytest.mark.skipif(host not in ('cs-ccr-teepc2.cern.ch'),
        reason="no grid root certificate inside CI")

device_ib = "RPAAO.866.02.ETH8"
device_v = "RFNA.866.01.ETH2"
device_maquette = "RPAGO.866.1.ETH4"
send_to_fgc = True
plot_funcs = True


class Params:

    @staticmethod
    def prbs_pars():
        default = Params()
        prbs_pars, _, _ = obcd_data_vals(device_ib)
        props_prbs = {'reg_mode': 'V', 'ref_mode': 'V_REF_(V)', 'meas_mode': 'I_MEAS_(A)',
        'period_iters': prbs_pars['period_iters'], 'amplitude_pp': prbs_pars['amp_pp'],
        'k_order': prbs_pars['k'], 'num_sequences': prbs_pars['num_seq']}
        for prop in props_prbs:
            setattr(default, prop, props_prbs[prop])
        return default

    @staticmethod
    def prbs_pars_v():
        default = Params()
        prbs_pars, _, _ = obcd_data_vals(device_v, mode='V')
        props_prbs = {'reg_mode': 'V', 'ref_mode': 'F_REF_LIMITED_(V)', 'meas_mode': 'I_CAPA_(A)',
        'period_iters': prbs_pars['period_iters'], 'amplitude_pp': prbs_pars['amp_pp'],
        'k_order': prbs_pars['k'], 'num_sequences': prbs_pars['num_seq']}

        for prop in props_prbs:
            setattr(default, prop, props_prbs[prop])

        return default


@requires_root_cert
def test_dataIB():
    P = Params()
    prbs_pars = P.prbs_pars()
    _, user, df = obcd_data_vals(device_ib)
    fgc_ib, user_pars_ib = user['fgc_ib'], user['user_pars_ib']
    # user_pars_ib.opt_method = 'H2'
    df, df_gd = frm.Frm_methods(device_ib).prbs(df['df_ib_time'], prbs_pars)
    # Test multimodel ################
    import pandas as pd
    df2 = pd.DataFrame({'f': df['f'].values, 'gain': df['gain'].values + 20 * np.log10(1.1),
                'phase': df['phase'].values - (2 * np.pi * df['f'] * 150e-6) * 180 / np.pi})
    df3 = pd.DataFrame({'f': df['f'].values, 'gain': df['gain'].values + 20 * np.log10(0.95),
                'phase': df['phase'].values + (2 * np.pi * df['f'] * 150e-6) * 180 / np.pi})
    df_tot = [df, df2, df3]
    ##################################
    df_tot = [df]
    X = cd.OptimizeIB(fgc_ib, user_pars_ib)
    opt_result, df_sens, margins = X.data_opt(df_tot)
    if plot_funcs:
        Plot.plot(df_sens, device_ib, user_pars_ib, open_loop=True)
        Plot.plot_gen(df_gd['f'], df_gd['group_delay'], df_gd['f'], df_gd['group_delay_ma'],
                      device=device_ib)

    assert margins['modulus_margin'][0] >= user_pars_ib.des_mm
    assert np.isnan(np.sum(opt_result.R)) == False
    assert np.isnan(np.sum(opt_result.S)) == False
    assert np.isnan(np.sum(opt_result.T)) == False
    assert np.isnan(np.sum(opt_result.L)) == False
    assert np.isnan(np.sum(opt_result.Q)) == False

    if user_pars_ib.q_bw > 0:
        assert np.isnan(np.sum(opt_result.Q)) == False
        np.testing.assert_approx_equal(np.sum(opt_result.Q), 1, significant=6)
        np.testing.assert_array_almost_equal(opt_result.Q, opt_result.Q[::-1])

    T_roots_max = np.amax(np.abs(np.roots(opt_result.T)))
    S_roots_max = np.amax(np.abs(np.roots(opt_result.S)))
    assert T_roots_max < 1
    assert S_roots_max <= 1 + 1e-5

    if send_to_fgc:
        cd.FgcProperties.to_fgc_ib(opt_result, user_pars_ib, device_ib)


@requires_root_cert
def test_dataV():
    P = Params()
    F = frm.Frm_methods(device_v)
    prbs_pars_v = P.prbs_pars_v()
    _, user, df = obcd_data_vals(device_v, mode='V')
    fgc_v, user_pars_v = user['fgc_v'], user['user_pars_v']
    df_icapa, _ = F.prbs(df['df_vreg'], prbs_pars_v)
    prbs_pars_v.ref_mode, prbs_pars_v.meas_mode = 'F_REF_LIMITED_(V)', 'V_MEAS_REG_(V)'
    df_vmeas, _ = F.prbs(df['df_vreg'], prbs_pars_v)
    prbs_pars_v.ref_mode, prbs_pars_v.meas_mode = 'V_REF_(V)', 'I_MEAS_(A)'
    df_imeas, _ = F.prbs(df['df_imeas1'], prbs_pars_v)
    df_gain = df['df_dcgain']
    df_gain.rename(columns={"I_MEAS_(A)": "I_MEAS", "V_REF_(V)": "F_REF_LIMITED"}, inplace=True)

    X = cd.OptimizeV(fgc_v, user_pars_v)
    opt_result, df_sens, margins = X.data_opt(df_icapa, df_vmeas, df_imeas, df_gain)
    if plot_funcs:
        Plot.plot([df_sens], device_v, user_pars_v, mode='V')

    print('K-damping = ', opt_result.Kd)
    print('K-voltage = ', opt_result.Kv)
    if send_to_fgc:
        cd.FgcProperties.to_fgc_v(opt_result, user_pars_v, device_v)
    # import pdb
    # pdb.set_trace()

@requires_root_cert
def test_maquette_V():
    import midas
    P = Params()
    _, user, df = obcd_data_vals(device_maquette, mode='V')
    fgc_v, user_pars_v = user['fgc_v'], user['user_pars_v']
    user_pars_v.damp_bw = 20
    user_pars_v.volt_bw = 10
    user_pars_v.damp_mm = 0.3
    user_pars_v.opt_method = 'Hinf'

    link_str = 'https://beraymon-preprod.cern.ch/powerspy/chart/?history=10437:51909?history=10435:51905?history=10436:51907?history=10569:52056'
    logs = midas.fetch(link_str)
    #import pdb; pdb.set_trace()
    df_imeas = logs[0].to_dataframe()
    df_imeas.columns = ['f', 'gain', 'phase']
    df_vmeas = logs[1].to_dataframe()
    df_vmeas.columns = ['f', 'gain', 'phase']
    df_icapa = logs[2].to_dataframe()
    df_icapa.columns = ['f', 'gain', 'phase']
    df_gain = logs[3].to_dataframe()
    df_gain.rename(columns={"I_MEAS_(A)": "I_MEAS", "V_MEAS_(V)": "F_REF_LIMITED"}, inplace=True)

    X = cd.OptimizeV(fgc_v, user_pars_v)
    opt_result, df_sens, margins = X.data_opt(df_icapa, df_vmeas, df_imeas, df_gain)
    if plot_funcs:
        Plot.plot([df_sens], device_maquette, user_pars_v, open_loop=True, mode='D')

    print('K-damping = ', opt_result.Kd)
    print('K-voltage = ', opt_result.Kv)
