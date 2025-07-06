import math
import numpy

import cv2

from hydrus.core.files.images import HydrusImageHandling
from hydrus.core.files.images import HydrusImageNormalisation

from hydrus.client import ClientGlobals as CG
from hydrus.client.caches import ClientCachesBase

# TODO: rework the cv2 stuff here to PIL or custom methods or whatever!


# to help smooth out jpeg artifacts, we can do a gaussian blur at 100% zoom
# jpeg artifacts are on the scale of 8x8 blocks. 0.8 sigma, which is about 3x that (2.4px) radius, is a nice sweet spot I have confirmed visually
JPEG_ARTIFACT_BLUR_FOR_PROCESSING = True
JPEG_ARTIFACT_GAUSSIAN_SIGMA_AT_100_ZOOM = 0.8

# saves lots of CPU time for no great change
NORMALISE_SCALE_FOR_LAB_HISTOGRAM_PROCESSING = True
LAB_HISTOGRAM_NORMALISED_RESOLUTION = ( 1024, 1024 )

LAB_HISTOGRAM_NUM_BINS = 256
LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION = 16
LAB_HISTOGRAM_NUM_TILES_DIMENSIONS = ( LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION, LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION )
LAB_HISTOGRAM_NUM_TILES = LAB_HISTOGRAM_NUM_TILES_DIMENSIONS[0] * LAB_HISTOGRAM_NUM_TILES_DIMENSIONS[1]

EDGE_MAP_PERCEPTUAL_RESOLUTION = ( 2048, 2048 )
EDGE_MAP_NORMALISED_RESOLUTION = ( 256, 256 )
EDGE_MAP_NUM_TILES_PER_DIMENSION = 8
EDGE_MAP_NUM_TILES_DIMENSIONS = ( EDGE_MAP_NUM_TILES_PER_DIMENSION, EDGE_MAP_NUM_TILES_PER_DIMENSION )
EDGE_MAP_NUM_TILES = EDGE_MAP_NUM_TILES_DIMENSIONS[0] * EDGE_MAP_NUM_TILES_DIMENSIONS[1]

class EdgeMap( ClientCachesBase.CacheableObject ):
    
    def __init__( self, edge_map_r: numpy.ndarray, edge_map_g: numpy.ndarray, edge_map_b: numpy.ndarray ):
        
        self.edge_map_r = edge_map_r
        self.edge_map_g = edge_map_g
        self.edge_map_b = edge_map_b
        
    
    def GetEstimatedMemoryFootprint( self ) -> int:
        
        # this is not a small object mate. maybe we'll scale down a little, let's see the accuracy of this thing
        
        # float32
        return 4 * EDGE_MAP_NORMALISED_RESOLUTION[0] * EDGE_MAP_NORMALISED_RESOLUTION[1] * 3
        
    

class LabHistograms( ClientCachesBase.CacheableObject ):
    
    def __init__( self, l_hist: numpy.ndarray, a_hist: numpy.ndarray, b_hist: numpy.ndarray ):
        
        self.l_hist = l_hist
        self.a_hist = a_hist
        self.b_hist = b_hist
        
    
    def GetEstimatedMemoryFootprint( self ) -> int:
        
        # float32
        return 4 * LAB_HISTOGRAM_NUM_BINS * 3
        
    
    def IsInteresting( self ):
        # a flat colour, or a png with very very flat straight colours, is not going to have much in the L histogram
        return numpy.count_nonzero( self.l_hist ) + numpy.count_nonzero( self.a_hist ) + numpy.count_nonzero( self.b_hist ) > 24
        
    

class VisualData( ClientCachesBase.CacheableObject ):
    
    def __init__( self, resolution, had_alpha: bool, lab_histograms: LabHistograms ):
        
        self.resolution = resolution
        self.had_alpha = had_alpha
        self.lab_histograms = lab_histograms
        
    
    def GetEstimatedMemoryFootprint( self ) -> int:
        
        # float32
        return self.lab_histograms.GetEstimatedMemoryFootprint()
        
    
    def IsInteresting( self ):
        
        return self.lab_histograms.IsInteresting()
        
    
    def ResolutionIsTooLow( self ):
        
        return self.resolution[0] < 32 or self.resolution[1] < 32
        
    

class VisualDataTiled( ClientCachesBase.CacheableObject ):
    
    def __init__( self, resolution, had_alpha: bool, histograms: list[ LabHistograms ], edge_map: EdgeMap ):
        
        self.resolution = resolution
        self.had_alpha = had_alpha
        self.histograms = histograms
        self.edge_map = edge_map
        
    
    def GetEstimatedMemoryFootprint( self ) -> int:
        
        return sum( ( histogram.GetEstimatedMemoryFootprint() for histogram in self.histograms ) ) + self.edge_map.GetEstimatedMemoryFootprint()
        
    
    def ResolutionIsTooLow( self ):
        
        return self.resolution[0] < 32 or self.resolution[1] < 32
        
    

class VisualDataStorage( ClientCachesBase.DataCache ):
    
    my_instance = None
    
    def __init__( self ):
        
        super().__init__( CG.client_controller, 'visual_data', 5 * 1024 * 1024 )
        
    
    @staticmethod
    def instance() -> 'VisualDataStorage':
        
        if VisualDataStorage.my_instance is None:
            
            VisualDataStorage.my_instance = VisualDataStorage()
            
        
        return VisualDataStorage.my_instance
        
    

class VisualDataTiledStorage( ClientCachesBase.DataCache ):
    
    my_instance = None
    
    def __init__( self ):
        
        super().__init__( CG.client_controller, 'visual_data_tiled', 32 * 1024 * 1024 )
        
    
    @staticmethod
    def instance() -> 'VisualDataTiledStorage':
        
        if VisualDataTiledStorage.my_instance is None:
            
            VisualDataTiledStorage.my_instance = VisualDataTiledStorage()
            
        
        return VisualDataTiledStorage.my_instance
        
    

def skewness_numpy( values ):
    
    values_numpy = numpy.asarray( values )
    
    mean = numpy.mean( values_numpy )
    
    std = numpy.std( values_numpy )
    
    if std == 0:
        
        return 0.0  # perfectly uniform array
        
    
    third_moment = numpy.mean( ( values_numpy - mean ) **  3 )
    
    skewness = third_moment / ( std ** 3 )
    
    return float( skewness )
    

# I tried detecting bimodality coefficient with this, but it didn't work for the sort of bump we were looking for
def kurtosis_numpy( values ):
    
    values = numpy.asarray( values )
    
    mean = numpy.mean( values )
    
    variance = numpy.var( values )
    
    if variance == 0:
        
        return 0
        
    
    m4 = numpy.mean( ( values - mean ) ** 4)
    
    kurt = m4 / ( variance ** 2 )
    
    return kurt
    

def log_gaussian(x, mean, var):
    
    return -0.5 * numpy.log( 2 * numpy.pi * var ) - 0.5 * ( ( x - mean ) ** 2 ) / var
    

# gaussian mixture modelling--how well does this distribution fit with n modes?
# it does its job well, but it is a liklihood based model that basically goes for maximising surface area
# so when it says 'yeah, this most looks bimodal, the means are here and here', it'll generally preference the bumps in the main blob and skip the tiny blob we are really looking for
def fit_gmm_1d( data, n_components=2, n_iter=100, tol=1e-6 ):
    
    data = numpy.asarray( data ).flatten()
    
    n = len( data )
    
    # Init: random means, uniform weights, global variance
    rng = numpy.random.default_rng()
    means = rng.choice( data, size=n_components, replace=False)
    variances = numpy.full( n_components, numpy.var(  data ) )
    weights = numpy.full( n_components, 1 / n_components )
    
    log_likelihoods = []
    
    for _ in range( n_iter ):
        
        # E-step: compute responsibilities
        log_probs = numpy.array( [
            numpy.log( weights[k] ) + log_gaussian( data, means[k], variances[k] )
            for k in range( n_components )
        ] )
        
        log_sum = numpy.logaddexp.reduce( log_probs, axis=0 )
        responsibilities = numpy.exp( log_probs - log_sum )
        
        # M-step: update parameters
        Nk = responsibilities.sum( axis=1 )
        weights = Nk / n
        means = numpy.sum( responsibilities * data, axis=1 ) / Nk
        variances = numpy.sum( responsibilities * ( data - means[:, numpy.newaxis] )**2, axis=1 ) / Nk

        # Log-likelihood
        ll = numpy.sum( log_sum )
        log_likelihoods.append( ll )
        if len( log_likelihoods ) > 1 and abs( log_likelihoods[-1] - log_likelihoods[-2] ) < tol:
            
            break
            
        
    
    # BIC = -2 * LL + p * log(n)
    # bayesian information criterion
    p = n_components * 3 - 1  # means, variances, weights (sum to 1)
    bic = -2 * log_likelihoods[-1] + p * numpy.log(n)
    
    return {
        'weights': weights,
        'means': means,
        'variances': variances,
        'log_likelihood': log_likelihoods[-1],
        'bic': bic
    }
    

def gaussian_pdf( x, mean, variance ):
    
    coef = 1 / math.sqrt( 2 * math.pi * variance )
    
    return coef * numpy.exp( -0.5 * ( ( x - mean ) ** 2) / variance )
    

def gaussian_cdf(x, mean, std ):
    
    z = ( x - mean ) / ( std * math.sqrt(2) )
    
    return 0.5 * ( 1 + math.erf( z ) )
    

def aberrant_bump_in_scores_giganto_brain( values ):
    """
    detect a second bump in our score list
    """
    
    '''
    Assuming we are generally talking about 1 curve here in a good situation, let's fit a gaussian to the main guy and then see if the latter section of our histogram still has any grass standing tall
    
    Ok I worked on this and added p-values, but it still wasn't nicely differentiating good from bad! I think the scoring still is the baseline thing we need to hunt here, oh well
    '''
    
    n = len( values )
    
    gmm_result = fit_gmm_1d( values, n_components = 1 )
    mean = gmm_result[ 'means' ][0]
    variance = gmm_result[ 'variances' ][0]
    
    std = variance ** 0.5
    
    # Scott's Rule
    bin_width = 3.5 * std / ( n ** ( 1 / 3 ) )
    num_bins = max( 1, min( round( WD_MAX_REGIONAL_SCORE / bin_width ), 2000 ) )
    
    ( values_histogram, bin_edges ) = numpy.histogram( values, bins = num_bins, range = ( 0, WD_MAX_REGIONAL_SCORE ), density = True )
    
    bin_centers = ( bin_edges[ : -1 ] + bin_edges[ 1 : ] ) / 2
    
    pdf = gaussian_pdf( bin_centers, mean, variance )
    
    model_histogram = pdf * numpy.sum( values_histogram ) * bin_width
    
    residual_histogram = values_histogram - model_histogram
    
    # ok previously we set the num_bins to 50 and just tested against a flat >10? value
    # we are now going bananas and doing P-values
    
    results = []
    
    for ( x, residual ) in zip( bin_centers, residual_histogram ):
        
        if x < mean:
            
            continue  # optional: ignore left tail
            
        
        # what is the probability that tha residual is >0 here?
        p = 1 - gaussian_cdf( x , mean, std )
        
        # if the liklihood is greater than x%, we won't consider that suspicious
        if p > 0.05:
            
            continue
            
        
        # now let's make a normalised 'residual mass' amount that normalises for our dynamic bin width
        
        residual_mass = residual * bin_width
        
        log_score = residual_mass * - math.log( p + 1e-10 )
        
        if log_score > 0:
            
            print( (p, log_score ) )
            
        
        if log_score > 0.07:
            
            print( 'anomaly_detected' )
            
        
    
    return True
    

def aberrant_bump_in_scores( values ):
    """
    detect a second bump in our score list
    """
    
    '''
    ok here is what we want to detect:
    
    array([176.47058824,  58.82352941, 137.25490196, 215.68627451,
       333.33333333, 294.11764706, 588.23529412, 549.01960784,
       588.23529412, 607.84313725, 352.94117647, 333.33333333,
       156.8627451 , 156.8627451 ,  58.82352941, 156.8627451 ,
        58.82352941,  78.43137255,  58.82352941,  19.60784314,
         0.        ,   0.        ,   0.        ,   0.        ,
         0.        ,   0.        ,   0.        ,   0.        ,
         0.        ,   0.        ,   0.        ,   0.        ,
         0.        ,   0.        ,   0.        ,   0.        ,
         0.        ,   0.        ,   0.        ,   0.        ,
         0.        ,  19.60784314,   0.        ,   0.        ,
         0.        ,   0.        ,   0.        ,   0.        ,
         0.        ,   0.        ])
    
    basically, a nice big bump and then a small bump--that's our weird change
    skew does not catch this reliably since the large bump is so large
    
    I tried some algorithms to detect bimodality and such, but really I think the simple solution is just to say 'if there are a bunch of zeroes and then data, that's an odd little bump mate'
    EDIT: After thinking about this more, maybe we need to massage the data coming in more. since we now know that tiles are not equal when it comes to jpeg artifact differences
        perhaps we should be thinking about getting higher quality scores before trying harder to hunt for odd bumps--some of our bumps are currently good!
    EDIT 2025-06: Edge detection finally worked out and pretty much made this method moot.
    '''
    
    values_histogram = numpy.histogram( values, bins = 50, range = ( 0, WD_MAX_REGIONAL_SCORE ), density = True )[0]
    
    NUM_ZEROES_THRESHOLD = 6
    
    have_hit_main_bump = False
    current_num_zeroes = 0
    
    for i in range( len( values_histogram ) ):
        
        value = values_histogram[ i ]
        
        if not have_hit_main_bump:
            
            if value > 0:
                
                have_hit_main_bump = True
                
            
        else:
            
            if value == 0:
                
                current_num_zeroes += 1
                
            else:
                
                # ok, we hit the main bump, did some zeroes, and now hit new data!!
                if current_num_zeroes >= NUM_ZEROES_THRESHOLD:
                    
                    return True
                    
                
                current_num_zeroes = 0
                
            
        
    
    return False
    

# spreading these out in case we want to insert more in future
VISUAL_DUPLICATES_RESULT_NOT = 0
VISUAL_DUPLICATES_RESULT_PROBABLY = 40
VISUAL_DUPLICATES_RESULT_VERY_PROBABLY = 60
VISUAL_DUPLICATES_RESULT_ALMOST_CERTAINLY = 85
VISUAL_DUPLICATES_RESULT_NEAR_PERFECT = 100

result_str_lookup = {
    VISUAL_DUPLICATES_RESULT_NOT : 'not duplicates',
    VISUAL_DUPLICATES_RESULT_PROBABLY : 'probably visual duplicates',
    VISUAL_DUPLICATES_RESULT_VERY_PROBABLY : 'very probably visual duplicates',
    VISUAL_DUPLICATES_RESULT_ALMOST_CERTAINLY : 'almost certainly visual duplicates',
    VISUAL_DUPLICATES_RESULT_NEAR_PERFECT : 'near-perfect visual duplicates',
}

def BlurRGBNumPy( numpy_image: numpy.ndarray, sigmaX ):
    
    return numpy.stack(
        [ cv2.GaussianBlur( numpy_image[ ..., i ], (0, 0), sigmaX = sigmaX ) for i in range( 3 ) ],
        axis = -1
    )
    

def FilesAreVisuallySimilarRegional( lab_tile_hist_1: VisualDataTiled, lab_tile_hist_2: VisualDataTiled ):
    
    if lab_tile_hist_1.had_alpha or lab_tile_hist_2.had_alpha:
        
        if lab_tile_hist_1.had_alpha and lab_tile_hist_2.had_alpha:
            
            message = 'cannot determine visual duplicates\n(they have transparency)'
            
        else:
            
            message = 'not visual duplicates\n(one has transparency)'
            
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, message )
        
    
    if FilesHaveDifferentRatio( lab_tile_hist_1.resolution, lab_tile_hist_2.resolution ):
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, 'not visual duplicates\n(different ratio)' )
        
    
    if lab_tile_hist_1.ResolutionIsTooLow() or lab_tile_hist_2.ResolutionIsTooLow():
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, 'cannot determine visual duplicates\n(too low resolution)' )
        
    
    #
    
    ( they_are_similar_edge, result_edge, statement_edge ) = FilesAreVisuallySimilarRegionalEdgeMap( lab_tile_hist_1.edge_map, lab_tile_hist_2.edge_map )
    
    if they_are_similar_edge:
        
        ( they_are_similar_lab, result_lab, statement_lab ) = FilesAreVisuallySimilarRegionalLabHistograms( lab_tile_hist_1.histograms, lab_tile_hist_2.histograms )
        
        if result_edge < result_lab:
            
            return ( they_are_similar_edge, result_edge, statement_edge )
            
        else:
            
            return ( they_are_similar_lab, result_lab, statement_lab )
            
        
    else:
        
        return ( they_are_similar_edge, result_edge, statement_edge )
        
    

# ok here I tried several things. tile comparison, some stats, some absolute skew calculations
# ultimately I'm settling on KISS. tiling just softens out our rich data, and absolute skew gubbins was producing false positives
# we might have success doing tiles of only like 8x8 and summing/averaging, so we are locating pockets of edge difference rather than points
# we might have success capturing the average of the top quintile or similar to again detect real bumps from a general fuzz
# but there did seem to be a fair amount of unpredictable general noise, so we can't be too clever
# as I have said for the colour histograms, if we want to make further big changes here, I think we should do it properly with a test suite that we can tune programatically

# this overall, however, seems to work well. sometimes there is a heavy re-encode pair at 18, and sometimes there is a subtle alternate pair at 18, but generally speaking these numbers are safely reliable:

EDGE_MAX_POINT_DIFFERENCE = 15

EDGE_VERY_GOOD_MAX_POINT_DIFFERENCE = 11

EDGE_PERFECT_MAX_POINT_DIFFERENCE = 3

EDGE_RUBBISH_MIN_POINT_DIFFERENCE = 45

def FilesAreVisuallySimilarRegionalEdgeMap( edge_map_1: EdgeMap, edge_map_2: EdgeMap ):
    
    # each edge map is -255 to +255, hovering around 0
    
    difference_edge_map_r = edge_map_1.edge_map_r - edge_map_2.edge_map_r
    difference_edge_map_g = edge_map_1.edge_map_g - edge_map_2.edge_map_g
    difference_edge_map_b = edge_map_1.edge_map_b - edge_map_2.edge_map_b
    
    largest_point_difference_r = numpy.max( numpy.abs( difference_edge_map_r ) )
    largest_point_difference_g = numpy.max( numpy.abs( difference_edge_map_g ) )
    largest_point_difference_b = numpy.max( numpy.abs( difference_edge_map_b ) )
    
    largest_point_difference = max( largest_point_difference_r, largest_point_difference_g, largest_point_difference_b )
    
    if largest_point_difference < EDGE_PERFECT_MAX_POINT_DIFFERENCE:
        
        return ( True, VISUAL_DUPLICATES_RESULT_NEAR_PERFECT, 'near-perfect visual duplicates' )
        
    elif largest_point_difference < EDGE_VERY_GOOD_MAX_POINT_DIFFERENCE:
        
        return ( True, VISUAL_DUPLICATES_RESULT_ALMOST_CERTAINLY, 'almost certainly visual duplicates' )
        
    elif largest_point_difference < EDGE_MAX_POINT_DIFFERENCE:
        
        return ( True, VISUAL_DUPLICATES_RESULT_VERY_PROBABLY, 'very probably visual duplicates' )
        
    elif largest_point_difference > EDGE_RUBBISH_MIN_POINT_DIFFERENCE:
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, 'not visual duplicates\n(alternate)')
        
    else:
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, 'probably not visual duplicates\n(alternate/severe re-encode?)')
        
    

# I tried a bunch of stuff, and it seems like we want to look at multiple variables to catch our different situations
# detecting jpeg artifacts is difficult! they are pretty noisy from certain perspectives, and differentiating that noise from other edits is not simple. however they are _uniform_
# I tried with some correlation coefficient and chi squared stuff, but it wasn't smoothing out the noise nicely. I could fit the numbers to detect original from artist correction, but 70% vs artist correction was false positive

# New attempt with Earth Mover Distance, Wasserstein Distance. this should smooth out little fuzzy jpeg artifacts but notice bigger bumps better
# hesitant, but I think it is a huge success--check out that variance on the true dupes!
# when I compare the correction to 70%, I now get a skew worth something (12.681), so this is correctly measuring the uniform weight of jpeg artifacts and letting us exclude them as noise

# note in this case a 0.0 score is a perfect match, 1.0 is totally different

# vs our original normal image:

# scaled down: max 0.008 / mean 0.002299 / variance 0.000001 / skew 0.788
# 60%: max 0.004 / mean 0.001666 / variance 0.000001 / skew 0.316
# 70%: max 0.003 / mean 0.001561 / variance 0.000000 / skew 0.211
# 80%: max 0.002 / mean 0.000845 / variance 0.000000 / skew 0.503

# correction: max 0.032 / mean 0.000155 / variance 0.000004 / skew 14.726
# watermark: max 0.107 / mean 0.001669 / variance 0.000103 / skew 7.110

# dechroma: max 0.022 / mean 0.011325 / variance 0.000027 / skew -0.313
# hue phase: max 0.063 / mean 0.026598 / variance 0.000264 / skew 0.430
# darkness: max 0.059 / mean 0.055800 / variance 0.000002 / skew -2.117
# saturation: max 0.028 / mean 0.009552 / variance 0.000038 / skew 1.107
# colour temp: max 0.087 / mean 0.035031 / variance 0.000473 / skew 0.181

# therefore, I am choosing these decent defaults to start us off:
#WD_MAX_REGIONAL_SCORE = 0.01
#WD_MAX_MEAN = 0.003
#WD_MAX_VARIANCE = 0.000002
#WD_MAX_SKEW = 1.0

# ok after some more IRL testing, we are adjusting to:
WD_MAX_REGIONAL_SCORE = 0.01
WD_MAX_MEAN = 0.003
WD_MAX_VARIANCE = 0.0000035
WD_MAX_ABSOLUTE_SKEW_PULL = 50.0

# and, additionally, after visual score histogram inspection...
WD_VERY_GOOD_MAX_REGIONAL_SCORE = 0.004
WD_VERY_GOOD_MAX_MEAN = 0.0015
WD_VERY_GOOD_MAX_VARIANCE = 0.000001
WD_VERY_GOOD_MAX_SKEW_PULL = 5.0

WD_PERFECT_MAX_REGIONAL_SCORE = 0.001
WD_PERFECT_MAX_MEAN = 0.0001
WD_PERFECT_MAX_VARIANCE = 0.000001
WD_PERFECT_MAX_SKEW_PULL = 1.5

# some future ideas:

# set up a really nice test suite with lots of good example pairs and perform some sort of multi-factor analysis on these output weights
    # then, instead of doing separate bools, have coefficients (or more complicated weights) that we multiply the inputs by to make a total weight and test against one threshold value
    # this would be far more precise than bool gubbins, but we'd have to do research and do it right

# we could adjust our skew detection for how skewed the original file is. jpeg artifacts are focused around borders
    # if a tile has a lot of borders (messy hair) but the rest of the image is simple, we get a relatively high skew despite low mean and such
    # i.e. in this case, jpeg artifacts are not equally distributed across the image
    # so, perhaps a tile histogram could also have some edge/busy-ness detection as well
        # either we reduce the score by the busy-ness (yeah probably this)
        # or we bin the histograms by busy-ness and compare separately (probably convoluted and no better results than a busy-ness weight)

# train an ML to do it lol

# if we did this in HSL, we might be able to detect trivial recolours specifically

def FilesAreVisuallySimilarRegionalLabHistograms( histograms_1: list[ LabHistograms ], histograms_2: list[ LabHistograms ] ):
    
    lab_data = []
    
    for ( i, ( lab_hist_1, lab_hist_2 ) ) in enumerate( zip( histograms_1, histograms_2 ) ):
        
        lab_data.append( GetVisualDataWassersteinDistanceScore( lab_hist_1, lab_hist_2 ) )
        
    
    we_have_no_interesting_tiles = True not in ( interesting_tile for ( interesting_tile, lab_score ) in lab_data )
    we_have_an_interesting_tile_that_matches_perfectly = True in ( interesting_tile and lab_score < 0.0000001 for ( interesting_tile, lab_score ) in lab_data )
    
    scores = [ lab_score for ( interesting_tile, lab_score ) in lab_data ]
    
    max_regional_score = max( scores )
    mean_score = float( numpy.mean( scores ) )
    score_variance = float( numpy.var( scores ) )
    score_skew = skewness_numpy( scores )
    
    # ok so skew alone is normalised and can thus be whack when we have a really tight, low variance distribution
    # so, let's multiply it by the maximum value we saw, and that gives us a nicer thing that scales to relevance with a decent sized distribution
    absolute_skew_pull = score_skew * max_regional_score * 1000
    
    we_have_a_mix_of_perfect_and_non_perfect_matches = we_have_an_interesting_tile_that_matches_perfectly and max_regional_score > 0.0001 and absolute_skew_pull > 8.0
    
    exceeds_regional_score = max_regional_score > WD_MAX_REGIONAL_SCORE
    exceeds_mean = mean_score > WD_MAX_MEAN
    exceeds_variance = score_variance > WD_MAX_VARIANCE
    exceeds_skew = absolute_skew_pull > WD_MAX_ABSOLUTE_SKEW_PULL
    
    debug_score_statement = f'max {max_regional_score:.6f} ({"ok" if not exceeds_regional_score else "bad"}) / mean {mean_score:.6f} ({"ok" if not exceeds_mean else "bad"})'
    debug_score_statement += '\n'
    debug_score_statement += f'variance {score_variance:.7f} ({"ok" if not exceeds_variance else "bad"}) / skew {score_skew:.3f}/{absolute_skew_pull:.2f} ({"ok" if not exceeds_skew else "bad"})'
    debug_score_statement += '\n'
    debug_score_statement += f'perfect/imperfect: {we_have_an_interesting_tile_that_matches_perfectly} {"ok" if not we_have_a_mix_of_perfect_and_non_perfect_matches else "bad"}'
    
    #print( debug_score_statement )
    
    if exceeds_skew or exceeds_variance or exceeds_mean or exceeds_regional_score or we_have_a_mix_of_perfect_and_non_perfect_matches or we_have_no_interesting_tiles:
        
        they_are_similar = False
        result = VISUAL_DUPLICATES_RESULT_NOT
        
        if we_have_no_interesting_tiles:
            
            statement = f'too simple to compare'
            
        elif we_have_a_mix_of_perfect_and_non_perfect_matches:
            
            statement = 'probably not visual duplicates\n(small difference?)'
            
        elif exceeds_skew:
            
            statement = 'not visual duplicates\n(alternate/watermark?)'
            
        elif not exceeds_variance:
            
            statement = 'probably not visual duplicates\n(alternate/severe re-encode?)'
            
        else:
            
            statement = 'probably not visual duplicates'
            
        
    else:
        
        they_are_similar = True
        
        if max_regional_score < WD_PERFECT_MAX_REGIONAL_SCORE and mean_score < WD_PERFECT_MAX_MEAN and score_variance < WD_PERFECT_MAX_VARIANCE and absolute_skew_pull < WD_PERFECT_MAX_SKEW_PULL:
            
            statement = 'near-perfect visual duplicates'
            result = VISUAL_DUPLICATES_RESULT_NEAR_PERFECT
            
        elif max_regional_score < WD_VERY_GOOD_MAX_REGIONAL_SCORE and mean_score < WD_VERY_GOOD_MAX_MEAN and score_variance < WD_VERY_GOOD_MAX_VARIANCE and absolute_skew_pull < WD_VERY_GOOD_MAX_SKEW_PULL:
            
            statement = 'almost certainly visual duplicates'
            result = VISUAL_DUPLICATES_RESULT_ALMOST_CERTAINLY
            
        else:
            
            statement = 'very probably visual duplicates'
            result = VISUAL_DUPLICATES_RESULT_VERY_PROBABLY
            
        
    
    return ( they_are_similar, result, statement )
    

def FilesAreVisuallySimilarSimple( visual_data_1: VisualData, visual_data_2: VisualData ):
    
    # if I do not scale images to be the same size, this guy falls over!
    # I guess the INTER_AREA or something is doing an implicit gaussian of some sort and my tuned numbers assume that
    
    if visual_data_1.had_alpha or visual_data_2.had_alpha:
        
        if visual_data_1.had_alpha and visual_data_2.had_alpha:
            
            message = 'cannot determine visual duplicates\n(they have transparency)'
            
        else:
            
            message = 'not visual duplicates\n(one has transparency)'
            
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, message )
        
    
    if FilesHaveDifferentRatio( visual_data_1.resolution, visual_data_2.resolution ):
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, 'not visual duplicates\n(different ratio)' )
        
    
    if visual_data_1.ResolutionIsTooLow() or visual_data_2.ResolutionIsTooLow():
        
        return ( False, VISUAL_DUPLICATES_RESULT_NOT, 'cannot determine visual duplicates\n(too low resolution)' )
        
    
    # this is useful to rule out easy false positives, but as expected it suffers from lack of fine resolution
    
    ( interesting_tile, lab_score ) = GetVisualDataWassersteinDistanceScore( visual_data_1.lab_histograms, visual_data_2.lab_histograms )
    
    # experimentally, I generally find that most are < 0.0008, but a couple of high-quality-range jpeg pairs are 0.0018
    # so, let's allow this thing to examine deeper on this range of things but otherwise quickly discard
    # a confident negative result but less confident positive result is the way around we want
    
    they_are_similar = lab_score < 0.003
    
    if not interesting_tile:
        
        statement = f'too simple to compare'
        result = VISUAL_DUPLICATES_RESULT_NOT
        
    elif they_are_similar:
        
        statement = f'probably visual duplicates'
        result = VISUAL_DUPLICATES_RESULT_PROBABLY
        
    else:
        
        statement = f'not visual duplicates'
        result = VISUAL_DUPLICATES_RESULT_NOT
        
    
    return ( they_are_similar, result, statement )
    

def FilesHaveDifferentRatio( resolution_1, resolution_2 ):
    
    from hydrus.client.search import ClientNumberTest
    
    ( s_w, s_h ) = resolution_1
    ( c_w, c_h ) = resolution_2
    
    s_ratio = s_w / s_h
    c_ratio = c_w / c_h
    
    return not ClientNumberTest.NumberTest( operator = ClientNumberTest.NUMBER_TEST_OPERATOR_APPROXIMATE_PERCENT, value = 1 ).Test( s_ratio, c_ratio )
    

def GenerateEdgeMapNumPy( rgb_numpy_image: numpy.ndarray ) -> EdgeMap:
    """
    Receives the full image normalised to the bounding perceptual resolution. Not a tile.
    Comparable images should have the same 'size' of edge coming in here, and thus we can use the same 'perceptual' scale gaussian radii
    """
    
    # maybe we will convert this to be Lab also, I dunno
    
    rgb_numpy_image = rgb_numpy_image.astype( numpy.float32 )
    
    # Compute Difference of Gaussians
    # note we already did 0.8 blur on the 100% zoom
    # I tried several upper range blurs, 10.0 works well visually and with the final stats
    # ultimately this is more of a 'filtered and scaled image' more than a strict tight-band edge-map, but this seembs to handle general situations better
    dog = rgb_numpy_image - BlurRGBNumPy( rgb_numpy_image, 10.0 )
    #dog = BlurRGBNumPy( rgb_numpy_image, 2.0 ) - BlurRGBNumPy( rgb_numpy_image, 6.0 )
    
    # this is in a range of -255->255 and hovers around 0
    dog = dog.astype( numpy.float32 )
    
    # ok collapse to something smaller, using mean average
    edge_map = cv2.resize( dog, EDGE_MAP_NORMALISED_RESOLUTION, interpolation = cv2.INTER_AREA )
    
    edge_map_r = edge_map[ :, :, 0 ]
    edge_map_g = edge_map[ :, :, 1 ]
    edge_map_b = edge_map[ :, :, 2 ]
    
    return EdgeMap( edge_map_r, edge_map_g, edge_map_b )
    

def GenerateImageVisualDataNumPy( numpy_image: numpy.ndarray, cache_key: object ) -> VisualData:
    
    ( width, height ) = ( numpy_image.shape[1], numpy_image.shape[0] )
    
    resolution = ( width, height )
    
    numpy_image_rgb = HydrusImageNormalisation.StripOutAnyAlphaChannel( numpy_image )
    
    # TODO: add an alpha histogram or something and an alpha comparison
    had_alpha = numpy_image.shape != numpy_image_rgb.shape
    
    #numpy_image_gray = cv2.cvtColor( numpy_image_rgb, cv2.COLOR_RGB2GRAY )
    
    if JPEG_ARTIFACT_BLUR_FOR_PROCESSING:
        
        numpy_image_rgb = BlurRGBNumPy( numpy_image_rgb, JPEG_ARTIFACT_GAUSSIAN_SIGMA_AT_100_ZOOM )
        
    
    # Lab histogram
    
    if NORMALISE_SCALE_FOR_LAB_HISTOGRAM_PROCESSING:
        
        lab_histogram_numpy_image_rgb = cv2.resize( numpy_image_rgb, LAB_HISTOGRAM_NORMALISED_RESOLUTION, interpolation = cv2.INTER_AREA )
        
    else:
        
        lab_histogram_numpy_image_rgb = numpy_image_rgb
        
    
    numpy_image_lab = cv2.cvtColor( lab_histogram_numpy_image_rgb, cv2.COLOR_RGB2Lab )
    
    l = numpy_image_lab[ :, :, 0 ]
    a = numpy_image_lab[ :, :, 1 ]
    b = numpy_image_lab[ :, :, 2 ]
    
    # just a note here, a and b are usually -128 to +128, but opencv normalises to 0-255, so we are good
    
    ( l_hist, l_gubbins ) = numpy.histogram( l, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
    ( a_hist, a_gubbins ) = numpy.histogram( a, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
    ( b_hist, b_gubbins ) = numpy.histogram( b, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
    
    lab_histograms = LabHistograms( l_hist.astype( numpy.float32 ), a_hist.astype( numpy.float32 ), b_hist.astype( numpy.float32 ) )
    
    return VisualData( resolution, had_alpha, lab_histograms )
    

def GenerateImageVisualDataTiledNumPy( numpy_image: numpy.ndarray, cache_key: object ) -> VisualDataTiled:
    
    ( width, height ) = ( numpy_image.shape[1], numpy_image.shape[0] )
    
    resolution = ( width, height )
    
    numpy_image_rgb = HydrusImageNormalisation.StripOutAnyAlphaChannel( numpy_image )
    
    had_alpha = numpy_image.shape != numpy_image_rgb.shape
    
    if JPEG_ARTIFACT_BLUR_FOR_PROCESSING:
        
        numpy_image_rgb = BlurRGBNumPy( numpy_image_rgb, JPEG_ARTIFACT_GAUSSIAN_SIGMA_AT_100_ZOOM )
        
    
    # RGB edge-map
    
    scale_resolution = HydrusImageHandling.GetThumbnailResolution( resolution, EDGE_MAP_PERCEPTUAL_RESOLUTION, HydrusImageHandling.THUMBNAIL_SCALE_TO_FIT, 100 )
    
    edge_map_numpy_image_rgb = cv2.resize( numpy_image_rgb, scale_resolution, interpolation = cv2.INTER_AREA )
    
    edge_map = GenerateEdgeMapNumPy( edge_map_numpy_image_rgb )
    
    # Lab histograms (tiled)
    
    # ok scale the image up to the nearest multiple of num_tiles
    tile_fitting_width = ( ( width + LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION - 1 ) // LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION ) * LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION
    tile_fitting_height = ( ( height + LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION - 1 ) // LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION ) * LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION
    
    if NORMALISE_SCALE_FOR_LAB_HISTOGRAM_PROCESSING:
        
        lab_size_we_will_scale_to = LAB_HISTOGRAM_NORMALISED_RESOLUTION
        
    else:
        
        lab_size_we_will_scale_to = ( tile_fitting_width, tile_fitting_height )
        
    
    scaled_numpy = cv2.resize( numpy_image_rgb, lab_size_we_will_scale_to, interpolation = cv2.INTER_AREA )
    
    numpy_image_lab = cv2.cvtColor( scaled_numpy, cv2.COLOR_RGB2Lab )
    
    l = numpy_image_lab[ :, :, 0 ]
    a = numpy_image_lab[ :, :, 1 ]
    b = numpy_image_lab[ :, :, 2 ]
    
    histograms = []
    
    ( lab_tile_x, lab_tile_y ) = ( lab_size_we_will_scale_to[0] // LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION, lab_size_we_will_scale_to[1] // LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION )
    
    for x in range( LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION ):
        
        for y in range( LAB_HISTOGRAM_NUM_TILES_PER_DIMENSION ):
            
            l_tile = l[ y * lab_tile_y : ( y + 1 ) * lab_tile_y, x * lab_tile_x : ( x + 1 ) * lab_tile_x ]
            a_tile = a[ y * lab_tile_y : ( y + 1 ) * lab_tile_y, x * lab_tile_x : ( x + 1 ) * lab_tile_x ]
            b_tile = b[ y * lab_tile_y : ( y + 1 ) * lab_tile_y, x * lab_tile_x : ( x + 1 ) * lab_tile_x ]
            
            # just a note here, a and b are usually -128 to +128, but opencv normalises to 0-255, so we are good but the average will usually be ~128
            
            ( l_hist, l_gubbins ) = numpy.histogram( l_tile, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
            ( a_hist, a_gubbins ) = numpy.histogram( a_tile, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
            ( b_hist, b_gubbins ) = numpy.histogram( b_tile, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
            
            histograms.append( LabHistograms( l_hist.astype( numpy.float32 ), a_hist.astype( numpy.float32 ), b_hist.astype( numpy.float32 ) ) )
            
        
    
    return VisualDataTiled( resolution, had_alpha, histograms, edge_map )
    

def GenerateImageRGBHistogramsNumPy( numpy_image: numpy.ndarray ):
    
    numpy_image_rgb = HydrusImageNormalisation.StripOutAnyAlphaChannel( numpy_image )
    
    r = numpy_image_rgb[ :, :, 0 ]
    g = numpy_image_rgb[ :, :, 1 ]
    b = numpy_image_rgb[ :, :, 2 ]
    
    # ok the density here tells it to normalise, so images with greater saturation appear similar
    ( r_hist, r_gubbins ) = numpy.histogram( r, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
    ( g_hist, g_gubbins ) = numpy.histogram( g, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
    ( b_hist, b_gubbins ) = numpy.histogram( b, bins = LAB_HISTOGRAM_NUM_BINS, range = ( 0, 255 ), density = True )
    
    return ( r_hist, g_hist, b_hist )
    

def GetHistogramNormalisedWassersteinDistance( hist_1: numpy.ndarray, hist_2: numpy.ndarray ) -> float:
    
    # Earth Movement Distance
    # how much do we have to rejigger one hist to be the same as the other?
    
    EMD = numpy.sum( numpy.abs( numpy.cumsum( hist_1 - hist_2 ) ) )
    
    # 0 = no movement, 255 = max movement
    
    return float( EMD / ( len( hist_1 ) - 1 ) )
    

def GetEdgeMapSlicedWasstersteinDistanceScore( edge_map_1: numpy.ndarray, edge_map_2: numpy.ndarray ):
    
    # this is a fast alternate of a 2D wasserstein distance
    
    def wasserstein_1d(p, q):
        
        return numpy.sum( numpy.abs( numpy.cumsum( p - q ) ) )
        
    
    row_diff = sum( wasserstein_1d( edge_map_1[i], edge_map_2[i] ) for i in range( edge_map_1.shape[0] ) )
    col_diff = sum( wasserstein_1d( edge_map_1[:, j], edge_map_2[:, j] ) for j in range( edge_map_1.shape[1] ) )
    
    return row_diff + col_diff
    

def GetVisualDataWassersteinDistanceScore( lab_hist_1: LabHistograms, lab_hist_2: LabHistograms ):
    
    l_score = GetHistogramNormalisedWassersteinDistance( lab_hist_1.l_hist, lab_hist_2.l_hist )
    a_score = GetHistogramNormalisedWassersteinDistance( lab_hist_1.a_hist, lab_hist_2.a_hist )
    b_score = GetHistogramNormalisedWassersteinDistance( lab_hist_1.b_hist, lab_hist_2.b_hist )
    
    interesting_tile = lab_hist_1.IsInteresting() or lab_hist_2.IsInteresting()
    
    return ( interesting_tile, 0.6 * l_score + 0.2 * a_score + 0.2 * b_score )
    
