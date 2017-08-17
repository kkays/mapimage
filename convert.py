import PIL.Image
import PIL.ExifTags
import math
import os
import argparse
import zipfile

IMAGE_FILETYPES = ('.jpg', '.gif', '.png')

# Takes name, url, lon, lat
KML_PLACEMARK_PHOTO = """
      <Placemark>
        <name>{name}</name>
        <description><![CDATA[<img width="600" src="images/{url}"/><br><br>]]></description>
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

def convert_file(filename):
  try:
    lat, lon = _get_lat_lon(filename)
  except KeyError as e:
    print e
    return ''
  filename = filename.split('/')[-1]
  return KML_PLACEMARK_PHOTO.format(
      name=filename,
      url=filename,
      lat=lat,
      lon=lon)

def get_image_list(directory):
  for f in os.listdir(directory):
    p = os.path.join(directory, f)
    if os.path.isfile(p) and p.endswith(IMAGE_FILETYPES):
      yield p

def get_folder_list(directory):
  for f in os.listdir(directory):
    p = os.path.join(directory, f)
    if os.path.isdir(p):
      yield p

def convert_dir(directory):
  photo_contents = ''.join(map(convert_file, get_image_list(directory)))
  folder_contents = ''.join(map(convert_dir, get_folder_list(directory)))
  return KML_FOLDER.format(
    name=directory.split('/')[-1],
    contents=folder_contents + photo_contents
  )

def main(directory, target):
  output = zipfile.ZipFile(target, mode='w')
  try:
    for image in get_image_list(directory):
      output.write(image, 'images/' + image.split('/')[-1])
    output.writestr('main.kml', '<kml>' + convert_dir(directory) + '</kml>')
  finally:
    output.close()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Create a KMZ file from a directory of images (jpg, gif, png).')
  parser.add_argument('source', metavar='s', type=str,
      help='the name of the directory where images are stored.' )
  parser.add_argument('target', metavar='t', type=str, default='out.kmz',
      help='the name of the kmz output.' )
  args = parser.parse_args()
  main(args.source, args.target)
