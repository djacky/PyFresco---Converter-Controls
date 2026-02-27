import cvxpy as cp
import numpy as np
from pyfresco.obcd import constants as cn
from pyfresco.obcd import common_funcs as cf
from pyfresco.obcd import solve as slv
# import sys


class OptAlgoV:
    def __init__(self, F, Ts, user_pars, print_callback):

        self.w = F['w']
        self.GH = F['ref_to_icapa']
        self.GM = F['ref_to_imeas']
        self.Gf = F['ref_to_vmeas']
        self.DC = F['DC_mag']
        self.Ts_fund = Ts
        self.user_pars = user_pars
        self.print_callback = print_callback

        self.Td, self.Wd = cf.Funcs.des_2nd_order(self.w, self.user_pars.volt_bw,
                    self.user_pars.volt_z, self.user_pars.ref_delay)
        self.Td_filt, self.Wd_filt = cf.Funcs.des_2nd_order(self.w, self.user_pars.damp_bw,
                    self.user_pars.damp_z, self.user_pars.ref_delay)

    def damping_struct(self, K, **kwargs):
        # K[0]=Ki, K[1]=Kd, K[2]=Ku
        if kwargs['opt']:
            H1 = cp.multiply(K[0], self.GH)
            H2 = cp.multiply(K[1], self.GM)
            H3 = cp.multiply(K[2], self.Gf)
            PSI = 1 + H1 + H2 + H3

        elif not kwargs['opt']:
            H1_init = K[0] * self.GH
            H2_init = K[1] * self.GM
            H3_init = K[2] * self.Gf
            PSI = 1 + H1_init + H2_init + H3_init

        return PSI

    def damping_hinf(self):

        g_lmi = np.insert(np.zeros(100), 0, 1e6)
        it = 1

        K, Ki = cp.Variable(3), 1e-4 * np.ones(3)
        PSI = OptAlgoV.damping_struct(self, K, opt=True)

        while g_lmi[it - 1] - g_lmi[it] > cn.LMI_tol:

            PSI_0 = OptAlgoV.damping_struct(self, Ki, opt=False)

            gamma = cp.Parameter(nonneg=True, value=2 / cn.g_max)
            t1 = 2 * cp.real(cp.multiply(cp.conj(PSI_0), PSI)) - cp.power(cp.abs(PSI_0), 2)
            x1 = cp.multiply(gamma, cp.power(cp.abs(cp.multiply(self.Wd_filt, PSI -
                cp.multiply(self.Gf, (1 + K[2] + cp.multiply(K[1], self.DC))))), 2))
            x2 = cp.power(self.user_pars.damp_mm, 2)

            constraints = [x1 - t1 <= -1e-6, x2 - t1 <= -1e-6, K[2] >= 0]
            if self.user_pars.positive_coeff:
                constraints += [K >= 0]
            if self.user_pars.kd_0:
                constraints += [K[1] == 0]
            g_max, g_min = (cn.g_max, 1e-3)
            bis = slv.Solve(constraints, K, cn.bis_tol)
            bis_sol = bis.bisection(gamma, g_max, g_min, self.print_callback)

            g_lmi[1] = 1e6
            g_lmi[it + 1] = np.sqrt(bis_sol['g-opt-bis'])
            it += 1

            if g_lmi[it] > g_lmi[it - 1] and it > 2:
                break
            else:
                gamma_opt, Ki = (bis_sol['g-opt-bis'], bis_sol['x'])

            if (np.sqrt(gamma_opt) > cn.g_max and it == 10) or \
                    (gamma_opt > (1 / g_min) * 0.5 and it == 2):
                raise Exception('Bad solution or infeasible problem. Check input data'
                    ' and/or change your desired specifications.')
            self.print_callback('info',
                f'Feasible for iteration {it - 1} ({cn.ug} = {round(g_lmi[it], cn.g_digits)})')

        PSI_CL = OptAlgoV.damping_struct(self, Ki, opt=False)
        Tcl = (self.Gf * (1 + Ki[2] + Ki[1] * self.DC)) / PSI_CL
        self.T_damp = Tcl

        return {'gamma_opt': np.sqrt(gamma_opt), 'K-dloop': Ki,
                'T-damping': Tcl, 'Sens-damp': 1 / PSI_CL}

    def damping_h2(self):

        g_lmi_0 = np.zeros(100)
        g_lmi = np.insert(g_lmi_0, 0, 1e6)
        it = 1

        K, Ki = cp.Variable(3), 1e-4 * np.ones(3)
        PSI = OptAlgoV.damping_struct(self, K, opt=True)

        while g_lmi[it - 1] - g_lmi[it] > cn.LMI_tol:
            gamma = cp.Variable(len(self.w), nonneg=True)

            PSI_0 = OptAlgoV.damping_struct(self, Ki, opt=False)
            con = []
            for i in range(len(self.w)):

                con1 = 2 * cp.real(cp.multiply(cp.conj(PSI_0[i]),
                    PSI[i])) - cp.power(cp.abs(PSI_0[i]), 2)
                con2 = cp.multiply((2 * np.pi * self.user_pars.damp_bw) / (1j * self.w[i]),
                     cp.multiply(self.Gf[i],
                     (1 + K[2] + K[1] * self.DC)) - cp.multiply(self.Td_filt[i], PSI[i]))
                # con2 = cp.multiply(self.Wd_filt[i], PSI[i] - cp.multiply(self.Gf[i],
                #        (1 + K[2] + K[1] * self.DC)))
                con3 = cp.conj(con2)
                con4 = gamma[i]

                A1, A2 = (cp.hstack([con1, con3]), cp.hstack([con2, con4]))
                MAT1 = cp.vstack([A1, A2])

                con11 = con1
                con21 = self.user_pars.damp_mm
                con31 = cp.conj(con21)
                con41 = 1

                A11, A12 = (cp.hstack([con11, con31]), cp.hstack([con21, con41]))
                MAT2 = cp.vstack([A11, A12])

                con += [MAT1 >> 0, MAT2 >> 0]

            cnst = con + [K[2] >= 0]
            if self.user_pars.positive_coeff:
                cnst += [K >= 0]
            if self.user_pars.kd_0:
                cnst += [K[1] == 0]
            OB = 0
            for v in range(len(self.w) - 1):
                OB = OB + 0.5 * (gamma[v] + gamma[v+1]) * (self.w[v+1] - self.w[v])
            OB = self.Ts_fund / np.pi * OB
            prob = cp.Problem(cp.Minimize(OB), cnst)
            stat = slv.Solve.solve(prob, self.print_callback, opt_type='lmi')

            if stat == "optimal" or stat == "optimal_inaccurate":
                Ki = K.value
                PSI_CL = OptAlgoV.damping_struct(self, Ki, opt=False)
                Tcl = (self.Gf * (1 + Ki[2] + Ki[1] * self.DC)) / PSI_CL
                g_lmi[1], g_lmi[it + 1] = (1e6, OB.value)
                it += 1
                gamma_opt = g_lmi[it]
                self.print_callback('info',
                    f'Feasible for iteration {it - 1} ({cn.ug} = {g_lmi[it]:.2E})')
                if g_lmi[it] > g_lmi[it - 1] and it > 2:
                    break
            else:
                raise Exception('Bad solution or infeasible problem. Check input data'
                    ' and/or change your desired specifications.')

            if gamma_opt > 10 and it == 10:
                raise Exception('Bad solution or infeasible problem. Check input data'
                    ' and/or change your desired specifications.')
        self.T_damp = Tcl

        return {'gamma_opt': np.sqrt(gamma_opt), 'K-dloop': Ki,
                'T-damping': Tcl, 'Sens-damp': 1 / PSI_CL}

    def init_PI(self, lag):
        x = cp.Variable(2)
        Xo = cp.multiply((cp.multiply(x[0], 1j * self.w) + x[1]), 1 / (1j * self.w + lag))
        Yo = (1j * self.w) / (1j * self.w + lag)

        gamma = cp.Parameter(nonneg=True, value=2 / cn.g_max)
        PSI = cp.real(Yo + cp.multiply(Xo, self.T_damp))
        F1 = cp.multiply(gamma, cp.abs(self.Wd * Yo))
        constraints2 = [F1 - PSI <= -1e-6]
        if self.user_pars.positive_coeff:
            constraints2 += [x >= 0]
        g_max, g_min = (cn.g_max, 1e-3)
        bis = slv.Solve(constraints2, x, cn.bis_tol)
        bis_sol = bis.bisection(gamma, g_max, g_min, self.print_callback)

        return bis_sol['g-opt-bis'], bis_sol['x']

    def voltage_hinf(self, Ki):

        g_lmi_0 = np.zeros(100)
        g_lmi = np.insert(g_lmi_0, 0, 1e6)
        it = 1

        Kv = cp.Variable(3)
        # X = cp.multiply(Kv[0], 1j*self.w) + Kv[1]; Y = 1j*self.w
        C = cp.multiply(cp.multiply(Kv[0], 1j * self.w) + Kv[1], 1 / (1j * self.w))
        k_list = []
        while g_lmi[it - 1] - g_lmi[it] > cn.LMI_tol:

            gamma = cp.Parameter(nonneg=True, value=2 / cn.g_max)
            C_init = cp.multiply(cp.multiply(Ki[0], 1j * self.w) + Ki[1], 1 / (1j * self.w))

            PSI_0 = 1 + cp.multiply(C_init, self.T_damp)
            PSI = 1 + cp.multiply(C, self.T_damp)

            t2 = 2 * cp.real(cp.multiply(cp.conj(PSI_0), PSI)) - cp.power(cp.abs(PSI_0), 2)
            x2 = cp.multiply(gamma, cp.power(cp.abs(cp.multiply(self.Wd,
                    PSI - cp.multiply(self.T_damp, C + Kv[2]))), 2))
            x3 = cp.power(self.user_pars.volt_mm, 2)

            constraints3 = [x2 - t2 <= -1e-6, x3 - t2 <= -1e-6]
            if self.user_pars.positive_coeff:
                constraints3 += [Kv >= 0]
            g_max, g_min = (cn.g_max, 1e-3)
            bis = slv.Solve(constraints3, Kv, cn.bis_tol)
            bis_sol = bis.bisection(gamma, g_max, g_min, self.print_callback)
            gamma_opt = bis_sol['g-opt-bis']
            k_list.append(bis_sol)

            g_lmi[1] = 1e6
            g_lmi[it + 1] = np.sqrt(gamma_opt)
            it += 1

            if g_lmi[it] > g_lmi[it - 1] and it > 2:
                Ki = k_list[it - 3]['x']
                gamma_opt = k_list[it - 3]['g-opt-bis']
                break
            else:
                gamma_opt, Ki = (bis_sol['g-opt-bis'], bis_sol['x'])

            if (np.sqrt(gamma_opt) > cn.g_max and it == 10) or \
                    (gamma_opt > (1 / g_min) * 0.5 and it == 2):
                raise Exception('Bad solution or infeasible problem. Check input data'
                    ' and/or change your desired specifications.')
            self.print_callback('info',
                f'Feasible for iteration {it - 1} ({cn.ug} = {round(g_lmi[it], cn.g_digits)})')

        Cf = (Ki[0] * 1j * self.w + Ki[1]) / (1j * self.w)

        PSI_CL = 1 + Cf * self.T_damp
        Tcl = (self.T_damp * (Ki[2] + Cf)) / PSI_CL
        Sens = 1 / PSI_CL

        return {'gamma_opt': np.sqrt(gamma_opt), 'K-vloop': Ki, 'T-voltage': Tcl,
                'Sens-volt': Sens}

    def voltage_h2(self, Ki):

        g_lmi_0 = np.zeros(100)
        g_lmi = np.insert(g_lmi_0, 0, 1e6)
        it = 1

        Kv = cp.Variable(3)
        C = cp.multiply(cp.multiply(Kv[0], 1j * self.w) + Kv[1], 1 / (1j * self.w))

        while g_lmi[it - 1] - g_lmi[it] > cn.LMI_tol:
            gamma = cp.Variable(len(self.w), nonneg=True)
            C_init = cp.multiply(cp.multiply(Ki[0], 1j * self.w) + Ki[1], 1 / (1j * self.w))

            PSI_0 = 1 + cp.multiply(C_init, self.T_damp)
            PSI = 1 + cp.multiply(C, self.T_damp)

            con = []
            for i in range(len(self.w)):

                con1 = 2 * cp.real(cp.multiply(cp.conj(PSI_0[i]),
                    PSI[i])) - cp.power(cp.abs(PSI_0[i]), 2)
                con2 = cp.multiply((2 * np.pi * self.user_pars.volt_bw) / (1j * self.w[i]),
                     cp.multiply(self.T_damp[i],
                     (Kv[2] + C[i])) - cp.multiply(self.Td[i], PSI[i]))
                # con2 = cp.multiply(self.Wd[i], PSI[i] - cp.multiply(self.T_damp[i],
                #     (Kv[2] + C[i])))
                con3 = cp.conj(con2)
                con4 = gamma[i]

                A1, A2 = (cp.hstack([con1, con3]), cp.hstack([con2, con4]))
                MAT1 = cp.vstack([A1, A2])

                con11 = con1
                con21 = self.user_pars.volt_mm
                con31 = cp.conj(con21)
                con41 = 1

                A11, A12 = (cp.hstack([con11, con31]), cp.hstack([con21, con41]))
                MAT2 = cp.vstack([A11, A12])

                con += [MAT1 >> 0, MAT2 >> 0]

            cnst = con
            if self.user_pars.positive_coeff:
                cnst += [Kv >= 0]
            OB = 0
            for v in range(len(self.w) - 1):
                OB = OB + 0.5 * (gamma[v] + gamma[v+1]) * (self.w[v+1] - self.w[v])
            OB = self.Ts_fund / np.pi * OB
            prob = cp.Problem(cp.Minimize(OB), cnst)
            stat = slv.Solve.solve(prob, self.print_callback, opt_type='lmi')

            if stat == "optimal" or stat == "optimal_inaccurate":
                Ki = Kv.value
                Cf = (Ki[0] * 1j * self.w + Ki[1]) / (1j * self.w)
                PSI_CL = 1 + Cf * self.T_damp
                Tcl = (self.T_damp * (Ki[2] + Cf)) / PSI_CL
                g_lmi[1], g_lmi[it + 1] = (1e6, OB.value)
                it += 1
                if g_lmi[it] > g_lmi[it - 1] and it > 2:
                    break
                gamma_opt = g_lmi[it]
                self.print_callback('info',
                    f'Feasible for iteration {it - 1} ({cn.ug} = {g_lmi[it]:.2E})')
            else:
                raise Exception('Bad solution or infeasible problem. Check input data'
                    ' and/or change your desired specifications.')

            if gamma_opt > 10 and it == 10:
                raise Exception('Bad solution or infeasible problem. Check input data'
                    ' and/or change your desired specifications.')

        Sens = 1 / PSI_CL

        return {'gamma_opt': gamma_opt, 'K-vloop': Ki, 'T-voltage': Tcl, 'Sens-volt': Sens}