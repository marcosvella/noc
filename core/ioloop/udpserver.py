# ----------------------------------------------------------------------
# Tornado IOLoop UDP server
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import socket
import platform
import errno
import os
import sys

# Third-party modules
from tornado.ioloop import IOLoop
from tornado.platform.auto import set_close_exec
from tornado import process
from typing import Iterable, Tuple, Optional, Any


class UDPServer(object):
    def __init__(self):
        self._sockets = {}  # fd -> socket object
        self._pending_sockets = []
        self._started: bool = False

    def iter_listen(self, cfg: str) -> Iterable[Tuple[str, int]]:
        """
        Parses listen configuration and yield (address, port) tuples.
        Listen configuration is comma-separated string with items:
        * address:port
        * port

        :param cfg:
        :return:
        """
        for listen in cfg.split(","):
            listen = listen.strip()
            if ":" in listen:
                addr, port = listen.split(":")
            else:
                addr, port = "", listen
            yield addr, int(port)

    def listen(self, port: int, address: str = "") -> None:
        """Starts accepting connections on the given port.

        This method may be called more than once to listen on multiple ports.
        `listen` takes effect immediately; it is not necessary to call
        `UDPServer.start` afterwards.  It is, however, necessary to start
        the `.IOLoop`.
        """
        sockets = self.bind_udp_sockets(port, address=address)
        self.add_sockets(sockets)

    def add_sockets(self, sockets):
        """Makes this server start accepting connections on the given sockets.

        The ``sockets`` parameter is a list of socket objects such as
        those returned by `~tornado.netutil.bind_sockets`.
        `add_sockets` is typically used in combination with that
        method and `tornado.process.fork_processes` to provide greater
        control over the initialization of a multi-process server.
        """
        for sock in sockets:
            self._sockets[sock.fileno()] = sock
            IOLoop.current().add_handler(sock.fileno(), self.accept_handler, IOLoop.READ)

    def add_socket(self, socket):
        """Singular version of `add_sockets`.  Takes a single socket object."""
        self.add_sockets([socket])

    def bind(self, port, address=None, family=socket.AF_UNSPEC, backlog=128):
        """Binds this server to the given port on the given address.

        To start the server, call `start`. If you want to run this server
        in a single process, you can call `listen` as a shortcut to the
        sequence of `bind` and `start` calls.

        Address may be either an IP address or hostname.  If it's a hostname,
        the server will listen on all IP addresses associated with the
        name.  Address may be an empty string or None to listen on all
        available interfaces.  Family may be set to either `socket.AF_INET`
        or `socket.AF_INET6` to restrict to IPv4 or IPv6 addresses, otherwise
        both will be used if available.

        The ``backlog`` argument has the same meaning as for
        `socket.listen <socket.socket.listen>`.

        This method may be called multiple times prior to `start` to listen
        on multiple ports or interfaces.
        """
        sockets = self.bind_udp_sockets(port, address=address, family=family, backlog=backlog)
        if self._started:
            self.add_sockets(sockets)
        else:
            self._pending_sockets.extend(sockets)

    def start(self, num_processes: int = 1):
        """Starts this server in the `.IOLoop`.

        By default, we run the server in this process and do not fork any
        additional child process.

        If num_processes is ``None`` or <= 0, we detect the number of cores
        available on this machine and fork that number of child
        processes. If num_processes is given and > 1, we fork that
        specific number of sub-processes.

        Since we use processes and not threads, there is no shared memory
        between any server code.

        Note that multiple processes are not compatible with the autoreload
        module (or the ``autoreload=True`` option to `tornado.web.Application`
        which defaults to True when ``debug=True``).
        When using multiple processes, no IOLoops can be created or
        referenced until after the call to ``TCPServer.start(n)``.
        """
        assert not self._started
        self._started = True
        if num_processes != 1:
            process.fork_processes(num_processes)
        sockets = self._pending_sockets
        self._pending_sockets = []
        self.add_sockets(sockets)

    def stop(self):
        """Stops listening for new connections.

        Requests currently in progress may still continue after the
        server is stopped.
        """
        for fd, sock in self._sockets.items():
            IOLoop.current().remove_handler(fd)
            sock.close()

    def accept_handler(self, fd, events):
        sock = self._sockets[fd]
        while True:
            try:
                data, address = sock.recvfrom(2500)
            except OSError as e:
                if e.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise
            self.on_read(data, address)

    def on_read(self, data: bytes, address: Tuple[str, int]):
        """
        To be overriden
        """

    def bind_udp_sockets(
        self, port, address: str = None, family: int = socket.AF_UNSPEC, flags: Any = None
    ):
        """Creates listening sockets bound to the given port and address.

        Returns a list of socket objects (multiple sockets are returned if
        the given address maps to multiple IP addresses, which is most common
        for mixed IPv4 and IPv6 use).

        Address may be either an IP address or hostname.  If it's a hostname,
        the server will listen on all IP addresses associated with the
        name.  Address may be an empty string or None to listen on all
        available interfaces.  Family may be set to either `socket.AF_INET`
        or `socket.AF_INET6` to restrict to IPv4 or IPv6 addresses, otherwise
        both will be used if available.

        The ``backlog`` argument has the same meaning as for
        `socket.listen() <socket.socket.listen>`.

        ``flags`` is a bitmask of AI_* flags to `~socket.getaddrinfo`, like
        ``socket.AI_PASSIVE | socket.AI_NUMERICHOST``.
        """
        sockets = []
        if address == "":
            address = None
        if not socket.has_ipv6 and family == socket.AF_UNSPEC:
            # Python can be compiled with --disable-ipv6, which causes
            # operations on AF_INET6 sockets to fail, but does not
            # automatically exclude those results from getaddrinfo
            # results.
            # http://bugs.python.org/issue16208
            family = socket.AF_INET
        if flags is None:
            flags = socket.AI_PASSIVE
        bound_port = None
        for res in set(socket.getaddrinfo(address, port, family, socket.SOCK_DGRAM, 0, flags)):
            af, socktype, proto, canonname, sockaddr = res
            if (
                platform.system() == "Darwin"
                and address == "localhost"
                and af == socket.AF_INET6
                and sockaddr[3] != 0
            ):
                # Mac OS X includes a link-local address fe80::1%lo0 in the
                # getaddrinfo results for 'localhost'.  However, the firewall
                # doesn't understand that this is a local address and will
                # prompt for access (often repeatedly, due to an apparent
                # bug in its ability to remember granting access to an
                # application). Skip these addresses.
                continue
            try:
                sock = socket.socket(af, socktype, proto)
            except OSError as e:
                if e.args[0] == errno.EAFNOSUPPORT:
                    continue
                raise
            set_close_exec(sock.fileno())
            if os.name != "nt":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if af == socket.AF_INET6:
                # On linux, ipv6 sockets accept ipv4 too by default,
                # but this makes it impossible to bind to both
                # 0.0.0.0 in ipv4 and :: in ipv6.  On other systems,
                # separate sockets *must* be used to listen for both ipv4
                # and ipv6.  For consistency, always disable ipv4 on our
                # ipv6 sockets and use a separate ipv4 socket when needed.
                #
                # Python 2.x on windows doesn't have IPPROTO_IPV6.
                if hasattr(socket, "IPPROTO_IPV6"):
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

            # automatic port allocation with port=None
            # should bind on the same port on IPv4 and IPv6
            host, requested_port = sockaddr[:2]
            if requested_port == 0 and bound_port is not None:
                sockaddr = tuple([host, bound_port] + list(sockaddr[2:]))

            sock.setblocking(0)
            self.setup_socket(sock)
            sock.bind(sockaddr)
            bound_port = sock.getsockname()[1]
            sockets.append(sock)
        return sockets

    def enable_reuseport(self) -> bool:
        """
        Override if SO_REUSEPORT should be set
        :return:
        """
        return False

    def enable_freebind(self) -> bool:
        """
        Override if IP_FREEBIND should be set
        :return:
        """
        return True

    @property
    def has_reuseport(self) -> bool:
        return hasattr(socket, "SO_REUSEPORT")

    @property
    def has_frebind(self) -> bool:
        return self.get_ip_freebind() is not None

    def setup_socket(self, sock: "socket"):
        """
        Called after socket created but before .bind().
        Can be overriden to adjust socket options in superclasses
        :param sock: socket instance
        :return: None
        """
        # Set SO_REUSEPORT option
        if self.has_reuseport and self.enable_reuseport():
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # Set IP_FREEBIND option
        if self.has_frebind and self.enable_freebind():
            sock.setsockopt(socket.SOL_IP, self.get_ip_freebind(), 1)

    def get_ip_freebind(self) -> Optional[int]:
        """
        Many python distributions does not include IP_FREEBIND to socket module
        :return: IP_FREEBIND value or None
        """
        if hasattr(socket, "IP_FREEBIND"):
            # Valid distribution
            return socket.IP_FREEBIND
        if sys.platform == "linux2":
            return 15
        return None
