# Config Fetching

`Fetching` is the process of retrieving of device configuration.
Performed by [config check](../../admin/discovery/box/config.md) of [box discovery](../../admin/discovery/box/index.md).
According to the `Config Policy` setting in [Managed Object Profile](../../reference/concepts/managed-object-profile/index.md)
there are two method possible:

* Script
* Download from external storage

# Fetching via script
[get_config](../../dev/scripts/get_config.md) script for target platform is necessary.
Usually it is the second script besides [get_version](../../dev/scripts/get_version.md) to implement.

# Fetching from external storage
`Discovery` can download configuration from [External Storage](../../reference/concepts/external-storage/index.md).
Supposed that configuration supplied to storage via external process:
device uploads config by itself or some third-party system (like RANCID),
performs all dirty work for us. Fetching from external storage is
the integrated feature of `Discovery` and provided out-of-the box.
