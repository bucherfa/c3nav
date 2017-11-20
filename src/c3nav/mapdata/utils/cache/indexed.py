import math
import struct

import numpy as np
from PIL import Image
from django.conf import settings
from shapely import prepared
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry


class GeometryIndexed:
    # binary format (everything little-endian):
    # 1 byte (uint8): variant id
    # 1 byte (uint8): resolution
    # 2 bytes (uint16): origin x
    # 2 bytes (uint16): origin y
    # 2 bytes (uint16): origin width
    # 2 bytes (uint16): origin height
    # (optional meta data, depending on subclass)
    # x bytes data, line after line. (cell size depends on subclass)
    dtype = np.uint16
    variant_id = 0

    def __init__(self, resolution=settings.CACHE_RESOLUTION, x=0, y=0, data=None, filename=None):
        self.resolution = resolution
        self.x = x
        self.y = y
        self.data = data if data is not None else self._get_empty_array()
        self.filename = filename

    @classmethod
    def _get_empty_array(cls):
        return np.empty((0, 0), dtype=cls.dtype)

    @classmethod
    def open(cls, filename):
        with open(filename, 'rb') as f:
            instance = cls.read(f)
        instance.filename = filename
        return instance

    @classmethod
    def read(cls, f):
        variant_id, resolution, x, y, width, height = struct.unpack('<BBHHHH', f.read(10))
        if variant_id != cls.variant_id:
            raise ValueError('variant id does not match')

        kwargs = {
            'resolution': resolution,
            'x': x,
            'y': y,
        }
        cls._read_metadata(f, kwargs)

        # noinspection PyTypeChecker
        kwargs['data'] = np.fromstring(f.read(width*height*cls.dtype().itemsize), cls.dtype).reshape((height, width))
        return cls(**kwargs)

    @classmethod
    def _read_metadata(cls, f, kwargs):
        pass

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        if filename is None:
            raise ValueError('Missing filename.')

        with open(filename, 'wb') as f:
            self.write(f)

    def write(self, f):
        f.write(struct.pack('<BBHHHH', self.variant_id, self.resolution, self.x, self.y, *reversed(self.data.shape)))
        self._write_metadata(f)
        f.write(self.data.tobytes('C'))

    def _write_metadata(cls, f):
        pass

    def _get_geometry_bounds(self, geometry):
        minx, miny, maxx, maxy = geometry.bounds
        return (
            int(math.floor(minx / self.resolution)),
            int(math.floor(miny / self.resolution)),
            int(math.ceil(maxx / self.resolution)),
            int(math.ceil(maxy / self.resolution)),
        )

    def fit_bounds(self, minx, miny, maxx, maxy):
        height, width = self.data.shape

        if self.data.size:
            minx = min(self.x, minx)
            miny = min(self.y, miny)
            maxx = max(self.x + width, maxx)
            maxy = max(self.y + height, maxy)

        new_data = np.zeros((maxy - miny, maxx - minx), dtype=self.dtype)

        if self.data.size:
            dx = self.x - minx
            dy = self.y - miny
            new_data[dy:(dy + height), dx:(dx + width)] = self.data

        self.data = new_data
        self.x = minx
        self.y = miny

    def get_geometry_cells(self, geometry, bounds=None):
        if bounds is None:
            bounds = self._get_geometry_bounds(geometry)
        minx, miny, maxx, maxy = bounds

        height, width = self.data.shape
        minx = max(minx, self.x)
        miny = max(miny, self.y)
        maxx = min(maxx, self.x + width)
        maxy = min(maxy, self.y + height)

        cells = np.zeros_like(self.data, dtype=np.bool)
        prep = prepared.prep(geometry)
        res = self.resolution
        for iy, y in enumerate(range(miny * res, maxy * res, res), start=miny - self.y):
            for ix, x in enumerate(range(minx * res, maxx * res, res), start=minx - self.x):
                if prep.intersects(box(x, y, x + res, y + res)):
                    cells[iy, ix] = True

        return cells

    @property
    def bounds(self):
        height, width = self.data.shape
        return self.x, self.y, self.x+width, self.y+height

    def __getitem__(self, key):
        if isinstance(key, BaseGeometry):
            bounds = self._get_geometry_bounds(key)
            return self.data[self.get_geometry_cells(key, bounds)]

        if isinstance(key, tuple):
            xx, yy = key

            minx = int(math.floor(xx.start / self.resolution))
            miny = int(math.floor(yy.start / self.resolution))
            maxx = int(math.ceil(xx.stop / self.resolution))
            maxy = int(math.ceil(yy.stop / self.resolution))

            height, width = self.data.shape
            minx = min(self.x, minx) - self.x
            miny = min(self.y, miny) - self.x
            maxx = max(self.x + width, maxx) - self.y
            maxy = max(self.y + height, maxy) - self.y

            return self.data[miny:maxy, minx:maxx].flatten()

        raise TypeError('GeometryIndexed index must be a shapely geometry or tuple, not %s' % type(key).__name__)

    def __setitem__(self, key, value):
        if isinstance(key, BaseGeometry):
            bounds = self._get_geometry_bounds(key)
            self.fit_bounds(*bounds)
            cells = self.get_geometry_cells(key, bounds)
            self.data[cells] = value
            return

        raise TypeError('GeometryIndexed index must be a shapely geometry, not %s' % type(key).__name__)

    def to_image(self):
        from c3nav.mapdata.models import Source
        (minx, miny), (maxx, maxy) = Source.max_bounds()

        height, width = self.data.shape
        image_data = np.zeros((int(math.ceil((maxy-miny)/self.resolution)),
                               int(math.ceil((maxx-minx)/self.resolution))), dtype=np.uint8)

        if self.data.size:
            minval = min(self.data.min(), 0)
            maxval = max(self.data.max(), minval+0.01)
            visible_data = ((self.data.astype(float)-minval)*255/(maxval-minval)).clip(0, 255).astype(np.uint8)
            image_data[self.y:self.y+height, self.x:self.x+width] = visible_data

        return Image.fromarray(np.flip(image_data, axis=0), 'L')
