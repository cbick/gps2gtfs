# Copyright (c) 2010 Colin Bick, Robert Damphousse

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from time import time

def rand_hex_color(): 
  colorchoices = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'] 
  hexnum = '#' 
  for x in range(0,6): 
      hexnum += choice(colorchoices) 
  return hexnum

def now():
  return str(int(time())) 


class KFeature(object):
  def __init__(self):
    self.visibility = True

class KGeometry(object):
  pass

class KStyleSelector(object):
  pass

class KStyle(KStyleSelector):
  '''
  <Style id="ID">
  <!-- extends StyleSelector -->

  <!-- specific to Style -->
    <IconStyle>...</IconStyle>
    <LabelStyle>...</LabelStyle>
    <LineStyle>...</LineStyle>
    <PolyStyle>...</PolyStyle>
    <BalloonStyle>...</BalloonStyle>
    <ListStyle>...</ListStyle>
  </Style>
  '''

  def __init__(self):
    self.__iconStyle=None
    self.__labelStyle=None
    self.__lineStyle=None
    self.__polyStyle=None
    self.__baloonStyle=None
    self.__listStyle=None
    
  #iconStyle = property(getIconStyle,setIconStyle)
  #labelStyle = property(getLabelStyle,setLabelStyle)
  #lineStyle = property(getLineStyle,setLineStyle)
  #polyStyle = property(getPolyStyle,setPolyStyle)

class KLineStyle(object):
  def __init__(self,style_id=None):
    '''
    <LineStyle id="ID">
      <!-- inherited from ColorStyle -->
      <color>ffffffff</color>            <!-- kml:color -->
      <colorMode>normal</colorMode>      <!-- colorModeEnum: normal or random -->

      <!-- specific to LineStyle -->
      <width>1</width>                   <!-- float -->
    </LineStyle>
    '''
    self.style_id = style_id
    self.color = 'ffffffff'
    self.colorMode = 'normal'
    self.width = 1
  def kml(self):
    if self.style_id:
      idm = 'id="%s"' % self.style_id
    else:
      idm = ''
    markup = '''
    <LineStyle%s>
      <color>%s</color>
      <colorMode>%s</colorMode>
      <width>%s</width>
    </LineStyle>
    '''\
    %(idm,self.color,self.colorMode,self.width)
    return markup

class KFolder(KFeature):
  def __init__(self, name="Untitled Folder",description=''):
    super(KFolder,self).__init__()
    self.name = str(name)
    self.description = description
    self.child_objects = []     
    
  def add(self,placemark):
    self.child_objects.append(placemark)    
  def kml(self):  
    data = ''.join([obj.kml() for obj in self.child_objects]) 
    self.markup = """<Folder><name>%s</name>
    <visibility>%s</visibility>
    <description>%s</description>
    %s
    </Folder>""" % (self.name,int(self.visibility),self.description,data)    
    
    return self.markup

class KPlacemark(KFeature):
  def __init__(self,kml_object,name="Untitled",style_url=''):
    super(KPlacemark,self).__init__()
    self.name = str(name)
    self.style_url = style_url
    self.kml_object = kml_object
    
  def kml(self):
    self.markup = """<Placemark>
      <name>%s</name>
      <visibility>%s</visibility>
			<styleUrl>%s</styleUrl>
			%s
		</Placemark>""" % (self.name,int(self.visibility),self.style_url,self.kml_object.kml())
    return self.markup



class KPoint(object):
  def __init__(self,lation):
    self.lat = lation[0]
    self.lon = lation[1]
    self.lation = [self.lat,self.lon]
  def kml(self):
    self.markup = "<Point><coordinates>%s,%s,0</coordinates></Point>" % (self.lon,self.lat)
    return self.markup
    

class KPath(object):
  def __init__(self):
    self.lations=[]
    
  def add(self,lation):
    self.lations.append(lation)
    
  def kml(self):
    coordinate_string = ''
    for lation in self.lations:
      coordinate_string += "%s,%s,0\n" % (lation[1],lation[0])
    
    self.markup = "<LineString><coordinates>%s</coordinates></LineString>" % coordinate_string
    return self.markup

class KDocument(object):
  def __init__(self,template_path='kml/document.kml',docname="Untitled",fname=now()+".kml",top_object=KFolder(),style_doc=''):
    self.template_path = template_path
    self.template_file = open(self.template_path)
    self.template = ''.join(self.template_file.readlines())
    self.top_object = top_object
    self.docname = docname
    self.outfile = fname
    self.style_doc_path = style_doc
  def kml(self):
    if self.style_doc_path:
      style_file = open(self.style_doc_path)
      styles = ''.join(style_file.readlines())
    else:
      styles = ''
    
    kml = self.template.replace('<!--DOCNAME-->',self.docname)
    kml = kml.replace('<!--STYLES-->',styles)
    kml = kml.replace('<!--FOLDERS-->',self.top_object.kml())
    
    return kml
  def write(self):
    of = open(self.outfile,'w')
    of.write(self.kml())
    of.close()
    
