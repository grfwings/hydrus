from qtpy import QtCore as QC

try:
    
    from qtpy import QtCharts as QCh
    
    QT_CHARTS_OK = True
    
    class BarChartBandwidthHistory( QCh.QtCharts.QChartView ):
        
        def __init__( self, parent, monthly_usage ):
            
            super().__init__( parent )
            
            divisor = 1.0
            unit = 'B'
            
            highest_usage = max( ( m[1] for m in monthly_usage ) )
            
            lines = [ ( 1073741824.0, 'GB' ), ( 1048576.0, 'MB' ), ( 1024.0, 'KB' ) ]
            
            for ( line_divisor, line_unit ) in lines:
                
                if highest_usage > line_divisor:
                    
                    divisor = line_divisor
                    unit = line_unit
                    
                    break
                    
                
            
            monthly_usage = [ ( month_str, month_value / divisor ) for ( month_str, month_value ) in monthly_usage ]
            
            ( month_strs, month_values ) = zip( *monthly_usage )
            
            bar_set = QCh.QtCharts.QBarSet( 'Bandwidth' )
            x_category_axis = QCh.QtCharts.QBarCategoryAxis()
            
            bar_set.append( month_values )
            x_category_axis.append( month_strs )
            x_category_axis.setLabelsAngle( 90 )
            
            y_value_axis = QCh.QtCharts.QValueAxis()
            
            y_value_axis.setRange( 0.0, ( highest_usage * 1.2 ) / line_divisor )
            
            y_value_axis.setLabelFormat( '%i{}'.format( unit ) )
            
            y_value_axis.applyNiceNumbers()
            
            bar_series = QCh.QtCharts.QBarSeries()
            
            bar_series.append( bar_set )
            
            chart = QCh.QtCharts.QChart()
            
            chart.addSeries( bar_series )
            chart.addAxis( x_category_axis, QC.Qt.AlignmentFlag.AlignBottom )
            chart.addAxis( y_value_axis, QC.Qt.AlignmentFlag.AlignLeft )
            
            chart.legend().setVisible( False )
            
            bar_series.attachAxis( x_category_axis )
            bar_series.attachAxis( y_value_axis )
            
            self.setChart( chart )
            
        
    
    class FileHistory( QCh.QtCharts.QChartView ):
        
        def __init__( self, parent, file_history: dict, show_current: bool, show_inbox: bool, show_archive: bool, show_deleted: bool ):
            
            super().__init__( parent )
            
            self._file_history = file_history
            self._show_current = show_current
            self._show_inbox = show_inbox
            self._show_archive = show_archive
            self._show_deleted = show_deleted
            
            # this lad takes ms timestamp, not s, so * 1000
            # note you have to give this floats for the ms or it throws a type problem of big number to C long
            
            self._current_files_series = QCh.QtCharts.QLineSeries()
            
            self._current_files_series.setName( 'all files' )
            
            self._max_num_files_current = 0
            
            for ( timestamp, num_files ) in self._file_history[ 'current' ]:
                
                self._current_files_series.append( timestamp * 1000.0, num_files )
                
                self._max_num_files_current = max( self._max_num_files_current, num_files )
                
            
            #
            
            self._deleted_files_series = QCh.QtCharts.QLineSeries()
            
            self._deleted_files_series.setName( 'deleted' )
            
            self._max_num_files_deleted = 0
            
            for ( timestamp, num_files ) in self._file_history[ 'deleted' ]:
                
                self._deleted_files_series.append( timestamp * 1000.0, num_files )
                
                self._max_num_files_deleted = max( self._max_num_files_deleted, num_files )
                
            
            #
            
            self._inbox_files_series = QCh.QtCharts.QLineSeries()
            
            self._inbox_files_series.setName( 'inbox' )
            
            self._max_num_files_inbox = 0
            
            for ( timestamp, num_files ) in self._file_history[ 'inbox' ]:
                
                self._inbox_files_series.append( timestamp * 1000.0, num_files )
                
                self._max_num_files_inbox = max( self._max_num_files_inbox, num_files )
                
            
            #
            
            self._archive_files_series = QCh.QtCharts.QLineSeries()
            
            self._archive_files_series.setName( 'archive' )
            
            self._max_num_files_archive = 0
            
            for ( timestamp, num_files ) in self._file_history[ 'archive' ]:
                
                self._archive_files_series.append( timestamp * 1000.0, num_files )
                
                self._max_num_files_archive = max( self._max_num_files_archive, num_files )
                
            
            # takes ms since epoch
            self._x_datetime_axis = QCh.QtCharts.QDateTimeAxis()
            
            self._x_datetime_axis.setTickCount( 25 )
            self._x_datetime_axis.setLabelsAngle( 90 )
            
            self._x_datetime_axis.setFormat( 'yyyy-MM-dd' )
            
            self._y_value_axis = QCh.QtCharts.QValueAxis()
            
            self._y_value_axis.setLabelFormat( '%\'i' )
            
            self._chart = QCh.QtCharts.QChart()
            
            self._chart.addAxis( self._x_datetime_axis, QC.Qt.AlignmentFlag.AlignBottom )
            self._chart.addAxis( self._y_value_axis, QC.Qt.AlignmentFlag.AlignLeft )
            
            self._chart.addSeries( self._current_files_series )
            self._chart.addSeries( self._inbox_files_series )
            self._chart.addSeries( self._archive_files_series )
            self._chart.addSeries( self._deleted_files_series )
            
            self._current_files_series.attachAxis( self._x_datetime_axis )
            self._current_files_series.attachAxis( self._y_value_axis )
            
            self._inbox_files_series.attachAxis( self._x_datetime_axis )
            self._inbox_files_series.attachAxis( self._y_value_axis )
            
            self._archive_files_series.attachAxis( self._x_datetime_axis )
            self._archive_files_series.attachAxis( self._y_value_axis )
            
            self._deleted_files_series.attachAxis( self._x_datetime_axis )
            self._deleted_files_series.attachAxis( self._y_value_axis )
            
            self._RedrawLines()
            
            self.setChart( self._chart )
            
        
        def _CalculateYRange( self ):
            
            max_num_files = 1
            
            if self._show_current:
                
                max_num_files = max( self._max_num_files_current, max_num_files )
                
            
            if self._show_inbox:
                
                max_num_files = max( self._max_num_files_inbox, max_num_files )
                
            
            if self._show_archive:
                
                max_num_files = max( self._max_num_files_archive, max_num_files )
                
            
            if self._show_deleted:
                
                max_num_files = max( self._max_num_files_deleted, max_num_files )
                
            
            self._y_value_axis.setRange( 0, max_num_files )
            
            self._y_value_axis.applyNiceNumbers()
            
        
        def _RedrawLines( self ):
            
            self._current_files_series.setVisible( self._show_current )
            self._inbox_files_series.setVisible( self._show_inbox )
            self._archive_files_series.setVisible( self._show_archive )
            self._deleted_files_series.setVisible( self._show_deleted )
            
            self._CalculateYRange()
            
        
        def FlipAllVisible( self ):
            
            self._show_current = not self._show_current
            
            self._RedrawLines()
            
        
        def FlipArchiveVisible( self ):
            
            self._show_archive = not self._show_archive
            
            self._RedrawLines()
            
        
        def FlipDeletedVisible( self ):
            
            self._show_deleted = not self._show_deleted
            
            self._RedrawLines()
            
        
        def FlipInboxVisible( self ):
            
            self._show_inbox = not self._show_inbox
            
            self._RedrawLines()
            
        
    
except:
    
    QT_CHARTS_OK = False
    
