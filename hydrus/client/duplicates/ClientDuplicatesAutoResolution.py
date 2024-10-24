import random
import threading
import typing

from hydrus.core import HydrusSerialisable

from hydrus.client.duplicates import ClientDuplicates
from hydrus.client.metadata import ClientMetadataConditional

# in the database I guess we'll assign these in a new table to all outstanding pairs that match a search
DUPLICATE_STATUS_DOES_NOT_MATCH_SEARCH = 0
DUPLICATE_STATUS_MATCHES_SEARCH_BUT_NOT_TESTED = 1
DUPLICATE_STATUS_MATCHES_SEARCH_FAILED_TEST = 2
DUPLICATE_STATUS_MATCHES_SEARCH_PASSED_TEST = 3 # presumably this will not be needed much since we'll delete the duplicate pair soon after, but we may as well be careful
DUPLICATE_STATUS_NOT_SEARCHED = 4 # assign this to new pairs that are added, by default??? then re-do the search with system:hash tacked on maybe, regularly

class PairComparator( HydrusSerialisable.SerialisableBase ):
    
    def Test( self, media_result_better, media_result_worse ):
        
        raise NotImplementedError()
        
    

LOOKING_AT_BETTER_CANDIDATE = 0
LOOKING_AT_WORSE_CANDIDATE = 1

class PairComparatorOneFile( PairComparator ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_PAIR_COMPARATOR_ONE_FILE
    SERIALISABLE_NAME = 'Duplicates Auto-Resolution Pair Comparator - One File'
    SERIALISABLE_VERSION = 1
    
    def __init__( self ):
        """
        This guy holds one test and is told to test either the better or worse candidate. Multiple of these stacked up make for 'the better file is a jpeg over one megabyte, the worse file is a jpeg under 100KB'.
        """
        
        super().__init__()
        
        # this guy tests the better or the worse for a single property
        # user could set up multiple on either side of the equation
        # what are we testing?
            # better file mime is jpeg (& worse file is png)
            # better file has icc profile
            # worse file filesize < 200KB
        
        self._looking_at = LOOKING_AT_BETTER_CANDIDATE
        
        self._metadata_conditional = ClientMetadataConditional.MetadataConditional()
        
    
    # serialisable gubbins
    # get/set
    
    def Test( self, media_result_better, media_result_worse ):
        
        if self._looking_at == LOOKING_AT_BETTER_CANDIDATE:
            
            return self._metadata_conditional.Test( media_result_better )
            
        else:
            
            return self._metadata_conditional.Test( media_result_worse )
            
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_PAIR_COMPARATOR_ONE_FILE ] = PairComparatorOneFile

class PairComparatorRelative( PairComparator ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_PAIR_COMPARATOR_TWO_FILES_RELATIVE
    SERIALISABLE_NAME = 'Duplicates Auto-Resolution Pair Comparator - Relative'
    SERIALISABLE_VERSION = 1
    
    def __init__( self ):
        """
        This guy compares the pair directly. It can say 'yes the better candidate is 4x bigger than the worse'. 
        """
        
        super().__init__()
        
        # this work does not need to be done yet!
        
        # if I am feeling big brain, isn't this just a dynamic one-file metadata conditional?
            # if we want 4x size, then we just pull the size of A and ask if B is <0.25x that or whatever. we don't need a clever two-file MetadataConditional test
        # so, this guy should yeah just store two or three simple enums to handle type, operator, and quantity
        
        # property
            # width
            # filesize
            # age
            # etc..
        # operator
            # is more than 4x larger
            # is at least x absolute value larger?
        
    
    # serialisable gubbins
    # get/set
    
    def Test( self, media_result_better, media_result_worse ):
        
        pass
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_PAIR_COMPARATOR_TWO_FILES_RELATIVE ] = PairComparatorRelative

class PairSelectorAndComparator( HydrusSerialisable.SerialisableBase ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_PAIR_SELECTOR_AND_COMPARATOR
    SERIALISABLE_NAME = 'Duplicates Auto-Resolution Pair Selector and Comparator'
    SERIALISABLE_VERSION = 1
    
    def __init__( self ):
        """
        This guy holds a bunch of rules. It is given a pair of media and it tests all the rules both ways around. If the files pass all the rules, we have a match and thus a confirmed better file.
        
        A potential future expansion here is to attach scores to the rules and have a score threshold, but let's not get ahead of ourselves.
        """
        
        super().__init__()
        
        self._comparators = HydrusSerialisable.SerialisableList()
        
    
    # serialisable gubbins
    # get/set
    
    def GetMatchingMedia( self, media_result_1, media_result_2 ):
        
        pair = [ media_result_1, media_result_2 ]
        
        # just in case both match
        random.shuffle( pair )
        
        ( media_result_1, media_result_2 ) = pair
        
        if False not in ( comparator.Test( media_result_1, media_result_2 ) for comparator in self._comparators ):
            
            return media_result_1
            
        elif False not in ( comparator.Test( media_result_2, media_result_1 ) for comparator in self._comparators ):
            
            return media_result_2
            
        else:
            
            return None
            
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_PAIR_SELECTOR_AND_COMPARATOR ] = PairSelectorAndComparator

class DuplicatesAutoResolutionRule( HydrusSerialisable.SerialisableBaseNamed ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_RULE
    SERIALISABLE_NAME = 'Duplicates Auto-Resolution Rule'
    SERIALISABLE_VERSION = 1
    
    def __init__( self, name ):
        """
        This guy holds everything to make a single auto-resolution job work. It knows the search it wants to do, and, when given pairs from that search, will confirm whether one file passes its auto-resolution threshold and should be auto-considered better.
        """
        
        super().__init__( name )
        
        # the id here will be for the database to match up rules to cached pair statuses. slightly wewmode, but we'll see
        self._id = -1
        
        # TODO: Yes, do this before we get too excited here
        # maybe make this search part into its own object? in ClientDuplicates
        # could wangle duplicate pages and client api dupe stuff to work in the same guy, great idea
        # duplicate search, too, rather than passing around a bunch of params
        self._file_search_context_1 = None
        self._file_search_context_2 = None
        self._dupe_search_type = ClientDuplicates.DUPE_SEARCH_ONE_FILE_MATCHES_ONE_SEARCH
        self._pixel_dupes_preference = ClientDuplicates.SIMILAR_FILES_PIXEL_DUPES_ALLOWED
        self._max_hamming_distance = 4
        
        self._selector_and_comparator = None
        
        self._paused = False
        
        # action info
            # set as better
            # delete the other one
            # optional custom merge options
        
        # a search cache that we can update on every run, just some nice numbers for the human to see or force-populate in UI that say 'ok for this search we have 700,000 pairs, and we already processed 220,000'
        # I think a dict of numbers to strings
        # number of pairs that match the search
        # how many didn't pass the comparator test
        # also would be neat just to remember how many pairs we have successfully processed
        
    
    # serialisable gubbins
    # get/set
    # 'here's a pair of media results, pass/fail?'
    
    def GetId( self ) -> int:
        
        return self._id
        
    
    def GetActionSummary( self ) -> str:
        
        return 'set A as better, delete worse'
        
    
    def GetComparatorSummary( self ) -> str:
        
        return 'if A is jpeg and B is png'
        
    
    def GetRuleSummary( self ) -> str:
        
        return 'system:filetype is jpeg & system:filetype is png, pixel duplicates'
        
    
    def GetSearchSummary( self ) -> str:
        
        return 'unknown'
        
    
    def IsPaused( self ) -> bool:
        
        return self._paused
        
    
    def SetId( self, value: int ):
        
        self._id = value
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_DUPLICATES_AUTO_RESOLUTION_RULE ] = DuplicatesAutoResolutionRule

def GetDefaultRuleSuggestions() -> typing.List[ DuplicatesAutoResolutionRule ]:
    
    suggested_rules = []
    
    #
    
    duplicates_auto_resolution_rule = DuplicatesAutoResolutionRule( 'pixel-perfect jpegs vs pngs' )
    
    suggested_rules.append( duplicates_auto_resolution_rule )
    
    # add on a thing here about resolution. one(both) files need to be like at least 128x128
    
    #
    
    return suggested_rules
    

# TODO: get this guy to inherit that new MainLoop Daemon class and hook it into the other client controller managers
# ditch the instance() stuff or don't, whatever you like
class DuplicatesAutoResolutionManager( object ):
    
    my_instance = None
    
    def __init__( self ):
        """
        This guy is going to be the mainloop daemon that runs all this gubbins.
        
        Needs some careful locking for when the edit dialog is open, like import folders manager etc..
        """
        
        DuplicatesAutoResolutionManager.my_instance = self
        
        self._ids_to_rules = {}
        
        # load rules from db or whatever on controller init
        # on program first boot, we should initialise with the defaults set to paused!
        
        self._lock = threading.Lock()
        
    
    @staticmethod
    def instance() -> 'DuplicatesAutoResolutionManager':
        
        if DuplicatesAutoResolutionManager.my_instance is None:
            
            DuplicatesAutoResolutionManager()
            
        
        return DuplicatesAutoResolutionManager.my_instance
        
    
    def GetRules( self ):
        
        return []
        
    
    def GetRunningStatus( self, rule_id: int ) -> str:
        
        return 'idle'
        
    
    def SetRules( self, rules: typing.Collection[ DuplicatesAutoResolutionRule ] ):
        
        # save to database
        
        # make sure the rules that need ids now have them
        
        self._ids_to_rules = { rule.GetId() : rule for rule in rules }
        
        # send out an update signal
        
    
    def Wake( self ):
        
        pass
        
    
