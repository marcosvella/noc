# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# VRF model
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
from __future__ import absolute_import
import operator
from threading import Lock
# Third-party modules
import six
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models import Q
import cachetools
# NOC modules
from noc.project.models.project import Project
from noc.lib.validators import check_rd
from noc.core.model.fields import TagsField, DocumentReferenceField, JSONField
from noc.lib.app.site import site
from noc.lib.db import SQL
from noc.main.models.textindex import full_text_search
from noc.core.model.decorator import on_delete_check, on_init
from noc.vc.models.vpnprofile import VPNProfile
from noc.wf.models.state import State
from noc.sa.interfaces.base import ListOfParameter, ModelParameter, StringParameter
from noc.sa.models.administrativedomain import AdministrativeDomain
from noc.sa.models.useraccess import UserAccess
from .vrfgroup import VRFGroup
from noc.core.wf.decorator import workflow
from noc.core.vpn import get_vpn_id


id_lock = Lock()

is_prefix_perm = ListOfParameter(element=[
    ModelParameter(User, required=False),
    ModelParameter(Group, required=False),
    StringParameter(choices=["can_view", "can_change", "can_create"])
], default=[])


@full_text_search
@on_init
@workflow
@on_delete_check(check=[
    ("ip.Address", "vrf"),
    ("ip.AddressRange", "vrf"),
    ("ip.PrefixAccess", "vrf"),
    ("ip.Prefix", "vrf"),
    # ("ip.DynamicIPPoolUsage", "vrf"),
    ("sa.ManagedObject", "vrf"),
    ("sa.ManagedObjectSelector", "filter_vrf"),
    ("vc.VCBindFilter", "vrf"),
])
@six.python_2_unicode_compatible
class VRF(models.Model):
    """
    VRF
    """
    class Meta(object):
        verbose_name = _("VRF")
        verbose_name_plural = _("VRFs")
        db_table = "ip_vrf"
        app_label = "ip"
        ordering = ["name"]

    name = models.CharField(
        _("VRF"),
        unique=True,
        max_length=64,
        help_text=_("Unique VRF Name"))
    profile = DocumentReferenceField(VPNProfile)
    vrf_group = models.ForeignKey(
        VRFGroup, verbose_name=_("VRF Group"),
        null=True, blank=True
    )
    rd = models.CharField(
        _("RD"),
        max_length=21,
        validators=[check_rd],
        null=True, blank=True,
        help_text=_("Route Distinguisher in form of ASN:N or IP:N"))
    # RFC2685-compatible VPN id
    vpn_id = models.CharField(
        _("VPN ID"),
        max_length=15,
        help_text=_("RFC2685 compatible VPN ID"),
        unique=True
    )
    afi_ipv4 = models.BooleanField(
        _("IPv4"),
        default=True,
        help_text=_("Enable IPv4 Address Family"))
    afi_ipv6 = models.BooleanField(
        _("IPv6"),
        default=False,
        help_text=_("Enable IPv6 Address Family"))
    project = models.ForeignKey(
        Project, verbose_name="Project",
        null=True, blank=True, related_name="vrf_set")
    description = models.TextField(
        _("Description"), blank=True, null=True)
    tt = models.IntegerField(
        _("TT"),
        blank=True,
        null=True,
        help_text=_("Ticket #"))
    tags = TagsField(_("Tags"), null=True, blank=True)
    state = DocumentReferenceField(
        State,
        null=True, blank=True
    )
    allocated_till = models.DateField(
        _("Allocated till"),
        null=True,
        blank=True,
        help_text=_("VRF temporary allocated till the date"))
    source = models.CharField(
        "Source",
        max_length=1,
        choices=[
            ("M", "Manual"),
            ("i", "Interface"),
            ("m", "MPLS"),
            ("c", "ConfDB")
        ],
        null=False, blank=False,
        default="M"
    )
    administrative_domain = models.ForeignKey(
        AdministrativeDomain, verbose_name="Administrative domain",
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name="adm_domain_set")
    direct_permissions = JSONField(blank=True, null=True)

    GLOBAL_RD = "0:0"
    IPv4_ROOT = "0.0.0.0/0"
    IPv6_ROOT = "::/0"

    def __str__(self):
        if self.rd == self.GLOBAL_RD:
            return u"global"
        else:
            return self.name

    _id_cache = cachetools.TTLCache(maxsize=1000, ttl=60)
    _vpn_id_cache = cachetools.TTLCache(maxsize=1000, ttl=60)

    @classmethod
    @cachetools.cachedmethod(
        operator.attrgetter("_id_cache"),
        lock=lambda _: id_lock)
    def get_by_id(cls, id):
        vrf = VRF.objects.filter(id=id)[:1]
        if vrf:
            return vrf[0]
        return None

    @classmethod
    @cachetools.cachedmethod(
        operator.attrgetter("_vpn_id_cache"),
        lock=lambda _: id_lock)
    def get_by_vpn_id(cls, vpn_id):
        vrf = VRF.objects.filter(vpn_id=vpn_id)[:1]
        if vrf:
            return vrf[0]
        return None

    def get_absolute_url(self):
        return site.reverse("ip:vrf:change", self.id)

    @classmethod
    def get_global(cls):
        """
        Returns VRF 0:0
        """
        return VRF.get_by_vpn_id(cls.GLOBAL_RD)

    def save(self, **kwargs):
        """
        Create root entries for all enabled AFIs
        """
        from .prefix import Prefix

        # Generate unique rd, if empty
        if not self.vpn_id:
            vdata = {
                "type": "VRF",
                "name": self.name,
                "rd": self.rd
            }
            self.vpn_id = get_vpn_id(vdata)
        if self.initial_data["id"]:
            # Delete empty ipv4 root if AFI changed
            if self.initial_data.get("afi_ipv4") != self.afi_ipv4 and not self.afi_ipv4:
                root = Prefix.objects.filter(vrf=self, afi="4", prefix=self.IPv4_ROOT)[:1]
                if root:
                    root = root[0]
                    if root.is_empty():
                        root.disable_delete_protection()
                        root.delete()
                    else:
                        # Cannot change until emptied
                        self.afi_ipv4 = True
            # Delete empty ipv4 root if AFI changed
            if self.initial_data.get("afi_ipv6") != self.afi_ipv6 and not self.afi_ipv6:
                root = Prefix.objects.filter(vrf=self, afi="6", prefix=self.IPv6_ROOT)[:1]
                if root:
                    root = root[0]
                    if root.is_empty():
                        root.disable_delete_protection()
                        root.delete()
                    else:
                        # Cannot change until emptied
                        self.afi_ipv6 = True
        if self.direct_permissions:
            is_prefix_perm.clean(self.direct_permissions)
        # Save VRF
        super(VRF, self).save(**kwargs)
        if self.afi_ipv4:
            # Create IPv4 root, if not exists
            Prefix.objects.get_or_create(
                vrf=self, afi="4", prefix=self.IPv4_ROOT,
                defaults={
                    "description": "IPv4 Root",
                    "profile": self.profile.default_prefix_profile
                })
        if self.afi_ipv6:
            # Create IPv6 root, if not exists
            Prefix.objects.get_or_create(
                vrf=self, afi="6", prefix=self.IPv6_ROOT,
                defaults={
                    "description": "IPv6 Root",
                    "profile": self.profile.default_prefix_profile
                })

    def get_index(self):
        """
        Full-text search
        """
        content = [self.name, str(self.rd)]
        card = "VRF %s. RD %s" % (self.name, self.rd)
        if self.description:
            content += [self.description]
            card += " (%s)" % self.description
        r = {
            "id": "ip.vrf:%s" % self.id,
            "title": self.name,
            "content": "\n".join(content),
            "card": card
        }
        if self.tags:
            r["tags"] = self.tags
        return r

    @classmethod
    def get_search_result_url(cls, obj_id):
        return "/api/card/view/vrf/%s/" % obj_id

    def delete(self, *args, **kwargs):
        # Cleanup prefixes
        self.afi_ipv4 = False
        self.afi_ipv6 = False
        self.save()
        # Delete
        super(VRF, self).delete(*args, **kwargs)

    def get_permission(self):
        return self.direct_permissions or []

    @classmethod
    def read_Q(cls, user, include_prefix=True):
        from .prefix import Prefix
        if user.is_superuser:
            return Q()  # No restrictions
        ads = tuple(UserAccess.get_domains(user))
        groups = list(user.groups.values_list("id", flat=True))
        q = "EXISTS(SELECT 1 FROM jsonb_array_elements(direct_permissions) perm " \
            "WHERE (administrative_domain_id isnull %s) AND (perm -> 0 @> '%s' OR perm -> 1 <@ '%s'))" % (
                "" if not ads else "OR administrative_domain_id IN %s" % str(ads),
                str(user.id), str(groups))
        if include_prefix:
            vrf_ids = set(Prefix.objects.filter(Prefix.read_Q(user)).values_list("vrf_id", flat=True))
            if vrf_ids:
                q += " OR ip_vrf.id = ANY(ARRAY%s)" % str(list(vrf_ids))
        return SQL(q)

    def has_access(self, user, include_prefix=True):
        from .prefix import Prefix
        # filter(administrative_domain__in=UserAccess.get_domains(user)
        if user.is_superuser:
            return True
        ads = UserAccess.get_domains(user)
        if self.administrative_domain and self.administrative_domain not in ads:
            # Default deny
            return False
        groups = set(user.groups.values_list("id", flat=True))
        r = [perm for p_user, p_group, perm in self.get_permission() if p_user == user.id or p_group in groups]
        if include_prefix:
            r = Prefix.has_access(user, self, self.afi_ipv4, "0.0.0.0/0")
        return r
