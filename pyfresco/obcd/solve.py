import cvxpy as cp


class Solve:
    def __init__(self, constraints, opt_vars, bis_tol):
        self.constraints = constraints
        self.opt_vars = opt_vars
        self.bis_tol = bis_tol

    @staticmethod
    def solve(prob, print_callback, opt_type='bisection', i=None):
        fail_message = 'All solvers failed. Please change your ' + \
                        'desired specifications and/or verify that ' + \
                        'your input data is correct.'
        if opt_type == 'bisection':
            try:
                prob.solve(solver=cp.ECOS, abstol_inacc=1, max_iters=10000)
            except:
                print_callback('warning', 'ECOS solver failed. '
                                'Trying a more robust solver...')
                try:
                    prob.solve(solver=cp.CVXOPT, kktsolver='robust')
                except:
                    raise Exception(fail_message)
                print_callback('warning', 'Robust solver succeeded! '
                                          f'Moving on to iteration {i}...')
        elif opt_type == 'lmi':
            try:
                prob.solve(solver=cp.CVXOPT, kktsolver='qr')
            except:
                raise Exception(fail_message)
        elif opt_type == 'Q':
            try:
                prob.solve(solver=cp.CVXOPT, kktsolver='robust')
            except:
                raise Exception('Q-filter design for ILC failed. '
                                'Try to increase Q-filter order.')
        elif opt_type == 'L':
            try:
                prob.solve(solver=cp.CVXOPT, kktsolver='robust')
            except:
                raise Exception('ILC solver failed. Try to modify '
                                'your desired specifications.')
        else:
            try:
                prob.solve(solver=cp.CVXOPT, kktsolver='robust')
            except:
                raise Exception(fail_message)

        stat = prob.status

        return stat

    '''
    def bisection(self, gamma, g_max, g_min):
        # Function which minimizes gamma

        gamma.value = (g_max + g_min) / 2
        bis_flag = []
        while g_max - g_min > self.bis_tol:

            prob = cp.Problem(cp.Minimize(gamma), self.constraints)
            stat = Solve.solve(prob)

            if stat == "optimal":
                # print(f'Feasible (gamma = {gamma.value})')
                gamma_opt = gamma.value
                x = [x0.value for x0 in self.opt_vars]
                g_max = gamma.value
                gamma.value = np.average([gamma.value, g_min])
                bis_flag.append(False)

            else:
                # print(f'Infeasible (gamma = {gamma.value})')
                g_min = gamma.value
                gamma.value = np.average([gamma.value, g_max])
                bis_flag.append(True)

        if all(bis_flag):
            bis_out = {'x': 1, 'g-opt-bis': gamma.value}
        else:
            bis_out = {'x': x, 'g-opt-bis': gamma_opt}

        return bis_out
    '''

    def bisection(self, gamma, g_max, g_min, print_callback):

        # gamma.value = (g_max + g_min) / 2
        i, bis_flag = 1, []
        while g_max - g_min > self.bis_tol:

            prob = cp.Problem(cp.Minimize(gamma), self.constraints)
            stat = Solve.solve(prob, print_callback, i=i)

            if stat == "optimal":
                # print(f'Feasible (gamma = {gamma.value})')
                gamma_opt = 1 / gamma.value
                x = [x0.value for x0 in self.opt_vars]
                g_min = gamma.value
                gamma.value = (gamma.value + g_max) / 2
                bis_flag.append(False)

            else:
                # print(f'Infeasible (gamma = {gamma.value})')
                g_max = gamma.value
                gamma.value = (gamma.value + g_min) / 2
                bis_flag.append(True)
            i += 1

        if all(bis_flag):
            bis_out = {'x': 1, 'g-opt-bis': 1 / gamma.value}
        elif True not in bis_flag:
            raise Exception('Could not perform bisection algorithm. Please modify'
                ' your desired parameters and/or verify your data.')
        else:
            bis_out = {'x': x, 'g-opt-bis': gamma_opt}

        return bis_out