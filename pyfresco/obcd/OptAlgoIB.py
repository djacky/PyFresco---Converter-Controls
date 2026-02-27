import cvxpy as cp
import numpy as np
from pyfresco.obcd import constants as cn
from pyfresco.obcd import common_funcs as cf
from pyfresco.obcd import solve as slv


class OptAlgoIB:
    """
    This class is used to run the RST and ILC optimization algorithms for
    current and field control.
    """
    def __init__(self, G_multi, MA_filt, w, Ts, user_pars, print_callback):
        """
        The constructor for OptAlgoIB.

        Arguments:
                G (complex array): open-loop frequency response.
                MA_filt (complex array): moving average frequency response.
                w (real array): frequency vector in rad/s.
                Ts (float): regulation sampling time in seconds.
                user_pars (attributes): UI parameters
        """

        self.w = w
        self.G_multi = G_multi
        self.MA = MA_filt
        self.Ts = Ts
        self.user_pars = user_pars
        self.print_callback = print_callback

        self.Td, self.Wd = cf.Funcs.des_2nd_order(w,
                user_pars.des_bw, user_pars.des_z, user_pars.ref_delay)

    def cont_struct(self, **kwargs):
        """
        Function is used to construct RST frequency response functions. If kwargs['opt]
        == True, the RST's are constructed to be optimized. If kwargs['opt'] == False,
        then the RST's are used to construct the sensitivity functions.
        """

        if kwargs['opt']:
            n_r, n_s, n_t = (kwargs['n_r'], kwargs['n_s'], kwargs['n_t'])

            rho_r, rho_s, rho_t = (cp.Variable(n_r),
                    cp.Variable(n_s - 1 - self.user_pars.n_integrators), cp.Variable(n_t))
            self.rho_r, self.rho_s, self.rho_t = (rho_r, rho_s, rho_t)

        elif not kwargs['opt']:
            rho_r, rho_s, rho_t = (kwargs['r'], kwargs['s'], kwargs['t'])
            n_r, n_s, n_t = (len(rho_r), len(rho_s) + 1 + self.user_pars.n_integrators, len(rho_t))

        z = lambda x: np.exp(x * 1j * self.w * self.Ts)

        Ro = 0
        for i in range(n_r):
            Ro += rho_r[i] * z(-i)

        So = 0
        for i in range(n_s - 1 - self.user_pars.n_integrators):
            So += rho_s[i] * z(-(i + 1))

        if kwargs['opt']:
            So_with_int = cp.multiply(np.power((1 - z(-1)), self.user_pars.n_integrators), 1 + So)
            self.So_no_int = 1 + So
        elif not kwargs['opt']:
            So_with_int = np.multiply(np.power((1 - z(-1)), self.user_pars.n_integrators), 1 + So)

        To = 0
        for i in range(n_t):
            To += rho_t[i] * z(-i)

        return Ro, So_with_int, To

    def rst_init(self, order, T_flag):
        """
        Function is used to design initial stabilizing RST controller.

        Arguments:
                order (dict): orders of R, S, and T polynomials.
                T_flag (bool): flag to ensure stability of 1/T (if needed).
        """

        Ro, So, To = OptAlgoIB.cont_struct(self, opt=True,
                    n_r=order['n_r'], n_s=order['n_s'], n_t=order['n_t'])

        gamma = cp.Parameter(nonneg=True, value=2 / 10)
        constraints = []
        for G in self.G_multi:
            PSI = So + cp.multiply(G * self.MA, Ro)
            F1 = cp.multiply(gamma, cp.abs(cp.multiply(self.Wd,
                    PSI - cp.multiply(G, To)))) - cp.real(PSI)

            F2 = cp.abs(cp.multiply(self.user_pars.des_mm, So)) - cp.real(PSI)

            con_noise = []
            if self.user_pars.noise_rej:
                for pair in self.user_pars.noise_rej:
                    index = np.where(self.w == 2 * np.pi * pair[0])[0][0]
                    gain_abs = 10 ** (-pair[1] / 20)
                    xn = cp.abs(cp.multiply(gain_abs * G[index], So[index]))
                    con_noise += [xn - cp.real(PSI[index]) <= -1e-6]

            if not T_flag:
                constraints += [F1 <= -1e-6, F2 <= -1e-6,
                            cp.real(self.So_no_int) >= 5e-3] + con_noise
            elif T_flag:
                constraints += [F1 <= -1e-6, F2 <= -1e-6,
                            cp.real(self.So_no_int) >= 5e-3, cp.real(To) >= 5e-3] + con_noise
        g_max, g_min = (cn.g_max, 0.1)
        bis = slv.Solve(constraints, (self.rho_r, self.rho_s, self.rho_t), cn.bis_tol)
        bis_sol = bis.bisection(gamma, g_max, g_min, self.print_callback)

        if bis_sol['g-opt-bis'] > (1 / g_min) * 0.9:
            return {'gamma_opt': 100}

        R0, S0, T0 = OptAlgoIB.cont_struct(self, opt=False,
                    r=bis_sol['x'][0], s=bis_sol['x'][1], t=bis_sol['x'][2])
        GAIN = np.sum(bis_sol['x'][2]) / np.sum(bis_sol['x'][0])

        return {'gamma_opt': bis_sol['g-opt-bis'],
                'R_vec': bis_sol['x'][0],
                'S_vec': bis_sol['x'][1],
                'T_vec': bis_sol['x'][2], 'Gain': GAIN,
                'Rf': R0, 'Sf': S0, 'Tf': T0}

    def hinf(self, R0, S0, order, T_flag):
        """
        Function that executes the optimization for H-infinity control

        Arguments:
                R0 (complex array): frequency response of initial R polynomial.
                S0 (complex array): frequency response of initial S polynomial.
                order (dict): orders of R, S, and T polynomials.
                T_flag (bool): flag to ensure stability of 1/T (if needed).
        """

        Ro, So, To = OptAlgoIB.cont_struct(self, opt=True,
                    n_r=order['n_r'], n_s=order['n_s'], n_t=order['n_t'])

        g_lmi = np.insert(np.zeros(100), 0, 1e6)
        it = 1
        rst_list = []
        while g_lmi[it - 1] - g_lmi[it] > cn.LMI_tol:

            gamma = cp.Parameter(nonneg=True, value=2 / 200)
            constraints = []
            for G in self.G_multi:
                PSI2 = So + cp.multiply(G * self.MA, Ro)
                PSI2_0 = S0 + np.multiply(G * self.MA, R0)

                t1 = 2 * cp.real(cp.multiply(cp.conj(PSI2_0), PSI2)) - cp.power(cp.abs(PSI2_0), 2)
                # x1 = cp.multiply(cp.inv_pos(gamma),cp.power(cp.abs(cp.multiply((2*np.pi)
                # /(1j*w),cp.multiply(G,To) - cp.multiply(Td,PSI2))),2))
                x1 = cp.multiply(gamma, cp.power(cp.abs(cp.multiply(self.Wd,
                        PSI2 - cp.multiply(G, To))), 2))
                x2 = cp.power(cp.abs(cp.multiply(self.user_pars.des_mm, So)), 2)

                con_noise = []
                if self.user_pars.noise_rej:
                    for pair in self.user_pars.noise_rej:
                        index = np.where(self.w == 2 * np.pi * pair[0])[0][0]
                        gain_abs = 10 ** (-pair[1] / 20)
                        xn = cp.power(cp.abs(cp.multiply(gain_abs * G[index], So[index])), 2)
                        con_noise += [xn - t1[index] <= -1e-6]

                g_max, g_min = (10, 1e-3)
                if not T_flag:
                    constraints += [x1 - t1 <= -1e-6, x2 - t1 <= -1e-6,
                                cp.real(self.So_no_int) >= 5e-3] + con_noise

                elif T_flag:
                    constraints += [x1 - t1 <= -1e-6, x2 - t1 <= -1e-6,
                                cp.real(self.So_no_int) >= 5e-3, cp.real(To) >= 5e-3] + con_noise

            bis = slv.Solve(constraints, (self.rho_r, self.rho_s, self.rho_t),
                cn.bis_tol)
            bis_sol = bis.bisection(gamma, g_max, g_min, self.print_callback)
            rst_list.append(bis_sol['x'])

            g_lmi[1] = 1e6
            g_lmi[it + 1] = np.sqrt(bis_sol['g-opt-bis'])
            it = it + 1

            if bis_sol['g-opt-bis'] > cn.g_thresh:
                return {'gamma_opt': 1000}
            elif (g_lmi[it] < 1 and it > 2):
                return {'gamma_opt': g_lmi[it]}
            elif (g_lmi[it] > g_lmi[it - 1] and it > 2):
                break
            else:
                self.print_callback('info',
                    f'Feasible for iteration {it - 1} ({cn.ug} = {round(g_lmi[it], cn.g_digits)})')
                GAIN = np.sum(bis_sol['x'][2]) / np.sum(bis_sol['x'][0])
                R0, S0, T0 = OptAlgoIB.cont_struct(self, opt=False,
                            r=bis_sol['x'][0], s=bis_sol['x'][1], t=bis_sol['x'][2])

        # Troots = np.abs(np.roots(bis_sol['T-vec-bis']))
        T0 = T0 / GAIN

        return {'gamma_opt': np.sqrt(bis_sol['g-opt-bis']),
                'R_vec': bis_sol['x'][0],
                'S_vec': bis_sol['x'][1],
                'T_vec': bis_sol['x'][2], 'Gain': GAIN,
                'Rf': R0, 'Sf': S0, 'Tf': T0}

    def h2(self, R0, S0, order, T_flag):
        """
        Function that executes the optimization for H-2 control

        Arguments:
                R0 (complex array): frequency response of initial R polynomial.
                S0 (complex array): frequency response of initial S polynomial.
                order (dict): orders of R, S, and T polynomials.
                T_flag (bool): flag to ensure stability of 1/T (if needed).
        """
        Ro, So, To = OptAlgoIB.cont_struct(self, opt=True,
                    n_r=order['n_r'], n_s=order['n_s'], n_t=order['n_t'])

        g_lmi = np.insert(np.zeros(100), 0, 1e6)
        it = 1

        while g_lmi[it - 1] - g_lmi[it] > cn.LMI_tol:
            gamma = cp.Variable(len(self.w), nonneg=True)
            con = []

            for G in self.G_multi:
                PSI2 = So + cp.multiply(G * self.MA, Ro)
                PSI2_0 = S0 + np.multiply(G * self.MA, R0)

                for i in range(len(self.w)):
                    Wr = (2 * np.pi * self.user_pars.des_bw) / (1j * self.w[i])
                    con1 = 2 * cp.real(cp.multiply(np.conj(PSI2_0[i]), PSI2[i])) \
                        - np.power(np.abs(PSI2_0[i]), 2)
                    # con2 = cp.multiply(self.Wd[i], So[i] + cp.multiply(G[i],
                    #    Ro[i] - To[i]))
                    con2 = cp.multiply(Wr,
                        cp.multiply(G[i], To[i]) - cp.multiply(self.Td[i], PSI2[i]))
                    con3 = cp.conj(con2)
                    con4 = gamma[i]

                    A1, A2 = cp.hstack([con1, con3]), cp.hstack([con2, con4])
                    MAT1 = cp.vstack([A1, A2])

                    con11 = 2 * cp.real(cp.multiply(np.conj(PSI2_0[i]), PSI2[i])) \
                        - np.power(np.abs(PSI2_0[i]), 2)
                    con21 = cp.multiply(self.user_pars.des_mm, So[i])
                    con31 = cp.conj(con21)
                    con41 = 1

                    A11, A12 = cp.hstack([con11, con31]), cp.hstack([con21, con41])
                    MAT2 = cp.vstack([A11, A12])

                    con += [MAT1 >> 0, MAT2 >> 0]

            con_noise = []
            if self.user_pars.noise_rej:
                for G in self.G_multi:
                    for pair in self.user_pars.noise_rej:
                        index = np.where(self.w == 2 * np.pi * pair[0])[0][0]
                        gain_abs = 10 ** (-pair[1] / 20)
                        xn = cp.power(cp.abs(cp.multiply(gain_abs * G[index], So[index])), 2)
                        t1 = 2 * cp.real(cp.multiply(cp.conj(PSI2_0[index]), PSI2[index])) \
                            - cp.power(cp.abs(PSI2_0[index]), 2)
                        con_noise += [xn - t1 <= -1e-6]

            if not T_flag:
                cnst = con + [cp.real(self.So_no_int) >= 5e-3] + con_noise
            elif T_flag:
                cnst = con + [cp.real(self.So_no_int) >= 5e-3] + [cp.real(To) >= 5e-3] + con_noise

            OB = 0
            for v in range(len(self.w) - 1):
                OB = OB + 0.5 * (gamma[v] + gamma[v+1]) * (self.w[v+1] - self.w[v])
            OB = self.Ts / np.pi * OB
            prob = cp.Problem(cp.Minimize(OB), cnst)
            stat = slv.Solve.solve(prob, self.print_callback, opt_type='lmi')

            if stat == "optimal" or stat == "optimal_inaccurate":
                rho_r_OPT, rho_s_OPT, rho_t_OPT = (self.rho_r.value, self.rho_s.value,
                                                self.rho_t.value)
                GAIN = np.sum(rho_t_OPT) / np.sum(rho_r_OPT)
                R0, S0, T0 = OptAlgoIB.cont_struct(self, opt=False,
                                                   r=rho_r_OPT, s=rho_s_OPT, t=rho_t_OPT)
                T0 = T0 / GAIN

                # g_lmi[1], g_lmi[it + 1] = (1e6, np.sum(gamma.value))
                g_lmi[1], g_lmi[it + 1] = (1e6, OB.value)
                it = it + 1
                if g_lmi[it] > g_lmi[it - 1] and it > 2:
                    break
                self.print_callback('info',
                    f"Feasible for iteration {it - 1} ({cn.ug} = {g_lmi[it]:.2E})")
                gamma_opt = g_lmi[it]
            else:
                return {'gamma_opt': 1000}

        return {'gamma_opt': gamma_opt,
                'R_vec': rho_r_OPT,
                'S_vec': rho_s_OPT,
                'T_vec': rho_t_OPT, 'Gain': GAIN,
                'Rf': R0, 'Sf': S0, 'Tf': T0}

    def h1(self, order, **kwargs):
        """
        Function that executes the optimization for H-1 control. This is a two-step
        optimization where the R and S polynomials are designed to get a desired modulus
        margin, and T is then designed to get the desired performance.

        Arguments:
                order (dict): orders of R, S, and T polynomials.
                kwargs['T_stable_flag']: flag to ensure stability of 1/T (if needed).
        """
        Ro, So, To = OptAlgoIB.cont_struct(self, opt=True,
                    n_r=order['n_r'], n_s=order['n_s'], n_t=order['n_t'])

        cnst = []
        for G in self.G_multi:
            PSI = So + cp.multiply(G * self.MA, Ro)
            F2 = cp.abs(cp.multiply(self.user_pars.des_mm, So)) - cp.real(PSI)

            con_noise = []
            if self.user_pars.noise_rej:
                for pair in self.user_pars.noise_rej:
                    index = np.where(self.w == 2 * np.pi * pair[0])[0][0]
                    gain_abs = 10 ** (-pair[1] / 20)
                    xn = cp.abs(cp.multiply(gain_abs * G[index], So[index]))
                    con_noise += [xn - cp.real(PSI[index]) <= -1e-6]

            cnst += [F2 <= -1e-6, cp.real(self.So_no_int) >= 5e-3] + con_noise

        prob = cp.Problem(cp.Minimize(0), cnst)
        stat = slv.Solve.solve(prob, self.print_callback)

        if stat == "optimal":
            # print("Feasible")
            rho_r_OPT, rho_s_OPT = (self.rho_r.value, self.rho_s.value)
            RS_flag = False

        else:
            # print("Infeasible")
            return {'RS-flag': True}

        R0, S0, _ = OptAlgoIB.cont_struct(self, opt=False, r=rho_r_OPT, s=rho_s_OPT, t=[0, 0])
        OB = 0
        for G in self.G_multi:
            TCL = cp.multiply(cp.multiply(G, To), 1 / (S0 + R0 * G * self.MA))
            F_OB = cp.multiply(cp.multiply(2 * np.pi * self.user_pars.des_bw, 1 / (1j * self.w)),
                TCL - self.Td)
            OB += cp.pnorm(F_OB, 1)

        if not kwargs['T_stable_flag']:
            prob2 = cp.Problem(cp.Minimize(OB))
        elif kwargs['T_stable_flag']:
            prob2 = cp.Problem(cp.Minimize(OB), [cp.real(To) >= 5e-3])

        stat2 = slv.Solve.solve(prob2, self.print_callback, opt_type='h1')

        if stat2 == "optimal":
            T_flag = False
            rho_t_OPT = self.rho_t.value
            GAIN = np.sum(rho_t_OPT) / np.sum(rho_r_OPT)

            _, _, T0 = OptAlgoIB.cont_struct(self, opt=False,
                    r=rho_r_OPT, s=rho_s_OPT, t=rho_t_OPT)

            T0 = T0 / GAIN
        else:
            T_flag = True
            return {'T-flag': T_flag, 'RS-flag': RS_flag}

        return {'R_vec': rho_r_OPT,
                'S_vec': rho_s_OPT,
                'T_vec': rho_t_OPT, 'Gain': GAIN,
                'Rf': R0, 'Sf': S0, 'Tf': T0, 'RS-flag': RS_flag, 'T-flag': T_flag}

    def q_filt_opt(self, Qd):
        """
        Function to design non-causal FIR Q-filter (to be used in the ILC optimization)

        Arguments:
                Qd (complex array): desired low-pass filter for Q.
        """
        self.print_callback('info', 'Starting the Q-filter optimization...')
        rho_q = cp.Variable(2 * self.user_pars.n_q + 1)
        n_vector = np.arange(-self.user_pars.n_q, self.user_pars.n_q + 1).astype(int)
        z = lambda x: np.exp(x * 1j * self.w * self.Ts)

        Q = 0
        for index, i in enumerate(n_vector):
            Q += cp.multiply(rho_q[index], z(i))

        prob = cp.Problem(cp.Minimize(cp.pnorm((np.abs(Qd) - Q), 1)), [cp.sum(rho_q) == 1])
        stat = slv.Solve.solve(prob, self.print_callback, opt_type='Q')

        if stat == "optimal":
            Q0 = 0
            for index, i in enumerate(n_vector):
                Q0 += rho_q.value[index] * z(i)
            # flag = False
            obj = cf.Funcs.norm1(self.Ts, self.w, (np.abs(Qd) - Q0))
            self.print_callback('info', f'Q-filter design finished! ({cn.ugq} = {round(obj, 5)})')
        else:
            raise Exception('Q-filter design for ILC failed. '
                    'Try to increase Q-filter order.')

        return Q0, rho_q.value

    def ilc(self, G_multi, n):
        """
        Function to design L-filter for ILC.

        Arguments:
                G (complex array): Closed-loop frequency response
                n (int): order of ILC L-filter
        """

        rho = cp.Variable(2 * n + 1)
        n_vector = np.arange(-n, n + 1).astype(int)
        z = lambda x: np.exp(x * 1j * self.w * self.Ts)

        if self.user_pars.q_bw == 0:
            Q, Q_vec = 1, 1
        elif self.user_pars.q_bw > 0:
            Qd, _ = cf.Funcs.des_2nd_order(self.w, self.user_pars.q_bw, 1, 0)
            Q, Q_vec = OptAlgoIB.q_filt_opt(self, Qd)

        L = 0
        for index, i in enumerate(n_vector):
            L += cp.multiply(rho[index], z(i))

        gamma = cp.Variable(1)
        constraints = []
        for G in G_multi:
            F1 = cp.abs(cp.multiply(Q, 1 - cp.multiply(L, G)))
            constraints += [F1 <= gamma]
        constraints = constraints + [gamma >= 0]
        prob = cp.Problem(cp.Minimize(gamma), constraints)
        stat = slv.Solve.solve(prob, self.print_callback, opt_type='L')

        if stat == "optimal" and gamma.value < 1:
            # print("Feasible Problem")
            gamma0, L_vec = (gamma.value, rho.value)
            flag = False
        else:
            # print("ILC: Infeasible Problem")
            return {'flag': True}

        L0 = 0
        for index, i in enumerate(n_vector):
            L0 += L_vec[index] * z(i)

        return {'gamma_opt': gamma0, 'flag': flag,
                'Lf': L0, 'Qf': Q, 'L_vec': L_vec, 'Q_vec': Q_vec}