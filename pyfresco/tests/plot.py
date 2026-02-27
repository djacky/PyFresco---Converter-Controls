import numpy as np
import matplotlib.pyplot as plt


class Plot:

    @staticmethod
    def plot_gen(*args, device=None, log=True):
        path = '/afs/cern.ch/work/a/anicolet/private/reg_tools_personal/plots/' \
                 + device + '/'
        fig, ax = plt.subplots()
        i = 0
        if log:
            for a in range(int(len(args)/2)):
                ax.semilogx(args[i], args[i + 1])
                i += 2
        else:
            for a in range(int(len(args)/2)):
                ax.plot(args[i], args[i + 1])
                i += 2
        ax.grid()
        name = 'General_Plot'
        plt.savefig(path + name + '.png')
        plt.show()


    @staticmethod
    def plot(df_tot, device, user_pars, mode='I', open_loop=None):

        for df in df_tot:
            if mode in ['I', 'B']:
                path = '/afs/cern.ch/work/a/anicolet/private/reg_tools_personal/plots/' \
                    + device + '/sensitivities_IB/'
                Sg = np.power(10, df['Sensitivity_dy_y']['gain'].values / 20)
                Sp = df['Sensitivity_dy_y']['phase'].values * np.pi / 180
            elif mode == 'V':
                path = '/afs/cern.ch/work/a/anicolet/private/reg_tools_personal/plots/' \
                    + device + '/sensitivities_V/'
                Sg = np.power(10, df['Sensitivity_dy_y_volt']['gain'].values / 20)
                Sp = df['Sensitivity_dy_y_volt']['phase'].values * np.pi / 180
            elif mode == 'D':
                path = '/afs/cern.ch/work/a/anicolet/private/reg_tools_personal/plots/' \
                    + device + '/sensitivities_V/'
                Sg = np.power(10, df['Sensitivity_dy_y_damp']['gain'].values / 20)
                Sp = df['Sensitivity_dy_y_damp']['phase'].values * np.pi / 180

            if open_loop:
                path_L = '/afs/cern.ch/work/a/anicolet/private/reg_tools_personal/plots/' \
                    + device + '/'
                S = Sg * np.exp(1j * Sp)
                L = 1 / S - 1
                theta = np.linspace(0, 2 * np.pi, 500)
                circ = np.exp(1j * theta)
                fig, ax = plt.subplots()
                ax.plot(np.real(L), np.imag(L))
                ax.plot(np.real(circ), np.imag(circ))
                if mode in ['I', 'B']:
                    ax.plot(np.real(-1 + user_pars.des_mm * circ),
                        np.imag(-1 + user_pars.des_mm * circ))
                elif mode == 'V':
                    ax.plot(np.real(-1 + user_pars.volt_mm * circ),
                        np.imag(-1 + user_pars.volt_mm * circ))
                ax.grid(True)
                axes = plt.gca()
                axes.set_xlim([-4, 4])
                axes.set_ylim([-4, 4])
                plt.savefig(path_L + 'open_loop' + '.png')

            col = df.columns.levels[0]
            f = df.index.values
            for name in col:

                fig, (ax1, ax2) = plt.subplots(2)
                for df in df_tot:
                    ax1.semilogx(f, df[name]['gain'].values)
                ax1.set_title(name)
                ax1.set_ylabel('Magnitude [dB]')
                ax1.grid(True)
                for df in df_tot:
                    ax2.semilogx(f, df[name]['phase'].values)
                ax2.set_xlabel('Frequency [Hz]')
                ax2.set_ylabel('Phase [deg]')
                ax2.grid(True)

                plt.savefig(path + name + '.png')
                plt.show()
