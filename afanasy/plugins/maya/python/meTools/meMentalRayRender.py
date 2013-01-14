"""
  meMentalRayRender

  ver.0.3.9 13 Jan 2013
    - added support for deferred .mi generation
    - fixed handling of image names and padding

  ver.0.3.8 27 Dec 2012
    - job specific functions moved to mrayJob class
    - backburner support dropped (temporary)
    - enchanced Afanasy jobs support
    - prepared support for deferred .mi generation

  ver.0.3.7 22 Aug 2012
    - backburner specific control fields are moved
      to corresponded tab, some unused parameters removed

  ver.0.3.6 9 Jul 2012
    - attempt to add Afanasy support

  ver.0.3.5 21 Mar 2012
  ver.0.3.4 16 Mar 2012
  ver.0.3.3 18 Nov 2011
  ver.0.3.1 14 Nov 2011

  Author:

  Yuri Meshalkin (aka mesh)
  mesh@kpp.kiev.ua

  (c) Kiev Post Production 2011

  Description:

  This UI script generates .mi files from open Maya scene
  and submits them to mentalray Standalone directly or by
  creating a job for backburner or Afanasy.

  "Use Remote Render" mode allows you to submit backburner job
  from your local OS to render-farm with other OS (e.g. linux)
  by using Directory Mapping.


  Usage:

  import meTools.meMentalRayRender as mr
  reload( mr ) # for debugging purposes
  mr = mr.meMentalRayRender()

  For using with Afanasy, add %AF_ROOT%\plugins\maya\python to %PYTHONPATH%
"""

import sys, os, string
import maya.OpenMaya as OpenMaya
from functools import partial
import maya.cmds as cmds
import maya.mel as mel

from mrayJob import MentalRayJob, MentalRayAfanasyJob  #, MentalRayBackburnerJob

self_prefix = 'meMentalRayRender_'
meMentalRayRenderVer = '0.3.9'
meMentalRayRenderMainWnd = self_prefix + 'MainWnd'
#
# meMentalRayRender
#
class meMentalRayRender( object ):
  #
  #
  #
  def __init__( self, selection='' ):
    #print ">> meMentalRayRender: Class created"
    self.selection = selection
    self.winMain = ''

    self.os = sys.platform
    if self.os.startswith('linux') : self.os = 'linux'
    elif self.os == 'darwin' : self.os = 'mac'
    elif self.os == 'win32' : self.os = 'win'

    print 'sys.platform = %s self.os = %s' % ( sys.platform, self.os )
    self.rootDir = cmds.workspace( q=True, rootDirectory=True )
    self.rootDir = self.rootDir[:-1]

    self.job = None
    self.job_param = {}
    self.mi_param = {}
    self.mr_param = {}
    self.img_param = {}
    self.afanasy_param = {}
    self.bkburn_param = {}

    self.migenCommand = 'Mayatomr -miStream'
    self.def_migenCommand = 'Render -r mi'
    self.def_scene_name = '' # maya scene name used for deferred .mi generation

    self.initParameters()
    self.ui=self.setupUI()
  #
  #
  #def __del__( self ): print( ">> meMentalRayRender: Class deleted" )
  #
  #
  def initParameters( self ):
    #
    # Job parameters
    #
    self.job_param['job_dispatcher'] = self.getDefaultStrValue( 'job_dispatcher', 'afanasy' )

    self.job_param['job_name'] = self.getMayaSceneName()
    self.job_param['job_description'] = self.getDefaultStrValue( 'job_description', '' )

    self.job_param['job_animation'] = self.getDefaultIntValue( 'job_animation', 1 ) is 1
    self.job_param['job_start'] = self.getDefaultIntValue( 'job_start', 1 )
    self.job_param['job_end'] = self.getDefaultIntValue( 'job_end', 100 )
    self.job_param['job_step'] = self.getDefaultIntValue( 'job_step', 1 )
    self.job_param['job_size'] = self.getDefaultIntValue( 'job_size', 1 )
    self.job_param['job_paused'] = self.getDefaultIntValue( 'job_paused', 1 ) is 1
    self.job_param['job_priority'] = self.getDefaultIntValue( 'job_priority', 50 )

    self.job_param['job_cleanup_mi'] = self.getDefaultIntValue( 'job_cleanup_rib', 0 ) is 1
    self.job_param['job_cleanup_script'] = self.getDefaultIntValue( 'job_cleanup_script', 0 ) is 1

    #
    # .mi generation parameters
    #
    self.mi_param['mi_reuse'] = self.getDefaultIntValue( 'mi_reuse', 1 ) is 1
    #self.mi_param['mi_dir'] = self.getDefaultStrValue( 'mi_dir', 'mi' )
    self.mi_param['mi_filename'] = 'mi/' + self.getMayaSceneName() + '.mi' # self.getDefaultStrValue( 'mi_filename',
    self.mi_param['mi_padding'] = self.getDefaultIntValue( 'mi_padding', 4 )

    self.mi_param['mi_perframe'] = self.getDefaultIntValue( 'mi_perframe', 1 ) is 1
    self.mi_param['mi_selection'] = self.getDefaultIntValue( 'mi_selection', 0 ) is 1
    self.mi_param['mi_filepaths'] = self.getDefaultStrValue( 'mi_filepaths', 'Relative' )
    #self.mi_param['mi_compression'] = self.getDefaultStrValue( 'mi_compression', 'Off' )
    #self.mi_param['mi_fileformat'] = self.getDefaultStrValue( 'mi_fileformat', 'ASCII' )
    self.mi_param['mi_binary'] = self.getDefaultIntValue( 'mi_binary', 0 ) is 1
    self.mi_param['mi_tabstop'] = self.getDefaultIntValue( 'mi_tabstop', 2 )
    self.mi_param['mi_verbosity'] = self.getDefaultStrValue( 'mi_verbosity', 'none' )

    self.mi_param['mi_deferred'] = self.getDefaultIntValue( 'mi_deferred', 0 ) is 1
    self.mi_param['mi_local_migen'] = self.getDefaultIntValue( 'mi_local_migen', 1 ) is 1
    self.mi_param['mi_def_task_size'] = self.getDefaultIntValue( 'mi_def_task_size', 4 )
    #
    # mentalray parameters
    #
    self.mr_param['mr_options'] = self.getDefaultStrValue( 'mr_options', '' )
    self.mr_param['mr_verbosity'] = self.getDefaultStrValue( 'mr_verbosity', 'none' )

    self.mr_param['mr_progress_frequency'] = self.getDefaultIntValue( 'mr_progress_frequency', 1 )
    self.mr_param['mr_threads'] = self.getDefaultIntValue( 'mr_threads', 4 )
    self.mr_param['mr_texture_continue'] = self.getDefaultIntValue( 'mr_texture_continue', 1 )
    #
    # image parameters
    #
    self.img_param['img_filename'] = self.getImageFileNamePrefix()
    self.img_param['img_format'] = self.getImageFormat()
    #
    # Afanasy parameters
    #
    self.afanasy_param['af_capacity'] = self.getDefaultIntValue( 'af_capacity', 1000 )
    self.afanasy_param['af_deferred_capacity'] = self.getDefaultIntValue( 'af_deferred_capacity', 1000 )
    self.afanasy_param['af_use_var_capacity'] = self.getDefaultIntValue( 'af_use_var_capacity', 0 ) is 1
    self.afanasy_param['af_cap_min'] = self.getDefaultFloatValue( 'af_cap_min', 1.0 )
    self.afanasy_param['af_cap_max'] = self.getDefaultFloatValue( 'af_cap_max', 1.0 )
    self.afanasy_param['af_max_running_tasks'] = self.getDefaultIntValue( 'af_max_running_tasks', -1 )
    self.afanasy_param['af_max_tasks_per_host'] = self.getDefaultIntValue( 'af_max_tasks_per_host', -1 )
    self.afanasy_param['af_service'] = self.getDefaultStrValue( 'af_service', 'mentalray' )
    self.afanasy_param['af_deferred_service'] = self.getDefaultStrValue( 'af_deferred_service', 'mayatomr' )
    self.afanasy_param['af_os'] = self.getDefaultStrValue( 'af_os', '' ) #linux mac windows
    # Hosts Mask - Job run only on renders which host name matches this mask.
    self.afanasy_param['af_hostsmask'] = self.getDefaultStrValue( 'af_hostsmask', '.*' )
    # Exclude Hosts Mask - Job can not run on renders which host name matches this mask.
    self.afanasy_param['af_hostsexcl'] = self.getDefaultStrValue( 'af_hostsexcl', '' )
    # Depend Mask - Job will wait other user jobs which name matches this mask.
    self.afanasy_param['af_depmask'] = self.getDefaultStrValue( 'af_depmask', '' )
    # Global Depend Mask - Job will wait other jobs from any user which name matches this mask.
    self.afanasy_param['af_depglbl'] = self.getDefaultStrValue( 'af_depglbl', '' )
    #self.afanasy_param['af_consolidate_subtasks'] = self.getDefaultIntValue( 'af_consolidate_subtasks', 1 ) is 1

    #
    # backburner parameters
    #
    """
    cmdjob_path = '/usr/discreet/backburner/cmdjob'

    if self.os == 'win': cmdjob_path = 'C:/Program Files (x86)/Autodesk/Backburner/cmdjob.exe'

    self.bkburn_param['bkburn_cmdjob_path'] = self.getDefaultStrValue( 'bkburn_cmdjob_path', cmdjob_path )

    self.bkburn_param['bkburn_manager'] = self.getDefaultStrValue( 'bkburn_manager', 'burn01' )
    self.bkburn_param['bkburn_server_list'] = self.getDefaultStrValue( 'bkburn_server_list', '' )
    self.bkburn_param['bkburn_server_group'] = self.getDefaultStrValue( 'bkburn_server_group', 'MRS_391_LIN' )
    self.bkburn_param['bkburn_server_count'] = self.getDefaultIntValue( 'bkburn_server_count', 0 )

  # UNUSED START
    #self.bkburn_param['bkburn_port'] = self.getDefaultIntValue( 'bkburn_port', 0 )
    #self.bkburn_param['bkburn_workpath'] = self.getDefaultIntValue( 'bkburn_workpath', 0 ) is 1
    #self.bkburn_param['bkburn_create_log'] = self.getDefaultIntValue( 'bkburn_create_log', 0 ) is 1
    #tmp_path = '/var/tmp'
    #if self.os == 'win': tmp_path = 'C:/TEMP'
    #self.bkburn_param['bkburn_log_dir'] = self.getDefaultStrValue( 'bkburn_log_dir', tmp_path )
    #self.bkburn_param['bkburn_create_tasklist'] = self.getDefaultIntValue( 'bkburn_create_tasklist', 0 ) is 1
    #self.bkburn_param['bkburn_tasklist'] = self.getDefaultStrValue( 'bkburn_tasklist', tmp_path + '/tasklist.txt' )

    #self.bkburn_param['bkburn_use_jobParamFile'] = self.getDefaultIntValue( 'bkburn_use_jobParamFile', 0 ) is 1
    #self.bkburn_param['bkburn_jobParamFile'] = self.getDefaultStrValue( 'bkburn_jobParamFile', tmp_path + '/jobParamFile.txt' )
  # UNUSED START
    self.job_param['job_use_remote'] = self.getDefaultIntValue( 'job_use_remote', 0 ) is 1
    self.job_param['job_dirmap_from'] = self.getDefaultStrValue( 'job_dirmap_from', '//openfiler/fc.raid.PROJECTS' )
    self.job_param['job_dirmap_to'] = self.getDefaultStrValue( 'job_dirmap_to', '/hosts/OPENFILER/mnt/fc/raid/PROJECTS' )
    """
#
# Renderer params
#
    mr_renderer_path = '/usr/autodesk/mrstand3.9.1-adsk2012-x64/bin/ray'

    if self.os == 'win': mr_renderer_path = 'C:/Autodesk/mrstand3.9.1-adsk2012/bin/ray.exe'
    elif self.os == 'mac': mr_renderer_path = '/Applications/Autodesk/mrstand3.9.1-adsk2012/bin/ray'

    self.mr_param['mr_renderer_local'] = self.getDefaultStrValue( 'mr_renderer_local', mr_renderer_path )
    self.mr_param['mr_renderer_remote'] = self.getDefaultStrValue( 'mr_renderer_remote', '/usr/autodesk/mrstand3.9.1-adsk2012-x64/bin/cmdray.sh' )
    self.mr_param['mr_root_as_param'] = self.getDefaultIntValue( 'mr_root_as_param', 0 ) is 1

  #
  # getDefaultStrValue
  #
  def getDefaultStrValue( self, name, value ):
    name = self_prefix + name
    if cmds.optionVar( exists=name ) == 1:
      ret = cmds.optionVar( q=name )
    else:
      cmds.optionVar( sv=( name, value) )
      ret = value
    return ret
  #
  # getDefaultIntValue
  #
  def getDefaultIntValue( self, name, value ):
    name = self_prefix + name
    if cmds.optionVar( exists=name ) == 1:
      ret = cmds.optionVar( q=name )
    else:
      cmds.optionVar( iv=( name, value) )
      ret = value
    return ret
  #
  # getDefaultFloatValue
  #
  def getDefaultFloatValue( self, name, value ):
    name = self_prefix + name
    if cmds.optionVar( exists=name ) == 1:
      ret = cmds.optionVar( q=name )
    else:
      cmds.optionVar( fv=( name, value) )
      ret = value
    return ret
  #
  # setDefaultIntValue
  #
  def setDefaultIntValue( self, name, value=None ):
    name = self_prefix + name
    cmds.optionVar( iv=( name, value) )
    return value
  #
  # setDefaultIntValue2
  #
  def setDefaultIntValue2( self, names, value1=None, value2=None ):
    name = self_prefix + names[0]
    cmds.optionVar( iv=( name, value1) )
    name = self_prefix + names[1]
    cmds.optionVar( iv=( name, value2) )
    return (value1, value2)
  #
  # setDefaultIntValue3
  #
  def setDefaultIntValue3( self, names, value1=None, value2=None, value3=None ):
    name = self_prefix + names[0]
    cmds.optionVar( iv=( name, value1) )
    name = self_prefix + names[1]
    cmds.optionVar( iv=( name, value2) )
    name = self_prefix + names[2]
    cmds.optionVar( iv=( name, value3) )
    return (value1, value2, value3)
  #
  # setDefaultFloatValue
  #
  def setDefaultFloatValue( self, name, value=None ):
    name = self_prefix + name
    cmds.optionVar( fv=( name, value) )
    return value
  #
  # setDefaultFloatValue2
  #
  def setDefaultFloatValue2( self, names, value1=None, value2=None ):
    name = self_prefix + names[0]
    cmds.optionVar( fv=( name, value1) )
    name = self_prefix + names[1]
    cmds.optionVar( fv=( name, value2) )
    return (value1, value2)
  #
  # setDefaultStrValue
  #
  def setDefaultStrValue( self, name, value ):
    name = self_prefix + name
    cmds.optionVar( sv=( name, value) )
    return value
  #
  # getMayaSceneName
  #
  def getMayaSceneName( self ):
    fullName=cmds.file( q=True, sceneName=True )
    sceneName = os.path.basename( fullName )
    (sceneName, ext) = os.path.splitext( sceneName )
    if sceneName == '' : sceneName='untitled'
    return sceneName
  #
  #
  #
  def getImageFileNamePrefix( self ):
    fileNamePrefix = cmds.getAttr( 'defaultRenderGlobals.imageFilePrefix' )
    if fileNamePrefix == None or fileNamePrefix == '' :
      fileNamePrefix = self.getMayaSceneName()
    return fileNamePrefix
  #
  # getImageFormat
  #
  def getImageFormat( self ):
    imageFormatStr = ''
    format_idx = cmds.getAttr( 'defaultRenderGlobals.imageFormat' )
    if format_idx == 0 : # Gif
      imageFormatStr = 'iff'
    elif format_idx == 1: # Softimage (pic)
      imageFormatStr = 'pic'
    elif format_idx == 2: # Wavefront (rla)
      imageFormatStr = 'rla'
    elif format_idx == 3 : # Tiff
      imageFormatStr = 'tif'
    elif format_idx == 4 : # Tiff16
      imageFormatStr = 'iff'
    elif format_idx == 5 : # SGI (rgb)
      imageFormatStr = 'rgb'
    elif format_idx == 6 : # Alias (pix)
      imageFormatStr = 'pix'
    elif format_idx == 7 : # Maya IFF (iff)
      imageFormatStr = 'iff'
    elif format_idx == 8 : # JPEG (jpg)
      imageFormatStr = 'jpg'
    elif format_idx == 9 : # EPS (eps)
      imageFormatStr = 'eps'
    elif format_idx == 10 : # Maya 16 IFF (iff)
      imageFormatStr = 'iff'
    elif format_idx == 11 : # Cineon
      imageFormatStr = 'iff'
    elif format_idx == 12 : # Quantel PAL (yuv)
      imageFormatStr = 'yuv'
    elif format_idx == 13 : # SGI 16
      imageFormatStr = 'iff'
    elif format_idx == 19 : # Targa (tga)
      imageFormatStr = 'tga'
    elif format_idx == 20 : # Windows Bitmap (bmp)
      imageFormatStr = 'bmp'
    elif format_idx == 21 : # SGI Movie
      imageFormatStr = 'iff'
    elif format_idx == 22 : # Quicktime
      imageFormatStr = 'iff'
    elif format_idx == 23 : # AVI
      imageFormatStr = 'iff'
    elif format_idx == 30 : # MacPaint
      imageFormatStr = 'iff'
    elif format_idx == 31 : # PSD
      imageFormatStr = 'psd'
    elif format_idx == 32 : # PNG
      imageFormatStr = 'png'
    elif format_idx == 33 : # QuickDraw
      imageFormatStr = 'iff'
    elif format_idx == 34 : # QuickTime Image
      imageFormatStr = 'iff'
    elif format_idx == 35 : # DDS
      imageFormatStr = 'iff'
    elif format_idx == 36 : # PSD Layered
      imageFormatStr = 'psd'
    elif format_idx == 50 : # IMF plugin
      imageFormatStr = 'iff'
    elif format_idx == 51 : # Custom Image Format
      imageFormatStr = 'tif'
    elif format_idx == 60 : # Macromedia SWF (swf)
      imageFormatStr = 'iff'
    elif format_idx == 61 : # Adobe Illustrator (ai)
      imageFormatStr = 'iff'
    elif format_idx == 62 : # SVG (svg)
      imageFormatStr = 'iff'
    elif format_idx == 63 : # Swift3DImporter (swft)
      imageFormatStr = 'iff'

    return imageFormatStr
  #
  # isRelative
  #
  def isRelative( self, fileName ):
    ret = True
    if fileName != '':
      if string.find( fileName, ':' ) == 1 or string.find( fileName, '/' ) == 0 or string.find( fileName, '\\' ) == 0:
        ret = False
    return ret
  #
  # checkShaders
  #
  def checkShaders( self, value ): mel.eval( "mrShaderManager" )
  #
  # checkTextures
  #
  def checkTextures( self, value ):
    import meTools.meCheckTexturePaths as tx
    #reload( tx )
    tx.meCheckTexturePaths()
  #
  # fromNativePath
  #
  def fromNativePath( self, nativePath ):
    return str(nativePath).replace( '\\', '/')
  #
  # browseDirectory
  #
  def browseDirectory( self, control ):
    path = cmds.textFieldButtonGrp( control, q=True, text=True )
    startDir = path
    if self.isRelative( path ) :
      startDir = os.path.join( self.rootDir, path )
    dirNames = cmds.fileDialog2( fileMode=3, startingDirectory=startDir, dialogStyle=1 ) #
    if dirNames is not None :
      dirName = cmds.workspace( projectPath=self.fromNativePath( dirNames[0] ) )
      #print ( "dirName = %s abspath = %s" ) % (dirNames[0], dirName)
      cmds.textFieldButtonGrp( control, e=True, text=dirName, forceChangeCommand=True )
  #
  # browseFile
  #
  def browseFile( self, control, extFilter ):
    path = cmds.textFieldButtonGrp( control, q=True, text=True )
    startDir = path
    if self.isRelative( path ) :
      startDir = os.path.join( self.rootDir, path )
    fileNames = cmds.fileDialog2( fileMode=1, startingDirectory=os.path.dirname( startDir ), dialogStyle=1, fileFilter=extFilter ) #
    if fileNames is not None :
      fileName = cmds.workspace( projectPath=self.fromNativePath( fileNames[0] ) )
      #print ( "dirName = %s abspath = %s" ) % (dirNames[0], dirName)
      cmds.textFieldButtonGrp( control, e=True, text=fileName, forceChangeCommand=True )
  #
  # validate_mi_FileName
  #
  def validate_mi_FileName( self, control, extFilter ):
    pass
  #
  # setup_dirmaps
  #
  def setupDirmaps ( self, enableDirmap=True, fromPath='', toPath='' ):
    #
    job = self.winMain + '|f0|t0|tc0|'
    dirmaps = cmds.dirmap( getAllMappings=True )

    for i in range( 0, len( dirmaps ), 2 ):
      print "unmapDirectory: %s %s" % (dirmaps[i], dirmaps[i+1])
      cmds.dirmap( unmapDirectory=dirmaps[i] )

    if enableDirmap:
      if fromPath != '' and toPath != '' :
        print "mapDirectory: %s to %s" % ( fromPath, toPath )
        cmds.dirmap( mapDirectory=( fromPath, toPath ) )

    cmds.dirmap( enable=enableDirmap )
  #
  # getDeferredCmd
  #
  def getDeferredCmd ( self  ) :
    gen_cmd = self.def_migenCommand + ' '
    gen_cmd += '-rd ' + '"' + self.rootDir + '"' + ' '
    #gen_cmd += '-im ' + '"images/' + self.getImageFileNamePrefix() + '"' + ' '
    #gen_cmd += '-of ' + self.getImageFormat() + ' '
    gen_cmd += self.get_migen_options()
    
    return gen_cmd
  #
  # getRenderCmd
  #
  def getRenderCmd ( self  ) :
    mray = self.winMain + '|f0|t0|tc2|fr1|fc1|'
    render_cmd = 'ray'
    options = str( cmds.textFieldGrp( mray + 'mr_options', q=True, text=True )).strip()
    mr_threads = cmds.intFieldGrp( mray + 'mr_threads', q=True, value1=True )

    mr_verbosity_level = cmds.optionMenuGrp( mray + 'mr_verbosity', q=True, sl=True ) - 1
    mr_progress_frequency = cmds.intFieldGrp( mray + 'mr_progress_frequency', q=True, value1=True )
    mr_texture_continue = cmds.checkBoxGrp( mray + 'mr_texture_continue', q=True, value1=True )

    if mr_verbosity_level < 5: mr_verbosity_level = 5
    if mr_progress_frequency == 0 : mr_progress_frequency = 1

    cmd = render_cmd + ' '
    if mr_verbosity_level != 0 : cmd += '-v ' + str( mr_verbosity_level ) + ' '
    if mr_progress_frequency != 0 : cmd += '-progress_frequency ' + str( mr_progress_frequency ) + ' '
    if mr_threads != 0 : cmd += '-threads ' + str( mr_threads ) + ' '
    if mr_texture_continue != 0 : cmd += '-texture_continue on'  + ' '
    
    cmd += '-file_dir "' + str( self.rootDir ) + '/images/" '
    #cmd += '-file_name "' + self.getImageFileNamePrefix() + '" ' 
    #cmd += '-file_type ' + self.getImageFormat() + ' '

    cmd += options
    return cmd
  #
  #
  #
  def get_mi_file_names ( self ) :
    mi = self.winMain + '|f0|t0|tc1|fr1|fc1|'

    mi_filename = cmds.textFieldGrp( mi + 'mi_filename', q=True, text=True )
    mi_perframe = cmds.checkBoxGrp( mi + 'mi_perframe', q=True, value1=True )
    mi_padding = cmds.intFieldGrp( mi + 'mi_padding', q=True, value1=True )
    pad_str = '#'
    if mi_padding > 0 and mi_perframe == True :
      for i in range( 1, mi_padding ):
        pad_str += '#'

    filename = cmds.workspace( expandName=mi_filename )
    (name, ext) = os.path.splitext( filename )
    #dot_pos = name.rfind('.')
    #miFileName = name[0:dot_pos] + '.' + ('@' + pad_str + '@') + '.mi'
    miFileName = name + '.' + ('@' + pad_str + '@') + '.mi'
    return miFileName
  #
  #
  #
  def get_image_names ( self ) :
    mi = self.winMain + '|f0|t0|tc1|fr1|fc1|'

    mi_perframe = cmds.checkBoxGrp( mi + 'mi_perframe', q=True, value1=True )
    mi_padding = cmds.intFieldGrp( mi + 'mi_padding', q=True, value1=True )
    pad_str = '#'
    if mi_padding > 0 and mi_perframe == True :
      for i in range( 1, mi_padding ):
        pad_str += '#'

    imageFileName = ''

    images = cmds.renderSettings( fullPath = True, genericFrameImageName = ('@' + pad_str + '@')  )
    imageFileName = ';'.join ( images )

    return self.fromNativePath( imageFileName )
  #
  # get_migen_options
  #
  def get_migen_options ( self ) :
    job = self.winMain + '|f0|t0|tc0|fr1|fc1|'
    mi = self.winMain + '|f0|t0|tc1|fr1|fc1|'
    mi_def = self.winMain + '|f0|t0|tc1|fr3|fc3|'
    
    animation = cmds.checkBoxGrp( job + 'job_animation', q=True, value1=True )
    start = cmds.intFieldGrp( job + 'job_range', q=True, value1=True )
    stop = cmds.intFieldGrp( job + 'job_range', q=True, value2=True )
    step = cmds.intFieldGrp( job + 'job_range', q=True, value3=True )

    mi_reuse = cmds.checkBoxGrp( mi + 'mi_reuse', q=True, value1=True )
    mi_selection = cmds.checkBoxGrp( mi + 'mi_selection', q=True, value1=True )

    mi_filename = cmds.textFieldGrp( mi + 'mi_filename', q=True, text=True )
    mi_padding = cmds.intFieldGrp( mi + 'mi_padding', q=True, value1=True )
    mi_perframe = cmds.checkBoxGrp( mi + 'mi_perframe', q=True, value1=True )
    mi_tabstop = cmds.intFieldGrp( mi + 'mi_tabstop', q=True, value1=True )
    mi_binary = cmds.checkBoxGrp( mi + 'mi_binary', q=True, value1=True )
    mi_filepaths = cmds.optionMenuGrp( mi + 'mi_filepaths', q=True, value=True )

    # mi_compression = cmds.optionMenuGrp( mi + 'mi_compression', q=True, value=True )
    # mi_verbosity_level = cmds.optionMenuGrp( mi + 'mi_verbosity', q=True, sl=True ) - 1
    
    filename = cmds.workspace( expandName=mi_filename )
    (filename, ext) = os.path.splitext( filename )
    if ext == '' or ext == '.' : ext = '.mi'
    filename += ext
    
    migen_cmd = '-file \"' + filename + '\" '
    
    #if mi_verbosity_level < 5 : mi_verbosity_level = 5
    #migen_cmd += '-v ' + str( mi_verbosity_level ) + ' '
    
    migen_cmd += '-perframe '
    if mi_perframe :
      migen_cmd += '2 ' # (name.#.ext)
      migen_cmd += '-padframe ' + str( mi_padding ) + ' '
    else:
      migen_cmd += '0 ' # (single .mi file)

    if mi_binary :
      migen_cmd += '-binary '
    else:
      migen_cmd += '-tabstop ' + str( mi_tabstop ) + ' '

    #migen_cmd += '-pcm ' # export pass contribition maps
    #migen_cmd += '-pud ' # export pass user data

    migen_cmd += '-exportPathNames nn'
    if mi_filepaths == 'Absolute' :
      migen_cmd += 'aaaaaaaa '
    elif mi_filepaths == 'Relative':
      migen_cmd += 'rrrrrrrr '
    else:
      migen_cmd += 'nnnnnnnn '

    if mi_selection : migen_cmd += '-active '
  
    return migen_cmd
  #
  # generate_mi
  #
  def generate_mi ( self, isSubmitingJob=False ):
    #
    job = self.winMain + '|f0|t0|tc0|fr1|fc1|'
    mi = self.winMain + '|f0|t0|tc1|fr1|fc1|'
    mi_def = self.winMain + '|f0|t0|tc1|fr3|fc3|'

    skipExport = False

    animation = cmds.checkBoxGrp( job + 'job_animation', q=True, value1=True )
    start = cmds.intFieldGrp( job + 'job_range', q=True, value1=True )
    stop = cmds.intFieldGrp( job + 'job_range', q=True, value2=True )
    step = cmds.intFieldGrp( job + 'job_range', q=True, value3=True )

    mi_reuse = cmds.checkBoxGrp( mi + 'mi_reuse', q=True, value1=True )
    mi_selection = cmds.checkBoxGrp( mi + 'mi_selection', q=True, value1=True )

    mi_filename = cmds.textFieldGrp( mi + 'mi_filename', q=True, text=True )
    mi_padding = cmds.intFieldGrp( mi + 'mi_padding', q=True, value1=True )
    mi_perframe = cmds.checkBoxGrp( mi + 'mi_perframe', q=True, value1=True )
    mi_tabstop = cmds.intFieldGrp( mi + 'mi_tabstop', q=True, value1=True )
    mi_binary = cmds.checkBoxGrp( mi + 'mi_binary', q=True, value1=True )
    mi_filepaths = cmds.optionMenuGrp( mi + 'mi_filepaths', q=True, value=True )

    # mi_compression = cmds.optionMenuGrp( mi + 'mi_compression', q=True, value=True )
    #mi_verbosity_level = cmds.optionMenuGrp( mi + 'mi_verbosity', q=True, sl=True ) - 1

    mi_deferred = cmds.checkBoxGrp( mi_def + 'mi_deferred', q=True, value1=True )

    filename = cmds.workspace( expandName=mi_filename )
    (filename, ext) = os.path.splitext( filename )
    if ext == '' or ext == '.' : ext = '.mi'
    filename += ext

    dirname = os.path.dirname( filename )
    if not os.path.exists( dirname ):
      print ( "path %s not exists" ) % dirname
      os.mkdir( dirname )

    # TODO!!! check if files are exist and have to be overriden
    if isSubmitingJob and mi_reuse:
      skipExport = True
      print "Skipping .mi files generation ..."

    if not skipExport:
      if not animation :
        start = stop = int( cmds.currentTime( q=True ) )
        step = 1
      #
      # save RenderGlobals
      #
      defGlobals = 'defaultRenderGlobals'
      saveGlobals = {}
      saveGlobals['animation'] = cmds.getAttr( defGlobals + '.animation' )
      saveGlobals['startFrame'] = cmds.getAttr( defGlobals + '.startFrame' )
      saveGlobals['endFrame'] = cmds.getAttr( defGlobals + '.endFrame' )
      saveGlobals['byFrameStep'] = cmds.getAttr( defGlobals + '.byFrameStep' )
      saveGlobals['extensionPadding'] = cmds.getAttr( defGlobals + '.extensionPadding' )
      saveGlobals['imageFilePrefix'] = str( cmds.getAttr( defGlobals + '.imageFilePrefix' ) )

      migen_cmd = self.migenCommand + ' ' + self.get_migen_options()

      print "migen_cmd = %s" % migen_cmd
      #
      # override RenderGlobals
      #
      cmds.setAttr( defGlobals + '.animation', True ) # True even for single frame, for proper image name
      cmds.setAttr( defGlobals + '.startFrame', start )
      cmds.setAttr( defGlobals + '.endFrame', stop )
      cmds.setAttr( defGlobals + '.byFrameStep', step )
      cmds.setAttr( defGlobals + '.extensionPadding', mi_padding ) # set images padding same as .mi
      
      image_name = self.getImageFileNamePrefix()

      if mi_deferred :
      # generate uniquie maya scene name and save it
      # with current render and .mi generation settings
        print 'Use deferred .mi generation'
        
        cmds.setAttr( defGlobals + '.imageFilePrefix', ( 'images/' + image_name ), type='string' )
        
        scene_name = self.getMayaSceneName() # get scene name without extension
        def_scene_name = scene_name + '_deferred'

        cmds.file( rename=def_scene_name )
        self.def_scene_name = cmds.file( save=True, de=True ) # save it with default extension
        cmds.file( rename=scene_name ) # rename scene back
        

      else :
        migen_cmd += '-pcm ' # export pass contribition maps
        migen_cmd += '-pud ' # export pass user data
        cmds.setAttr( defGlobals + '.imageFilePrefix', image_name, type='string' ) # will use MayaSceneName if empty
        
        mel.eval( migen_cmd )
      #
      # restore RenderGlobals
      #
      cmds.setAttr( defGlobals + '.animation', saveGlobals['animation'] )
      cmds.setAttr( defGlobals + '.startFrame', saveGlobals['startFrame'] )
      cmds.setAttr( defGlobals + '.endFrame', saveGlobals['endFrame'] )
      cmds.setAttr( defGlobals + '.byFrameStep', saveGlobals['byFrameStep'] )
      cmds.setAttr( defGlobals + '.extensionPadding', saveGlobals['extensionPadding'] )
      cmds.setAttr( defGlobals + '.imageFilePrefix', saveGlobals['imageFilePrefix'], type='string' )
  #
  # submitJob
  #
  def submitJob( self, param=None ):
    # print ">> meMentalRayRender: submitJob()"

    job = self.winMain + '|f0|t0|tc0|fr1|fc1|'
    #job2 = self.winMain + '|f0|t0|tc0|fr2|fc2|'
    mi = self.winMain + '|f0|t0|tc1|fr1|fc1|'
    mi_def = self.winMain + '|f0|t0|tc1|fr3|fc3|'
    mray = self.winMain + '|f0|t0|tc2|fr1|fc1|'
    af = self.winMain + '|f0|t0|tc3|fr1|fc1|'
    bkburn = self.winMain + '|f0|t0|tc4|fr1|fc1|'
    bkburn2 = self.winMain + '|f0|t0|tc4|fr2|fc2|'

    job_name = cmds.textFieldGrp( job + 'job_name', q=True, text=True )
    if job_name == '' : job_name = self.getMayaSceneName()
    job_description = cmds.textFieldGrp( job + 'job_description', q=True, text=True )

    mi_deferred = cmds.checkBoxGrp( mi_def + 'mi_deferred', q=True, value1=True )
    mi_local_migen = cmds.checkBoxGrp( mi_def + 'mi_local_migen', q=True, value1=True )
    mi_def_task_size = cmds.intFieldGrp( mi_def + 'mi_def_task_size', q=True, value1=True )
    mi_reuse = cmds.checkBoxGrp( mi + 'mi_reuse', q=True, value1=True )

    job_dispatcher = cmds.optionMenuGrp( job + 'job_dispatcher', q=True, value=True )

    if job_dispatcher == 'afanasy' :
      self.job = MentalRayAfanasyJob ( job_name, job_description )
      self.job.capacity = cmds.intFieldGrp( af + 'af_capacity', q=True, value1=True )
      self.job.deferred_capacity = cmds.intFieldGrp( af + 'af_deferred_capacity', q=True, value1=True )

      self.job.use_var_capacity = cmds.checkBoxGrp( af + 'af_use_var_capacity', q=True, value1=True )
      
      self.job.capacity_coeff_min = cmds.floatFieldGrp( af + 'af_var_capacity', q=True, value1=True )
      self.job.capacity_coeff_max = cmds.floatFieldGrp( af + 'af_var_capacity', q=True, value2=True )

      self.job.max_running_tasks = cmds.intFieldGrp( af + 'af_max_running_tasks', q=True, value1=True )
      self.job.max_tasks_per_host = cmds.intFieldGrp( af + 'af_max_tasks_per_host', q=True, value1=True )

      self.job.service = str( cmds.textFieldGrp( af + 'af_service', q=True, text=True )).strip()
      self.job.deferred_service = str( cmds.textFieldGrp( af + 'af_deferred_service', q=True, text=True )).strip()

      self.job.hostsmask = str( cmds.textFieldGrp( af + 'af_hostsmask', q=True, text=True )).strip()
      self.job.hostsexcl = str( cmds.textFieldGrp( af + 'af_hostsexcl', q=True, text=True )).strip()
      self.job.depmask = str( cmds.textFieldGrp( af + 'af_depmask', q=True, text=True )).strip()
      self.job.depglbl = str( cmds.textFieldGrp( af + 'af_depglbl', q=True, text=True )).strip()
      self.job.need_os = str( cmds.textFieldGrp( af + 'af_os', q=True, text=True )).strip()
    elif job_dispatcher == 'backburner' :
      print 'backburner not supported in this version'
      #self.job = MentalRayBackburnerJob ( job_name, job_description )
      return
    else :
      mi_deferred = False
      self.job = MentalRayJob ( job_name, job_description )

    self.job.work_dir = self.rootDir

    self.job.priority = cmds.intFieldGrp( job + 'job_priority', q=True, value1=True )
    self.job.paused = cmds.checkBoxGrp( job + 'job_paused', q=True, value1=True )

    self.job.task_size = cmds.intFieldGrp( job + 'job_size', q=True, value1=True )
    self.job.padding = cmds.intFieldGrp( mi + 'mi_padding', q=True, value1=True )

    self.job.animation = cmds.checkBoxGrp( job + 'job_animation', q=True, value1=True )
    self.job.start = cmds.intFieldGrp( job + 'job_range', q=True, value1=True )
    self.job.stop = cmds.intFieldGrp( job + 'job_range', q=True, value2=True )
    self.job.step = cmds.intFieldGrp( job + 'job_range', q=True, value3=True )

    self.generate_mi( True ) # isSubmitingJob=True

    if not self.job.animation :
      self.job.start = int( cmds.currentTime( q=True ) )
      self.job.stop = self.job.start
      self.job.step = 1

    if mi_deferred and not mi_reuse:
      self.job.use_gen_cmd = True
      gen_cmd = self.getDeferredCmd ()
      gen_cmd += ( ' -s @#@' ) 
      gen_cmd += ( ' -e @#@' ) 
      gen_cmd += ( ' -b ' + str( self.job.step ) ) 
                
      self.job.gen_cmd = gen_cmd
      self.job.gen_scene_name = self.def_scene_name 
      self.job.gen_task_size = mi_def_task_size
      self.job.use_local_gen = mi_local_migen
      
      print 'gen_cmd = %s %s' % ( self.job.gen_cmd, self.job.gen_scene_name )

    self.job.cmd = self.getRenderCmd ()
    self.job.mi_files = self.get_mi_file_names ()
    self.job.images = self.get_image_names ()

    self.job.begin ()
    self.job.frame_tasks ()
    self.job.end ()
  #
  #
  #
  def miFileNameChanged( self, name, value ):
    self.setDefaultStrValue( name, value )
    self.setResolvedPath()
  #
  #
  #
  def setResolvedPath( self ):
    mi = self.winMain + '|f0|t0|tc1|fr1|fc1|'
    mi2 = self.winMain + '|f0|t0|tc1|fr2|fc2|'
    mi_filename = cmds.textFieldGrp( mi + 'mi_filename', q=True, text=True )
    mi_padding = cmds.intFieldGrp( mi + 'mi_padding', q=True, value1=True )
    mi_perframe = cmds.checkBoxGrp( mi + 'mi_perframe', q=True, value1=True )

    filename = cmds.workspace( expandName=mi_filename )
    (filename, ext) = os.path.splitext( filename )
    if ext == '' or ext == '.' : ext = '.mi'

    if mi_padding > 0 and mi_perframe == True :
      filename += '.'
      pad_str = '#'
      for i in range( 1, mi_padding ): pad_str += '#'
      filename += pad_str
    filename += ext
    cmds.textFieldGrp( mi2 + 'mi_resolved_path', edit=True, text=filename )
  #
  # Open Maya Render Settings window
  #
  def maya_render_globals ( self, arg ) :
    mel.eval( "unifiedRenderGlobalsWindow" )
  #
  #
  #
  def enable_range ( self, arg ) :
    job = self.winMain + '|f0|t0|tc0|fr1|fc1|'
    self.setDefaultIntValue( 'job_animation', arg )
    cmds.intFieldGrp( job + 'job_range', edit = True, enable = arg )
  #
  #
  #
  def enable_var_capacity ( self, arg ) :
    af = self.winMain + '|f0|t0|tc3|fr1|fc1|'
    self.setDefaultIntValue( 'af_use_var_capacity', arg )
    cmds.floatFieldGrp( af + 'af_var_capacity', edit = True, enable = arg )
  #
  #
  #
  def enable_deferred ( self, arg ) :
    mi_def = self.winMain + '|f0|t0|tc1|fr3|fc3|'

    self.setDefaultIntValue( 'mi_deferred', arg )
    cmds.checkBoxGrp( mi_def + 'mi_local_migen', edit = True, enable = arg )
    cmds.intFieldGrp( mi_def + 'mi_def_task_size', edit = True, enable = arg )
  #
  # setupUI
  #
  def setupUI( self ):
    #print ">> meMentalRayRender: setupUI()"
    self.deleteUI( True )
    #
    # Main window setup
    #
    self.winMain = cmds.window( meMentalRayRenderMainWnd,
                                title='meMentalRayRender ver.' + meMentalRayRenderVer + ' (' + self.os + ')' ,
                                menuBar=True,
                                retain=False,
                                widthHeight=(420, 460) )

    self.mainMenu = cmds.menu( label="Commands", tearOff=False )
    cmds.menuItem( label='Render Globals ...', command = self.maya_render_globals )
    cmds.menuItem( label='Check Shaders ...', command=self.checkShaders )
    cmds.menuItem( label='Check Texture Paths ...', command=self.checkTextures )
    cmds.menuItem( label='Generate .mi', command=self.generate_mi )
    cmds.menuItem( label='Submit Job', command=self.submitJob )
    cmds.menuItem( divider=True )
    cmds.menuItem( label='Close', command=self.deleteUI )
    # cmds.menuItem( label='Render' )
    cw1 = 120
    cw2 = 60
    cw3 = 20
    mr_hi = 8

    form = cmds.formLayout( 'f0', numberOfDivisions=100 )
    proj = cmds.columnLayout( 'c0', columnAttach=('left',0), rowSpacing=2, adjustableColumn=True, height=32 )
    cmds.textFieldGrp( cw=( 1, 70 ), adj=2, label="Project Root ", text=self.rootDir, editable=False )
    cmds.setParent( '..' )
    #
    # setup tabs
    #
    tab = cmds.tabLayout( 't0', scrollable=True, childResizable=True )  # tabLayout -scr true -cr true  tabs; //
    #
    # Job tab
    #
    tab_job = cmds.columnLayout( 'tc0', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True ) # string $displayColumn = `columnLayout -cat left 0 -rs 0 -adj true displayTab`;
    cmds.frameLayout( 'fr1', label=' Parameters ', borderVisible=True, borderStyle='etchedIn', marginHeight=mr_hi  )
    cmds.columnLayout( 'fc1', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )
    #
    job_dispatcher = cmds.optionMenuGrp( 'job_dispatcher', cw=( (1, cw1), ), cal=(1, 'right'),
                        label="Job Dispatcher ",  enable=True,
                        cc=partial( self.setDefaultStrValue, 'job_dispatcher' ) )
    for name in ('none', 'afanasy' ): cmds.menuItem( label=name ) # 'backburner',
    cmds.optionMenuGrp( job_dispatcher, e=True, value=self.job_param['job_dispatcher'] )
    cmds.text( label='' )
    cmds.textFieldGrp( 'job_name', cw=( 1, cw1 ), adj=2, label="Job Name ", text=self.job_param['job_name'] )
    cmds.textFieldGrp( 'job_description', cw=( 1, cw1 ), adj=2,
                        label="Description ",
                        text=self.job_param['job_description'],
                        cc=partial( self.setDefaultStrValue, 'job_description' ) )
    cmds.checkBoxGrp( 'job_paused', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label="Start Paused ",
                      value1=self.job_param['job_paused'],
                      cc=partial( self.setDefaultIntValue, 'job_paused' ) )

    cmds.text( label='' )

    cmds.checkBoxGrp( 'job_animation', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label="Animation ",
                      value1=self.job_param['job_animation'],
                      cc=partial( self.enable_range ) )

    cmds.intFieldGrp( 'job_range', cw=( (1, cw1), (2, cw2), (3, cw2), (4, cw2) ), nf=3, label="Start/Stop/By ",
                       value1=self.job_param['job_start'],
                       value2=self.job_param['job_end'],
                       value3=self.job_param['job_step'],
                        enable = self.job_param['job_animation'],
                       cc=( partial( self.setDefaultIntValue3, ('job_start', 'job_end', 'job_step') ) ) )


    cmds.intFieldGrp( 'job_size', cw=( (1, cw1), (2, cw2) ),
                      label="Task Size ",
                      ann="Should be smaller then number of frames to render",
                      value1=self.job_param['job_size'],
                      cc=partial( self.setDefaultIntValue, 'job_size' ) )

    cmds.intFieldGrp( 'job_priority', cw=( (1, cw1), (2, cw2) ),
                      label="Priority ",
                      value1=self.job_param['job_priority'],
                      cc=partial( self.setDefaultIntValue, 'job_priority' ) )
    #cmds.text( label='' )
    #
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.frameLayout( 'fr2', label=' Cleanup ', borderVisible=True, borderStyle='etchedIn', marginHeight=mr_hi, cll=True, cl=True  )
    cmds.columnLayout( 'fc2', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )

    cmds.checkBoxGrp( 'job_cleanup_mi', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label='', label1=' .mi files',
                      value1=self.job_param['job_cleanup_mi'],
                      enable=False,
                      cc = partial( self.setDefaultIntValue, 'job_cleanup_mi' ) )
    cmds.checkBoxGrp( 'job_cleanup_script', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label='', label1=' script file',
                      value1=self.job_param['job_cleanup_script'],
                      enable=False,
                      cc = partial( self.setDefaultIntValue, 'job_cleanup_script' ) )

    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.setParent( '..' )
    #
    # .mi files generation tab
    #
    tab_miparam = cmds.columnLayout( 'tc1', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )
    cmds.frameLayout( 'fr1', label=' Export Settings ', borderVisible=True, borderStyle='etchedIn', marginHeight=mr_hi  )
    cmds.columnLayout( 'fc1', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )
    #
    cmds.checkBoxGrp( 'mi_reuse', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label="Use existing .mi files ",
                      ann = "Do not generate .mi files if they are exist",
                      value1=self.mi_param['mi_reuse'],
                      cc=partial( self.setDefaultIntValue, 'mi_reuse' ) )
    cmds.text( label='' )
    #mi_dir = cmds.textFieldButtonGrp( cw=( 1, cw1 ), adj=2, label="Directory ", buttonLabel="...", text=self.mi_param['mi_dir'] )
    #cmds.textFieldButtonGrp( mi_dir, edit=True, bc=partial( self.browseDirectory, mi_dir ), cc=partial( self.setDefaultStrValue, 'mi_dir' ) )
    mi_filename = cmds.textFieldButtonGrp( 'mi_filename', cw=( 1, cw1 ), adj=2,
                                           label="File Name ", buttonLabel="...",
                                           text=self.mi_param['mi_filename'],
                                           cc=partial( self.miFileNameChanged, 'mi_filename' ) )
    cmds.textFieldButtonGrp( mi_filename, edit=True, bc=partial( self.browseFile, mi_filename, 'mentalray files (*.mi)' ) )
    #cmds.text( label='' )
    # Resolved Path
    #
    cmds.intFieldGrp( 'mi_padding', cw=( (1, cw1), (2, cw2) ),
                      label="Frame Padding ",
                      value1=self.mi_param['mi_padding'],
                      cc=partial( self.miFileNameChanged, 'mi_padding' ) )
    cmds.checkBoxGrp( 'mi_perframe', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label = '', label1 = " File Per Frame ",
                      value1=self.mi_param['mi_perframe'],
                      cc=partial( self.miFileNameChanged, 'mi_perframe' ) )
    #cmds.text( label='' )
    cmds.checkBoxGrp( 'mi_selection', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label = '', label1 = " Export Only Selected Objects",
                      value1=self.mi_param['mi_selection'],
                      cc=partial( self.setDefaultIntValue, 'mi_selection' ) )
    #cmds.text( label='' )


    #mi_fileformat = cmds.optionMenuGrp( 'mi_fileformat', cw=( (1, cw1), ), cal=(1, 'right'),
    #                                    label="Format .mi ",
    #                                    cc=partial( self.setDefaultStrValue, 'mi_fileformat' ) )
    #for name in ('Binary', 'ASCII'):
    #  cmds.menuItem( label=name )
    #cmds.optionMenuGrp( mi_fileformat, e=True, value=self.mi_param['mi_fileformat'] )
    cmds.checkBoxGrp( 'mi_binary', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label = '', label1 = " Binary",
                      value1 = self.mi_param [ 'mi_binary' ],
                      cc = partial( self.setDefaultIntValue, 'mi_binary' ) )

    cmds.intFieldGrp( 'mi_tabstop', cw=( (1, cw1), (2, cw2) ),
                      label="Tab stop (ASCII) ",
                      value1=self.mi_param['mi_tabstop'],
                      cc=partial( self.setDefaultIntValue, 'mi_tabstop' ) )
    #mi_compression = cmds.optionMenuGrp( 'mi_compression', cw=( (1, cw1), ), label="Compression ", cal=(1, 'right'), cc=partial( self.setDefaultStrValue, 'mi_compression' ) )
    #cmds.menuItem( label='Off' )
    #cmds.menuItem( label='GzipBestSpeed' )
    #cmds.menuItem( label='GzipDefault' )
    #cmds.menuItem( label='GzipBest' )
    #cmds.optionMenuGrp( mi_compression, e=True, value=self.mi_param['mi_compression'] )

    mi_filepaths = cmds.optionMenuGrp( 'mi_filepaths', cw=( (1, cw1), ), cal=(1, 'right'),
                                       label="Export File Paths ",
                                       cc=partial( self.setDefaultStrValue, 'mi_filepaths' ) )
    for name in ( 'NoPath', 'Relative', 'Absolute' ):
      cmds.menuItem( label=name )
    cmds.optionMenuGrp( mi_filepaths, e=True, value=self.mi_param['mi_filepaths'] )

    # mi_verbosity = none, fatal, error, warning, info, progress, and details
    #mi_verbosity = cmds.optionMenuGrp( 'mi_verbosity', cw=( (1, cw1), ), cal=(1, 'right'),
    #                                   label="Verbosity ",
    #                                   cc=partial( self.setDefaultStrValue, 'mi_verbosity' ) )
    #for name in ('none', 'fatal', 'error', 'warning', 'info', 'progress', 'details'):
    #  cmds.menuItem( label=name )

    #cmds.optionMenuGrp( mi_verbosity, e=True, value=self.mi_param['mi_verbosity'] )
    #
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.frameLayout( 'fr2', label=' Resolved Path ', borderVisible=True, borderStyle='etchedIn', marginHeight=mr_hi  )
    cmds.columnLayout( 'fc2', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )
    #
    cmds.textFieldGrp( 'mi_resolved_path', cw=( 1, 0 ), adj=2, label='', text='', editable=False )
    self.setResolvedPath()
    #
    cmds.setParent( '..' )
    cmds.setParent( '..' )
    cmds.frameLayout( 'fr3', label=' Deferred .mi generation ', borderVisible=True, borderStyle='etchedIn', marginHeight=mr_hi, cll=True, cl=True  )
    cmds.columnLayout( 'fc3', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )
    cmds.checkBoxGrp( 'mi_deferred', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label = "Use deferred ",
                      ann = "Generate .mi files in background process",
                      value1 = self.mi_param[ 'mi_deferred' ],
                      cc = partial( self.enable_deferred )) # self.setDefaultIntValue, 'rib_deferred_ribgen' ) )

    cmds.checkBoxGrp( 'mi_local_migen', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label = '', label1 = " Only on localhost ",
                      ann = "Do not use remote hosts",
                      value1 = self.mi_param[ 'mi_local_migen' ],
                      enable = self.mi_param[ 'mi_deferred' ],
                      cc = partial( self.setDefaultIntValue, 'mi_local_migen' ) )

    cmds.intFieldGrp( 'mi_def_task_size', cw=( (1, cw1), (2, cw2) ),
                      label = "Task Size ",
                      value1 = self.mi_param [ 'mi_def_task_size' ],
                      enable = self.mi_param[ 'mi_deferred' ],
                      cc = partial( self.setDefaultIntValue, 'mi_def_task_size' ) )
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.setParent( '..' )
    #
    # Renderer tab
    #
    tab_mray = cmds.columnLayout( 'tc2', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )
    #cmds.text( label='' )
    cmds.frameLayout( 'fr1', label=' MentalRay command line options ', borderVisible=True, borderStyle='etchedIn', marginHeight=mr_hi  )
    cmds.columnLayout( 'fc1', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )

    cmds.textFieldGrp( 'mr_options', cw=( 1, cw1 ), adj=2,
                       label="Additional Options ",
                       text=self.mr_param['mr_options'],
                       cc=partial( self.setDefaultStrValue, 'mr_options' ) )
    cmds.text( label='' )
    mr_verbosity = cmds.optionMenuGrp( 'mr_verbosity', cw=( (1, cw1), ), cal=(1, 'right'),
                                       label="Verbosity ",
                                       cc=partial( self.setDefaultStrValue, 'mr_verbosity' ) )
    for name in ('none', 'fatal', 'error', 'warning', 'info', 'progress', 'debug', 'details'):
      cmds.menuItem( label=name )

    cmds.optionMenuGrp( mr_verbosity, e=True, value=self.mr_param['mr_verbosity'] )

    cmds.intFieldGrp( 'mr_progress_frequency', cw=( (1, cw1), (2, cw2) ),
                      label="Progress frequency ",
                      ann = 'Progress information should be emitted only when this percentage of the whole render time has passed.',
                      value1=self.mr_param['mr_progress_frequency'],
                      cc=partial( self.setDefaultIntValue, 'mr_progress_frequency' ) )
    cmds.intFieldGrp( 'mr_threads', cw=( (1, cw1), (2, cw2) ),
                      label="Threads ",
                      ann = 'The number of threads.',
                      value1=self.mr_param['mr_threads'],
                      cc=partial( self.setDefaultIntValue, 'mr_threads' ) )
    cmds.checkBoxGrp( 'mr_texture_continue', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label='', label1=" Skip missing textures",
                      ann = 'If this option is specified, mental ray will continue for missing texture files',
                      value1=self.mr_param['mr_texture_continue'],
                      cc=partial( self.setDefaultIntValue, 'mr_texture_continue' ) )

    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.setParent( '..' )
    #
    # Afanasy tab
    #
    tab_afanasy = cmds.columnLayout( 'tc3', columnAttach=('left',0), rowSpacing=0, adjustableColumn=True )
    cmds.frameLayout( 'fr1', label=' Parameters ', borderVisible=True, borderStyle='etchedIn', marginHeight=mr_hi )
    cmds.columnLayout( 'fc1', columnAttach=('left',4), rowSpacing=0, adjustableColumn=True )

    cmds.intFieldGrp( 'af_capacity', cw=( (1, cw1), (2, cw2) ),
                      label="Task Capacity ",
                      value1=self.afanasy_param['af_capacity'],
                      cc=partial( self.setDefaultIntValue, 'af_capacity' ) )
                      
    cmds.intFieldGrp( 'af_deferred_capacity', cw=( (1, cw1), (2, cw2) ),
                      label="Deferred Capacity ",
                      value1=self.afanasy_param['af_deferred_capacity'],
                      cc=partial( self.setDefaultIntValue, 'af_deferred_capacity' ) )                      

    cmds.checkBoxGrp( 'af_use_var_capacity', cw=( (1, cw1), (2, cw1 * 2 ) ),
                      label = "Use Variable Capacity ",
                      ann = "Block can generate tasks with capacity*coefficient to fit free render capacity",
                      value1 = self.afanasy_param[ 'af_use_var_capacity' ],
                      cc = partial( self.enable_var_capacity ) )

    cmds.floatFieldGrp( 'af_var_capacity', cw=( (1, cw1), (2, cw2), (3, cw2), (4, cw2) ), nf=2, pre=2,
                       label="Min/Max coefficient ",
                       value1 = self.afanasy_param['af_cap_min'],
                       value2 = self.afanasy_param['af_cap_max'],
                       enable = self.afanasy_param[ 'af_use_var_capacity' ],
                       cc = ( partial( self.setDefaultFloatValue2, ('af_cap_min', 'af_cap_max') ) ) )

    cmds.intFieldGrp( 'af_max_running_tasks', cw=( (1, cw1), (2, cw2) ),
                      label = "Max Running Tasks ",
                      value1 = self.afanasy_param[ 'af_max_running_tasks' ],
                      cc = partial( self.setDefaultIntValue, 'af_max_running_tasks' ) )

    cmds.intFieldGrp( 'af_max_tasks_per_host', cw=( (1, cw1), (2, cw2) ),
                      label = "Max Tasks Per Host ",
                      value1 = self.afanasy_param[ 'af_max_tasks_per_host' ],
                      cc = partial( self.setDefaultIntValue, 'af_max_tasks_per_host' ) )

    cmds.textFieldGrp( 'af_service', cw=( 1, cw1 ), adj=2,
                        label = "Service ",
                        text = self.afanasy_param [ 'af_service' ],
                        cc = partial( self.setDefaultStrValue, 'af_service' ) )
    cmds.textFieldGrp( 'af_deferred_service', cw=( 1, cw1 ), adj=2,
                        label = "Deferred Service ",
                        text = self.afanasy_param [ 'af_deferred_service' ],
                        cc = partial( self.setDefaultStrValue, 'af_deferred_service' ) )

    cmds.textFieldGrp( 'af_hostsmask', cw=( 1, cw1 ), adj=2,
                        label = "Hosts Mask ",
                        ann="Job run only on renders which host name matches this mask\n e.g.  .* or host.*",
                        text = self.afanasy_param [ 'af_hostsmask' ],
                        cc = partial( self.setDefaultStrValue, 'af_hostsmask' ) )

    cmds.textFieldGrp( 'af_hostsexcl', cw=( 1, cw1 ), adj=2,
                        label = "Exclude Hosts Mask ",
                        ann="Job can not run on renders which host name matches this mask\n e.g.  host.* or host01|host02",
                        text = self.afanasy_param [ 'af_hostsexcl' ],
                        cc = partial( self.setDefaultStrValue, 'af_hostsexcl' ) )

    cmds.textFieldGrp( 'af_depmask', cw=( 1, cw1 ), adj=2,
                        label = "Depend Mask ",
                        ann="Job will wait other user jobs which name matches this mask",
                        text = self.afanasy_param [ 'af_depmask' ],
                        cc = partial( self.setDefaultStrValue, 'af_depmask' ) )

    cmds.textFieldGrp( 'af_depglbl', cw=( 1, cw1 ), adj=2,
                        label = "Global Depend Mask ",
                        ann="Job will wait other jobs from any user which name matches this mask",
                        text = self.afanasy_param [ 'af_depglbl' ],
                        cc = partial( self.setDefaultStrValue, 'af_depglbl' ) )

    cmds.textFieldGrp( 'af_os', cw=( 1, cw1 ), adj=2,
                        label = "Needed OS ",
                        ann="windows linux mac",
                        text = self.afanasy_param [ 'af_os' ],
                        cc = partial( self.setDefaultStrValue, 'af_os' ) )

    #cmds.checkBoxGrp( 'af_consolidate_subtasks', cw=( (1, cw1), (2, cw1 * 2 ) ),
    #                  label="Consolidate subtasks ",
    #                  ann="Put perframe subtasks in block",
    #                  value1=self.afanasy_param ['af_consolidate_subtasks'],
    #                  cc=partial( self.setDefaultIntValue, 'af_consolidate_subtasks' ) )

    cmds.setParent( '..' )
    cmds.setParent( '..' )

    cmds.setParent( '..' )

    cmds.tabLayout( tab, edit=True,
                    tabLabel=( ( tab_job, "Job" ),
                               ( tab_miparam, ".mi" ),
                               ( tab_mray, "Renderer" ),
                               ( tab_afanasy, "Afanasy" )
                             )
                  )

    cmds.setParent( form )
    btn_sbm = cmds.button( label="Submit", command=self.submitJob, ann='Generate .mi files and submit to dispatcher' )
    btn_gen = cmds.button( label="Generate .mi", command=self.generate_mi, ann='Force .mi files generation' )
    btn_cls = cmds.button( label="Close", command=self.deleteUI )

    cmds.formLayout(  form, edit=True,
                      attachForm=( ( proj, 'top',    0 ),
                                   ( proj, 'left',    0 ),
                                   ( proj, 'right',    0 ),
                                   ( tab, 'left',    0 ),
                                   ( tab, 'right',    0 ),
                                   ( btn_cls,   'bottom', 0 ),
                                   ( btn_gen,   'bottom', 0 ),
                                   ( btn_sbm,   'bottom', 0 ),
                                   ( btn_sbm,   'left',   0 ),
                                   ( btn_cls,   'right',  0 )
                                 ),
                      attachControl=( ( tab, 'top', 0, proj ),
                                      ( tab, 'bottom', 0, btn_sbm ),
                                      ( btn_gen, 'left', 0, btn_sbm ),
                                      ( btn_gen, 'right', 0, btn_cls )
                                    ),
                      attachPosition=( ( btn_sbm, 'right', 0, 33 ),
                                       ( btn_gen, 'right', 0, 66 ),
                                       ( btn_cls, 'left', 0, 66 )
                                      )
                   )

    cmds.showWindow( self.winMain )
    return form
  #
  # deleteUI
  #
  def deleteUI( self, param ):
    #print (">> meMentalRayRender: deleteUI() "  )
    winMain = meMentalRayRenderMainWnd

    if cmds.window( winMain, exists=True ): cmds.deleteUI( winMain, window=True )
    if cmds.windowPref( winMain, exists=True ): cmds.windowPref( winMain, remove=True )
#
#
#
print 'meMentalRayRender sourced ...'

