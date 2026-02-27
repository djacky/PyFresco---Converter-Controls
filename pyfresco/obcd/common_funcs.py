import numpy as np
import pandas as pd
import control as co


class Funcs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def norm1(Ts, w, X):
        Xn = Ts / np.pi * np.trapz(np.abs(X), w)
        return Xn

    @staticmethod
    def norm2(Ts, w, X):
        Xn = np.sqrt(Ts / np.pi * np.trapz(np.power(np.abs(X), 2), w))
        return Xn

    @staticmethod
    def interp_freq(*args):
        wvals = np.linspace(args[0][0], args[0][-1], 350)
        w = wvals
        if len(args) == 2:
            amp_db_inter = np.interp(wvals, args[0], 20 * np.log10(np.abs(args[1])))
            phase_inter = np.interp(wvals, args[0], np.unwrap(np.angle(args[1])))
            G = np.power(10, amp_db_inter / 20) * np.exp(1j * phase_inter)
        else:
            G = []
            index = 0
            for a in range(int(len(args)/2)):
                amp_db_inter = np.interp(wvals, args[index],
                                         20 * np.log10(np.abs(args[index + 1])))
                phase_inter = np.interp(wvals, args[index],
                                        np.unwrap(np.angle(args[index + 1])))
                G1 = np.power(10, amp_db_inter / 20) * np.exp(1j * phase_inter)
                G.append(G1)
                index += 2
        return w, G

    @staticmethod
    def interp_x(X, Y, ind, y):
        x0, x1 = X[ind - 1], X[ind]
        y0, y1 = Y[ind - 1], Y[ind]
        slope = (y1 - y0) / (x1 - x0)
        x = (y - y0) / slope + x0
        return x

    @staticmethod
    def interp_y(X, Y, ind, x):
        x0, x1 = X[ind - 1], X[ind]
        y0, y1 = Y[ind - 1], Y[ind]
        slope = (y1 - y0) / (x1 - x0)
        y = slope * (x - x0) + y0
        return y

    @staticmethod
    def sign_index(X):
        asign = np.sign(X)
        sz = asign == 0
        while sz.any():
            asign[sz] = np.roll(asign, 1)[sz]
            sz = asign == 0
        signchange = ((np.roll(asign, 1) - asign) != 0).astype(int)
        signchange[0] = 0
        ind_cross = np.where(signchange == 1)[0]
        return ind_cross

    @staticmethod
    def bw_estimate(w, CL_tot, print_callback):
        bw_hz = []
        for CL in CL_tot:
            CL_db = 20 * np.log10(np.abs(CL))
            ind = np.where(CL_db < -3)[0]
            try:
                ind1 = ind[0]
                bw = Funcs.interp_x(w, CL_db, ind1, -3)
                bw_hz.append(bw / (2 * np.pi))
            except:
                print_callback('warning', 'Could not compute closed-loop bandwidth.')
                bw_hz.append(0)
        return round(np.mean(bw_hz), 2)

    @staticmethod
    def margin(w, df_tot, print_callback, mode=None):

        gm_tot, pm_tot, dm_tot, mm_tot = [], [], [], []
        for df in df_tot:
            if mode == 'V':
                Sg = np.power(10, df['Sensitivity_dy_y_volt']['gain'].values / 20)
                Sp = df['Sensitivity_dy_y_volt']['phase'].values * np.pi / 180
            elif mode == 'D':
                Sg = np.power(10, df['Sensitivity_dy_y_damp']['gain'].values / 20)
                Sp = df['Sensitivity_dy_y_damp']['phase'].values * np.pi / 180
            else:
                Sg = np.power(10, df['Sensitivity_dy_y']['gain'].values / 20)
                Sp = df['Sensitivity_dy_y']['phase'].values * np.pi / 180

            S = Sg * np.exp(1j * Sp)
            L = 1 / S - 1
            L_db, L_phase_deg = 20 * np.log10(np.abs(L)), np.unwrap(np.angle(L)) * 180 / np.pi
            mm = 1 / np.amax(np.abs(S))
            mm_tot.append(round(mm, 3))

            try:
                gm, pm, wg, wp = co.margin((np.abs(L), L_phase_deg, w))
                gm_db, pm = 20 * np.log10(gm), np.abs(pm)
                dm = (pm * np.pi / 180) / wp * 1e3
                gm_tot.append(round(gm_db, 2))
                pm_tot.append(round(pm, 2))
                dm_tot.append(round(dm, 5))
            except:
                try:
                    # Calculate cross-over freq, phase margin, and delay margin by interpolation
                    ind_cross = Funcs.sign_index(L_db)
                    phase_margin_list = []
                    delay_margin_list = []
                    for ind in ind_cross:
                        wcr = Funcs.interp_x(w, L_db, ind, 0)
                        phase_cr = Funcs.interp_y(w, L_phase_deg, ind, wcr)
                        if phase_cr > 180:
                            phase_margin = phase_cr - 180
                        elif phase_cr > 0 and phase_cr < 180:
                            phase_margin = 180 - phase_cr
                        elif phase_cr < 0 and phase_cr > -180:
                            phase_margin = phase_cr + 180
                        phase_margin = np.abs(phase_margin)
                        phase_margin_list.append(phase_margin)
                        delay_margin_list.append((phase_margin * np.pi / 180) / wcr * 1e3)

                    pm = phase_margin_list[0]
                    dm = delay_margin_list[0]
                    pm_tot.append(round(pm, 2))
                    dm_tot.append(round(dm, 5))

                except:
                    print_callback('warning',
                        'Could not compute phase and delay margins.')
                    pm, dm = 0, 0
                    pm_tot.append(pm)
                    dm_tot.append(dm)

                try:
                    # Calculate gain margin by interpolation
                    ind_cross = Funcs.sign_index(np.imag(L))
                    gain_margin_list = []
                    for ind in ind_cross:
                        if np.real(L[ind]) > -1:
                            wg = Funcs.interp_x(w, np.imag(L), ind, 0)
                            gain = Funcs.interp_y(w, np.abs(L), ind, wg)
                            gain_margin_list.append(1 / gain)

                    gm_db = 20 * np.log10(gain_margin_list[0])
                    gm_tot.append(round(gm_db, 2))
                except:
                    print_callback('warning', 'Could not compute gain margin.')
                    gm_db = 0
                    gm_tot.append(gm_db)

        return {'modulus_margin': mm_tot, 'gain_margin': gm_tot,
                'phase_margin': pm_tot, 'delay_margin': dm_tot}

    @staticmethod
    def des_2nd_order(w, bw, zeta, ref_delay):

        wn = (2 * np.pi * bw) / np.sqrt(1 - 2 * np.power(zeta, 2) +
                np.sqrt(2 - 4 * np.power(zeta, 2) + 4 * np.power(zeta, 4)))
        Td = np.power(wn, 2) / (-np.power(w, 2) +
                2 * zeta * wn * 1j * w + np.power(wn, 2))

        Td = Td * np.exp(-1j * w * ref_delay)
        Wd = 1 / (1 - Td)

        return Td, Wd

    @staticmethod
    def df_to_complex(df, index=None):
        amp = np.power(10, df['gain'].values[0:index] / 20)
        phase = df['phase'].values[0:index] * np.pi / 180
        G = amp * np.exp(1j * phase)
        w = 2 * np.pi * df['f'].values[0:index]
        return w, G

    @staticmethod
    def complex_2_df(f, G):
        amp_db, phase_deg = 20 * np.log10(np.absolute(G)), (180 / np.pi) * np.unwrap(np.angle(G))
        df = pd.DataFrame(data={'f': f, 'gain': amp_db,
                'phase': phase_deg}).sort_values(by=['f'])
        return df

    @staticmethod
    def nyquist(mm, S_dy_y):
        L = 1 / S_dy_y - 1
        theta = np.linspace(0, 2 * np.pi, 5000)
        unit_circle = np.exp(1j * theta)
        mm_circle = -1 + mm * unit_circle

        return {'open_loop': [np.real(L), np.imag(L)],
                'unit_circle': [np.real(unit_circle), np.imag(unit_circle)],
                'mm_circle': [np.real(mm_circle), np.imag(mm_circle)]}

    @staticmethod
    def sensitivities_ib(P, R, S, T):

        def amp_db(X):
            return 20 * np.log10(np.abs(X))

        def phase_deg(X):
            return np.unwrap(np.angle(X)) * 180 / (np.pi)

        df_tot = []
        for G in P.G_multi:
            psi = G * P.MA * R + S
            Sens_ref_out = (G * T) / psi
            Sens_do_out = S / psi
            Sens_di_out = (G * S) / psi
            Sens_n_out = (-G * R * P.MA) / psi
            Sens_ref_u = T / psi

            Sens = [Sens_ref_out, Sens_do_out, Sens_di_out, Sens_n_out, Sens_ref_u, P.Td]
            # sens_names = ['Sens_r_y', 'Sens_do_y', 'Sens_di_y', 'Sens_n_y', 'Sens_r_u']
            arrays = [['Sensitivity_r_y', 'Sensitivity_r_y',
                    'Sensitivity_dy_y', 'Sensitivity_dy_y',
                    'Sensitivity_dv_y', 'Sensitivity_dv_y',
                    'Sensitivity_n_y', 'Sensitivity_n_y',
                    'Sensitivity_r_u', 'Sensitivity_r_u',
                    'Sensitivity_r_y_DESIRED', 'Sensitivity_r_y_DESIRED'],
                    ['gain', 'phase', 'gain', 'phase', 'gain', 'phase',
                    'gain', 'phase', 'gain', 'phase', 'gain', 'phase']]
            tuples = list(zip(*arrays))
            M1 = []
            for S1 in Sens:
                M1.append([amp_db(S1), phase_deg(S1)])
            M = [item for sublist in M1 for item in sublist]
            index = pd.MultiIndex.from_tuples(tuples)
            df = pd.DataFrame(np.transpose(M), index=P.w / (2 * np.pi), columns=index)
            df_tot.append(df)

        # import pdb
        # pdb.set_trace()
        return df_tot

    @staticmethod
    def sensitivities_v(P, Sens_damp_ry, Sens_volt_ry, Sens_damp_mm, Sens_volt_mm):

        def amp_db(X):
            return 20 * np.log10(np.abs(X))

        def phase_deg(X):
            return np.unwrap(np.angle(X)) * 180 / (np.pi)

        Sens = [Sens_damp_ry, Sens_volt_ry, Sens_damp_mm, Sens_volt_mm, P.Td_filt, P.Td]
        # sens_names = ['Sens_r_y', 'Sens_do_y', 'Sens_di_y', 'Sens_n_y', 'Sens_r_u']
        arrays = [['Sensitivity_r_y_damping', 'Sensitivity_r_y_damping',
                 'Sensitivity_r_y_voltage', 'Sensitivity_r_y_voltage',
                 'Sensitivity_dy_y_damp', 'Sensitivity_dy_y_damp',
                 'Sensitivity_dy_y_volt', 'Sensitivity_dy_y_volt',
                 'Sensitivity_r_y_damping_DESIRED', 'Sensitivity_r_y_damping_DESIRED',
                 'Sensitivity_r_y_voltage_DESIRED', 'Sensitivity_r_y_voltage_DESIRED'],
                ['gain', 'phase', 'gain', 'phase', 'gain', 'phase',
                 'gain', 'phase', 'gain', 'phase', 'gain', 'phase']]
        tuples = list(zip(*arrays))
        M1 = []
        for S in Sens:
            M1.append([amp_db(S), phase_deg(S)])
        M = [item for sublist in M1 for item in sublist]
        index = pd.MultiIndex.from_tuples(tuples)
        df = pd.DataFrame(np.transpose(M), index=P.w / (2 * np.pi), columns=index)
        # import pdb
        # pdb.set_trace()
        return df
