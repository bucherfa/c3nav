# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-10 18:26
from __future__ import unicode_literals

from django.db import migrations


def assign_locations_roomsection_poi(apps, schema_editor):
    AreaLocation = apps.get_model('mapdata', 'AreaLocation')
    Space = apps.get_model('mapdata', 'Space')
    LocationSlug = apps.get_model('mapdata', 'LocationSlug')
    Area = apps.get_model('mapdata', 'Area')
    Point = apps.get_model('mapdata', 'Point')
    Area.objects.all().update(can_search=False, can_describe=False)
    for obj in AreaLocation.objects.filter(location_type__in=('roomsegment', 'poi')).order_by('slug'):
        spaces = [s for s in Space.objects.filter(section=obj.section, level='')
                  if s.geometry.intersection(obj.geometry).area/obj.geometry.area > 0.20]
        if len(spaces) == 0:
            obj.delete()
            continue
        elif len(spaces) > 1:
            obj.location_type = 'area'
            obj.save()
            continue
        space = spaces[0]

        if obj.location_type == 'roomsegment':
            to_obj = Area()
            to_obj.geometry = obj.geometry
        elif obj.location_type == 'poi':
            to_obj = Point()
            to_obj.geometry = obj.geometry.centroid

        to_obj.locationslug_ptr = LocationSlug.objects.create(slug=obj.slug)
        to_obj.space = space
        to_obj.titles = obj.titles
        to_obj.can_search = obj.can_search
        to_obj.can_describe = obj.can_describe
        to_obj.color = obj.color
        to_obj.save()
        to_obj.groups.add(*obj.groups.all())
        to_obj.save()
        obj.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mapdata', '0086_auto_20170510_1820'),
    ]

    operations = [
        migrations.RunPython(assign_locations_roomsection_poi),
    ]
