import pyfgc
import time
import numpy as np
from .exceptions import Check
# import json


def delay_ib(ind, Ts_fund, control_mode, device, rbac_token):

    P = FgcProperties.from_fgc_ib(device, rbac_token=rbac_token, control_mode=control_mode)
    prop = vars(P)

    if prop['VS.ACTUATION'] == 'FIRING_REF':
        Delay_firing = prop['VS.FIRING.DELAY']
    elif prop['VS.ACTUATION'] == 'VOLTAGE_REF':
        clbw_vs, zeta_vs = prop['VS.SIM.BANDWIDTH'], prop['VS.SIM.Z']
        wn = (2 * np.pi * clbw_vs) / np.sqrt(1 - 2 * np.power(zeta_vs, 2) +
            np.sqrt(2 - 4 * np.power(zeta_vs, 2) + 4 * np.power(zeta_vs, 4)))
        Delay_firing = 2 * zeta_vs / wn
    else:
        Delay_firing = 0

    Delay_actuation = prop['VS.ACT_DELAY_ITERS'] * Ts_fund

    meas_select = prop['REG.{}.EXTERNAL.MEAS_SELECT'.format(control_mode)]
    if meas_select == 'UNFILTERED' or meas_select == 'FILTERED':
        Delay_meas = prop['MEAS.{}.DELAY_ITERS'.format(control_mode)] * Ts_fund
    else:
        Delay_meas = 0

    if meas_select == 'FILTERED':
        Delay_MA = 0
        for d_val in prop[f'MEAS.{control_mode}.FIR_LENGTHS']:
            if d_val >= 1:
                Delay_MA += (d_val - 1) / 2 * Ts_fund
    else:
        Delay_MA = 0

    return Delay_meas + Delay_firing + Delay_actuation + Delay_MA


class UiParams:

    """
    A class which contains the default values to be used for the ObCD UI.
    """
    def __init__(self):
        self.des_bw = None
        self.des_z = None
        self.des_mm = None
        self.n_integrators = None
        self.ref_delay = None
        self.opt_method = None
        self.n_r = None
        self.n_s = None
        self.n_t = None
        self.n_ilc = None
        self.n_q = None
        self.q_bw = None
        self.control_mode = None
        self.test_select = None
        self.debug = None
        self.noise_rej = None

        self.damp_bw = None
        self.damp_z = None
        self.volt_mm = None
        self.volt_bw = None
        self.volt_z = None
        self.positive_coeff = None
        self.kd_0 = None

    @staticmethod
    def default_bw(device, rbac_token, mode='I'):
        ind = int(pyfgc.get(device, 'LOAD.SELECT', rbac_token=rbac_token).value)
        Ts_fund = round(float(pyfgc.get(device, 'FGC.ITER_PERIOD',
                                        rbac_token=rbac_token).value), 6)
        if mode == 'B':
            reg_period = int(pyfgc.get(device, f'REG.B.PERIOD_ITERS[{ind}]',
                                       rbac_token=rbac_token).value)
            Fs = 1 / (Ts_fund * reg_period)
            f_bw, q_bw = Fs / 15, Fs / 5
        elif mode == 'I':
            reg_period = int(pyfgc.get(device, f'REG.I.PERIOD_ITERS[{ind}]',
                                       rbac_token=rbac_token).value)
            Fs = 1 / (Ts_fund * reg_period)
            f_bw, q_bw = Fs / 15, Fs / 5
        elif mode == 'V':
            w = np.logspace(-2, np.log10(np.pi / 100e-6), 2000)
            prop = vars(FgcProperties.from_fgc_v(device, rbac_token))
            Check.prop_v_model(prop, print)
            Zd = prop['LOAD.OHMS_MAG'] + 1j * w * prop['LOAD.HENRYS']
            M = 1 / (prop['LOAD.OHMS_SER'] + 1 / (1 / prop['LOAD.OHMS_PAR'] + 1 / Zd))

            Zmt = 1 / M
            Z1 = prop['VS.FILTER.OHMS'] + 1 / (1j * w * prop['VS.FILTER.FARADS1'])
            Z2 = 1 / (1j * w * prop['VS.FILTER.FARADS2'])
            Z3 = (Z1 * Z2) / (Z1 + Z2)
            ZT = (Z3 * Zmt) / (Z3 + Zmt)

            G = (ZT / (prop['VS.FILTER.HENRYS'] * 1j * w + ZT))
            try:
                bw_index = np.where(np.abs(G) ** 2 <= 1 / 2)[0][0]
                f_bw = w[bw_index] / (2 * np.pi)
                q_bw = None
            except:
                delay = prop['VS.FIRING.DELAY']
                if delay == 0:
                    f_bw, q_bw = 30, None
                elif delay > 0:
                    f_bw, q_bw = int(1 / (4 * np.pi * delay)), None
        return f_bw, q_bw

    @staticmethod
    def get_default_i(device: str, rbac_token: str = None):
        """
        :param device: FGC device name
        :type device: str
        :param rbac_token: RBAC token needed to access the FGC properties
        :type rbac_token: str
        :return: Object which contains the UI paramater default values
                 (for :ref:`control_mode <control_mode>` = ``I``).
        """
        default_i = UiParams()
        # delay = delay_ib(ind, Ts_fund, 'I', device, rbac_token)
        achievable_bw, q_bw = UiParams.default_bw(device, rbac_token)
        round_bw = int(np.ceil(achievable_bw / 10)) * 10

        props_ib = {
            'des_bw': round_bw,
            'des_z': 0.8,
            'des_mm': 0.5,
            'n_integrators': 1,
            'ref_delay': 0,
            'opt_method': 'Hinf',
            'n_r': 6, 'n_s': 6, 'n_t': 6,
            'n_ilc': 5,
            'n_q': 5, 'q_bw': q_bw,
            'control_mode': 'I',
            'test_select': False,
            'debug': False,
            'ilc_only': False,
            'noise_rej': []
        }
        for prop in props_ib:
            setattr(default_i, prop, props_ib[prop])
        return default_i

    @staticmethod
    def get_default_b(device: str, rbac_token: str = None):
        """
        :param device: FGC device name
        :type device: str
        :param rbac_token: RBAC token needed to access the FGC properties
        :type rbac_token: str
        :return: Object which contains the UI paramater default values
                 (for :ref:`control_mode <control_mode>` = ``B``).
        """
        default_b = UiParams()
        achievable_bw, q_bw = UiParams.default_bw(device, rbac_token, mode='B')
        round_bw = int(np.ceil(achievable_bw / 10)) * 10

        props_ib = {
            'des_bw': round_bw,
            'des_z': 0.8,
            'des_mm': 0.5,
            'n_integrators': 1,
            'ref_delay': 0,
            'opt_method': 'Hinf',
            'n_r': 6, 'n_s': 6, 'n_t': 6,
            'n_ilc': 5,
            'n_q': 5, 'q_bw': q_bw,
            'control_mode': 'B',
            'test_select': False,
            'debug': False,
            'ilc_only': False,
            'noise_rej': []
        }
        for prop in props_ib:
            setattr(default_b, prop, props_ib[prop])
        return default_b


    @staticmethod
    def get_default_v(device: str, rbac_token: str = None):
        """
        :param device: FGC device name
        :type device: str
        :param rbac_token: RBAC token needed to access the FGC properties
        :type rbac_token: str
        :return: Object which contains the UI paramater default values
                 (for :ref:`control_mode <control_mode>` = ``V``).
        """
        default_v = UiParams()
        achievable_bw, _ = UiParams.default_bw(device, rbac_token, mode='V')
        round_bw = int(np.ceil(achievable_bw / 10)) * 10

        props_v = {
            'damp_bw': int(1.5 * round_bw),
            'damp_z': 0.8,
            'volt_mm': 0.5,
            'damp_mm': 0.4,
            'opt_method': 'Hinf',
            'volt_bw': round_bw,
            'volt_z': 0.8,
            'ref_delay': 0,
            'control_mode': 'V',
            'debug': False,
            'positive_coeff': False,
            'kd_0': False
        }
        for prop in props_v:
            setattr(default_v, prop, props_v[prop])
        return default_v


class FgcProperties:
    """
    A class to send and extract the FGC device property values needed for the ObCD package.

    If :ref:`test_select <test_select>` = 1, the property values are extracted based on
    `LOAD.TEST_SELECT <https://proj-fgc.web.cern.ch/proj-fgc/
    gendoc/def/PropertyLOAD.htm#LOAD.TEST_SELECT>`__ .

    If :ref:`test_select <test_select>` = 0, the property values are extracted based on
    `LOAD.SELECT <https://proj-fgc.web.cern.ch/proj-fgc/
    gendoc/def/PropertyLOAD.htm#LOAD.SELECT>`__ .
    """

    prop_name_ib = ['LOAD.OHMS_SER', 'LOAD.OHMS_MAG', 'LOAD.OHMS_PAR', 'LOAD.HENRYS',
                'LOAD.GAUSS_PER_AMP', 'VS.SIM.BANDWIDTH', 'VS.SIM.Z', 'VS.ACTUATION',
                'VS.FIRING.DELAY', 'VS.ACT_DELAY_ITERS',
                'REG.{control_mode}.PERIOD_ITERS', 'FGC.ITER_PERIOD',
                'REG.{control_mode}.INTERNAL.PURE_DELAY_PERIODS',
                'MEAS.{control_mode}.DELAY_ITERS', 'MEAS.V.DELAY_ITERS',
                'REG.{control_mode}.EXTERNAL.MEAS_SELECT',
                'REG.{control_mode}.EXTERNAL.Z',
                'REG.{control_mode}.EXTERNAL.MOD_MARGIN',
                'REG.{control_mode}.EXTERNAL_ALG',
                'REG.{control_mode}.EXTERNAL.TRACK_DELAY_PERIODS']

    prop_name_v = ['LOAD.OHMS_SER', 'LOAD.OHMS_MAG',
                'LOAD.OHMS_PAR', 'LOAD.HENRYS', 'LOAD.GAUSS_PER_AMP',
                'VS.ACTUATION', 'VS.FIRING.DELAY', 'VS.ACT_DELAY_ITERS',
                'FGC.ITER_PERIOD', 'VS.FILTER.FARADS1',
                'VS.FILTER.FARADS2', 'VS.FILTER.OHMS', 'VS.FILTER.HENRYS',
                'REG.I.INTERNAL.PURE_DELAY_PERIODS',
                'MEAS.I.DELAY_ITERS', 'MEAS.V.DELAY_ITERS']

    def __init__(self):
        pass

    @staticmethod
    def from_fgc_ib(device: str, rbac_token: str = None, control_mode='I', test_select=False):
        """
        :param device: FGC device name
        :type device: str
        :param rbac_token: RBAC token needed to access the FGC properties
        :type rbac_token: str
        :param control_mode: Select FGC properties based on which loop to control. For current
                             control, ``I``; For field control, ``B``
        :type control_mode: str
        :param test_select: Select FGC properties based on test parameters
        :type test_select: bool
        :return: Object which contains the FGC properties and values needed for
                 current/field control.
        """
        def hasNumbers(inputString):
            return any(char.isdigit() for char in inputString)

        fgc_props = FgcProperties()
        # control_mode = user_pars.control_mode

        if test_select:
            ind = int(pyfgc.get(device, 'LOAD.TEST_SELECT', rbac_token=rbac_token).value)
        else:
            ind = int(pyfgc.get(device, 'LOAD.SELECT', rbac_token=rbac_token).value)

        for prop_pattern in fgc_props.prop_name_ib:
            prop = prop_pattern.format(control_mode=control_mode)
            r = pyfgc.get(device, prop, rbac_token=rbac_token)
            p_val_all = r.value.split(',')

            if len(p_val_all) > 1 and hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, float(p_val_all[ind]))
            elif len(p_val_all) > 1 and not hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, p_val_all[ind])

            if len(p_val_all) == 1 and hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, float(p_val_all[0]))
            elif len(p_val_all) == 1 and not hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, p_val_all[0])

        fir = f'MEAS.{control_mode}.FIR_LENGTHS'
        R = f'REG.{control_mode}.EXTERNAL.OP.R'
        S = f'REG.{control_mode}.EXTERNAL.OP.S'
        T = f'REG.{control_mode}.EXTERNAL.OP.T'
        Rl = [float(i) for i in pyfgc.get(device, R, rbac_token=rbac_token).value.split(',')]
        Sl = [float(i) for i in pyfgc.get(device, S, rbac_token=rbac_token).value.split(',')]
        Tl = [float(i) for i in pyfgc.get(device, T, rbac_token=rbac_token).value.split(',')]
        setattr(fgc_props, fir, list(map(int, pyfgc.get(device,
                    fir, rbac_token=rbac_token).value.split(','))))
        setattr(fgc_props, R, Rl)
        setattr(fgc_props, S, Sl)
        setattr(fgc_props, T, Tl)

        return fgc_props

    @staticmethod
    def from_fgc_v(device: str, rbac_token: str = None):
        """
        :param device: FGC device name
        :type device: str
        :param rbac_token: RBAC token needed to access the FGC properties
        :type rbac_token: str
        :return: Object which contains the FGC properties and values needed for
                 voltage control.
        """
        fgc_props = FgcProperties()

        ind = int(pyfgc.get(device, 'LOAD.SELECT', rbac_token=rbac_token).value)

        def hasNumbers(inputString):
            return any(char.isdigit() for char in inputString)

        for prop in fgc_props.prop_name_v:
            r = pyfgc.get(device, prop, rbac_token=rbac_token)
            p_val_all = r.value.split(',')

            if len(p_val_all) > 1 and hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, float(p_val_all[ind]))
            elif len(p_val_all) > 1 and not hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, p_val_all[ind])

            if len(p_val_all) == 1 and hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, float(p_val_all[0]))
            elif len(p_val_all) == 1 and not hasNumbers(p_val_all[0]):
                setattr(fgc_props, prop, p_val_all[0])

        # with open('FgcProps_v_file.json', 'w') as outfile:
        #    json.dump(vars(fgc_props), outfile)

        return fgc_props

    @staticmethod
    def to_fgc_ib(opt_result, user_pars, device: str, rbac_token: str = None):
        """
        Sends the optimization results for current/field control to the FGC and sets
        `REG.I.EXTERNAL_ALG <http://proj-fgc.web.cern.ch/proj-fgc/
        gendoc/def/PropertyREG.htm#REG.I.EXTERNAL_ALG>`__
        (or
        `REG.B.EXTERNAL_ALG <http://proj-fgc.web.cern.ch/proj-fgc/
        gendoc/def/PropertyREG.htm#REG.B.EXTERNAL_ALG>`__ )
        to *ENABLED* (depending on the selection of :ref:`control_mode <control_mode>`).

        :param opt_result: RST and ILC parameters resulting from the optimization algorithms.
        :type opt_result: class
        :param user_pars: UI input parameters.
        :type user_pars: class
        :param device: FGC device name
        :type device: str
        :param rbac_token: RBAC token needed to access the FGC properties
        :type rbac_token: str
        :return: Not applicable.
        """
        def hasNumbers(inputString):
            return any(char.isdigit() for char in inputString)

        control_mode = user_pars.control_mode
        test_select = user_pars.test_select

        if test_select:
            ind = str(int(pyfgc.get(device, 'LOAD.TEST_SELECT', rbac_token=rbac_token).value))
        else:
            ind = str(int(pyfgc.get(device, 'LOAD.SELECT', rbac_token=rbac_token).value))

        par_dict = {f'REG.{control_mode}.EXTERNAL_ALG[{ind}]': 'ENABLED',
                f'REG.{control_mode}.EXTERNAL.CLBW[{ind}]': user_pars.des_bw,
                f'REG.{control_mode}.EXTERNAL.Z[{ind}]': user_pars.des_z,
                f'REG.{control_mode}.EXTERNAL.MOD_MARGIN[{ind}]': user_pars.des_mm,
                f'REG.{control_mode}.EXTERNAL.TRACK_DELAY_PERIODS[{ind}]': opt_result.track_delay,
                'REF.ILC.ORDER': 0,
                'REF.ILC.FUNCTION': ','.join([str(x) for x in opt_result.L])}

        if test_select:
            par_dict[f'REG.{control_mode}.EXTERNAL.TEST.R'] = \
                ','.join([str(x) for x in opt_result.R])
            par_dict[f'REG.{control_mode}.EXTERNAL.TEST.S'] = \
                ','.join([str(x) for x in opt_result.S])
            par_dict[f'REG.{control_mode}.EXTERNAL.TEST.T'] = \
                ','.join([str(x) for x in opt_result.T])
        else:
            par_dict[f'REG.{control_mode}.EXTERNAL.OP.R'] = \
                ','.join([str(x) for x in opt_result.R])
            par_dict[f'REG.{control_mode}.EXTERNAL.OP.S'] = \
                ','.join([str(x) for x in opt_result.S])
            par_dict[f'REG.{control_mode}.EXTERNAL.OP.T'] = \
                ','.join([str(x) for x in opt_result.T])

        if user_pars.q_bw > 0:
            par_dict['REF.ILC.Q_FUNCTION'] = ','.join([str(x)
                                            for x in opt_result.Q[user_pars.n_q:]])

        for par in par_dict:
            pyfgc.set(device, par, par_dict[par], rbac_token=rbac_token)

        # time.sleep(1)

        # for par in par_dict:
        #    if hasNumbers(str(par_dict[par])):
        #        v_get = [float(i) for i in pyfgc.get(device, par,
        #                rbac_token=rbac_token).value.split(',')]
        #        v_sent = [float(i) for i in str(par_dict[par]).split(',')]
        #        if abs(sum(np.array(v_get) - np.array(v_sent))) >= 1e-4:
        #            print(f'WARNING: Conflict with {par} in FGC and results from PyFresco.')

    @staticmethod
    def to_fgc_v(opt_result, user_pars, device: str, rbac_token: str = None):
        """
        Sends the optimization results for voltage control to the FGC.

        :param opt_result: Damping and voltage parameters resulting from the optimization
                           algorithms.
        :type opt_result: class
        :param user_pars: UI input parameters.
        :type user_pars: class
        :param device: FGC device name
        :type device: str
        :param rbac_token: RBAC token needed to access the FGC properties
        :type rbac_token: str
        :return: Not applicable.
        """

        par_dict = {'REG.V.FILTER.EXTERNAL.K_I': opt_result.Kd[0],
            'REG.V.FILTER.EXTERNAL.K_D': opt_result.Kd[1],
            'REG.V.FILTER.EXTERNAL.K_U': opt_result.Kd[2],
            'REG.V.FILTER.EXTERNAL.CLBW': user_pars.damp_bw,
            'REG.V.FILTER.EXTERNAL.Z': user_pars.damp_z,
            'REG.V.EXTERNAL.K_P': opt_result.Kv[0],
            'REG.V.EXTERNAL.K_INT': opt_result.Kv[1],
            'REG.V.EXTERNAL.K_FF': opt_result.Kv[2],
            'REG.V.EXTERNAL.CLBW': user_pars.volt_bw,
            'REG.V.EXTERNAL.Z': user_pars.volt_z}

        for par in par_dict:
            pyfgc.set(device, par, par_dict[par], rbac_token=rbac_token)

        # time.sleep(1)

        # for par in par_dict:
        #    V = float(pyfgc.get(device, par, rbac_token=rbac_token).value)
        #    if np.abs(V - par_dict[par]) >= 1e-4:
        #        print(f'WARNING: Conflict with {par} in FGC and results from PyFresco.')
