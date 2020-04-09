"""Theil Inequality metrics

"""
__author__ = "Sergio J. Rey <srey@asu.edu> "

# from libpysal.common import *
import numpy as np
import pandas as pd
__all__ = ['Theil', 'TheilD', 'TheilDSim', 'TheilPop', 'TheilDPop']

SMALL = np.finfo('float').tiny


class Theil:
    """
    Classic Theil measure of inequality

    .. math::

        T = \sum_{i=1}^n \left( \\frac{y_i}{\sum_{i=1}^n y_i} \ln \left[ N \\frac{y_i}{\sum_{i=1}^n y_i}\\right] \\right)

    Parameters
    ----------
    y   : array (n,t) or (n,)
          with n taken as the observations across which inequality is
          calculated.  If y is (n,) then a scalar inequality value is
          determined. If y is (n,t) then an array of inequality values are
          determined, one value for each column in y.

    Attributes
    ----------

    T   : array (t,) or (1,)
          Theil's T for each column of y

    Notes
    -----
    This computation involves natural logs. To prevent ln[0] from occurring, a
    small value is added to each element of y before beginning the computation.

    Examples
    --------
    >>> import libpysal
    >>> import numpy as np
    >>> from inequality.theil import Theil
    >>> f=libpysal.io.open(libpysal.examples.get_path("mexico.csv"))
    >>> vnames=["pcgdp%d"%dec for dec in range(1940,2010,10)]
    >>> y=np.array([f.by_col[v] for v in vnames]).T
    >>> theil_y=Theil(y)
    >>> theil_y.T
    array([0.20894344, 0.15222451, 0.10472941, 0.10194725, 0.09560113,
           0.10511256, 0.10660832])
    """

    def __init__(self, y):

        n = len(y)
        y = y + SMALL * (y == 0)  # can't have 0 values
        yt = y.sum(axis=0)
        s = y / (yt * 1.0)
        lns = np.log(n * s)
        slns = s * lns
        t = sum(slns)
        self.T = t


class TheilD:
    """Decomposition of Theil's T based on partitioning of
    observations into exhaustive and mutually exclusive groups

    Parameters
    ----------
    y         : array  (n,t) or (n, )
                with n taken as the observations across which inequality is
                calculated If y is (n,) then a scalar inequality value is
                determined. If y is (n,t) then an array of inequality values are
                determined, one value for each column in y.
    partition : array (n, )
                elements indicating which partition each observation belongs
                to. These are assumed to be exhaustive.

    Attributes
    ----------
    T  : array (n,t) or (n,)
         global inequality T
    bg : array (n,t) or (n,)
         between group inequality
    wg : array (n,t) or (n,)
         within group inequality

    Examples
    --------
    >>> import libpysal
    >>> from inequality.theil import TheilD
    >>> import numpy as np
    >>> f=libpysal.io.open(libpysal.examples.get_path("mexico.csv"))
    >>> vnames=["pcgdp%d"%dec for dec in range(1940,2010,10)]
    >>> y = np.array([f.by_col[v] for v in vnames]).T
    >>> regimes=np.array(f.by_col('hanson98'))
    >>> theil_d=TheilD(y,regimes)
    >>> theil_d.bg
    array([0.0345889 , 0.02816853, 0.05260921, 0.05931219, 0.03205257,
           0.02963731, 0.03635872])
    >>> theil_d.wg
    array([0.17435454, 0.12405598, 0.0521202 , 0.04263506, 0.06354856,
           0.07547525, 0.0702496 ])
   """
    def __init__(self, y, partition):
        groups = np.unique(partition)
        T = Theil(y).T
        ytot = y.sum(axis=0)

        #group totals
        gtot = np.array([y[partition == gid].sum(axis=0) for gid in groups])
        mm = np.dot

        if ytot.size == 1:  # y is 1-d
            sg = gtot / (ytot * 1.)
            sg.shape = (sg.size, 1)
        else:
            sg = mm(gtot, np.diag(1. / ytot))
        ng = np.array([sum(partition == gid) for gid in groups])
        ng.shape = (ng.size,)  # ensure ng is 1-d
        n = y.shape[0]
        # between group inequality
        sg = sg + (sg==0) # handle case when a partition has 0 for sum
        bg = np.multiply(sg, np.log(mm(np.diag(n * 1. / ng), sg))).sum(axis=0)
        self.T = T
        self.bg = bg
        self.wg = T - bg


class TheilDSim:
    """Random permutation based inference on Theil's inequality decomposition.

    Provides for computationally based inference regarding the inequality
    decomposition using random spatial permutations. See :cite:`rey_interregional_2010`. 

    Parameters
    ----------
    y            : array  (n,t) or (n, )
                   with n taken as the observations across which inequality is
                   calculated If y is (n,) then a scalar inequality value is
                   determined. If y is (n,t) then an array of inequality values are
                   determined, one value for each column in y.
    partition    : array (n, )
                   elements indicating which partition each observation belongs
                   to. These are assumed to be exhaustive.
    permutations : int
                   Number of random spatial permutations for computationally
                   based inference on the decomposition.

    Attributes
    ----------

    observed   : array (n,t) or (n,)
                 TheilD instance for the observed data.

    bg         : array (permutations+1,t)
                 between group inequality

    bg_pvalue  : array (t,1)
                 p-value for the between group measure.  Measures the
                 percentage of the realized values that were greater than
                 or equal to the observed bg value. Includes the observed
                 value.

    wg         : array (size=permutations+1)
                 within group inequality Depending on the shape of y, 1 or 2-dimensional

    Examples
    --------
    >>> import libpysal
    >>> from inequality.theil import TheilDSim
    >>> import numpy as np
    >>> f=libpysal.io.open(libpysal.examples.get_path("mexico.csv"))
    >>> vnames=["pcgdp%d"%dec for dec in range(1940,2010,10)]
    >>> y=np.array([f.by_col[v] for v in vnames]).T
    >>> regimes=np.array(f.by_col('hanson98'))
    >>> np.random.seed(10)
    >>> theil_ds=TheilDSim(y,regimes,999)
    >>> theil_ds.bg_pvalue
    array([0.4  , 0.344, 0.001, 0.001, 0.034, 0.072, 0.032])

    """
    def __init__(self, y, partition, permutations=99):

        observed = TheilD(y, partition)
        bg_ct = observed.bg == observed.bg  # already have one extreme value
        bg_ct = bg_ct * 1.0
        results = [observed]
        for perm in range(permutations):
            yp = np.random.permutation(y)
            t = TheilD(yp, partition)
            bg_ct += (1.0 * t.bg >= observed.bg)
            results.append(t)
        self.results = results
        self.T = observed.T
        self.bg_pvalue = bg_ct / (permutations * 1.0 + 1)
        self.bg = np.array([r.bg for r in results])
        self.wg = np.array([r.wg for r in results])


class TheilPop:
    """
    Between-set heil's inequality measure.

    Parameters
    ----------
    pci : array
          (n,t) or (n,), per capita income.
          With n taken as the observations across which
          inequality is calculated. If pci is (n,) then a scalar inequality value is
          determined. If pci is (n,t) then an array of inequality values are
          determined, one value for each column in y.
    pop : array
          (n,t) or (n,), population.
          With n taken as the observations across which
          inequality is calculated. If Tpci is (n,) then a scalar inequality value is
          determined. If pci is (n,t) then an array of inequality values are
          determined, one value for each column in y.

    Attributes
    ----------

    T   : array (t,) or (1,)
          Theil's T for each column of y

    """

    def __init__(self, pci, pop):
        pci = np.asarray(pci)
        pop = np.asarray(pop)
        total = pci * pop
        y = total / total.sum(axis=0)  # state income share
        x = pop / pop.sum(axis=0)  # state population share
        self.T = (y * np.log(y / x)).sum(axis=0)


class TheilDPop:
    """
    Between-set Theil's inequality measure and its further regional decomposition.

    Parameters
    ----------
    pci : array
          (n,t) or (n,), per capita income.
          With n taken as the observations across which
          inequality is calculated. If pci is (n,) then a scalar inequality value is
          determined. If pci is (n,t) then an array of inequality values are
          determined, one value for each column in y.
    pop : array
          (n,t) or (n,), population.
          With n taken as the observations across which
          inequality is calculated. If Tpci is (n,) then a scalar inequality value is
          determined. If pci is (n,t) then an array of inequality values are
          determined, one value for each column in y.
    regime : array
             (n, ), elements indicating which partition each observation belongs
                to. These are assumed to be exhaustive.

    Attributes
    ----------
    T  : array (n,t) or (n,)
         global inequality T
    bg : array (n,t) or (n,)
         between regime inequality
    wg : array (n,t) or (n,)
         within regime inequality

    """

    def __init__(self, pci, pop, regime):
        pci = np.asarray(pci)
        pop = np.asarray(pop)
        regime = np.asarray(regime)
        total = pci * pop
        y_t = total / total.sum(axis=0)  # state income share
        x_t = pop / pop.sum(axis=0)  # state population share

        def pd_theil(data):
            eta = data.incshare.values / data.incshare.sum()
            xi = data.popshare.values / data.popshare.sum()
            return sum(eta * np.log(eta / xi))

        t = pci.shape[1]
        theil_w_all = np.zeros(t)
        theil_b_all = np.zeros(t)
        for i in range(t):
            y = y_t[:, i]
            x = x_t[:, i]
            df = pd.DataFrame(np.array([regime, y, x]).T, columns=["regime", "incshare", "popshare"])
            df_shareG = df.groupby("regime").sum()
            X_g = df_shareG.popshare.values
            Y_g = df_shareG.incshare.values
            theil_b_all[i] = sum(Y_g * np.log(Y_g / X_g))

            def pd_theil(data):
                eta = data.incshare.values / data.incshare.sum()
                xi = data.popshare.values / data.popshare.sum()
                return sum(eta * np.log(eta / xi))

            df_within = df.groupby("regime").apply(pd_theil)
            I_g = df_within.values
            theil_w_all[i] = sum(df_shareG.incshare.values * I_g)
        self.T = theil_w_all + theil_b_all
        self.bg = theil_b_all
        self.wg = theil_w_all


