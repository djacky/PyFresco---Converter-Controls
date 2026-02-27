import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyfgc
import scipy.signal as sig
from .exceptions import Check


def plot_bode(df0, png_name):
    font = {'family': 'monospace',
        'weight': 'bold',
        'size': 15}

    plt.rc('font', **font)
    plt.subplot(2, 1, 1)
    plt.semilogx(df0['f'].values, df0['gain'].values)
    plt.ylabel('Magnitude [dB]')
    plt.grid(True, which="both")

    plt.subplot(2, 1, 2)
    plt.semilogx(df0['f'].values, df0['phase'].values)
    plt.ylabel('Phase [deg]')
    plt.xlabel('Frequency [Hz]')
    plt.grid(True, which="both")
    plt.savefig(png_name)
    plt.show()


class Frm_methods:
    """
    This class is used to call the PRBS or sine-fit algorithms for the frequency
    response measurements.

    :param device: FGC device name.
    :type device: str
    :param rbac_token: Name of RBAC token.
    :type rbac_token: str
    :param print_callback: Callback function which outputs print commands to the console.
    :type print_callback: func
    """

    def __init__(self, device: str, rbac_token: str = None, print_callback=print):
        self.rbac_token = rbac_token
        self.device = device
        Ts_fund = round(float(pyfgc.get(device, 'FGC.ITER_PERIOD',
                                        rbac_token=rbac_token).value), 6)
        self.Ts_fund = Ts_fund
        self.print_callback = print_callback

    @staticmethod
    def complex_2_df(f, G):
        amp_db, phase_deg = 20 * np.log10(np.absolute(G)), (180 / np.pi) * np.unwrap(np.angle(G))
        df = pd.DataFrame(data={'f': f, 'gain': amp_db,
                'phase': phase_deg}).sort_values(by=['f'])
        return df

    def sampling_freq(self, method, pars):

        if method == 'PRBS':
            if pars.reg_mode == 'V':
                Ts = self.Ts_fund * pars.period_iters
            elif pars.reg_mode in ['I', 'B']:
                ind = int(pyfgc.get(self.device, 'LOAD.SELECT',
                                    rbac_token=self.rbac_token).value)
                reg_period = int(pyfgc.get(self.device, f'REG.{pars.reg_mode}.PERIOD_ITERS[{ind}]',
                        rbac_token=self.rbac_token).value)
                Ts = self.Ts_fund * reg_period * pars.period_iters
            else:
                raise Exception('Invalid character set for reg_mode.')
        elif method == 'Sine':
            if pars.reg_mode == 'V':
                Ts = self.Ts_fund
            elif pars.reg_mode in ['I', 'B']:
                ind = int(pyfgc.get(self.device, 'LOAD.SELECT', rbac_token=self.rbac_token).value)
                reg_period = int(pyfgc.get(self.device, f'REG.{pars.reg_mode}.PERIOD_ITERS[{ind}]',
                        rbac_token=self.rbac_token).value)
                Ts = self.Ts_fund * reg_period
            else:
                raise Exception('Invalid character set for reg_mode.')

        Fs = 1 / Ts

        return Fs

    def permitted_period(self, f, pars):
        f = int(np.ceil(f))
        T_permitted = self.Ts_fund * np.arange(1, 5000, 1)
        F_permitted = 1. / T_permitted
        k_fmax = np.where(F_permitted >= 2 * f)
        if round(2 * f, 1) in F_permitted:
            f_sample_max = F_permitted[k_fmax[0][-1]]
        else:
            f_sample_max = F_permitted[k_fmax[0][-1] + 1]
        Ts_max = 1 / f_sample_max
        div = int(np.ceil(Ts_max / self.Ts_fund))
        if pars.reg_mode == 'V':
            self.print_callback('warning', '[FOR CONTROL PURPOSES]: '
                                f'Given the maximum frequency of {f} Hz, '
                                f'REG.I/B.PERIOD_ITERS must be >= {div}.')
        return None

    @staticmethod
    def group_delay(f, phase_deg):
        gd = - np.gradient(phase_deg * np.pi / 180, 2 * np.pi * f) * 1e3
        df = pd.DataFrame(data={'f': f, 'group_delay': gd}).sort_values(by=['f'])
        df['group_delay'].ffill(inplace=True)
        b, a = sig.butter(4, 0.1)
        df['group_delay_ma'] = sig.filtfilt(b, a, df['group_delay'].values)
        return df

    def prbs_params_calc(self, fmin, fmax, amp_pp, num_sequences, reg_mode):

        ind = int(pyfgc.get(self.device, 'LOAD.SELECT', rbac_token=self.rbac_token).value)
        if reg_mode == 'V':
            Ts = self.Ts_fund
            fgc_rate = float(pyfgc.get(self.device, 'LIMITS.V.RATE',
                                rbac_token=self.rbac_token).value)
        elif reg_mode == 'I':
            reg = int(pyfgc.get(self.device, 'REG.I.PERIOD_ITERS',
                                    rbac_token=self.rbac_token).value.split(',')[ind])
            fgc_rate = float(pyfgc.get(self.device, 'LIMITS.I.RATE',
                                rbac_token=self.rbac_token).value.split(',')[ind])
            Ts = reg * self.Ts_fund
        elif reg_mode == 'B':
            reg = int(pyfgc.get(self.device, 'REG.B.PERIOD_ITERS',
                                    rbac_token=self.rbac_token).value.split(',')[ind])
            fgc_rate = float(pyfgc.get(self.device, 'LIMITS.B.RATE',
                                rbac_token=self.rbac_token).value.split(',')[ind])
            Ts = reg * self.Ts_fund

        k_calc = int(np.ceil(np.log2(1 + 1 / (Ts * fmin))))
        if fmax > 1 / (2 * Ts):
            self.print_callback('warning', 'Cannot set the maximum frequency larger than '
                                'the Nyquist frequency. Setting the period such that the '
                                f'maximum frequency = {1 / (2 * Ts)}.')
            P_calc = 1
        else:
            P_calc = int(np.floor(1 / (2 * Ts * fmax)))
        pyfgc.set(self.device, 'REF.PRBS.PERIOD_ITERS', P_calc, rbac_token=self.rbac_token)
        pyfgc.set(self.device, 'REF.PRBS.K', k_calc, rbac_token=self.rbac_token)
        fmin_meas = 1 / (Ts * (2**k_calc - 1))
        fmax_meas = 1 / (2 * Ts * P_calc)

        # num_sequences = int(pyfgc.get(self.device, 'REF.PRBS.NUM_SEQUENCES',
        #                              rbac_token=self.rbac_token).value)
        prbs_duration = Ts * ((2 ** k_calc) - 1) * num_sequences * P_calc
        rate = (amp_pp/2) / Ts
        if fgc_rate > 0 and rate > fgc_rate:
            raise Exception(f'PRBS rate too large. Either modify LIMITS.{reg_mode}.RATE '
                            'or reduce the peak-to-peak amplitude.')

        return {'k': k_calc, 'period_iters': P_calc,
                'freq_range': [fmin_meas, fmax_meas], 'duration_seconds': prbs_duration}

    def prbs(self, df, pars):
        """
        Function which calculates the frequency response from a PRBS measurement.

        :param df: Dataframe containing the time [s], input and output (analog) signal arrays.
        :type df: dataframe
        :param pars: PRBS UI input parameters.
        :type pars: class
        :return: Dataframe containing the frequency [Hz], gain [dB], and phase [deg] arrays;
                 dataframe containing the group delay [ms] and it's moving average.
        :rtype: dataframe, dataframe

        :Example:

        >>> import pyfresco
        >>> device = 'RFNA.866.01.ETH2'
        >>> df, df_gd = pyfresco.frm.prbs(df, pars)
        >>> df
                    f       gain       phase
        0       2.442599  15.508934  -36.688132
        1       4.885198  12.440699  -57.037145
        2       7.327797   9.782238  -67.844468
        3       9.770396   7.631363  -74.412529
        4      12.212995   5.864185  -78.913022
        ..           ...        ...         ...
        """
        Check.check_prbs_pars(pars)

        df = df.loc[:, ~df.columns.duplicated()]
        Fs = Frm_methods.sampling_freq(self, 'PRBS', pars)

        in_array = df[pars.ref_mode]['sample'].values
        out_array = df[pars.meas_mode]['sample'].values

        if len(np.unique(in_array)) == 1 or len(np.unique(out_array)) == 1:
            raise Exception('No PRBS data detected.')

        if 'V_MEAS' in pars.ref_mode:
            amp = pars.amplitude_pp / 2
            start_index = np.where(np.absolute(in_array) > in_array[0] + amp / 3)[0][0]
        else:
            start_index = np.where(in_array != in_array[0])[0][0]

        dat_length = 2**pars.k_order - 1
        p_start, p_end = 4, pars.num_sequences - 1

        y = out_array[start_index::pars.period_iters]
        r = in_array[start_index::pars.period_iters]
        y11 = y[p_start * dat_length:p_end * dat_length]
        r11 = r[p_start * dat_length:p_end * dat_length]

        self.print_callback('info', 'Now measuring the frequency response...')
        Glist = []
        s_index, e_index = 0, dat_length
        for k in range(p_start, p_end):
            y_part = y11[s_index:e_index]
            r_part = r11[s_index:e_index]
            yfft, rfft = np.fft.rfft(y_part), np.fft.rfft(r_part)
            L = len(y_part)
            s_index += dat_length
            e_index += dat_length

            RP2n = rfft / L
            RP1n = RP2n[0:int(np.floor((L + 1) / 2 + 1))]
            RP1n[1:] = 2 * RP1n[1:]
            YP2n = yfft / L
            YP1n = YP2n[0:int(np.floor((L + 1) / 2 + 1))]
            YP1n[1:] = 2 * YP1n[1:]

            with np.errstate(divide='ignore'):
                N_FRF = YP1n / RP1n
            Glist.append(N_FRF)

        G1 = np.mean(Glist, axis=0)
        f1 = Fs * np.linspace(0, int((dat_length + 1) / 2 - 1),
            int((dat_length + 1) / 2)) / dat_length
        self.print_callback('info', 'Measurement finished!')

        beg_freq = 50
        if pars.k_order in {7, 8, 9, 10}:
            G, f = G1[1:], f1[1:]
        elif pars.k_order > 10:
            K_ORDER_step = int(str(pars.k_order)[-1])
            f = np.concatenate((f1[1:beg_freq], f1[beg_freq + 1::2**K_ORDER_step], f1[-1]),
                axis=None)
            G = np.concatenate((G1[1:beg_freq], G1[beg_freq + 1::2**K_ORDER_step], G1[-1]),
                axis=None)

        Frm_methods.permitted_period(self, Fs / 2, pars)
        df0 = Frm_methods.complex_2_df(f, G)
        df_gd = Frm_methods.group_delay(df0['f'].values, df0['phase'].values)

        # plot_bode(df0, 'PRBS_bode_Avg.png')

        return df0, df_gd

    @staticmethod
    def sine_fit_alg(t, f, r, y):
        V = np.transpose(np.array([np.cos(2 * np.pi * f * t),
            np.sin(2 * np.pi * f * t), np.ones(t.shape)]))
        P = np.linalg.pinv(V)
        x_meas, x_ref = np.matmul(P, y), np.matmul(P, r)
        A_meas = np.linalg.norm(x_meas[0:2], 2)
        ph_meas = np.arctan2(-x_meas[1], x_meas[0])
        A_ref = np.linalg.norm(x_ref[0:2], 2)
        ph_ref = np.arctan2(-x_ref[1], x_ref[0])

        Amplitude, Phase = A_meas / A_ref, ph_meas - ph_ref
        return Amplitude, Phase

    def sine_freq_array(self, f1, f2, num_freq, pars):
        """
        Function which returns a logarithmically-spaced frequency array that is used to obtain the
        frequency response from the sine-fit algorithm.

        :param f1: Initial frequency for sine measurement.
        :type f1: float
        :param f2: Final frequency for sine measurement.
        :type f2: float
        :param num_freq: Number of frequency points used for the sinusoudal excitations.
        :type num_freq: int
        :param pars: UI user parameters for sine-fit measurement.
        :type pars: class

        :Example:

        >>> import pyfresco
        >>> f1 = 1; f2 = 1000; num_freq = 5; # assume pars object was obtained from UI
        >>> device = 'RFNA.866.01.ETH2'
        >>> F = pyfresco.frm.Frm_methods(device)
        >>> freq = F.sine_freq_array(f1, f2, num_freq, pars)
        >>> freq
        array([1, 5.62341325, 31.6227766, 177.827941, 1000])
        """
        Fs = Frm_methods.sampling_freq(self, 'Sine', pars)
        min_freq, max_freq = 0.025, 0.1 * Fs

        if pars.reg_mode == 'V':
            # if f1 > min_freq:
            #    self.print_callback('warning',
            #                        '[FOR CONTROL PURPOSES]: '
            #                        f'Recommended that the minimum frequency = {min_freq} Hz.')
            if num_freq <= 80:
                self.print_callback('warning',
                                    '[FOR CONTROL PURPOSES]: '
                                    'Number of frequency points is too low for controller '
                                    'synthesis. Choose at least 150 points for proper synthesis.')
        if f1 < min_freq:
            raise Exception(f'Cannot select a minimum frequency < {min_freq} Hz. '
                            '(logs are limited in the amount of data stored.)')

        if f2 > max_freq:
            raise Exception(f'Cannot select a maximum frequency > {max_freq} Hz. '
                            'Must have at least 10 samples in the highest frequency sinusoid.')

        sine_array = np.logspace(np.log10(f1), np.log10(f2), num_freq)
        Frm_methods.permitted_period(self, f2, pars)

        return sine_array

    def sine_fit(self, f, df, pars):
        """
        Function which calculates the frequency response from a sine-fit measurement.

        :param f: Frequency [Hz] array of each sinusoidal input.
        :type f: array
        :param df: A list of dataframes where each index contains the time [s], input
                   and output (analog) signal arrays from each experiment.
        :type df: list of dataframe
        :param pars: Sine-fit UI input parameters
        :type pars: class
        :return: Dataframe containing the frequency [Hz], gain [dB], and phase [deg] arrays.
                 dataframe containing the group delay [ms] and it's moving average.
        :rtype: dataframe, dataframe

        :Example:

        >>> import pyfresco
        >>> device = 'RFNA.866.01.ETH2'
        >>> F = pyfresco.frm.Frm_methods(device)
        >>> df, df_gd = F.sine_fit(f, df, pars)
        >>> df
                    f          gain       phase
        0     0.025000 -1.193218e-07   -0.019967
        1     0.074767 -1.083062e-06   -0.059714
        2     0.223607 -9.599316e-06   -0.178588
        3     0.668740 -8.587503e-05   -0.534103
        4     2.000000 -7.680953e-04   -1.597387
        ..         ...           ...         ...
        """
        Check.check_sine_pars(pars)

        amp = np.empty(len(f))
        phase = np.empty(len(f))
        self.print_callback('info', 'Now measuring the frequency response...')
        for i in range(len(f)):
            df2 = df[i].loc[:, ~df[i].columns.duplicated()]
            t1 = df2[pars.ref_mode]['t_local'].values
            t = t1 - t1[0]
            r = df2[pars.ref_mode]['sample'].values
            y = df2[pars.meas_mode]['sample'].values
            amp[i], phase[i] = Frm_methods.sine_fit_alg(t, f[i], r, y)

        self.print_callback('info', 'Measurement finished!')
        G = amp * np.exp(1j * np.unwrap(phase))
        df0 = Frm_methods.complex_2_df(f, G)
        df_gd = Frm_methods.group_delay(df0['f'].values, df0['phase'].values)

        # plot_bode(df0, 'Sine_bode.png')

        return df0, df_gd
