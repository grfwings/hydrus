from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from hydrus.client import ClientConstants as CC
from hydrus.client import ClientGlobals as CG
from hydrus.client.gui import ClientGUIFunctions
from hydrus.client.gui import QtPorting as QP
from hydrus.client.gui.widgets import ClientGUICommon

AUDIO_GLOBAL = 0
AUDIO_MEDIA_VIEWER = 1
AUDIO_PREVIEW = 2

volume_types_str_lookup = {}

volume_types_str_lookup[ AUDIO_GLOBAL ] = 'global'
volume_types_str_lookup[ AUDIO_MEDIA_VIEWER ] = 'media viewer'
volume_types_str_lookup[ AUDIO_PREVIEW ] = 'preview'

volume_types_to_option_names = {}

volume_types_to_option_names[ AUDIO_GLOBAL ] = ( 'global_audio_mute', 'global_audio_volume' )
volume_types_to_option_names[ AUDIO_MEDIA_VIEWER ] = ( 'media_viewer_audio_mute', 'media_viewer_audio_volume' )
volume_types_to_option_names[ AUDIO_PREVIEW ] = ( 'preview_audio_mute', 'preview_audio_volume' )

def ChangeVolume( volume_type, volume ):
    
    ( mute_option_name, volume_option_name ) = volume_types_to_option_names[ volume_type ]
    
    CG.client_controller.new_options.SetInteger( volume_option_name, volume )
    
    CG.client_controller.pub( 'new_audio_volume' )
    
def FlipMute( volume_type ):
    
    ( mute_option_name, volume_option_name ) = volume_types_to_option_names[ volume_type ]
    
    CG.client_controller.new_options.FlipBoolean( mute_option_name )
    
    CG.client_controller.pub( 'new_audio_mute' )
    
def SetMute( volume_type, mute ):
    
    ( mute_option_name, volume_option_name ) = volume_types_to_option_names[ volume_type ]
    
    CG.client_controller.new_options.SetBoolean( mute_option_name, mute )
    
    CG.client_controller.pub( 'new_audio_mute' )
    

class AudioMuteButton( ClientGUICommon.IconButton ):
    
    def __init__( self, parent, volume_type ):
        
        self._volume_type = volume_type
        
        icon = self._GetCorrectIcon()
        
        super().__init__( parent, icon, FlipMute, self._volume_type )
        
        CG.client_controller.sub( self, 'UpdateMute', 'new_audio_mute' )
        
    
    def _GetCorrectIcon( self ):
        
        ( mute_option_name, volume_option_name ) = volume_types_to_option_names[ self._volume_type ]
        
        if CG.client_controller.new_options.GetBoolean( mute_option_name ):
            
            icon = CC.global_icons().mute
            
        else:
            
            icon = CC.global_icons().sound
            
        
        return icon
        
    
    def UpdateMute( self ):
        
        icon = self._GetCorrectIcon()
        
        self.SetIconSmart( icon )
        
    

class VolumeControl( QW.QWidget ):
    
    def __init__( self, parent, canvas_type, direction = 'down' ):
        
        super().__init__( parent )
        
        self._canvas_type = canvas_type
        
        self._global_mute = AudioMuteButton( self, AUDIO_GLOBAL )
        
        self._global_mute.setToolTip( ClientGUIFunctions.WrapToolTip( 'Global mute/unmute' ) )
        self._global_mute.setFocusPolicy( QC.Qt.FocusPolicy.NoFocus )
        
        vbox = QP.VBoxLayout( margin = 0, spacing = 0 )
        
        QP.AddToLayout( vbox, self._global_mute, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
        
        self.setLayout( vbox )
        
        # TODO: same as with much of the media controls mess, this needs to be plugged into the layout system properly
        # we should have a custom layout here that specifies where the slider should go and do raise/show/hide while still reporting a nice small sizeHint
        
        self._popup_window = self._PopupWindow( self, canvas_type, direction = direction )
        
    
    def enterEvent( self, event ):
        
        if not self.isVisible():
            
            event.ignore()
            
            return
            
        
        self._popup_window.DoShowHide()
        
        event.ignore()
        
    
    def leaveEvent( self, event ):
        
        if not self.isVisible():
            
            self._popup_window.setVisible( False )
            
            event.ignore()
            
            return
            
        
        self._popup_window.DoShowHide()
        
        event.ignore()
        
    
    def moveEvent( self, event ):
        
        super().moveEvent( event )
        
        self._popup_window.DoShowHide()
        
    
    def PopupIsVisible( self ):
        
        return not self._popup_window.isHidden()
        
    
    def resizeEvent( self, event ):
        
        super().resizeEvent( event )
        
        CG.client_controller.CallAfterQtSafe( self, 'volume popup resize event', self._popup_window.DoShowHide )
        
    
    def setVisible( self, *args, **kwargs ):
        
        super().setVisible( *args, **kwargs )
        
        self._popup_window.DoShowHide()
        
    
    class _PopupWindow( QW.QFrame ):
        
        def __init__( self, parent, canvas_type, direction = 'down' ):
            
            super().__init__( parent )
            
            self._canvas_type = canvas_type
            
            self._direction = direction
            
            self.setWindowFlags( QC.Qt.WindowType.Tool | QC.Qt.WindowType.FramelessWindowHint )
            
            self.setAttribute( QC.Qt.WidgetAttribute.WA_ShowWithoutActivating )
            
            if self._canvas_type in CC.CANVAS_MEDIA_VIEWER_TYPES:
                
                option_to_use = 'media_viewer_uses_its_own_audio_volume'
                volume_type = AUDIO_MEDIA_VIEWER
                
            else:
                
                option_to_use = 'preview_uses_its_own_audio_volume'
                volume_type = AUDIO_PREVIEW
                
            
            self._specific_mute = AudioMuteButton( self, volume_type )
            
            self._specific_mute.setToolTip( ClientGUIFunctions.WrapToolTip( 'Mute/unmute: {}'.format( CC.canvas_type_str_lookup[ self._canvas_type ] ) ) )
            
            if CG.client_controller.new_options.GetBoolean( option_to_use ):
                
                slider_volume_type = volume_type
                
            else:
                
                slider_volume_type = AUDIO_GLOBAL
                
            
            self._volume = VolumeSlider( self, slider_volume_type )
            
            vbox = QP.VBoxLayout()
            
            if self._direction == 'down':
                
                QP.AddToLayout( vbox, self._specific_mute, CC.FLAGS_CENTER )
                QP.AddToLayout( vbox, self._volume, CC.FLAGS_CENTER )
                
            else:
                
                QP.AddToLayout( vbox, self._volume, CC.FLAGS_CENTER )
                QP.AddToLayout( vbox, self._specific_mute, CC.FLAGS_CENTER )
                
            
            #vbox.setAlignment( self._volume, QC.Qt.AlignmentFlag.AlignHCenter )
            #vbox.setAlignment( self._specific_mute, QC.Qt.AlignmentFlag.AlignHCenter )
            
            self.setLayout( vbox )
            
            self.hide()
            
            self.adjustSize()
            
            CG.client_controller.sub( self, 'NotifyNewOptions', 'notify_new_options' )
            
        
        def DoReposition( self ):
            
            parent = self.parentWidget()
            
            if not parent.isVisible():
                
                self.hide()
                
                return
                
            
            horizontal_offset = ( self.width() - parent.width() ) // 2 
            
            if self._direction == 'down':
                
                pos = parent.mapToGlobal( parent.rect().bottomLeft() )
                
            else:
                
                pos = parent.mapToGlobal( parent.rect().topLeft() - self.rect().bottomLeft() )
                
            
            pos.setX( pos.x() - horizontal_offset )
            
            self.move( pos )
            
        
        def DoShowHide( self ):
            
            self.DoReposition()
            
            parent = self.parentWidget()
            
            if not parent.isVisible():
                
                self.hide()
                
                return
                
            
            over_parent = ClientGUIFunctions.MouseIsOverWidget( parent ) and parent.isEnabled()
            over_me = ClientGUIFunctions.MouseIsOverWidget( self )
            
            should_show = over_parent
            should_hide = not ( over_parent or over_me )
            
            if should_show:
                
                self.show()
                
            elif should_hide:
                
                self.hide()
                
            
        
        def leaveEvent( self, event ):
            
            if self.isVisible():
                
                self.DoShowHide()
                
            
            event.ignore()
            
        
        def NotifyNewOptions( self ):
            
            if self._canvas_type in CC.CANVAS_MEDIA_VIEWER_TYPES:
                
                option_to_use = 'media_viewer_uses_its_own_audio_volume'
                volume_type = AUDIO_MEDIA_VIEWER
                
            else:
                
                option_to_use = 'preview_uses_its_own_audio_volume'
                volume_type = AUDIO_PREVIEW
                
            
            if CG.client_controller.new_options.GetBoolean( option_to_use ):
                
                slider_volume_type = volume_type
                
            else:
                
                slider_volume_type = AUDIO_GLOBAL
                
            
            if slider_volume_type != self._volume.GetVolumeType():
                
                self._volume.SetVolumeType( slider_volume_type )
                
            
        
    
class VolumeSlider( QW.QSlider ):
    
    def __init__( self, parent, volume_type ):
        
        super().__init__( parent )
        
        self._volume_type = volume_type
        
        self.setOrientation( QC.Qt.Orientation.Vertical )
        self.setTickInterval( 1 )
        self.setTickPosition( QW.QSlider.TickPosition.TicksBothSides )
        self.setRange( 0, 100 )
        
        volume = self._GetCorrectValue()
        
        self.setValue( volume )
        
        self.valueChanged.connect( self._VolumeSliderMoved )
        
    
    def _GetCorrectValue( self ):
        
        ( mute_option_name, volume_option_name ) = volume_types_to_option_names[ self._volume_type ]
        
        return CG.client_controller.new_options.GetInteger( volume_option_name )
        
    
    def _VolumeSliderMoved( self ):
        
        ChangeVolume( self._volume_type, self.value() )
        
    
    def GetVolumeType( self ):
        
        return self._volume_type
        
    
    def SetVolumeType( self, volume_type ):
        
        self._volume_type = volume_type
        
        volume = self._GetCorrectValue()
        
        self.setValue( volume )
        
    
    def UpdateMute( self ):
        
        volume = self._GetCorrectValue()
        
        self.setValue( volume )
        
    
