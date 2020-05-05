# ---------------------------------------------------------------------
# SAE API
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.core.service.api import API, APIError, api
from noc.core.script.loader import loader
from noc.core.script.scheme import CLI_PROTOCOLS, HTTP_PROTOCOLS, PROTOCOLS, BEEF
from noc.sa.models.managedobject import (
    ManagedObject,
    CREDENTIAL_CACHE_VERSION,
)  # noqa Do not delete
from noc.sa.models.objectcapabilities import ObjectCapabilities
from noc.sa.models.profile import Profile
from noc.inv.models.vendor import Vendor
from noc.inv.models.platform import Platform
from noc.inv.models.firmware import Firmware
from noc.main.models.template import Template
from noc.main.models.extstorage import ExtStorage
from noc.core.cache.decorator import cachedmethod
from noc.core.dcs.base import ResolutionError
from noc.config import config
from noc.core.perf import metrics

# Increase whenever new field added or removed
CREDENTIALS_CACHE_VERSION = 2


class SAEAPI(API):
    """
    SAE API
    """

    name = "sae"

    RUN_SQL = """
        SELECT
            mo.name, mo.is_managed, mo.profile,
            mo.vendor, mo.platform, mo.version,
            mo.scheme, mo.address, mo.port,
            mo."user", mo.password, mo.super_password, mo.remote_path,
            mo.snmp_ro, mo.pool, mo.software_image,
            mo.auth_profile_id,
            ap.user, ap.password, ap.super_password,
            ap.snmp_ro, ap.snmp_rw,
            mo.cli_privilege_policy, mop.cli_privilege_policy,
            mo.access_preference, mop.access_preference,
            mop.beef_storage, mop.beef_path_template_id,
            (
              SELECT json_object_agg(key, value)
              FROM sa_managedobjectattribute
              WHERE managed_object_id = %s
            )
        FROM
            sa_managedobject mo
            JOIN sa_managedobjectprofile mop ON (mo.object_profile_id = mop.id)
            LEFT JOIN sa_authprofile ap ON (mo.auth_profile_id = ap.id)
        WHERE mo.id = %s
    """

    async def resolve_activator(self, pool):
        sn = "activator-%s" % pool
        for i in range(config.sae.activator_resolution_retries):
            try:
                svc = await self.service.dcs.resolve(
                    sn, timeout=config.sae.activator_resolution_timeout
                )
                return svc
            except ResolutionError as e:
                self.logger.info("Cannot resolve %s: %s", sn, e)
                metrics["error", ("type", "resolve_activator")] += 1
        return None

    async def get_activator_url(self, pool):
        svc = await self.resolve_activator(pool)
        if svc:
            return "http://%s/api/activator/" % svc
        else:
            metrics["error", ("type", "empty_activator_list_response")] += 1
            return None

    @api
    async def script(self, object_id, script, args=None, timeout=None):
        """
        Execute SA script against ManagedObject
        :param object_id: Managed Object id
        :param script: Script name (Either with or without profile)
        :param args: Dict with input arguments
        :param timeout: Script timeout in seconds
        """
        # Resolve object data
        data = await self.service.run_in_executor("db", self.get_object_data, object_id)
        # Find pool name
        pool = self.service.get_pool_name(data["pool_id"])
        if not pool:
            metrics["error", ("type", "pool_not_found")] += 1
            raise APIError("Pool not found")
        # Check script is exists
        script_name = "%s.%s" % (data["profile"], script)
        if not loader.has_script(script_name):
            metrics["error", ("type", "invalid_scripts_request")] += 1
            raise APIError("Invalid script")
        #
        url = await self.get_activator_url(pool)
        if not url:
            raise APIError("No active activators for pool '%s'" % pool)
        return self.redirect(
            url,
            "script",
            [
                script_name,
                data["credentials"],
                data["capabilities"],
                data["version"],
                args,
                timeout,
            ],
        )

    @api
    async def get_credentials(self, object_id):
        # Resolve object data
        data = await self.service.run_in_executor("db", self.get_object_data, object_id)
        # Find pool name
        pool = self.service.get_pool_name(data["pool_id"])
        if not pool:
            metrics["error", ("type", "pool_not_found")] += 1
            raise APIError("Pool not found")
        data["pool"] = pool
        return data

    @cachedmethod(key="cred-%s", version=CREDENTIAL_CACHE_VERSION)
    def get_object_data(self, object_id):
        """
        Worker to resolve credentials
        """
        object_id = int(object_id)
        # Get Object's attributes
        with self.service.get_pg_connect() as connection:
            cursor = connection.cursor()
            cursor.execute(self.RUN_SQL, [object_id, object_id])
            data = cursor.fetchall()
        if not data:
            metrics["error", ("type", "object_not_found")] += 1
            raise APIError("Object is not found")
        # Build capabilities
        capabilities = ObjectCapabilities.get_capabilities(object_id)
        # Get object credentials
        (
            name,
            is_managed,
            profile,
            vendor,
            platform,
            version,
            scheme,
            address,
            port,
            user,
            password,
            super_password,
            remote_path,
            snmp_ro,
            pool_id,
            sw_image,
            auth_profile_id,
            ap_user,
            ap_password,
            ap_super_password,
            ap_snmp_ro,
            ap_snmp_rw,
            privilege_policy,
            p_privilege_policy,
            access_preference,
            p_access_preference,
            beef_storage_id,
            beef_path_template_id,
            attrs,
        ) = data[0]
        # Check object is managed
        if not is_managed:
            metrics["error", ("type", "object_not_managed")] += 1
            raise APIError("Object is not managed")
        if auth_profile_id:
            user = ap_user
            password = ap_password
            super_password = ap_super_password
            snmp_ro = ap_snmp_ro
            snmp_rw = ap_snmp_rw  # noqa just to be
        #
        if privilege_policy == "E":
            raise_privileges = True
        elif privilege_policy == "P":
            raise_privileges = p_privilege_policy == "E"
        else:
            raise_privileges = False
        if access_preference == "P":
            access_preference = p_access_preference
        # Build credentials
        credentials = {
            "name": name,
            "address": address,
            "user": user,
            "password": password,
            "super_password": super_password,
            "path": remote_path,
            "raise_privileges": raise_privileges,
            "access_preference": access_preference,
        }
        if snmp_ro:
            credentials["snmp_ro"] = snmp_ro
            if capabilities.get("SNMP | v2c"):
                credentials["snmp_version"] = "v2c"
            elif capabilities.get("SNMP | v1"):
                credentials["snmp_version"] = "v1"
        if scheme in CLI_PROTOCOLS:
            credentials["cli_protocol"] = PROTOCOLS[scheme]
            if port:
                credentials["cli_port"] = port
        elif scheme in HTTP_PROTOCOLS:
            credentials["http_protocol"] = PROTOCOLS[scheme]
            if port:
                credentials["http_port"] = port
        # Build version
        if vendor and platform and version:
            vendor = Vendor.get_by_id(vendor)
            version = {
                "vendor": vendor.code[0] if vendor.code else vendor.name,
                "platform": Platform.get_by_id(platform).name,
                "version": Firmware.get_by_id(version).version,
            }
            if sw_image:
                version["image"] = sw_image
            if attrs:
                version["attributes"] = attrs
        else:
            version = None
        # Beef processing
        if scheme == BEEF and beef_storage_id and beef_path_template_id:
            mo = ManagedObject.get_by_id(object_id)
            tpl = Template.get_by_id(beef_path_template_id)
            beef_path = tpl.render_subject(object=mo)
            if beef_path:
                storage = ExtStorage.get_by_id(beef_storage_id)
                credentials["beef_storage_url"] = storage.url
                credentials["beef_path"] = beef_path
        return dict(
            profile=Profile.get_by_id(profile).name,
            pool_id=pool_id,
            credentials=credentials,
            capabilities=capabilities,
            version=version,
        )
