import os
import typing

from qtpy import QtWidgets as QW

from hydrus.core import HydrusData
from hydrus.core import HydrusExceptions
from hydrus.core import HydrusStaticDir
from hydrus.core import HydrusText

from hydrus.client.gui import QtInit

DEFAULT_HYDRUS_STYLESHEET = ''
ORIGINAL_STYLE_NAME = None
CURRENT_STYLE_NAME = None
ORIGINAL_STYLESHEET = None
CURRENT_STYLESHEET = None
CURRENT_STYLESHEET_FILENAME = None

def ClearStyleSheet():
    
    SetStyleSheet( ORIGINAL_STYLESHEET, None )
    

def GetAvailableStyles():
    
    # so eventually expand this to do QStylePlugin or whatever we are doing to add more QStyles
    
    return sorted( QW.QStyleFactory.keys(), key = HydrusText.HumanTextSortKey )
    

def GetAvailableStyleSheets():
    
    stylesheet_filenames = []
    
    extensions = [ '.qss', '.css' ]
    
    for path in HydrusStaticDir.ListStaticDirFilePaths( 'qss' ):
        
        ( d, filename ) = os.path.split( path )
        
        if True in ( filename.endswith( ext ) for ext in extensions ):
            
            stylesheet_filenames.append( filename )
            
        
    
    HydrusText.HumanTextSort( stylesheet_filenames )
    
    return stylesheet_filenames
    

def InitialiseDefaults():
    
    global DEFAULT_HYDRUS_STYLESHEET
    
    try:
        
        with open( HydrusStaticDir.GetStaticPath( os.path.join( 'qss', 'default_hydrus.qss' ) ), 'r', encoding = 'utf-8' ) as f:
            
            DEFAULT_HYDRUS_STYLESHEET = f.read()
            
        
    except Exception as e:
        
        HydrusData.Print( 'Failed to load default hydrus qss:' )
        HydrusData.PrintException( e )
        
        DEFAULT_HYDRUS_STYLESHEET = ''
        
    
    global ORIGINAL_STYLE_NAME
    global CURRENT_STYLE_NAME
    
    app_instance = typing.cast( QW.QApplication, QW.QApplication.instance() )
    
    if QtInit.WE_ARE_QT5:
        
        ORIGINAL_STYLE_NAME  = app_instance.style().objectName()
        
    else:
        
        ORIGINAL_STYLE_NAME  = app_instance.style().name()
        
    
    BETTER_SUPPORT_FOR_NOW = 'windowsvista'
    
    if ORIGINAL_STYLE_NAME == 'windows11' and BETTER_SUPPORT_FOR_NOW in GetAvailableStyles():
        
        ORIGINAL_STYLE_NAME = BETTER_SUPPORT_FOR_NOW
        
        SetStyleFromName( BETTER_SUPPORT_FOR_NOW )
        
    
    CURRENT_STYLE_NAME = ORIGINAL_STYLE_NAME
    
    global ORIGINAL_STYLESHEET
    global CURRENT_STYLESHEET
    
    ORIGINAL_STYLESHEET = app_instance.styleSheet()
    CURRENT_STYLESHEET = ORIGINAL_STYLESHEET
    

def ReloadStyleSheet():
    
    stylesheet_to_set = CURRENT_STYLESHEET_FILENAME
    
    ClearStyleSheet()
    
    if stylesheet_to_set is not None:
        
        SetStyleSheetFromPath( stylesheet_to_set )
        
    

def SetStyleFromName( name: str ):
    
    app_instance = typing.cast( QW.QApplication, QW.QApplication.instance() )
    
    if QtInit.WE_ARE_QT5:
        
        current_style_name  = app_instance.style().objectName()
        
    else:
        
        current_style_name  = app_instance.style().name()
        
    
    if name.casefold() == current_style_name.casefold():
        
        return
        
    
    try:
        
        new_style = app_instance.setStyle( name )
        
        global CURRENT_STYLE_NAME
        
        CURRENT_STYLE_NAME = name
        
        if new_style is None:
            
            raise HydrusExceptions.DataMissing( 'Style "{}" does not exist! If this is the default, perhaps a third-party custom style, you may have to restart the client to re-set it.'.format( name ) )
            
        
    except Exception as e:
        
        raise HydrusExceptions.DataMissing( 'Style "{}" could not be generated/applied. If this is the default, perhaps a third-party custom style, you may have to restart the client to re-set it. Extra error info: {}'.format( name, e ) )
        
    

def SetStyleSheet( stylesheet, name, prepend_hydrus = True ):
    
    stylesheet_to_use = stylesheet
    
    if prepend_hydrus:
        
        global DEFAULT_HYDRUS_STYLESHEET
        
        stylesheet_to_use = DEFAULT_HYDRUS_STYLESHEET + '\n' * 2 + stylesheet
        
    
    global CURRENT_STYLESHEET_FILENAME
    
    CURRENT_STYLESHEET_FILENAME = name
    
    global CURRENT_STYLESHEET
    
    if CURRENT_STYLESHEET != stylesheet_to_use:
        
        app_instance = typing.cast( QW.QApplication, QW.QApplication.instance() )
        
        app_instance.setStyleSheet( stylesheet_to_use )
        
        CURRENT_STYLESHEET = stylesheet_to_use
        
    

def SetStyleSheetFromPath( filename ):
    
    path = HydrusStaticDir.GetStaticPath( os.path.join( 'qss', filename ) )
    
    if not os.path.exists( path ):
        
        raise HydrusExceptions.DataMissing( 'StyleSheet "{}" does not exist!'.format( path ) )
        
    
    with open( path, 'r', encoding = 'utf-8' ) as f:
        
        qss = f.read()
        
    
    SetStyleSheet( qss, filename )
    
