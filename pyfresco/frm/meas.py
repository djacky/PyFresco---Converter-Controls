import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyfgc
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

    @staticmethod
    def complex_2_df(f, G):
        amp_db, phase_deg = 20 * np.log10(np.absolute(G)), (180 / np.pi) * np.unwrap(np.angle(G))
        df = pd.DataFrame(data={'f': f, 'gain': amp_db,
                'phase': phase_deg}).sort_values(by=['f'])
        return df

    @staticmethod
    def sampling_freq(method, pars, device, rbac_token):

        Ts_fund = round(float(pyfgc.get(device, 'FGC.ITER_PERIOD',
                    rbac_token=rbac_token).value), 6)

        if method == 'PRBS':
            if pars.reg_mode == 'V':
                Ts = Ts_fund * pars.period_iters
            elif pars.reg_mode in ['I', 'B']:
                ind = int(pyfgc.get(device, 'LOAD.SELECT', rbac_token=rbac_token).value)
                reg_period = int(pyfgc.get(device, f'REG.{pars.reg_mode}.PERIOD_ITERS[{ind}]',
                        rbac_token=rbac_token).value)
                Ts = Ts_fund * reg_period * pars.period_iters
            else:
                raise Exception('Invalid character set for reg_mode.')
        elif method == 'Sine':
            if pars.reg_mode == 'V':
                Ts = Ts_fund
            elif pars.reg_mode in ['I', 'B']:
                ind = int(pyfgc.get(device, 'LOAD.SELECT', rbac_token=rbac_token).value)
                reg_period = int(pyfgc.get(device, f'REG.{pars.reg_mode}.PERIOD_ITERS[{ind}]',
                        rbac_token=rbac_token).value)
                Ts = Ts_fund * reg_period
            else:
                raise Exception('Invalid character set for reg_mode.')

        Fs = 1 / Ts

        return Fs

    @staticmethod
    def prbs(df, pars, device: str, rbac_token: str = None, df_gain=None):
        """
        Function which calculates the frequency response from a PRBS measurement.

        :param df: Dataframe containing the time [s], input and output (analog) signal arrays.
        :type df: dataframe
        :param pars: PRBS UI input parameters.
        :type pars: class
        :param device: FGC device name.
        :type device: str
        :param rbac_token: Name of RBAC token.
        :type rbac_token: str
        :param df_gain: Dataframe containing constant (non zero) values of an input and output
                        signal. This data is used to compute the DC gain of the system (which is
                        needed for the voltage loop controller synthesis).
        :type df_gain: dataframe
        :return: Dataframe containing the frequency [Hz], gain [dB], and phase [deg] arrays.
        :rtype: dataframe

        :Example:

        >>> import pyfresco
        >>> device = 'RFNA.866.01.ETH2'
        >>> df = pyfresco.frm.prbs(df, pars, device)
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
        Fs = Frm_methods.sampling_freq('PRBS', pars, device, rbac_token)

        df = df.loc[:, ~df.columns.duplicated()]

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

        yfft, rfft = np.fft.rfft(y11), np.fft.rfft(r11)
        L = len(y11)

        RP2n = rfft / L
        RP1n = RP2n[0:int(np.floor((L + 1) / 2 + 1))]
        RP1n[1:] = 2 * RP1n[1:]
        YP2n = yfft / L
        YP1n = YP2n[0:int(np.floor((L + 1) / 2 + 1))]
        YP1n[1:] = 2 * YP1n[1:]

        with np.errstate(divide='ignore'):
            N_FRF = YP1n / RP1n
        G1 = N_FRF[0::int(p_end - p_start)]
        f1 = Fs * np.linspace(0, int((dat_length + 1) / 2 - 1),
            int((dat_length + 1) / 2)) / dat_length

        beg_freq = 50
        if pars.k_order in {7, 8, 9, 10}:
            G, f = G1[1:], f1[1:]
        elif pars.k_order > 10:
            K_ORDER_step = int(str(pars.k_order)[-1])
            f = np.concatenate((f1[1:beg_freq], f1[beg_freq + 1::2**K_ORDER_step], f1[-1]),
                axis=None)
            G = np.concatenate((G1[1:beg_freq], G1[beg_freq + 1::2**K_ORDER_step], G1[-1]),
                axis=None)

        df0 = Frm_methods.complex_2_df(f, G)

        if df_gain is None:
            pass
        elif not df_gain.empty:
            dc_gain = np.mean(df_gain[pars.meas_mode]['sample'].values) / \
                np.mean(df_gain[pars.ref_mode]['sample'].values)
            df0.loc[:, 'dc_gain'] = pd.Series([dc_gain])

        # plot_bode(df0, 'PRBS_bode_no_avg.png')

        return df0

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

    def sine_freq_array(self, Fs, num_freq):
        """
        Function which returns a logarithmically-spaced frequency array that is used to obtain the
        frequency response from the sine-fit algorithm.

        :param Fs: Sampling frequency of the loop [Hz]. See :ref:`Frequency Array <num_freq>`
                   for more information.
        :type Fs: float
        :param num_freq: Number of frequency points used for the sinusoudal excitations.
        :type num_freq: int

        :Example:

        >>> import pyfresco
        >>> # assume num_freq = 5, Fs = 10000
        >>> freq = pyfresco.frm.sine_freq_array(Fs, num_freq)
        >>> freq
        array([2.50000000e-02, 3.53553391e-01, 5.00000000e+00, 7.07106781e+01, 1.00000000e+03])
        """
        sine_array = np.logspace(np.log10(0.025), np.log10(0.1 * Fs), num_freq)

        return sine_array

    def sine_fit(self, f, df, pars, df_gain=None):
        """
        Function which calculates the frequency response from a sine-fit measurement.

        :param f: Frequency [Hz] array of each sinusoidal input.
        :type f: array
        :param df: A list of dataframes where each index contains the time [s], input
                   and output (analog) signal arrays from each experiment.
        :type df: list of dataframe
        :param pars: Sine-fit UI input parameters
        :type pars: class
        :param df_gain: Dataframe containing constant (non zero) values of an input and output
                        signal. This data is used to compute the DC gain of the system (which is
                        needed for the voltage loop controller synthesis).
        :type df_gain: dataframe
        :return: Dataframe containing the frequency [Hz], gain [dB], and phase [deg] arrays.
        :rtype: dataframe

        :Example:

        >>> import pyfresco
        >>> df = pyfresco.frm.sine_fit(f, df, pars)
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
        for i in range(len(f)):
            df2 = df[i].loc[:, ~df[i].columns.duplicated()]
            t1 = df2[pars.ref_mode]['t_local'].values
            t = t1 - t1[0]
            r = df2[pars.ref_mode]['sample'].values
            y = df2[pars.meas_mode]['sample'].values
            amp[i], phase[i] = Frm_methods.sine_fit_alg(t, f[i], r, y)

        G = amp * np.exp(1j * np.unwrap(phase))
        df0 = Frm_methods.complex_2_df(f, G)

        if df_gain is None:
            pass
        elif not df_gain.empty:
            dc_gain = np.mean(df_gain[pars.meas_mode]['sample'].values) / \
                np.mean(df_gain[pars.ref_mode]['sample'].values)
            df0.loc[:, 'dc_gain'] = pd.Series([dc_gain])

        # plot_bode(df0, 'Sine_bode.png')

        return df0