#!/usr/bin/env python
import logging
#from scipy.stats.mstats import chisquare
from scipy.stats import chisqprob
from scipy.stats import anderson_ksamp
from scipy.stats.mstats import ks_twosamp

from multiprocessing import Pool, TimeoutError

# need a dictionary of comparison objects.
# we'll want different comparisons for different histograms

def chisquare(s1, s2):
    '''
    Compare samples s1 ands2 with a Chi^2 test.
    Output:
        chisq : float
            A Chi^2 sum over all bins.
        p : float
            The p-value according to the Chi^2 distribution, nDOF = n(bins).

    TODO: Go through the scipy chisquare and find out exactly why
          it fails for two samples.  I suspect I know why, but it 
          will be important to verify.
    '''
    # calculate the \chi^2 test statistic
    terms = [(u - v)**2/float((u + v)) \
             for u,v in zip(s1, s2)\
             if u > 0 or v > 0]
    chisq = sum(terms)
    return chisq, chisqprob(chisq, df = len(terms))


def both_empty(h1, h2):
    '''
    Returns True if neither histogram has content.
    '''
    empty = lambda h : not any([True for v in h['bin_values'] if v > 0])
    return (empty(h1) and empty(h2))

def comparable(h1, h2):
    '''
    Returns True if two histograms are comparable,
    meaning they have the same name and binning and more
    than 1 non-zero bin.
    '''
    return ((h1['xmin'] == h2['xmin']) and\
            (h1['xmax'] == h2['xmax']) and\
            (h1['name'] == h2['name']) and\
            (len(h1['bin_values']) == len(h2['bin_values'])))

def identical(h1, h2):
    # take a swing at the softballs
    if h1['bin_values'] == h2['bin_values']:
        return True

def statistical_preconditions(h1, h2):
    n_common_nonzero_bins = len([True for u,v in zip(h1['bin_values'], h2['bin_values'])
                                 if u > 0 and v > 0])
    return n_common_nonzero_bins > 10
"""

def compare(h1, h2):
    '''
    Compares two histograms applying statistical tests.  Both histograms
    need to be comparable, meaning they have to have the same number of
    bins, the same x-axis ranges, and the same name.  In production they
    will always have the same name, since it's also the dictionary key.

    If either histogram one has only 0 or 1 non-empty bins
    then they're also not comparable.  This causes scipy statistical
    tests to lockup and this is not the tool you want to use in those cases.

    If the histograms are not comparable an empty dictionary is returned.

    If both histograms are comparable a dictionary is returned with the
    results of the statistical comparisons.

    {
      'both_empty': {'pvalue': pvalue},
      'comparable': {'pvalue': pvalue},
      'identity': {'pvalue': pvalue},
      'single_bin': {'pvalue': pvalue},
      'insufficient_statistics': {'pvalue': pvalue},
      'chisq': {'T': T, 'pvalue': pvalue},
      'KS': {'T': T, 'pvalue': pvalue}
    }
    '''
    result = {}
    if both_empty(h1, h2):
        pvalue = 0. if not comparable(h1, h2) else 1.
        return {'both_empty': {'pvalue': pvalue} }

    if not comparable(h1, h2):
        return {'comparable': {'pvalue': 0.} }

    if identical(h1, h2):
        return {'identity': {'pvalue': 1.} }

    # we'll likely want to make a stricter requirement of having
    # at least N non-zero bins in common. N = 1 might be a bit too low.
    n_nonzero_bins = lambda h : len([v for v in h['bin_values'] if v != 0])
    if n_nonzero_bins(h1) == 1 and \
       n_nonzero_bins(h2) == 1:
        # at this point if they're single bin then it's a fail because
        # we already know they're not identical
        return {'single_bin': {'pvalue': 0.} }

    if not statistical_preconditions(h1, h2):
        return {'insufficient_statistics': {'pvalue': 0.} }

    # Consider making these multi-threaded.
    # Not necessarily for performance reasons, but under certain
    # currently unknown conditions the KS test can lock up and
    # I'd like to be able to gracefully recover from that.

    pool = Pool(processes=3)
    
    try:
        #chi2_result = chisquare(h1['bin_values'], h2['bin_values'])
        res = pool.apply_async(chisquare, (h1['bin_values'], h2['bin_values']))
        chi2_result = res.get(timeout=1)
        result['chisq'] = {'T': chi2_result[0], 'pvalue': chi2_result[1]}
    except Exception as e:
        result['chisq'] = {'pvalue': 0, "Exception": str(e)}

    try:
        #ks_result = ks_twosamp(h1['bin_values'], h2['bin_values'])
        res = pool.apply_async(ks_twosamp, (h1['bin_values'], h2['bin_values']))
        ks_result = res.get(timeout=10)
        result['KS'] = {'T': ks_result[0], 'pvalue': ks_result[1]}
    except Exception as e:
        result['KS'] = {'pvalue': 0, "Exception": str(e)}

    try:
        #ad_result = anderson_ksamp([h1['bin_values'], h2['bin_values']], )
        res = pool.apply_async(anderson_ksamp, (h1['bin_values'], h2['bin_values']))
        ad_result = res.get(timeout=10)
        result['AD'] = {'T': ad_result[0], 'pvalue': ad_result[2]}
    except Exception as e:
        result['AD'] = {'pvalue': 0, "Exception": str(e)}

    pool.close()
    pool.join()
        
    return result


"""
from .metrics import norm_chisq 
from .metrics import shape_chisq
from .metrics import bdm 
from .metrics import kolmogorov_smirnof 
from .metrics import llh_ratio 
from .metrics import llh_value 
from .metrics import cramer_von_mises
from .metrics import anderson_darling

def _comparable(h1, h2):
    '''
    Returns True if two histograms are comparable,
    meaning they have the same name and binning.    
    '''
    return ((h1.xmin == h2.xmin) and\
       (h1.xmax == h2.xmax) and\
       (len(h1.bin_values) == len(h2.bin_values)))

def compare(hist1, hist2,
            test_norm_chisq = False, 
            test_shape_chisq = True, 
            test_bdm = False,
            test_ks = False,
            test_llh_ratio = False,
            test_llh_value = False,
            test_cramer_von_mises = False,
            test_anderson_darling = True):
    r'''For all enabled test_{name}, compare hist1 and hist2.
    Output:
        result : dict 
            test name : value of test statistic 
            Will be empty if no tests enabled, or histograms inconsistent.    
            llh_value often returns -inf for histograms with moderate bin contents.
            Taking it out of the rotation for now. 
    '''

    result = {}
    if not _comparable(hist1, hist2) :
        print("ERROR : histograms %s and %s are inconsistent." % (hist1.name, hist2.name))
        return result
    
    if test_norm_chisq:
        result["norm_chisq"] = norm_chisq.test_norm_chisq(hist1, hist2)

    if test_shape_chisq:
        result["shape_chisq"] = shape_chisq.test_shape_chisq(hist1, hist2)

    if test_llh_ratio:
        result["llh_ratio"] = llh_ratio.test_llh_ratio(hist1, hist2)

    if test_llh_value:
        result["llh_value"] = llh_value.test_llh_value(hist1, hist2)

    if test_cramer_von_mises:
        result["cramer_von_mises"] = cramer_von_mises.test_cramer_von_mises(hist1, hist2)

    if test_anderson_darling:
        result["anderson_darling"] = anderson_darling.test_anderson_darling(hist1, hist2)

    if test_bdm:
        result["bdm"] = bdm.test_bhattacharyya_distance_measure(hist1, hist2)

    if test_ks:
        result["ks"] = kolmogorov_smirnof.test_kolmogorov_smirnof(hist1, hist2)

    return result

