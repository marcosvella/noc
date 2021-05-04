# ----------------------------------------------------------------------
# Label REST API
# ----------------------------------------------------------------------
# Copyright (C) 2007-2021 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# NOC modules
from noc.main.models.label import Label
from ..models.label import DefaultLabelItem, LabelItem, FormLabelItem
from ..utils.ref import get_reference
from ..utils.rest.document import DocumentResourceAPI
from ..utils.rest.op import FilterExact, FuncFilter


class LabelAPI(DocumentResourceAPI[Label]):
    prefix = "/api/ui/label"
    model = Label
    list_ops = [
        FuncFilter("query", function=lambda qs, value: qs.filter(name__regex=value)),
        FilterExact("name"),
    ]

    @classmethod
    def item_to_label(cls, item: Label) -> LabelItem:
        return LabelItem(
            id=str(item.name),
            name=str(item.name),
            is_protected=item.is_protected,
            scope=item.name.rsplit("::", 1)[0] if item.is_scoped else "",
            value=item.name.split("::")[-1],
            bg_color1=f"#{item.bg_color1:06x}",
            fg_color1=f"#{item.fg_color1:06x}",
            bg_color2=f"#{item.bg_color2:06x}",
            fg_color2=f"#{item.fg_color2:06x}",
        )

    @classmethod
    def item_to_default(cls, item: Label) -> DefaultLabelItem:
        return DefaultLabelItem(
            id=str(item.id),
            name=str(item.name),
            description=item.description,
            bg_color1=item.bg_color1,
            fg_color1=item.fg_color1,
            bg_color2=item.bg_color2,
            fg_color2=item.fg_color2,
            is_protected=item.is_protected,
            is_autogenerated=item.is_autogenerated,
            # Label scope
            enable_agent=item.enable_agent,
            enable_service=item.enable_service,
            enable_serviceprofile=item.enable_serviceprofile,
            enable_managedobject=item.enable_managedobject,
            enable_managedobjectprofile=item.enable_managedobjectprofile,
            enable_administrativedomain=item.enable_administrativedomain,
            enable_authprofile=item.enable_authprofile,
            enable_commandsnippet=item.enable_commandsnippet,
            enable_allocationgroup=item.enable_allocationgroup,
            enable_networksegment=item.enable_networksegment,
            enable_object=item.enable_object,
            enable_objectmodel=item.enable_objectmodel,
            enable_platform=item.enable_platform,
            enable_resourcegroup=item.enable_resourcegroup,
            enable_sensor=item.enable_sensor,
            enable_sensorprofile=item.enable_sensorprofile,
            enable_subscriber=item.enable_subscriber,
            enable_subscriberprofile=item.enable_subscriberprofile,
            enable_supplier=item.enable_supplier,
            enable_supplierprofile=item.enable_supplierprofile,
            enable_dnszone=item.enable_dnszone,
            enable_dnszonerecord=item.enable_dnszonerecord,
            enable_division=item.enable_division,
            enable_kbentry=item.enable_kbentry,
            enable_ipaddress=item.enable_ipaddress,
            enable_addressprofile=item.enable_addressprofile,
            enable_ipaddressrange=item.enable_ipaddressrange,
            enable_ipprefix=item.enable_ipprefix,
            enable_prefixprofile=item.enable_prefixprofile,
            enable_vrf=item.enable_vrf,
            enable_vrfgroup=item.enable_vrfgroup,
            enable_asn=item.enable_asn,
            enable_assetpeer=item.enable_assetpeer,
            enable_peer=item.enable_peer,
            enable_vc=item.enable_vc,
            enable_vlan=item.enable_vlan,
            enable_vlanprofile=item.enable_vlanprofile,
            enable_vpn=item.enable_vpn,
            enable_vpnprofile=item.enable_vpnprofile,
            enable_slaprobe=item.enable_slaprobe,
            enable_slaprofile=item.enable_slaprofile,
            enable_alarm=item.enable_alarm,
            expose_metric=item.expose_metric,
            expose_datastream=item.expose_datastream,
            remote_system=get_reference(item.remote_system),
            remote_id=item.remote_id,
        )

    @classmethod
    def item_to_form(cls, item: Label) -> FormLabelItem:
        return FormLabelItem(
            name=item.name,
            description=item.description,
            bg_color1=item.bg_color1,
            fg_color1=item.fg_color1,
            bg_color2=item.bg_color2,
            fg_color2=item.fg_color2,
            is_protected=item.is_protected,
            enable_agent=item.enable_agent,
            enable_service=item.enable_service,
            enable_serviceprofile=item.enable_serviceprofile,
            enable_managedobject=item.enable_managedobject,
            enable_managedobjectprofile=item.enable_managedobjectprofile,
            enable_administrativedomain=item.enable_administrativedomain,
            enable_authprofile=item.enable_authprofile,
            enable_commandsnippet=item.enable_commandsnippet,
            enable_allocationgroup=item.enable_allocationgroup,
            enable_networksegment=item.enable_networksegment,
            enable_object=item.enable_object,
            enable_objectmodel=item.enable_objectmodel,
            enable_platform=item.enable_platform,
            enable_resourcegroup=item.enable_resourcegroup,
            enable_sensor=item.enable_sensor,
            enable_sensorprofile=item.enable_sensorprofile,
            enable_subscriber=item.enable_subscriber,
            enable_subscriberprofile=item.enable_subscriberprofile,
            enable_supplier=item.enable_supplier,
            enable_supplierprofile=item.enable_supplierprofile,
            enable_dnszone=item.enable_dnszone,
            enable_dnszonerecord=item.enable_dnszonerecord,
            enable_division=item.enable_division,
            enable_kbentry=item.enable_kbentry,
            enable_ipaddress=item.enable_ipaddress,
            enable_addressprofile=item.enable_addressprofile,
            enable_ipaddressrange=item.enable_ipaddressrange,
            enable_ipprefix=item.enable_ipprefix,
            enable_prefixprofile=item.enable_prefixprofile,
            enable_vrf=item.enable_vrf,
            enable_vrfgroup=item.enable_vrfgroup,
            enable_asn=item.enable_asn,
            enable_assetpeer=item.enable_assetpeer,
            enable_peer=item.enable_peer,
            enable_vc=item.enable_vc,
            enable_vlan=item.enable_vlan,
            enable_vlanprofile=item.enable_vlanprofile,
            enable_vpn=item.enable_vpn,
            enable_vpnprofile=item.enable_vpnprofile,
            enable_slaprobe=item.enable_slaprobe,
            enable_slaprofile=item.enable_slaprofile,
            enable_alarm=item.enable_alarm,
            expose_metric=item.expose_metric,
            expose_datastream=item.expose_datastream,
        )


router = LabelAPI().router
