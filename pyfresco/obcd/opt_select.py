import numpy as np
from pyfresco.obcd import constants as cn
from pyfresco.obcd import build_model as bm
from pyfresco.obcd import common_funcs as cf
from .exceptions import Check
from .OptAlgoIB import OptAlgoIB
from .OptAlgoV import OptAlgoV
from tabulate import tabulate


class OptResult:

    def __init__(self):
        pass

    @staticmethod
    def rst_ilc_obj(ilc_only, opt_out, ILC_out, dtrack, n_integrators, print_callback, debug):
        x = OptResult()
        # x = OptimizeIB(self.prop_class, self.user_pars)
        if not ilc_only:
            Rv = opt_out['R_vec']
            n_int_av = np.array([1, -1])
            n_int_a = np.polynomial.polynomial.polypow(n_int_av, n_integrators)
            sv = np.insert(opt_out['S_vec'], 0, 1)
            Sv = np.convolve(sv, n_int_a)
            Tv = opt_out['T_vec'] / opt_out['Gain']
        else:
            Rv = opt_out['R_vec']
            Sv = opt_out['S_vec']
            Tv = opt_out['T_vec']

        x.R, x.S, x.T, x.track_delay = Rv, Sv, Tv, dtrack
        x.L, x.Q = ILC_out['L_vec'], ILC_out['Q_vec']
        if debug:
            print_callback('raw', 'RST:')
            print_callback('raw', f'R: {x.R}')
            print_callback('raw', f'S: {x.S}')
            print_callback('raw', f'T: {x.T}')
            print_callback('raw', '\n')
            print_callback('raw', 'ILC:')
            print_callback('raw', f'Q: {x.Q}')
            print_callback('raw', f'L: {x.L}')
            print_callback('raw', '\n')
        return x

    @staticmethod
    def volt_obj(Kd, Kv, kd_constraint, print_callback, debug):
        x = OptResult()
        x.Kd, x.Kv = Kd, Kv
        if kd_constraint:
            x.Kd[1] = 0
        if debug:
            print_callback('raw', 'Damping parameters:')
            print_callback('raw', f'[ki, kd, kv]: {x.Kd}')
            print_callback('raw', '\n')
            print_callback('raw', 'Voltage parameters:')
            print_callback('raw', f'[kp, kint, kff]: {x.Kv}')
        return x


class OptimizeIB:
    """
    This class is used to call and execute the optimization algorithm in OptAlgoIB
    (for current/field control). The methods in this class iterate over the controller
    orders and display exceptions when an infeasibility occurs.
    Both model-driven and data-driven designs are used within this class.
    """
    def __init__(self, prop, user_pars, print_callback=print):
        """
        :param prop: Object of the FGC properties obtained with
                     **pyfresco.obcd.FgcProperties.from_fgc_ib**.
        :type prop: class
        :param user_pars: UI input parameters
                          (for :ref:`control_mode <control_mode>` = ``I`` or ``B``).
        :type user_pars: class
        :param print_callback: Callback function which outputs print commands to the console.
        :type print_callback: func
        """
        self.prop = vars(prop)
        self.prop_class = prop
        self.user_pars = user_pars
        self.Ts = int(self.prop[f'REG.{self.user_pars.control_mode}.PERIOD_ITERS']) * \
            round(self.prop['FGC.ITER_PERIOD'], 6)
        self.print_callback = print_callback
        if self.user_pars.debug:
            print_callback('raw', 'FGC Properties:')
            for key, value in vars(prop).items():
                print_callback('raw', f'{key}: {value}')
            print_callback('raw', '\n')
            print_callback('raw', 'UI Properties:')
            for key, value in vars(user_pars).items():
                print_callback('raw', f'{key}: {value}')

    def rst_opt_results(self, P, rst_out):

        Rf, Sf, Tf = (rst_out['Rf'], rst_out['Sf'], rst_out['Tf'])
        obj, Sens_ry = [], []

        if self.user_pars.opt_method == "Hinf" or self.user_pars.ilc_only:
            for (k, G) in enumerate(P.G_multi):
                Sens_ry.append((G * Tf) / (G * P.MA * Rf + Sf))
                obj.append(np.amax(np.abs(P.Wd * (1 - Sens_ry[k]))))
            print_gamma = cn.uginf
        elif self.user_pars.opt_method == "H2":
            for (k, G) in enumerate(P.G_multi):
                Sens_ry.append((G * Tf) / (G * P.MA * Rf + Sf))
                obj.append(cf.Funcs.norm2(self.Ts, P.w,
                (2 * np.pi * self.user_pars.des_bw) / (1j * P.w) * (Sens_ry[k] - P.Td)))
            print_gamma = cn.ug2
        elif self.user_pars.opt_method == "H1":
            for (k, G) in enumerate(P.G_multi):
                Sens_ry.append((G * Tf) / (G * P.MA * Rf + Sf))
                obj.append(cf.Funcs.norm1(self.Ts, P.w,
                    (2 * np.pi * self.user_pars.des_bw) / (1j * P.w) * (Sens_ry[k] - P.Td)))
            print_gamma = cn.ug1

        phase = np.unwrap(np.angle(np.mean(Sens_ry, axis=0)))
        Group_Delay = -np.gradient(phase, P.w)
        dtrack = Group_Delay[0] / self.Ts
        df_bode = cf.Funcs.sensitivities_ib(P, Rf, Sf, Tf)

        bw1 = cf.Funcs.bw_estimate(P.w, Sens_ry, self.print_callback)
        margins = cf.Funcs.margin(P.w, df_bode, self.print_callback)
        if len(margins['gain_margin']) > 1:
            gm = margins['gain_margin']
            pm = margins['phase_margin']
            dm = margins['delay_margin']
            mm = margins['modulus_margin']
        else:
            gm = margins['gain_margin'][0]
            pm = margins['phase_margin'][0]
            dm = margins['delay_margin'][0]
            mm = margins['modulus_margin'][0]

        if not self.user_pars.ilc_only:
            table = \
                tabulate([['RST', round(np.max(obj), cn.g_digits), bw1, gm, pm, dm, mm]],
                headers=[
                    '',
                    print_gamma,
                    f'Bandwidth \n (average) [Hz] \n (desired = {self.user_pars.des_bw} Hz)',
                    'Gain \n Margin [dB]',
                    'Phase \n Margin [deg]',
                    'Delay \n Margin [ms]',
                    f'Modulus \n Margin [-] \n (desired = {self.user_pars.des_mm})'],
                    tablefmt='orgtbl')
        elif self.user_pars.ilc_only:
            table = \
                tabulate([['RST', round(np.max(obj), cn.g_digits), bw1, gm, pm, dm, mm]],
                headers=[
                    '',
                    print_gamma,
                    f'Bandwidth \n (average) [Hz]',
                    'Gain \n Margin [dB]',
                    'Phase \n Margin [deg]',
                    'Delay \n Margin [ms]',
                    f'Modulus \n Margin [-]'],
                    tablefmt='orgtbl')

        return dtrack, df_bode, margins, Sens_ry, table

    def closed_loop_ilc_only(self, P=None, model=None):

        ext_alg = f'REG.{self.user_pars.control_mode}.EXTERNAL_ALG'
        if self.prop[ext_alg] == 'DISABLED':
            raise Exception(f'The property {ext_alg} is currently disabled. To enable an '
                            'externally calculated ILC, you must enable the externally '
                            'calculated RST.')
        rho_r = np.array(self.prop[f'REG.{self.user_pars.control_mode}.EXTERNAL.OP.R'])
        rho_s = np.array(self.prop[f'REG.{self.user_pars.control_mode}.EXTERNAL.OP.S'])
        rho_t = np.array(self.prop[f'REG.{self.user_pars.control_mode}.EXTERNAL.OP.T'])
        dtrack = self.prop[f'REG.{self.user_pars.control_mode}.EXTERNAL.TRACK_DELAY_PERIODS']
        rst_out = {'R_vec': rho_r, 'S_vec': rho_s, 'T_vec': rho_t}

        rho_r = rho_r[np.nonzero(rho_r)[0]]
        rho_s = rho_s[np.nonzero(rho_s)[0]]
        rho_t = rho_t[np.nonzero(rho_t)[0]]
        if (not rho_r.any()) or (not rho_s.any()) or (not rho_t.any()):
            raise Exception('You must have non-zero elements for the externally calculated RST. '
                            'Either run a full RST and ILC optimization or provide a set of '
                            'non-zero arrays for the RST (through the FGC).')

        if model:
            Nc = len(rho_r) + len(rho_s) + len(rho_t)
            mod = bm.Model(self.user_pars, self.prop)
            self.print_callback('info', 'Building model from FGC properties.')
            G, w = mod.model_frf(Nc, cn.epsilon, cn.beta)
            ma_filt = bm.MA_filter(w, self.user_pars.control_mode, self.prop)
            P = OptAlgoIB([G], ma_filt, w, self.Ts, self.user_pars, self.print_callback)

        z = lambda x: np.exp(x * 1j * P.w * self.Ts)

        Ro = 0
        for i in range(len(rho_r)):
            Ro += rho_r[i] * z(-i)

        So = 0
        for i in range(len(rho_s)):
            So += rho_s[i] * z(-i)

        To = 0
        for i in range(len(rho_t)):
            To += rho_t[i] * z(-i)

        rst_out['Rf'], rst_out['Sf'], rst_out['Tf'] = Ro, So, To
        Sens_ry = []
        for (k, G) in enumerate(P.G_multi):
            Sens_ry.append((G * To) / (G * P.MA * Ro + So))

        return P, Sens_ry, rst_out, dtrack


    def ilc_opt(self, P, CL):
        ilc_flag = True
        while ilc_flag:
            ILC_out = P.ilc(CL, self.user_pars.n_ilc)
            ilc_flag = ILC_out['flag']
            if ilc_flag:
                self.print_callback('warning', 'ILC problem infeasible...Increasing filter order')
                self.user_pars.n_ilc += 1
            if self.user_pars.n_ilc > cn.max_l_order:
                raise Exception('Could not find a robust ILC filter.')

        gamma_l = ILC_out['gamma_opt']
        self.print_callback('info',
            f'ILC design finished! ({cn.ugilc} = {round(gamma_l[0], cn.g_digits)})')
        return ILC_out

    def h1(self, P):

        H1_flag = True
        while H1_flag:
            rst_out = P.h1({'n_r': self.user_pars.n_r, 'n_s': self.user_pars.n_s,
                    'n_t': self.user_pars.n_t}, T_stable_flag=False)

            H1_flag = rst_out['RS-flag'] or rst_out['T-flag']

            if not H1_flag:
                T_roots_max = np.amax(np.abs(np.roots(rst_out['T_vec'])))
                if T_roots_max < 1:
                    self.print_callback('info', 'RST design finished!')
                    break
                else:
                    self.print_callback('warning', 'T has unstable zero. Will re-optimize '
                        'to ensure T^{-1} is stable...')
                    rst_out = P.h1({'n_r': self.user_pars.n_r, 'n_s': self.user_pars.n_s,
                        'n_t': self.user_pars.n_t}, T_stable_flag=True)
                    H1_flag = rst_out['RS-flag'] or rst_out['T-flag']
                    if not H1_flag:
                        self.print_callback('info', 'RST design finished!')
                        break
                    else:
                        raise Exception('Infeasible problem with H1 control. Try '
                                'increasing the controller orders.')
            else:
                if not H1_flag and self.user_pars.n_t >= cn.max_rst_coeff + 1:
                    raise Exception('Maximum coeffs of T reached. '
                                'Could not find a solution.')
                if rst_out['RS-flag']:
                    if self.user_pars.n_r == cn.max_rst_coeff or \
                            self.user_pars.n_s == cn.max_rst_coeff:
                        raise Exception('Maximum coeffs of R or S reached. Could not find a'
                                    ' solution.')
                    self.print_callback('warning',
                        'Initial RS design failed...increasing order of R and S')
                    self.user_pars.n_r += 1
                    self.user_pars.n_s += 1
                    self.user_pars.n_t += 1
                elif not rst_out['RS-flag'] and rst_out['T-flag']:
                    if self.user_pars.n_t == cn.max_rst_coeff:
                        raise Exception('Maximum coeffs of T reached. Could not find a '
                                    'solution.')
                    self.print_callback('warning', 'T design failed...increasing order of T')
                    self.user_pars.n_t += 1

        dtrack, df_bode, margins, CL, table = OptimizeIB.rst_opt_results(self, P, rst_out)

        self.print_callback('info', 'Starting optimization for ILC filter...')
        ilc_out = OptimizeIB.ilc_opt(self, P, CL)
        self.print_callback('raw', table)
        opt_result = OptResult().rst_ilc_obj(self.user_pars.ilc_only, rst_out, ilc_out, dtrack,
                    self.user_pars.n_integrators, self.print_callback, self.user_pars.debug)
        return opt_result, df_bode, margins

    def hinf_h2(self, P, init_out, **kwargs):

        self.print_callback('info', 'Now reducing the controller order...')
        gamma_BI, gamma_LMI = init_out['gamma_opt'], 1e6

        if self.user_pars.opt_method == "Hinf":
            while gamma_LMI - gamma_BI > 0:
                rst_out = P.hinf(init_out['Rf'], init_out['Sf'],
                    {'n_r': self.user_pars.n_r,
                    'n_s': self.user_pars.n_s,
                    'n_t': self.user_pars.n_t},
                    kwargs['T_flag'])
                gamma_LMI = rst_out['gamma_opt']
                if gamma_LMI < 1:
                    self.print_callback('error', 'Infeasible problem. Returning sub-optimal '
                        'controller. Try increasing the RST order or relaxing the problem '
                        'for better performance.')
                    rst_out = init_out
                    break
                elif gamma_LMI > cn.g_thresh:
                    self.user_pars.n_r += 1
                    self.user_pars.n_s += 1
                    self.user_pars.n_t += 1
                    self.print_callback('warning',
                        'Infeasible problem. Increasing controller order... '
                        f'R-order = {self.user_pars.n_r - 1}; '
                        f'S-order = {self.user_pars.n_s + self.user_pars.n_integrators}; '
                        f'T-order = {self.user_pars.n_t - 1}')
                elif (gamma_LMI - gamma_BI > 0) and (gamma_LMI < cn.g_thresh):
                    self.user_pars.n_r += 1
                    self.user_pars.n_s += 1
                    self.user_pars.n_t += 1
                    self.print_callback('info',
                        'Feasible, but still sub-optimal. Increasing controller order... '
                        f'R-order = {self.user_pars.n_r - 1}; '
                        f'S-order = {self.user_pars.n_s + self.user_pars.n_integrators}; '
                        f'T-order = {self.user_pars.n_t - 1}')
                else:
                    pass

        elif self.user_pars.opt_method == "H2":
            while gamma_LMI > cn.g_thresh:
                rst_out = P.h2(init_out['Rf'], init_out['Sf'],
                    {'n_r': self.user_pars.n_r,
                    'n_s': self.user_pars.n_s,
                    'n_t': self.user_pars.n_t},
                    kwargs['T_flag'])
                gamma_LMI = rst_out['gamma_opt']
                if gamma_LMI > cn.g_thresh:
                    self.user_pars.n_r += 1
                    self.user_pars.n_s += 1
                    self.user_pars.n_t += 1
                    self.print_callback('warning',
                                    'Infeasible problem. Increasing controller order... '
                                    f'R-order = {self.user_pars.n_r - 1}; '
                                    f'S-order = {self.user_pars.n_s + self.user_pars.n_integrators}; '
                                    f'T-order = {self.user_pars.n_t - 1}')
                elif gamma_LMI <= cn.g_thresh:
                    T_roots_max = np.amax(np.abs(np.roots(rst_out['T_vec'])))
                    if T_roots_max < 1:
                        pass
                    else:
                        self.print_callback('warning', 'T has unstable zero. Will re-optimize '
                            'to ensure T^{-1} is stable...')
                        T_flag = True
                        rst_out = P.h2(init_out['Rf'], init_out['Sf'],
                                       {'n_r': self.user_pars.n_r,
                                        'n_s': self.user_pars.n_s,
                                        'n_t': self.user_pars.n_t},
                                       T_flag)
                        gamma_LMI = rst_out['gamma_opt']
                        self.user_pars.n_r += 1
                        self.user_pars.n_s += 1
                        self.user_pars.n_t += 1

        self.print_callback('info', 'RST design finished!')
        dtrack, df_bode, margins, CL, table = OptimizeIB.rst_opt_results(self, P, rst_out)

        self.print_callback('info', 'Starting optimization for ILC filter...')
        ilc_out = OptimizeIB.ilc_opt(self, P, CL)
        self.print_callback('raw', table)
        opt_result = OptResult().rst_ilc_obj(self.user_pars.ilc_only, rst_out, ilc_out, dtrack,
                    self.user_pars.n_integrators, self.print_callback, self.user_pars.debug)
        return opt_result, df_bode, margins


    def rst_init_iter(self, P=None, model=None):
        n_high = cn.init_rst_vec
        if model:
            mod = bm.Model(self.user_pars, self.prop)
        for i in n_high:
            if model:
                self.print_callback('info', 'Building model from FGC properties.')
                G, w = mod.model_frf(3 * i, cn.epsilon, cn.beta)
                ma_filt = bm.MA_filter(w, self.user_pars.control_mode, self.prop)

                self.print_callback('info',
                    f'Setting up optimization problem (initial RST order = {i-1}).')
                P = OptAlgoIB([G], ma_filt, w, self.Ts, self.user_pars, self.print_callback)

            self.print_callback('info', 'Starting optimization for initial stabilizing '
                f'RST with {self.user_pars.opt_method} performance')
            BI_out = P.rst_init({'n_r': i, 'n_s': i, 'n_t': i}, T_flag=False)
            gamma_BI = BI_out['gamma_opt']

            if i == cn.max_rst_coeff and gamma_BI > cn.g_max:
                raise Exception('Could not find a solution for the initial RST design. '
                    'Please change your desired parameters and/or check your input data.')

            if gamma_BI <= cn.g_max:
                T_roots_max = np.amax(np.abs(np.roots(BI_out['T_vec'])))
                if T_roots_max < 1:
                    T_flag = False
                    self.print_callback('info',
                        f'Initial RST design finished! '
                        f'({cn.ug}_init = {round(gamma_BI, cn.g_digits)}).')
                    break
                else:
                    self.print_callback('warning', 'T has unstable zero. Will re-optimize '
                        'to ensure T^{-1} is stable...')
                    T_flag = True
                    BI_out = P.rst_init({'n_r': i, 'n_s': i, 'n_t': i}, T_flag=T_flag)
                    if BI_out['gamma_opt'] <= cn.g_max:
                        self.print_callback('info',
                            f'Initial RST design finished! '
                            f'({cn.ug}_init = {round(gamma_BI, cn.g_digits)}).')
                        break

            elif gamma_BI > cn.g_max:
                self.print_callback('warning',
                    'Poor performance for initializing RST...Increasing order.')
        return BI_out, P, T_flag

    def model_opt(self):
        """
        Function to execute the model-driven design.

        :return: Object containing optimization results (RST and ILC parameters); Dataframe
                 containing frequency [Hz], gain [dB], and phase [deg] of multiple sensitivity
                 functions; dictionary containing the robustness margins (``modulus_margin``,
                 ``gain_margin`` [dB], ``phase_margin`` [deg], ``delay_margin`` [ms]).
        :rtype: class, dataframe, dict
        """
        Check.check_ib_pars(self.user_pars, self.print_callback)
        Check.prop_ib_model(self.user_pars, self.prop, self.print_callback)
        mod = bm.Model(self.user_pars, self.prop)
        if not self.user_pars.ilc_only:
            if self.user_pars.opt_method in ["H2", "Hinf"]:
                BI_out, P, T_flag = OptimizeIB.rst_init_iter(self, model=True)
                self.print_callback('info', f'Starting RST optimization for '
                    f'{self.user_pars.opt_method} performance.')
                opt_result, df_sens, margins = OptimizeIB.hinf_h2(self, P, BI_out, T_flag=T_flag)
            else:
                self.print_callback('info', f'Starting RST optimization for '
                        f'{self.user_pars.opt_method} performance.')
                G, w = mod.model_frf(self.user_pars.n_r + self.user_pars.n_s + self.user_pars.n_t,
                        cn.epsilon, cn.beta)
                ma_filt = bm.MA_filter(w, self.user_pars.control_mode, self.prop)
                P = OptAlgoIB([G], ma_filt, w, self.Ts, self.user_pars, self.print_callback)
                opt_result, df_sens, margins = OptimizeIB.h1(self, P)
        elif self.user_pars.ilc_only:
            P, CL, rst_out, dtrack = OptimizeIB.closed_loop_ilc_only(self, model=True)
            self.print_callback('warning', 'Starting (model-based) optimization for ILC only.')
            ilc_out = OptimizeIB.ilc_opt(self, P, CL)
            opt_result = OptResult().rst_ilc_obj(self.user_pars.ilc_only, rst_out, ilc_out, dtrack,
                                                 0, self.print_callback, self.user_pars.debug)
            _, df_sens, margins, CL, table = OptimizeIB.rst_opt_results(self, P, rst_out)
            self.print_callback('raw', table)
        return opt_result, df_sens, margins

    @staticmethod
    def data_check_freq(df_tot):
        f = []
        if len(df_tot) == 1:
            pass
        elif len(df_tot) > 1:
            for df in df_tot:
                f.append(df['f'].values)

            for i in range(len(f) - 1):
                if np.array_equal(f[i], f[i + 1]) == False:
                    raise Exception('Frequency arrays for selected frequency responses '
                        'incoherent. Please select data with the same frequency arrays.')
        else:
            raise Exception('Dataframe must contain valid data.')
        return None

    def data_setup(self, df_tot):
        Ts_fund, Fs = round(self.prop['FGC.ITER_PERIOD'], 6), 1 / self.Ts
        G_multi = []
        for (df_ind, df) in enumerate(df_tot):
            del_freq = 5
            if df['f'].iloc[-1] >= Fs / 2 - del_freq:
                k_ind = np.where(2 * df['f'].values <= Fs)[0][-1] + 1
                w, G = cf.Funcs.df_to_complex(df, index=k_ind)
            elif df['f'].iloc[-1] < Fs / 2 - del_freq:
                T_permitted = Ts_fund * np.arange(1, 5000, 1)
                F_permitted = 1. / T_permitted
                k_fmax = np.where(F_permitted >= 2 * df['f'].iloc[-1])
                if round(2 * df['f'].iloc[-1], 1) in F_permitted:
                    f_sample_max = F_permitted[k_fmax[0][-1]]
                else:
                    f_sample_max = F_permitted[k_fmax[0][-1] + 1]
                Ts_max = 1 / f_sample_max
                div = int(np.ceil(Ts_max / Ts_fund))
                raise Exception('Insufficient data for the current regulation frequency. '
                        f'REG.{self.user_pars.control_mode}.PERIOD_ITERS must be >= {div}.')

            # print(f'Max freq of data = {w[-1] / (2 * np.pi)}, Fs/2 = {Fs / 2}')

            # Interpolate frequency response if not enough points for the controller optimization
            if len(w) <= 80:
                self.print_callback('warning',
                                    'Not enough frequency points for controller design. '
                                    'Will interpolate frequency response with more points.')
                w, G = cf.Funcs.interp_freq(w, G)

            # Interpolate for points selected in noise_rej object
            if self.user_pars.noise_rej:
                for pair in self.user_pars.noise_rej:
                    if pair[0] > 1 / (2 * self.Ts) or 2 * np.pi * pair[0] < w[0]:
                        raise Exception(f'ERROR: Cannot have a noise rejection frequency outside '
                                f'of the range [{w[0] / (2 * np.pi)}, {1 / (2 * self.Ts)}] Hz')
                    test_index = np.where(w == 2 * np.pi * pair[0])[0]
                    if test_index.any():
                        pass
                    else:
                        wr = 2 * np.pi * pair[0]
                        ind = np.where(w < wr)[0][-1] + 1
                        db_int = cf.Funcs.interp_y(w, 20 * np.log10(np.abs(G)), ind, wr)
                        phase_int = cf.Funcs.interp_y(w, np.unwrap(np.angle(G)), ind, wr)

                        w = np.sort(np.concatenate((w, [wr])))
                        index = np.where(w == wr)[0][0]
                        G = np.insert(G, index, np.power(10, db_int / 20) * np.exp(1j * phase_int))
            G_multi.append(G)
        return w, G_multi

    def data_opt(self, df_tot):
        """
        Function to execute the data-driven design.

        :param df_tot: List of dataframes, where each index of the list has a dataframe
                       containing the frequency [Hz], gain [dB] and phase [deg] arrays.
        :type df_tot: list of dataframes
        :return: Object containing optimization results (RST and ILC parameters); Dataframe
                 containing frequency [Hz], gain [dB], and phase [deg] of multiple sensitivity
                 functions; dictionary containing the robustness margins (``modulus_margin``,
                 ``gain_margin`` [dB], ``phase_margin`` [deg], ``delay_margin`` [ms]).
        :rtype: class, dataframe, dict
        """
        Check.check_ib_pars(self.user_pars, self.print_callback)
        OptimizeIB.data_check_freq(df_tot)
        w, G_multi = OptimizeIB.data_setup(self, df_tot)

        ma_filt = bm.MA_filter(w, self.user_pars.control_mode, self.prop)
        P = OptAlgoIB(G_multi, ma_filt, w, self.Ts, self.user_pars, self.print_callback)

        if not self.user_pars.ilc_only:
            if self.user_pars.opt_method in ["H2", "Hinf"]:
                BI_out, _, T_flag = OptimizeIB.rst_init_iter(self, P=P)
                opt_result, df_sens, margins = OptimizeIB.hinf_h2(self, P, BI_out, T_flag=T_flag)
            else:
                self.print_callback('info',
                    f'Starting optimization for {self.user_pars.opt_method} performance.')
                opt_result, df_sens, margins = OptimizeIB.h1(self, P)
        elif self.user_pars.ilc_only:
            _, CL, rst_out, dtrack = OptimizeIB.closed_loop_ilc_only(self, P=P)
            self.print_callback('warning', 'Starting (data-driven) optimization for ILC only.')
            ilc_out = OptimizeIB.ilc_opt(self, P, CL)
            opt_result = OptResult().rst_ilc_obj(self.user_pars.ilc_only, rst_out, ilc_out, dtrack,
                                                 0, self.print_callback, self.user_pars.debug)
            _, df_sens, margins, CL, table = OptimizeIB.rst_opt_results(self, P, rst_out)
            self.print_callback('raw', table)

        return opt_result, df_sens, margins


class OptimizeV:
    """
    This class is used to call and execute the optimization algorithm in OptAlgoV
    (for voltage control). Both model-driven and data-driven designs are used within this class.
    """
    def __init__(self, prop, user_pars, print_callback=print):
        """
        :param prop: Object of the FGC properties obtained with
                     **pyfresco.obcd.FgcProperties.from_fgc_v**.
        :type prop: class
        :param user_pars: UI input parameters (for :ref:`control_mode <control_mode>` = ``V``).
        :type user_pars: class
        :param print_callback: Callback function which outputs print commands to the console.
        :type print_callback: func
        """
        self.prop = vars(prop)
        self.prop_class = prop
        self.user_pars = user_pars
        self.Ts_fund = round(self.prop['FGC.ITER_PERIOD'], 6)
        self.print_callback = print_callback
        if self.user_pars.debug:
            print_callback('raw', 'FGC Properties:')
            for key, value in vars(prop).items():
                print_callback('raw', f'{key}: {value}')
            print_callback('raw', '\n')
            print_callback('raw', 'UI Properties:')
            for key, value in vars(user_pars).items():
                print_callback('raw', f'{key}: {value}')

    def volt_opt_results(self, P, damping, voltage):
        if self.user_pars.opt_method == "Hinf":
            obj_damping = np.amax(np.abs(P.Wd_filt * (1 - damping['T-damping'])))
            obj_voltage = np.amax(np.abs(P.Wd * (1 - voltage['T-voltage'])))
            print_gamma = cn.uginf
        elif self.user_pars.opt_method == "H2":
            obj_damping = cf.Funcs.norm2(self.Ts_fund, P.w,
                (2 * np.pi * self.user_pars.damp_bw) /
                (1j * P.w) * (damping['T-damping'] - P.Td_filt))
            obj_voltage = cf.Funcs.norm2(self.Ts_fund, P.w,
            (2 * np.pi * self.user_pars.volt_bw) / (1j * P.w) * (voltage['T-voltage'] - P.Td))
            print_gamma = cn.ug2
        bw_damp = cf.Funcs.bw_estimate(P.w, [damping['T-damping']], self.print_callback)
        bw_volt = cf.Funcs.bw_estimate(P.w, [voltage['T-voltage']], self.print_callback)
        df_bode = cf.Funcs.sensitivities_v(P, damping['T-damping'], voltage['T-voltage'],
                    damping['Sens-damp'], voltage['Sens-volt'])
        margins_damp = cf.Funcs.margin(P.w, [df_bode], self.print_callback, mode='D')
        margins = cf.Funcs.margin(P.w, [df_bode], self.print_callback, mode='V')

        self.print_callback('raw',
            tabulate([['Damping-loop', round(obj_damping, cn.g_digits),
                f'{bw_damp} (desired = {self.user_pars.damp_bw} Hz)',
                margins_damp['gain_margin'][0],
                margins_damp['phase_margin'][0],
                margins_damp['delay_margin'][0],
                f"{margins_damp['modulus_margin'][0]} (desired = {self.user_pars.damp_mm})"],
                ['Voltage-loop', round(obj_voltage, cn.g_digits),
                f'{bw_volt} (desired = {self.user_pars.volt_bw} Hz)',
                margins['gain_margin'][0],
                margins['phase_margin'][0],
                margins['delay_margin'][0],
                f"{margins['modulus_margin'][0]} (desired = {self.user_pars.volt_mm})"]],
                headers=[
                '',
                print_gamma,
                'Bandwidth [Hz]',
                'Gain \n Margin [dB]',
                'Phase \n Margin [deg]',
                'Delay \n Margin [ms]',
                'Modulus \n Margin [-]'],
                tablefmt='orgtbl'))
        return df_bode, margins

    def init_pi(self, P):
        lag = [(2 * np.pi * self.user_pars.volt_bw) / 3, 2 * np.pi * self.user_pars.volt_bw,
            (2 * np.pi * self.user_pars.volt_bw) * 3]
        gamma_init, K_init = ([], [])
        for a in lag:
            g_init, x0 = P.init_PI(a)
            gamma_init.append(g_init)
            K_init.append(x0)

        if np.amin(gamma_init) > cn.g_max:
            raise Exception('Could not find a stabilizing initial controller for '
                'the voltage loop. Please change your desired specifications.')
        PI_index_min = np.argmin(gamma_init)
        return K_init[PI_index_min]

    def hinf(self, P):
        self.print_callback('info', 'Now optimizing the damping-loop')
        damp = P.damping_hinf()
        self.print_callback('info', 'Damping loop optimization finished!')

        self.print_callback('info',
            'Designing the initial stabilizing (PI) controller for the voltage-loop.')
        C_init = OptimizeV.init_pi(self, P)
        self.print_callback('info',
            'Initial controller design finished! Now optimizing voltage-loop parameters...')
        volt = P.voltage_hinf(C_init)
        self.print_callback('info', 'Voltage loop optimization finished!')

        df_bode, margins = OptimizeV.volt_opt_results(self, P, damp, volt)

        x = OptResult().volt_obj(damp['K-dloop'], volt['K-vloop'], self.user_pars.kd_0,
                                 self.print_callback, self.user_pars.debug)
        return x, df_bode, margins

    def h2(self, P):
        self.print_callback('info', 'Now optimizing the damping-loop.')
        damp = P.damping_h2()
        self.print_callback('info', 'Damping loop optimization finished!')

        self.print_callback('info',
            'Designing the initial stabilizing (PI) controller for the voltage-loop.')
        C_init = OptimizeV.init_pi(self, P)
        self.print_callback('info',
            'Initial controller design finished! Now optimizing voltage-loop parameters...')
        volt = P.voltage_h2(C_init)
        self.print_callback('info', 'Voltage loop optimization finished!')

        df_bode, margins = OptimizeV.volt_opt_results(self, P, damp, volt)

        x = OptResult().volt_obj(damp['K-dloop'], volt['K-vloop'], self.user_pars.kd_0,
                                 self.print_callback, self.user_pars.debug)
        return x, df_bode, margins

    def model_opt(self):
        """
        Function to execute the model-driven design for the voltage loop.

        :return: Object containing optimization results (damping and voltage loop parameters);
                 Dataframe containing frequency [Hz], gain [dB], and phase [deg] of multiple
                 sensitivity functions; dictionary containing the robustness margins
                 (``modulus_margin``, ``gain_margin`` [dB], ``phase_margin`` [deg],
                 ``delay_margin`` [ms]).
        :rtype: class, dataframe, dict
        """
        Check.check_v_pars(self.user_pars, self.print_callback)
        Check.prop_v_model(self.prop, self.print_callback)

        self.print_callback('info', 'Building model from FGC properties.')
        MOD = bm.Model(self.user_pars, self.prop)
        min_bw = np.minimum(self.user_pars.volt_bw, self.user_pars.damp_bw)
        w_init, f_points = 2 * np.pi * min_bw / 100, 400
        F = MOD.model_frf_v(w_init, f_points)

        # Initialize optimization problem
        self.print_callback('info',
            f'Starting optimization for {self.user_pars.opt_method} performance.')
        P = OptAlgoV(F, self.Ts_fund, self.user_pars, self.print_callback)
        if self.user_pars.opt_method == 'Hinf':
            opt_results, df_bode, margins = OptimizeV.hinf(self, P)
        elif self.user_pars.opt_method == 'H2':
            opt_results, df_bode, margins = OptimizeV.h2(self, P)
        return opt_results, df_bode, margins

    def data_opt(self, df_icapa, df_vmeas, df_imeas, df_gain):
        """
        Function to execute the data-driven design for the voltage loop.

        :param df_icapa: Dataframe containing the frequency [Hz], gain [dB] and phase [deg] arrays
                         of the frequency response from F_REF_LIMITED to I_CAPA.
        :type df_icapa: dataframe
        :param df_vmeas: Dataframe containing the frequency [Hz], gain [dB] and phase [deg] arrays
                         of the frequency response from F_REF_LIMITED to V_MEAS_REG.
        :type df_vmeas: dataframe
        :param df_imeas: Dataframe containing the frequency [Hz], gain [dB] and phase [deg] arrays
                         (along with the DC gain) of the frequency response from F_REF_LIMITED (or
                         V_REF) to I_MEAS.
        :type df_imeas: dataframe
        :param df_gain: Dataframe containing constant (non zero) values of I_MEAS and
                        F_REF_LIMITED. This data is used to compute the DC gain of the system
                        (which is needed for the voltage loop controller synthesis).
        :type df_gain: dataframe
        :return: Object containing optimization results (damping and voltage loop parameters);
                 Dataframe containing frequency [Hz], gain [dB], and phase [deg] of multiple
                 sensitivity functions; dictionary containing the robustness margins
                 (``modulus_margin``, ``gain_margin`` [dB], ``phase_margin`` [deg],
                 ``delay_margin`` [ms]).
        :rtype: class, dataframe, dict
        """
        Check.check_v_pars(self.user_pars, self.print_callback)
        OptimizeIB.data_check_freq([df_icapa, df_vmeas, df_imeas])
        GAIN = np.mean(df_gain['I_MEAS']['sample'].values) / \
            np.mean(df_gain['F_REF_LIMITED']['sample'].values)

        _, G_icapa = cf.Funcs.df_to_complex(df_icapa)
        _, G_vmeas = cf.Funcs.df_to_complex(df_vmeas)
        w, G_imeas = cf.Funcs.df_to_complex(df_imeas)

        # Interpolate frequency response if not enough points for the controller optimization
        if len(w) <= 80:
            self.print_callback('warning', 'Not enough frequency points for controller design. '
                                           'Will interpolate frequency response with more points.')
            w, G = cf.Funcs.interp_freq(w, G_icapa, w, G_vmeas, w, G_imeas)
            G_icapa, G_vmeas, G_imeas = G[0], G[1], G[2]

        F = {
            'w': w,
            'ref_to_icapa': G_icapa,
            'ref_to_imeas': G_imeas,
            'ref_to_vmeas': G_vmeas,
            'DC_mag': GAIN
        }

        # Initialize optimization problem
        self.print_callback('info',
            f'Starting optimization for {self.user_pars.opt_method} performance.')
        P = OptAlgoV(F, self.Ts_fund, self.user_pars, self.print_callback)
        if self.user_pars.opt_method == 'Hinf':
            opt_results, df_bode, margins = OptimizeV.hinf(self, P)
        elif self.user_pars.opt_method == 'H2':
            opt_results, df_bode, margins = OptimizeV.h2(self, P)
        return opt_results, df_bode, margins