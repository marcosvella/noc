# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# SA Profile Base
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re
import functools
import warnings

# Third-party modules
import tornado.gen
import six
from typing import Dict, Callable, Union, Optional

# NOC modules
from noc.core.ip import IPv4
from noc.sa.interfaces.base import InterfaceTypeError
from noc.core.ecma48 import strip_control_sequences
from noc.core.handler import get_handler
from noc.core.comp import smart_text, smart_bytes
from noc.core.deprecations import RemovedInNOC2002Warning


class BaseProfileMetaclass(type):
    BINARY_ATTRS = (
        "command_submit",
        "pattern_username",
        "pattern_password",
        "pattern_super_password",
        "pattern_prompt",
        "pattern_unprivileged_prompt",
        "pattern_syntax_error",
        "pattern_operation_error",
        "username_submit",
        "password_submit",
        "command_super",
    )

    def __new__(mcs, name, bases, attrs):
        n = type.__new__(mcs, name, bases, attrs)
        n.rogue_char_cleaners = n._get_rogue_chars_cleaners()
        #
        if n.command_more:
            warnings.warn(
                "%s: 'command_more' is deprecated and will be removed in NOC 20.2" % n.name,
                RemovedInNOC2002Warning,
            )
        if isinstance(n.pattern_more, six.string_types):
            warnings.warn(
                "%s: 'command_more' must be a list of (pattern, command). "
                "Support for textual 'command_more' will be removed in NOC 20.2" % n.name,
                RemovedInNOC2002Warning,
            )
            n.pattern_more = [(n.pattern_more, n.command_more)]
            n.command_more = None
        # Fix binary attributes
        for attr in mcs.BINARY_ATTRS:
            v = getattr(n, attr, None)
            if v is not None and isinstance(v, six.text_type):
                warnings.warn(
                    "%s: '%s' must be of binary type. Support for text values will be removed in NOC 20.2"
                    % (n.name, attr),
                    RemovedInNOC2002Warning,
                )
                setattr(n, attr, smart_bytes(v))
        # Fix command_more
        pattern_more = []
        for pattern, cmd in n.pattern_more:
            if not isinstance(pattern, six.binary_type):
                warnings.warn(
                    "%s: 'pattern_more' %r pattern must be of binary type. "
                    "Support for text values will be removed in NOC 20.2" % (n.name, pattern)
                )
                pattern = smart_bytes(pattern)
            if not isinstance(cmd, six.binary_type):
                warnings.warn(
                    "%s: 'pattern_more' %r command must be of binary type. "
                    "Support for text values will be removed in NOC 20.2" % (n.name, cmd)
                )
                cmd = smart_bytes(cmd)
            pattern_more += [(pattern, cmd)]
        n.pattern_more = pattern_more
        # Build patterns
        n.patterns = n._get_patterns()
        # Build effective snmp_display_hints for subclasses
        if n.name:
            snmp_display_hints = {}
            for b in bases:
                if issubclass(b, BaseProfile):
                    snmp_display_hints.update(b.snmp_display_hints)
            snmp_display_hints.update(attrs.get("snmp_display_hints", {}))
            n.snmp_display_hints = {
                k: snmp_display_hints[k] for k in snmp_display_hints if snmp_display_hints[k]
            }
        return n


class BaseProfile(six.with_metaclass(BaseProfileMetaclass, object)):
    """
    Equipment profile. Contains all equipment personality and specific
    """

    # Profile name in form <vendor>.<system>
    name = None
    #
    # Device capabilities
    #

    #
    # A list of supported access schemes.
    # Access schemes constants are defined
    # in noc.sa.protocols.sae_pb2
    # (TELNET, SSH, HTTP, etc)
    # @todo: Deprecated
    #
    supported_schemes = []
    # Regular expression to catch user name prompt
    # (Usually during telnet sessions)
    pattern_username = "([Uu]ser ?[Nn]ame|[Ll]ogin): ?"
    # Regulal expression to catch password prompt
    # (Telnet/SSH sessions)
    pattern_password = "[Pp]ass[Ww]ord: ?"
    # Regular expression to catch implicit super password prompt
    # (Telnet/SSH sessions)
    pattern_super_password = None
    # Regular expression to catch command prompt
    # (CLI Sessions)
    pattern_prompt = r"^\S*[>#]"
    # Regular expression to catch unpriveleged mode command prompt
    # (CLI Session)
    pattern_unprivileged_prompt = None
    # Regular expression to catch pager
    # (Used in command results)
    # If pattern_more is string, send command_more
    # If pattern_more is a list of (pattern,command)
    # send appropriate command
    pattern_more = "^---MORE---"
    # Regular expression (string or compiled) to catch the syntax errors in cli output.
    # If CLI output matches pattern_syntax_error,
    # then CLISyntaxError exception raised
    pattern_syntax_error = None
    # Regular expression (string or compiled) to catch the CLI commands errors in cli output.
    # If CLI output matches pattern_syntax_error and not matches
    # pattern_syntax_error, then CLIOperationError exception raised
    pattern_operation_error = None
    # Reqular expression to start setup sequence
    # defined in setup_sequence list
    pattern_start_setup = None
    # String or list of string to recognize continued multi-line commands
    # Multi-line commands must be sent at whole, as the prompt will be
    # not available until end of command
    # NB: Sending logic is implemented in *commands* script
    # Examples:
    # "^.+\\" -- treat trailing backspace as continuation
    # "banner\s+login\s+(\S+)" -- continue until matched group
    pattern_multiline_commands = None
    # MML end of block pattern
    pattern_mml_end = None
    # MML continue pattern
    pattern_mml_continue = None
    # Device can strip long hostname in various modes
    # i.e
    # my.very.long.hostname# converts to
    # my.very.long.hos(config)#
    # In this case set can_strip_hostname_to = 16
    # None by default
    can_strip_hostname_to = None
    # Sequence to be send to list forward pager
    # If pattern_more is string and is matched
    command_more = b"\n"
    # Sequence to be send at the end of all CLI commands
    command_submit = b"\n"
    # Sequence to submit username. Use "\n" if None
    username_submit = None
    # Sequence to submit password. Use "\n" if None
    password_submit = None
    # Callable accepting script instance
    # to set up additional script attributes
    # and methods. Use Profile.add_script_method()
    # to add methods
    setup_script = None
    # Callable accepting script instance
    # to set up session.
    setup_session = None
    # Callable accepting script instance
    # to finaly close session
    shutdown_session = None
    # Callable accepting script instance to set up http session
    setup_http_session = None
    # List of middleware names to be applied to each HTTP request
    # Refer to core.script.http.middleware for details
    # Middleware may be set as
    # * name
    # * handler, leading to BaseMiddleware instance
    # * (name, config)
    # * (handler, config)
    # Where config is dict of middleware's constructor parameters
    http_request_middleware = None
    # Callable acceptings script instance to finaly close http session
    shutdown_http_session = None
    # Sequence to disable pager
    #
    command_disable_pager = None
    # Sequence to gracefully close session
    #
    command_exit = None
    # Sequence to enable priveleged mode
    #
    command_super = None
    # Sequence to enter configuration mode
    #
    command_enter_config = None
    # Sequence to leave configuration mode
    #
    command_leave_config = None
    # Sequence to save configuration
    #
    command_save_config = None
    # String or callable to send on syntax error to perform cleanup
    # Callable accepts three arguments
    # * cli instance
    # * command that caused syntax error
    # * error response.
    # Coroutines are also accepted.
    # SyntaxError exception will be raised after cleanup procedure
    send_on_syntax_error = None
    # List of chars to be stripped out of input stream
    # before checking any regular expressions
    # (when Action.CLEAN_INPUT==True)
    rogue_chars = [b"\r"]
    # String to send just after telnet connect is established
    telnet_send_on_connect = None
    # Password sending mode for telnet
    # False - send password at once
    # True - send password by characters
    telnet_slow_send_password = False
    # Telnet NAWS negotiation
    telnet_naws = b"\x00\x80\x00\x80"
    # List of strings containing setup sequence
    # Setup sequence is initialized on pattern_start_setup during
    # startup phase
    # Strings sending one-by-one, waiting for response after
    # each string, excluding last one
    setup_sequence = None
    # Does the equipment supports bitlength netmasks
    # or netmask should be converted to traditional formats
    requires_netmask_conversion = False
    # Upper concurrent scripts limit, if set
    max_scripts = None
    # Default config parser name. Full path to BaseParser subclass
    # i.e noc.cm.parsers.Cisco.IOS.switch.IOSSwitchParser
    # Can be overriden in get_parser method
    default_parser = None
    # CLI timeouts
    # Timeout between connection established and login prompt
    cli_timeout_start = 60
    # Timeout after user name provided
    cli_timeout_user = 30
    # Timeout after password provided
    cli_timeout_password = 30
    # Timeout after submitting *command_super*
    cli_timeout_super = 10
    # Timeout waiting next setup sequence response
    cli_timeout_setup = 10
    # Amount of retries for enable passwords
    # Increase if box asks for enable password twice
    cli_retries_super_password = 1
    # Additional hints for snmp binary OctetString data processing
    # Contains mapping of
    # oid -> render_callable
    # if render_callable is None, translation is disabled and binary data processed by default way
    # Otherwise it must be a callable, accepting (oid, raw_data) parameter
    # where oid is varbind's oid value, while raw_data is raw binary data of varbind value.
    # Callable should return six.text_type
    # It is possible to return six.binary_type in very rare specific cases,
    # when you have intention to process binary output in script directly
    snmp_display_hints = (
        {}
    )  # type: Dict[six.text_type, Optional[Callable[[six.text_type, six.binary_type], Union[six.text_type, six.binary_type]]]]
    # Aggregate up to *snmp_metrics_get_chunk* oids
    # to one SNMP GET request
    snmp_metrics_get_chunk = 15
    # Timeout for snmp GET request
    snmp_metrics_get_timeout = 3
    # Aggregate up to *snmp_ifstatus_get_chunk* oids
    # to one SNMP GET request for get_interface_status_ex
    snmp_ifstatus_get_chunk = 15
    # Timeout for snmp GET request for get_interface_status_ex
    snmp_ifstatus_get_timeout = 2
    # Allow CLI sessions by default
    enable_cli_session = True
    # True - Send multiline command at once
    # False - Send multiline command line by line
    batch_send_multiline = True
    # String to separate MML response header from body
    mml_header_separator = "\r\n\r\n"
    # Always enclose MML command arguments with quotes
    # False - pass integers as unquoted
    mml_always_quote = False
    # Config tokenizer name, from noc.core.confdb.tokenizer.*
    config_tokenizer = None
    # Configuration for config tokenizer
    config_tokenizer_settings = {}
    # Config normalizer handler
    config_normalizer = None
    # Config normalizer settings
    config_normalizer_settings = {}
    # List of confdb default tokens
    # To be appended on every confdb initiation
    confdb_defaults = None
    # Config applicators
    # List of (<applicator handler>, <applicator settings>) or <applicator handler>
    config_applicators = None
    # List of default applicators
    # Activated by ConfDB `hints` section
    default_config_applicators = [
        "noc.core.confdb.applicator.rebase.RebaseApplicator",
        "noc.core.confdb.applicator.interfacetype.InterfaceTypeApplicator",
        "noc.core.confdb.applicator.adminstatus.DefaultAdminStatusApplicator",
        "noc.core.confdb.applicator.fitype.DefaultForwardingInstanceTypeApplicator",
        "noc.core.confdb.applicator.lldpstatus.DefaultLLDPStatusApplicator",
        "noc.core.confdb.applicator.loopdetectstatus.DefaultLoopDetectStatusApplicator",
        "noc.core.confdb.applicator.stpstatus.DefaultSTPStatusApplicator",
        "noc.core.confdb.applicator.stppriority.DefaultSTPPriorityApplicator",
        "noc.core.confdb.applicator.cdpstatus.DefaultCDPStatusApplicator",
        "noc.core.confdb.applicator.ntp.DefaultNTPModeApplicator",
        "noc.core.confdb.applicator.ntp.DefaultNTPVersionApplicator",
        # Finally apply meta
        "noc.core.confdb.applicator.meta.MetaApplicator",
    ]
    # Collators
    # List of (<collator handler>, <collator settings>) or <collator_handler>
    collators = None
    # Matchers are helper expressions to calculate and fill
    # script's is_XXX properties
    matchers = {}
    # Filled by metaclass
    patterns = {}

    def convert_prefix(self, prefix):
        """
        Convert ip prefix to the format accepted by router's CLI
        """
        if "/" in prefix and self.requires_netmask_conversion:
            prefix = IPv4(prefix)
            return "%s %s" % (prefix.address, prefix.netmask.address)
        return prefix

    def convert_mac_to_colon(self, mac):
        """
        Leave 00:11:22:33:44:55 style MAC-address untouched
        """
        return mac

    def convert_mac_to_cisco(self, mac):
        """
        Convert 00:11:22:33:44:55 style MAC-address to 0011.2233.4455
        """
        v = mac.replace(":", "").lower()
        return "%s.%s.%s" % (v[:4], v[4:8], v[8:])

    def convert_mac_to_huawei(self, mac):
        """
        Convert 00:11:22:33:44:55 style MAC-address to 0011.2233.4455
        """
        v = mac.replace(":", "").lower()
        return "%s-%s-%s" % (v[:4], v[4:8], v[8:])

    def convert_mac_to_dashed(self, mac):
        """
        Convert 00:11:22:33:44:55 style MAC-address to 00-11-22-33-44-55
        """
        v = mac.replace(":", "").lower()
        return "%s-%s-%s-%s-%s-%s" % (v[:2], v[2:4], v[4:6], v[6:8], v[8:10], v[10:])

    #
    # Convert 00:11:22:33:44:55 style MAC-address to local format
    # Can be changed in derived classes
    #
    convert_mac = convert_mac_to_colon

    def convert_interface_name(self, s):
        """
        Normalize interface name
        """
        return s

    # Cisco-like translation
    rx_cisco_interface_name = re.compile(
        r"^(?P<type>[a-z]{2})[a-z\-]*\s*"
        r"(?P<number>\d+(/\d+(/\d+)?)?(\.\d+(/\d+)*(\.\d+)?)?(:\d+(\.\d+)*)?(/[a-z]+\d+(\.\d+)?)?(A|B)?)$",
        re.IGNORECASE,
    )

    def convert_interface_name_cisco(self, s):
        """
        >>> Profile().convert_interface_name_cisco("Gi0")
        'Gi 0'
        >>> Profile().convert_interface_name_cisco("GigabitEthernet0")
        'Gi 0'
        >>> Profile().convert_interface_name_cisco("Gi 0")
        'Gi 0'
        >>> Profile().convert_interface_name_cisco("tengigabitethernet 1/0/1")
        'Te 1/0/1'
        >>> Profile().convert_interface_name_cisco("tengigabitethernet 1/0/1.5")
        'Te 1/0/1.5'
        >>> Profile().convert_interface_name_cisco("Se 0/1/0:0")
        'Se 0/1/0:0'
        >>> Profile().convert_interface_name_cisco("Se 0/1/0:0.10")
        'Se 0/1/0:0.10'
        >>> Profile().convert_interface_name_cisco("ATM1/1/ima0")
        'At 1/1/ima0'
        >>> Profile().convert_interface_name_cisco("Port-channel5B")
        'Po 5B'
        """
        match = self.rx_cisco_interface_name.match(s)
        if not match:
            raise InterfaceTypeError("Invalid interface '%s'" % s)
        return "%s %s" % (match.group("type").capitalize(), match.group("number"))

    def root_interface(self, name):
        """
        Returns root interface
        >>> Profile().root_interface("Gi 0/1")
        'Gi 0/1'
        >>> Profile().root_interface("Gi 0/1.15")
        'Gi 0/1'
        """
        name = name.split(".")[0]
        name = name.split(":")[0]
        return name

    def get_interface_names(self, name):
        """
        Return possible alternative interface names,
        i.e. for LLDP discovery *Local* method
        """
        return []

    def get_linecard(self, interface_name):
        """
        Returns linecard number related to interface
        >>> Profile().get_linecard("Gi 4/15")
        4
        >>> Profile().get_linecard("Lo")
        >>> Profile().get_linecard("ge-1/1/0")
        1
        """
        if " " in interface_name:
            l, r = interface_name.split(" ")
        elif "-" in interface_name:
            l, r = interface_name.split("-")
        else:
            return None
        if "/" in r:
            return int(r.split("/", 1)[0])
        else:
            return None

    # Cisco-like translation
    rx_num1 = re.compile(r"^[a-z]{2}[\- ](?P<number>\d+)/\d+/\d+([\:\.]\S+)?$", re.IGNORECASE)
    # D-Link-like translation
    rx_num2 = re.compile(r"^(?P<number>\d+)[\:\/]\d+$")

    def get_stack_number(self, interface_name):
        """
        Returns stack number related to interface
        >>> Profile().get_stack_number("Gi 1/4/15")
        1
        >>> Profile().get_stack_number("Lo")
        >>> Profile().get_stack_number("Te 2/0/1.5")
        2
        >>> Profile().get_stack_number("Se 0/1/0:0.10")
        0
        >>> Profile().get_stack_number("3:2")
        3
        >>> Profile().get_stack_number("3/2")
        3
        """
        match = self.rx_num1.match(interface_name)
        if match:
            return int(match.group("number"))
        else:
            match = self.rx_num2.match(interface_name)
            if match:
                return int(match.group("number"))
        return None

    def generate_prefix_list(self, name, pl):
        """
        Generate prefix list:
        name - name of prefix list
        pl -  is a list of (prefix, min_len, max_len)
        Strict - should tested prefix be exactly matched
        or should be more specific as well
        """
        raise NotImplementedError()

    #
    # Volatile strings:
    # A list of strings can be changed over time, which
    # can be sweeped out of config safely or None
    # Strings are regexpes, compiled with re.DOTALL|re.MULTILINE
    #
    config_volatile = None

    def cleaned_input(self, input):
        # type: (six.binary_type) -> six.binary_type
        """
        Preprocessor to clean up and normalize input from device.
        Delete ASCII sequences by default.
        Can be overriden to achieve desired behavior
        """
        return strip_control_sequences(input)

    def clean_rogue_chars(self, s):
        # type: (six.binary_type) -> six.binary_type
        if self.rogue_chars:
            for cleaner in self.rogue_char_cleaners:
                s = cleaner(s)
        return s

    def cleaned_config(self, cfg):
        """
        Clean up config
        """
        if self.config_volatile:
            # Wipe out volatile strings before returning result
            for r in self.config_volatile:
                rx = re.compile(r, re.DOTALL | re.MULTILINE)
                cfg = rx.sub("", cfg)
        # Prevent serialization errors
        return smart_text(cfg, errors="ignore")

    def clean_lldp_neighbor(self, obj, neighbor):
        """
        Normalize and rewrite IGetLLDPNeighbors.neighbors structure
        in LLDP topology discovery.
        Remote object profile's .clean_lldp_neighbor() used

        :param obj: Managed Object reference
        :param neighbor: IGetLLDPNeighbors.neighbors item
        :return: IGetLLDPNeighbors.neighbors item
        """
        return neighbor

    @staticmethod
    def add_script_method(script, name, method):
        f = functools.partial(method, script)
        if not hasattr(f, "__name__"):
            setattr(f, "__name__", name)
        setattr(script, name, f)

    @classmethod
    def cmp_version(cls, v1, v2):
        """
        Compare two versions.
        Must return:
           <0 , if v1<v2
            0 , if v1==v2
           >0 , if v1>v2
         None , if v1 and v2 cannot be compared

        Default implementation compares a versions in format
        N1. .. .NM
        """
        p1 = [int(x) for x in v1.split(".")]
        p2 = [int(x) for x in v2.split(".")]
        # cmp-like semantic
        return (p1 > p2) - (p1 < p2)

    @classmethod
    def get_parser(cls, vendor, platform, version):
        """
        Returns full path to BaseParser instance to be used
        as config parser. None means no parser for particular platform
        """
        if six.PY3:
            return None
        return cls.default_parser

    @classmethod
    def get_interface_type(cls, name):
        """
        Return IGetInterface-compatible interface type
        :param Name: Normalized interface name
        """
        return None

    @classmethod
    def initialize(cls):
        """
        Called once by profile loader
        """

        def compile(pattern):
            if not pattern:
                return None
            if isinstance(pattern, six.string_types):
                return re.compile(pattern)
            if isinstance(pattern, six.binary_type):
                return re.compile(pattern)
            return pattern

        cls.rx_pattern_syntax_error = compile(cls.pattern_syntax_error)
        cls.rx_pattern_operation_error = compile(cls.pattern_operation_error)
        cls.rx_pattern_operation_error_str = compile(smart_text(cls.pattern_operation_error))

    @classmethod
    def get_telnet_naws(cls):
        # type: () -> six.binary_type
        return cls.telnet_naws

    @classmethod
    def allow_cli_session(cls, platform, version):
        return cls.enable_cli_session

    @classmethod
    @tornado.gen.coroutine
    def send_backspaces(cls, cli, command, error_text):
        # Send backspaces to clean up previous command
        yield cli.iostream.write(b"\x08" * len(command))
        # Send command_submit to force prompt
        yield cli.iostream.write(cls.command_submit)
        # Wait until prompt
        yield cli.read_until_prompt()

    def get_mml_login(self, script):
        """
        Generate MML login command. .get_mml_command may be used for formatting
        :param script: BaseScript instance
        :return: Login command
        """
        raise NotImplementedError()

    def get_mml_command(self, cmd, **kwargs):
        """
        Generate MML command
        :param cmd:
        :param kwargs:
        :return:
        """

        def qi(s):
            return '"%s"' % s

        def nqi(s):
            if isinstance(s, six.string_types):
                return '"%s"' % s
            else:
                return str(s)

        if ";" in cmd:
            return "%s\r\n" % cmd
        r = [cmd, ":"]
        if kwargs:
            if self.mml_always_quote:
                q = qi
            else:
                q = nqi
            r += [", ".join("%s=%s" % (k, q(kwargs[k])) for k in kwargs)]
        r += [";", "\r\n"]
        return "".join(r)

    def parse_mml_header(self, header):
        """
        Parse MML response header
        :param header: Response header
        :return: error code, error message
        """
        raise NotImplementedError()

    @classmethod
    def get_config_tokenizer(cls, object):
        """
        Returns config tokenizer name and settings.
        object.matchers.XXXX can be used
        :param object: ManagedObject instance
        :return: config tokenizer name, config tokenizer settings
        """
        return cls.config_tokenizer, cls.config_tokenizer_settings

    @classmethod
    def get_config_normalizer(cls, object):
        """
        Returns config normalizer name and settings
        :param object: ManagedObject instance
        :return:
        """
        return cls.config_normalizer, cls.config_normalizer_settings

    @classmethod
    def get_confdb_defaults(cls, object):
        """
        Returns a list of confdb defaults to be inserted on every ConfDB creation
        :param object:
        :return:
        """
        return cls.confdb_defaults

    @classmethod
    def iter_config_applicators(cls, object, confdb):
        """
        Returns config applicators and settings
        :param object: Managed Object instance
        :param confdb: ConfDB Engine instance
        :return: Iterate active config applicators (BaseApplicator instances)
        """

        def get_applicator(cfg):
            if isinstance(cfg, six.string_types):
                a_handler, a_cfg = cfg, {}
            else:
                a_handler, a_cfg = cfg
            if not a_handler.startswith("noc."):
                a_handler = "noc.sa.profiles.%s.confdb.applicator.%s" % (profile_name, a_handler)
            a_cls = get_handler(a_handler)
            assert a_cls, "Invalid applicator %s" % a_handler
            applicator = a_cls(object, confdb, **a_cfg)
            if applicator.can_apply():
                return applicator
            return None

        profile_name = object.get_profile().name
        # Apply default applicators
        if cls.default_config_applicators:
            for acfg in cls.default_config_applicators:
                a = get_applicator(acfg)
                if a:
                    yield a
        # Apply profile local applicators
        if cls.config_applicators:
            for acfg in cls.config_applicators:
                a = get_applicator(acfg)
                if a:
                    yield a

    @classmethod
    def iter_collators(cls, obj):
        def get_collator(cfg):
            if isinstance(cfg, six.string_types):
                c_handler, c_cfg = cfg, {}
            else:
                c_handler, c_cfg = cfg
            if not c_handler.startswith("noc."):
                c_handler = "noc.sa.profiles.%s.confdb.collator.%s" % (profile_name, c_handler)
            c_cls = get_handler(c_handler)
            assert c_cls, "Invalid collator %s" % c_handler
            return c_cls(**c_cfg)

        profile_name = obj.get_profile().name
        if cls.collators:
            for c_cfg in cls.collators:
                c = get_collator(c_cfg)
                if c:
                    yield c

    @classmethod
    def get_http_request_middleware(cls, script):
        """
        Returns list of http_request_middleware.
        matchers.XXXX can be used?
        :param script: Script instance
        :return:
        """
        return cls.http_request_middleware

    @classmethod
    def get_snmp_display_hints(cls, script):
        """
        Returns a dict of snmp display_hints mapping.
        matchers.XXXX can be used
        :param script: Script instance
        :return:
        """
        return cls.snmp_display_hints

    @classmethod
    def has_confdb_support(cls, object):
        tcls, _ = cls.get_config_tokenizer(object)
        if not tcls:
            return False
        ncls, _ = cls.get_config_normalizer(object)
        if not ncls:
            return False
        return True

    @classmethod
    def _get_patterns(cls):
        """
        Return dict of compiled regular expressions
        """
        patterns = {
            "username": re.compile(cls.pattern_username, re.DOTALL | re.MULTILINE),
            "password": re.compile(cls.pattern_password, re.DOTALL | re.MULTILINE),
            "prompt": re.compile(cls.pattern_prompt, re.DOTALL | re.MULTILINE),
        }
        if cls.pattern_unprivileged_prompt:
            patterns["unprivileged_prompt"] = re.compile(
                cls.pattern_unprivileged_prompt, re.DOTALL | re.MULTILINE
            )
        if cls.pattern_super_password:
            patterns["super_password"] = re.compile(
                cls.pattern_super_password, re.DOTALL | re.MULTILINE
            )
        if cls.pattern_start_setup:
            patterns["setup"] = re.compile(cls.pattern_start_setup, re.DOTALL | re.MULTILINE)
        # .more_patterns is a list of (pattern, command)
        more_patterns = [x[0] for x in cls.pattern_more]
        patterns["more_commands"] = [x[1] for x in cls.pattern_more]
        # Merge pager patterns
        patterns["pager"] = re.compile(
            b"|".join(b"(%s)" % p for p in more_patterns), re.DOTALL | re.MULTILINE
        )
        patterns["more_patterns"] = [re.compile(p, re.MULTILINE | re.DOTALL) for p in more_patterns]
        patterns["more_patterns_commands"] = list(
            zip(patterns["more_patterns"], patterns["more_commands"])
        )
        return patterns

    @classmethod
    def _get_rogue_chars_cleaners(cls):
        def get_bytes_cleaner(s):
            def _inner(x):
                return x.replace(s, b"")

            return _inner

        def get_re_cleaner(s):
            def _inner(x):
                return s.sub(b"", x)

            return _inner

        chain = []
        if cls.rogue_chars:
            for rc in cls.rogue_chars:
                if isinstance(rc, six.text_type):
                    warnings.warn(
                        "%s: 'rogue_char' %r pattern must be of binary type. "
                        "Support for text values will be removed in NOC 20.2" % (cls.name, rc)
                    )
                    chain += [get_bytes_cleaner(smart_bytes(rc))]
                elif isinstance(rc, six.binary_type):
                    chain += [get_bytes_cleaner(rc)]
                elif hasattr(rc, "sub"):
                    if not isinstance(rc.pattern, six.binary_type):
                        # Recompile as binary re
                        warnings.warn(
                            "%s: 'rogue_char' %r pattern must be of binary type. "
                            "Support for text values will be removed in NOC 20.2"
                            % (cls.name, rc.pattern)
                        )
                        # Remove re.UNICODE flag
                        flags = rc.flags
                        if flags & re.UNICODE:
                            warnings.warn(
                                "%s: 'rogue_char' %r pattern cannot be compiled with re.UNICODE flag."
                                % (cls.name, rc.pattern)
                            )
                            flags &= ~re.UNICODE
                        rc = re.compile(smart_bytes(rc.pattern), flags)
                    chain += [get_re_cleaner(rc)]
                else:
                    raise ValueError("Invalid rogue char expression: %r" % rc)
        return chain
