import pyfresco.obcd as cd
import numpy as np
import os
import pytest
from .plot import Plot
from .fgc_funcs import obcd_model_vals
from .plot import Plot

host = os.uname().nodename
requires_root_cert = pytest.mark.skipif(host not in ('cs-ccr-teepc2.cern.ch'),
        reason="no grid root certificate inside CI")

device = "RFNA.866.01.ETH2"
send_to_fgc = True
plot_funcs = True


@requires_root_cert
def test_modelIB_Hinf():
    P = obcd_model_vals(device)
    fgc_props, user_pars = P['fgc_ib'], P['user_pars_ib']
    X = cd.OptimizeIB(fgc_props, user_pars)
    opt_result, df_sens, margins = X.model_opt()

    assert margins['modulus_margin'][0] >= user_pars.des_mm
    assert np.isnan(np.sum(opt_result.R)) == False
    assert np.isnan(np.sum(opt_result.S)) == False
    assert np.isnan(np.sum(opt_result.T)) == False
    assert np.isnan(np.sum(opt_result.L)) == False

    if user_pars.q_bw > 0:
        assert np.isnan(np.sum(opt_result.Q)) == False
        np.testing.assert_approx_equal(np.sum(opt_result.Q), 1, significant=6)
        np.testing.assert_array_almost_equal(opt_result.Q, opt_result.Q[::-1])

    T_roots_max = np.amax(np.abs(np.roots(opt_result.T)))
    S_roots_max = np.amax(np.abs(np.roots(opt_result.S)))
    assert T_roots_max < 1
    assert S_roots_max <= 1 + 1e-5

    if send_to_fgc:
        cd.FgcProperties.to_fgc_ib(opt_result, user_pars, device)


@requires_root_cert
def test_modelIB_H2():
    P = obcd_model_vals(device)
    fgc_props, user_pars = P['fgc_ib'], P['user_pars_ib']
    user_pars.opt_method = 'H2'
    X = cd.OptimizeIB(fgc_props, user_pars)
    opt_result, df_sens, margins = X.model_opt()

    assert margins['modulus_margin'][0] >= user_pars.des_mm
    assert np.isnan(np.sum(opt_result.R)) == False
    assert np.isnan(np.sum(opt_result.S)) == False
    assert np.isnan(np.sum(opt_result.T)) == False
    assert np.isnan(np.sum(opt_result.L)) == False

    if user_pars.q_bw > 0:
        assert np.isnan(np.sum(opt_result.Q)) == False
        np.testing.assert_approx_equal(np.sum(opt_result.Q), 1, significant=7)
        np.testing.assert_array_almost_equal(opt_result.Q, opt_result.Q[::-1])

    T_roots_max = np.amax(np.abs(np.roots(opt_result.T)))
    S_roots_max = np.amax(np.abs(np.roots(opt_result.S)))
    assert T_roots_max < 1
    assert S_roots_max <= 1 + 1e-5
    if plot_funcs:
        Plot.plot(df_sens, device, user_pars, open_loop=True)

    if send_to_fgc:
        cd.FgcProperties.to_fgc_ib(opt_result, user_pars, device)


@requires_root_cert
def test_modelIB_H1():
    P = obcd_model_vals(device)
    fgc_props, user_pars = P['fgc_ib'], P['user_pars_ib']
    user_pars.opt_method = 'H1'
    X = cd.OptimizeIB(fgc_props, user_pars)
    opt_result, df_sens, margins = X.model_opt()

    assert margins['modulus_margin'][0] >= user_pars.des_mm
    assert np.isnan(np.sum(opt_result.R)) == False
    assert np.isnan(np.sum(opt_result.S)) == False
    assert np.isnan(np.sum(opt_result.T)) == False
    assert np.isnan(np.sum(opt_result.L)) == False

    if user_pars.q_bw > 0:
        assert np.isnan(np.sum(opt_result.Q)) == False
        np.testing.assert_approx_equal(np.sum(opt_result.Q), 1, significant=7)
        np.testing.assert_array_almost_equal(opt_result.Q, opt_result.Q[::-1])

    T_roots_max = np.amax(np.abs(np.roots(opt_result.T)))
    S_roots_max = np.amax(np.abs(np.roots(opt_result.S)))
    assert T_roots_max < 1
    assert S_roots_max <= 1 + 1e-5

    if send_to_fgc:
        cd.FgcProperties.to_fgc_ib(opt_result, user_pars, device)


@requires_root_cert
def test_modelV_Hinf():
    P = obcd_model_vals(device)
    fgc_props, user_pars = P['fgc_v'], P['user_pars_v']
    X = cd.OptimizeV(fgc_props, user_pars)
    opt_result, df_sens, margins = X.model_opt()
    max_Sens = np.amax(df_sens['Sensitivity_dy_y_volt']['gain'].values)
    mm = 1 / np.power(10, max_Sens / 20)
    print('K-damping = ', opt_result.Kd)
    print('K-voltage = ', opt_result.Kv)
    Plot.plot([df_sens], device, user_pars, open_loop=True, mode='V')

    assert mm >= user_pars.volt_mm
    assert np.isnan(np.sum(opt_result.Kd)) == False
    assert np.isnan(np.sum(opt_result.Kv)) == False

    if send_to_fgc:
        cd.FgcProperties.to_fgc_v(opt_result, user_pars, device)


@requires_root_cert
def test_modelV_H2():
    P = obcd_model_vals(device)
    fgc_props, user_pars = P['fgc_v'], P['user_pars_v']
    user_pars.opt_method = 'H2'
    X = cd.OptimizeV(fgc_props, user_pars)
    opt_result, df_sens, margins = X.model_opt()
    max_Sens = np.amax(df_sens['Sensitivity_dy_y_volt']['gain'].values)
    mm = 1 / np.power(10, max_Sens / 20)
    print('K-damping = ', opt_result.Kd)
    print('K-voltage = ', opt_result.Kv)
    Plot.plot([df_sens], device, user_pars, open_loop=True, mode='V')

    assert mm >= user_pars.volt_mm
    assert np.isnan(np.sum(opt_result.Kd)) == False
    assert np.isnan(np.sum(opt_result.Kv)) == False

    if send_to_fgc:
        cd.FgcProperties.to_fgc_v(opt_result, user_pars, device)
