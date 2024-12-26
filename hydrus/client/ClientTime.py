import datetime
import typing

from hydrus.core import HydrusConstants as HC
from hydrus.core import HydrusSerialisable

from hydrus.client import ClientConstants as CC
from hydrus.client import ClientGlobals as CG

try:
    
    from dateutil.relativedelta import relativedelta
    
    DATEUTIL_OK = True
    
except:
    
    DATEUTIL_OK = False
    

from hydrus.core import HydrusTime

try:
    
    import dateparser
    
    DATEPARSER_OK = True
    
except:
    
    DATEPARSER_OK = False
    

def CalendarDelta( dt: datetime.datetime, month_delta = 0, day_delta = 0 ) -> datetime.datetime:
    
    if DATEUTIL_OK:
        
        delta = relativedelta( months = month_delta, days = day_delta )
        
        return dt + delta
        
    else:
        
        total_days = ( 30 * month_delta ) + day_delta
        
        return dt + datetime.timedelta( days = total_days )
        
    

def ParseDate( date_string: str ):
    
    if not DATEPARSER_OK:
        
        raise Exception( 'Sorry, you need the dateparse library for this, please try reinstalling your venv!' )
        
    
    # as a weird note, this function appears, in one case, to raise the sorry Exception, after several seconds of delay, if the boot locale is ru_RU
    # it works on the same machine if locale is set to en_US. this suggests some environment variable locale-forcing or similar, or a bug in dateparser, that is causing the delay (and then?) failing the 'en' fallback 
    
    # dateparser does not have ru-RU in its internal locale mappings, nor en-US. it has a whole bunch like 'en-PH', which will parse "19 October 2024, 3:45 PM", but not the more common ones
    # it'll raise an error if you ask for en-US but not if you ask for locales = [ 'en' ], where 'en' _seems_ to be a proxy for 'en-US', so there's some weird locale init going on, idk
    
    dt = dateparser.parse( date_string )
    
    if dt is None:
        
        # '7/18/2023 8:32:00AM' will not parse if the locale is 'pl', seems to be a 24-hour clock thing
        # since most non-locale timestamps will be EN, let's do this as fallback
        dt = dateparser.parse( date_string, languages = ['en'] )
        
    
    if dt is None:
        
        raise Exception( 'Sorry, could not parse that date!' )
        
    
    return HydrusTime.DateTimeToTimestamp( dt )
    

def MergeModifiedTimes( existing_timestamp: typing.Optional[ int ], new_timestamp: typing.Optional[ int ] ) -> typing.Optional[ int ]:
    
    if ShouldUpdateModifiedTime( existing_timestamp, new_timestamp ):
        
        return new_timestamp
        
    else:
        
        return existing_timestamp
        
    

def ShouldUpdateModifiedTime( existing_timestamp: int, new_timestamp: typing.Optional[ int ] ) -> bool:
    
    if new_timestamp is None:
        
        return False
        
    
    if existing_timestamp is None:
        
        return True
        
    
    # only go backwards, in general
    if new_timestamp >= existing_timestamp:
        
        return False
        
    
    return True
    

def TimestampIsSensible( timestamp: typing.Optional[ int ] ) -> bool:
    
    if timestamp is None:
        
        return False
        
    
    # assume anything too early is a meme and a timestamp parsing conversion error
    if timestamp <= 86400 * 7:
        
        return False
        
    
    return True
    

REAL_SIMPLE_TIMESTAMP_TYPES = {
    HC.TIMESTAMP_TYPE_ARCHIVED,
    HC.TIMESTAMP_TYPE_MODIFIED_FILE
}

SIMPLE_TIMESTAMP_TYPES = {
    HC.TIMESTAMP_TYPE_ARCHIVED,
    HC.TIMESTAMP_TYPE_MODIFIED_FILE,
    HC.TIMESTAMP_TYPE_MODIFIED_AGGREGATE
}

FILE_SERVICE_TIMESTAMP_TYPES = {
    HC.TIMESTAMP_TYPE_IMPORTED,
    HC.TIMESTAMP_TYPE_DELETED,
    HC.TIMESTAMP_TYPE_PREVIOUSLY_IMPORTED
}

class TimestampData( HydrusSerialisable.SerialisableBase ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_TIMESTAMP_DATA
    SERIALISABLE_NAME = 'Timestamp Data'
    SERIALISABLE_VERSION = 2
    
    def __init__( self, timestamp_type = None, location = None, timestamp_ms: typing.Optional[ typing.Union[ int, float ] ] = None ):
        
        super().__init__()
        
        self.timestamp_type = timestamp_type
        self.location = location
        self.timestamp_ms = None if timestamp_ms is None else int( timestamp_ms )
        self.timestamp = HydrusTime.SecondiseMS( self.timestamp_ms ) # TODO: pretty sure I can delete this variable now, but I am currently attempting to fold space using the spice melange and don't want to make a foolish mistake
        
    
    def __eq__( self, other ):
        
        if isinstance( other, TimestampData ):
            
            return self.__hash__() == other.__hash__()
            
        
        return NotImplemented
        
    
    def __hash__( self ):
        
        return ( self.timestamp_type, self.location, self.timestamp_ms ).__hash__()
        
    
    def __repr__( self ):
        
        return self.ToString()
        
    
    def _GetSerialisableInfo( self ):
        
        if self.timestamp_type in FILE_SERVICE_TIMESTAMP_TYPES:
            
            serialisable_location = self.location.hex()
            
        else:
            
            serialisable_location = self.location # str, int, or None
            
        
        return ( self.timestamp_type, serialisable_location, self.timestamp_ms )
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        ( self.timestamp_type, serialisable_location, self.timestamp_ms ) = serialisable_info
        
        self.timestamp = HydrusTime.SecondiseMS( self.timestamp_ms )
        
        if self.timestamp_type in FILE_SERVICE_TIMESTAMP_TYPES:
            
            self.location = bytes.fromhex( serialisable_location )
            
        else:
            
            self.location = serialisable_location
            
        
    
    def _UpdateSerialisableInfo( self, version, old_serialisable_info ):
        
        if version == 1:
            
            ( timestamp_type, serialisable_location, timestamp ) = old_serialisable_info
            
            timestamp_ms = HydrusTime.MillisecondiseS( timestamp )
            
            new_serialisable_info = ( timestamp_type, serialisable_location, timestamp_ms )
            
            return ( 2, new_serialisable_info )
            
        
    
    def ToString( self ) -> str:
        
        if self.timestamp_type in SIMPLE_TIMESTAMP_TYPES:
            
            type_base = HC.timestamp_type_str_lookup[ self.timestamp_type ]
            
        else:
            
            if self.timestamp_type in FILE_SERVICE_TIMESTAMP_TYPES:
                
                try:
                    
                    service_string = CG.client_controller.services_manager.GetName( self.location )
                    
                except:
                    
                    service_string = 'unknown service'
                    
                
                type_base = '"{}" {}'.format( service_string, HC.timestamp_type_str_lookup[ self.timestamp_type ] )
                
            elif self.timestamp_type == HC.TIMESTAMP_TYPE_LAST_VIEWED:
                
                type_base = '{} {}'.format( CC.canvas_type_str_lookup[ self.location ], HC.timestamp_type_str_lookup[ self.timestamp_type ] )
                
            elif self.timestamp_type == HC.TIMESTAMP_TYPE_MODIFIED_DOMAIN:
                
                type_base = '"{}" {}'.format( self.location, HC.timestamp_type_str_lookup[ self.timestamp_type ] )
                
            else:
                
                type_base = 'unknown timestamp type'
                
            
        
        if self.timestamp_ms is None:
            
            # we are a stub, type summary is appropriate
            return type_base
            
        else:
            
            return '{}: {}'.format( type_base, HydrusTime.TimestampMSToPrettyTime( self.timestamp_ms ) )
            
        
    
    @staticmethod
    def STATICArchivedTime( timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_ARCHIVED, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICAggregateModifiedTime( timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_MODIFIED_AGGREGATE, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICDeletedTime( service_key: bytes, timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_DELETED, location = service_key, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICDomainModifiedTime( domain: str, timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_MODIFIED_DOMAIN, location = domain, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICFileModifiedTime( timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_MODIFIED_FILE, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICImportedTime( service_key: bytes, timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_IMPORTED, location = service_key, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICLastViewedTime( canvas_type: int, timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_LAST_VIEWED, location = canvas_type, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICPreviouslyImportedTime( service_key: bytes, timestamp_ms: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = HC.TIMESTAMP_TYPE_PREVIOUSLY_IMPORTED, location = service_key, timestamp_ms = timestamp_ms )
        
    
    @staticmethod
    def STATICSimpleStub( timestamp_type: int ) -> "TimestampData":
        
        return TimestampData( timestamp_type = timestamp_type )
        
    

HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_TIMESTAMP_DATA ] = TimestampData
