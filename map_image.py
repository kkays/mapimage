import PIL.Image
import PIL.ExifTags
import math
import os
import argparse
import zipfile

IMAGE_FILETYPES = ('.jpg', '.gif', '.png', '.tga')

# Takes name, url, lon, lat
KML_PLACEMARK_PHOTO = """
      <Placemark>
        <name>{name}</name>
        <description><![CDATA[<img width="600" src="images/{directory}"/><br><br>]]></description>
        <styleUrl>#icon-1899-DB4436</styleUrl>
        <Point>
          <coordinates>
            {lon},{lat},0
          </coordinates>
        </Point>
      </Placemark>
"""
KML_FOLDER = """
  <Folder>
    <name>{name}</name>
    {contents}
  </Folder>
"""

def _get_exif(img_path):
  img = PIL.Image.open(img_path)
  exif = {
      PIL.ExifTags.TAGS[k]: v
      for k, v in img._getexif().items()
      if k in PIL.ExifTags.TAGS
  }
  gps_data = {}
  for t in exif['GPSInfo']:
    gps_data[PIL.ExifTags.GPSTAGS.get(t, t)] = exif['GPSInfo'][t]
  return gps_data

def _to_real_float(num):
  main = str(num[0])
  places = int(math.log10(num[1]))
  return float(main if places == 0 else main[:-places] + '.' + main[-places:])

def _dms_to_dec(coord, ref):
  degrees = _to_real_float(coord[0])
  minutes = _to_real_float(coord[1])
  seconds = _to_real_float(coord[2])
  result = degrees + (minutes / 60) + (seconds / 3600)
  return -result if ref in 'SW' else result

def _get_lat_lon(filename):
  try:
    exif = _get_exif(filename)
    lat = _dms_to_dec(exif['GPSLatitude'], exif['GPSLatitudeRef'])
    lon = _dms_to_dec(exif['GPSLongitude'], exif['GPSLongitudeRef'])
    return lat, lon
  except (KeyError, AttributeError):
    raise KeyError('No exif data for {}'.format(filename))

def _get_image_list(directory):
  for f in os.listdir(directory):
    p = os.path.join(directory, f)
    if os.path.isfile(p):
      if p.lower().endswith(IMAGE_FILETYPES):
        yield p
      else:
        print 'Ignoring non-image file: ' + p

def _get_folder_list(directory):
  for f in os.listdir(directory):
    p = os.path.join(directory, f)
    if os.path.isdir(p):
      yield p

def convert_file(path):
  """Converts a file to a KML Placemark string."""
  try:
    lat, lon = _get_lat_lon(path)
  except KeyError as e:
    print e
    return ''
  return KML_PLACEMARK_PHOTO.format(
      name=path.split('/')[-1],
      directory=path,
      lat=lat,
      lon=lon)

def convert_dir(directory):
  """Converts a directory to a KML folder string."""
  photo_contents = ''.join(map(convert_file, _get_image_list(directory)))
  folder_contents = ''.join(map(convert_dir, _get_folder_list(directory)))
  return KML_FOLDER.format(
    name=directory.split('/')[-1],
    contents=folder_contents + photo_contents
  )

def zip_images(directory, zf):
  """Recursively zips all of the images in a directory into zf."""
  for root, dirs, files in os.walk(directory, topdown=True):
    for f in files:
      if f.lower().endswith(IMAGE_FILETYPES):
        zf.write(os.path.join(root, f), os.path.join('images', root, f))

def create_kmz(source, target):
  """Takes a source directory and writes to a kmz named target."""
  with zipfile.ZipFile(target, mode='w') as zf:
    zip_images(source, zf)
    zf.writestr('main.kml', '<kml>' + convert_dir(source) + '</kml>')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Create a KMZ file from a directory of images (jpg, gif, png).')
  parser.add_argument('source', metavar='s', type=str,
      help='the name of the directory where images are stored.' )
  parser.add_argument('target', metavar='t', type=str, default='out.kmz',
      help='the name of the kmz output.' )
  args = parser.parse_args()
  create_kmz(args.source, args.target)
