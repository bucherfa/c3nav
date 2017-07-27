from django.db import models
from django.utils.translation import ugettext_lazy as _

from c3nav.mapdata.fields import GeometryField
from c3nav.mapdata.models.access import AccessRestrictionMixin
from c3nav.mapdata.models.base import TitledMixin
from c3nav.mapdata.models.geometry.space import SpaceGeometryMixin


class GraphNode(SpaceGeometryMixin, models.Model):
    """
    A graph node
    """
    geometry = GeometryField('point')
    space_transfer = models.BooleanField(_('space transfer node'), default=False, db_index=True)

    class Meta:
        verbose_name = _('Graph Node')
        verbose_name_plural = _('Graph Nodes')
        default_related_name = 'graphnodes'

    def get_geojson_properties(self, *args, **kwargs) -> dict:
        result = super().get_geojson_properties(*args, **kwargs)
        if self.space_transfer:
            result['space_transfer'] = True
        return result


class WayType(TitledMixin, models.Model):
    """
    A special way type
    """
    color = models.CharField(max_length=32, verbose_name=_('edge color'))

    class Meta:
        verbose_name = _('Way Type')
        verbose_name_plural = _('Way Types')
        default_related_name = 'waytypes'


class GraphEdge(AccessRestrictionMixin, models.Model):
    """
    A directed edge connecting two graph nodes
    """
    from_node = models.ForeignKey(GraphNode, on_delete=models.PROTECT, related_name='edges_from_here',
                                  verbose_name=_('from node'))
    to_node = models.ForeignKey(GraphNode, on_delete=models.PROTECT, related_name='edges_to_here',
                                verbose_name=_('to node'))
    waytype = models.ForeignKey(WayType, null=True, blank=True, on_delete=models.PROTECT, verbose_name=_('Way Type'))

    class Meta:
        verbose_name = _('Graph Edge')
        verbose_name_plural = _('Graph Edges')
        default_related_name = 'graphedges'
        unique_together = (('from_node', 'to_node'), )