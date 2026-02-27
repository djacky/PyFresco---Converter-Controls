import numpy as np
import control as cs


def MA_filter(w, control_mode, prop):
    Ts_fund = round(prop['FGC.ITER_PERIOD'], 6)

    meas_select = prop['REG.{}.EXTERNAL.MEAS_SELECT'.format(control_mode)]
    if meas_select == 'UNFILTERED' or meas_select == 'EXTRAPOLATED':
        filter_tot = 1
    elif meas_select == 'FILTERED':
        z = lambda x: np.exp(x * 1j * w * Ts_fund)
        fir_len1 = prop['MEAS.{}.FIR_LENGTHS'.format(control_mode)][0]
        fir_len2 = prop['MEAS.{}.FIR_LENGTHS'.format(control_mode)][1]

        if fir_len1 == 0:
            fir_filter_1 = 1
        elif fir_len1 > 0:
            fir_filter_1 = 0
            for i in range(fir_len1):
                fir_filter_1 += z(-i)
            fir_filter_1 = fir_filter_1 / fir_len1
        else:
            raise Exception(f'Invalid value for MEAS.{control_mode}.FIR_LENGTHS.')

        if fir_len2 == 0:
            fir_filter_2 = 1
        elif fir_len2 > 0:
            fir_filter_2 = 0
            for i in range(fir_len2):
                fir_filter_2 += z(-i)
            fir_filter_2 = fir_filter_2 / fir_len2
        else:
            raise Exception(f'Invalid value for MEAS.{control_mode}.FIR_LENGTHS.')

        filter_tot = fir_filter_1 * fir_filter_2

    return filter_tot


def thiran(delay, Ts):

    D = delay / Ts
    N = int(np.ceil(D))
    d_vec = np.arange(1, N + 1)
    ak = []
    for k in d_vec:
        prod_term = 1
        for i in range(N + 1):
            prod_term = prod_term * (D - N + i) / (D - N + k + i)
        comb_term = np.math.factorial(N) / (np.math.factorial(k) * np.math.factorial(N - k))
        ak_term = (-1)**k * comb_term * prod_term
        ak.append(ak_term)

    akf = np.insert(ak, 0, 1)
    del_thiran = cs.tf(akf[::-1], akf, Ts)

    return del_thiran


class Model:
    def __init__(self, user_pars, prop):
        self.user_pars = user_pars
        self.control_mode = user_pars.control_mode
        self.prop = prop
        self.Ts_fund = round(self.prop['FGC.ITER_PERIOD'], 6)

    def delay(self):
        # Calculate total pure delay
        if self.prop['VS.ACTUATION'] == 'FIRING_REF':
            Delay_firing = self.prop['VS.FIRING.DELAY']
        else:
            Delay_firing = 0

        Delay_actuation = self.prop['VS.ACT_DELAY_ITERS'] * self.Ts_fund

        meas_select = self.prop['REG.{}.EXTERNAL.MEAS_SELECT'.format(self.control_mode)]
        if meas_select == 'UNFILTERED' or meas_select == 'FILTERED':
            Delay_meas = self.prop['MEAS.{}.DELAY_ITERS'.format(self.control_mode)] * self.Ts_fund
        else:
            Delay_meas = 0

        return Delay_meas + Delay_firing + Delay_actuation

    def model_frf(self, n, epsilon, beta):
        self.Ts = self.Ts_fund * int(self.prop[f'REG.{self.control_mode}.PERIOD_ITERS'])
        nu = n
        Nw = (1 / epsilon) * (np.log(1 / beta) + nu - 1 + np.sqrt(2 *
            (nu - 1) * np.log(1 / beta)))
        Nw = int(np.ceil(Nw))

        Rs = self.prop['LOAD.OHMS_SER']
        Rm = self.prop['LOAD.OHMS_MAG']
        Lm = self.prop['LOAD.HENRYS']
        Rp = self.prop['LOAD.OHMS_PAR']
        clbw_vs = self.prop['VS.SIM.BANDWIDTH']
        zeta_vs = self.prop['VS.SIM.Z']

        # Get initial frequency grid point w_init
        g0 = 1 / (Rs + Rp)
        g1 = 1 / (Rs + (Rp * Rm) / (Rp + Rm)) - g0
        tau = Lm / (Rm + (Rp * Rs) / (Rp + Rs))
        M_dc = g0 + g1
        minus_3db = M_dc * 10 ** (-3 / 20)
        w_init = 1 / tau * np.sqrt((minus_3db ** 2 - M_dc ** 2) /
            (g0 ** 2 - minus_3db ** 2)) / 100

        # Use w_init as the starting value for the frequency grid
        w = np.logspace(np.log10(w_init), np.log10(np.pi / self.Ts), Nw)
        if self.user_pars.noise_rej:
            for pair in self.user_pars.noise_rej:
                if pair[0] > 1 / (2 * self.Ts) or 2 * np.pi * pair[0] < w[0]:
                    raise Exception(f'ERROR: Cannot have a noise rejection frequency outside of '
                            f'the range [{w[0] / (2 * np.pi)}, {1 / (2 * self.Ts)}] Hz')
                w = np.concatenate((w, [2 * np.pi * pair[0]]))
        w = np.sort(w)

        wn = (2 * np.pi * clbw_vs) / np.sqrt(1 - 2 * np.power(zeta_vs, 2) +
            np.sqrt(2 - 4 * np.power(zeta_vs, 2) + 4 * np.power(zeta_vs, 4)))
        Vs = np.power(wn, 2) / (-np.power(w, 2) + 2 * zeta_vs * wn * 1j * w + np.power(wn, 2))

        Z1 = Rm + 1j * w * Lm
        M = 1 / (Rs + 1 / (1 / Rp + 1 / Z1))

        # Vss = cs.tf(wn**2, [1, 2*zeta_vs*wn, wn**2])
        # numv = [wn**2, 2*wn**2, wn**2]
        # denv = [4/(self.Ts**2) + 4/self.Ts * zeta_vs*wn + wn**2,
        #    2*wn**2 - 8/(self.Ts**2), 4/(self.Ts**2) - 4/self.Ts * zeta_vs * wn + wn**2]
        # Vsz = cs.tf(numv, denv, self.Ts)

        # t1 = Rs*Rm+Rs*Rp+Rm*Rp
        # Ms = cs.tf([Lm, Rm+Rp], [Rs*Lm+Rp*Lm, t1])

        Delay_total = Model.delay(self)
        # Gz = cs.c2d(Vss * Ms, self.Ts) * thiran(Delay_total, self.Ts)
        # Gz = cs.c2d(Ms, self.Ts) * Vsz * thiran(Delay_total, self.Ts)
        # mag, phase, w2 = cs.freqresp(Gz, w)
        # G = mag[0][0] * np.exp(1j*np.unwrap(phase[0][0]))

        # Formulate open-loop model
        if self.control_mode == 'I':
            Delay_fgc = self.prop['REG.I.INTERNAL.PURE_DELAY_PERIODS']
            if Delay_fgc == 0:
                G = M * Vs * np.exp(-1j * w * Delay_total)
            elif Delay_fgc > 0:
                G = M * Vs * np.exp(-1j * w * Delay_fgc)
            else:
                raise Exception('ERROR:REG.I.INTERNAL.PURE_DELAY_PERIODS must be positive.')
        elif self.control_mode == 'B':
            Delay_fgc = self.prop['REG.B.INTERNAL.PURE_DELAY_PERIODS']
            if Delay_fgc == 0:
                G = self.prop['LOAD.GAUSS_PER_AMP'] * M * Vs * np.exp(-1j * w * Delay_total)
            elif Delay_fgc > 0:
                G = self.prop['LOAD.GAUSS_PER_AMP'] * M * Vs * np.exp(-1j * w * Delay_fgc)
            else:
                raise Exception('ERROR:REG.I.INTERNAL.PURE_DELAY_PERIODS must be positive.')

        return G, w

    def model_frf_v(self, w_init, f_points):

        # Initialize frequency grid
        w = np.logspace(np.log10(w_init), np.log10(np.pi / self.Ts_fund), f_points)

        # Calculate delays
        if self.prop['VS.ACTUATION'] == 'FIRING_REF':
            Delay_firing = self.prop['VS.FIRING.DELAY']
        else:
            Delay_firing = 0

        del_act = np.exp(-1j * w * (Delay_firing +
                self.prop['VS.ACT_DELAY_ITERS'] * self.Ts_fund))
        del_ADC_v = np.exp(-1j * w * self.prop['MEAS.V.DELAY_ITERS'] * self.Ts_fund)
        del_ADC_i = np.exp(-1j * w * self.prop['MEAS.I.DELAY_ITERS'] * self.Ts_fund)

        # Formulate models
        # ref_to_vmeas = F_REF_LIMITED --> V_MEAS_REG,
        # GHi = F_REF_LIMITED --> I_CAPA,
        # GMag = F_REF_LIMITED --> I_MEAS
        Zd = self.prop['LOAD.OHMS_MAG'] + 1j * w * self.prop['LOAD.HENRYS']
        M = 1 / (self.prop['LOAD.OHMS_SER'] + 1 / (1 / self.prop['LOAD.OHMS_PAR'] + 1 / Zd))
        DC_mag = 1 / (self.prop['LOAD.OHMS_SER'] + self.prop['LOAD.OHMS_MAG'])

        Zmt = 1 / M
        Z1 = self.prop['VS.FILTER.OHMS'] + 1 / (1j * w * self.prop['VS.FILTER.FARADS1'])
        Z2 = 1 / (1j * w * self.prop['VS.FILTER.FARADS2'])
        Z3 = (Z1 * Z2) / (Z1 + Z2)
        ZT = (Z3 * Zmt) / (Z3 + Zmt)

        H_icappa = (1j * w) / (self.prop['VS.FILTER.OHMS'] * 1j * w + 1 /
                 self.prop['VS.FILTER.FARADS1'])

        G = (ZT / (self.prop['VS.FILTER.HENRYS'] * 1j * w + ZT)) * del_act
        GHi = G * H_icappa * del_ADC_i
        GMag = G * M * del_ADC_i
        Gdel = G * del_ADC_v

        return {'ref_to_icapa': GHi, 'ref_to_imeas': GMag, 'ref_to_vmeas': Gdel,
                'w': w, 'DC_mag': DC_mag}