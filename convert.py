import PIL.Image
import PIL.ExifTags
import math

# Takes name, url, lon, lat
KML_PHOTO = """
      <Placemark>
        <name>{name}</name>
        <description><![CDATA[<img src="{url}"/><br><br>]]></description>
        <styleUrl>#icon-1899-DB4436</styleUrl>
        <Point>
          <coordinates>
            {lon},{lat},0
          </coordinates>
        </Point>
      </Placemark>
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
  exif = _get_exif(filename)
  if ('GPSLatitude' not in exif or
      'GPSLatitudeRef' not in exif or
      'GPSLongitude' not in exif or
      'GPSLongitudeRef' not in exif):
    raise KeyError('No exif data for {}'.format('filename'))
  lat = _dms_to_dec(exif['GPSLatitude'], exif['GPSLatitudeRef'])
  lon = _dms_to_dec(exif['GPSLongitude'], exif['GPSLongitudeRef'])
  return lat, lon

def convert(filename):
  lat, lon = _get_lat_lon(filename)
  return KML_PHOTO.format(
      name=filename,
      url=filename,
      lat=lat,
      lon=lon)

if __name__ == '__main__':
  print(convert('images/img.jpg'))
