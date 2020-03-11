%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}

%define git_url git://git.freedesktop.org/git/dbus/dbus

Summary:	D-Bus message bus
Name:		dbus
Version:	1.12.16
Release:	3
License:	GPLv2+ or AFL
Group:		System/Servers
Url:		http://www.freedesktop.org/Software/dbus
Source0:	http://dbus.freedesktop.org/releases/dbus/%{name}-%{version}.tar.gz
Source2:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/00-start-message-bus.sh
Source3:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus.socket
Source4:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus-daemon.service
Source5:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus.user.socket
Source6:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus-daemon.user.service
Patch1:		0001-tools-Use-Python3-for-GetAllMatchRules.patch
Patch2:		dbus-1.8.14-headers-clang.patch
# (fc) 1.0.2-5mdv disable fatal warnings on check (fd.o bug #13270)
Patch3:		dbus-1.0.2-disable_fatal_warning_on_check.patch
Patch5:		dbus-1.8.0-fix-disabling-of-xml-docs.patch
# (tpg) ClearLinux patches
Patch6:		malloc_trim.patch
Patch7:		memory.patch
%ifnarch riscv64
BuildRequires:	asciidoc
BuildRequires:	docbook2x
BuildRequires:	docbook-dtd412-xml
BuildRequires:	doxygen
BuildRequires:	xmlto
%endif
BuildRequires:	libtool
BuildRequires:	autoconf-archive
BuildRequires:	pkgconfig(expat)
BuildRequires:	pkgconfig(glib-2.0)
BuildRequires:	pkgconfig(libcap-ng)
BuildRequires:	pkgconfig(sm)
BuildRequires:	pkgconfig(x11)
BuildRequires:	pkgconfig(libsystemd)
BuildRequires:	systemd-macros
# To make sure _rundir is defined
BuildRequires:	rpm-build >= 1:5.4.10-79
Requires:	dbus-broker >= 16

%description
D-Bus is a system for sending messages between applications. It is
used both for the systemwide message bus service, and as a
per-user-login-session messaging facility.

%package common
Summary:	D-BUS message bus configuration
Group:		System/Configuration
BuildArch:	noarch
%{?systemd_requires}

%description common
The %{name}-common package provides the configuration and setup files for D-Bus
implementations to provide a System and User Message Bus.

%package daemon
Summary:	D-BUS message bus
Group:		System/Servers
%{?systemd_requires}
Requires:	dbus-common = %{EVRD}
Requires:	%{libname} = %{EVRD}
Requires:	dbus-tools = %{EVRD}
Requires(pre):	shadow

%description daemon
D-BUS is a system for sending messages between applications. It is
used both for the system-wide message bus service, and as a
per-user-login-session messaging facility.

%package tools
Summary:	D-BUS Tools and Utilities
Group:		System/Configuration
Requires:	%{libname} = %{EVRD}

%description tools
Tools and utilities to interact with a running D-Bus Message Bus, provided by
the reference implementation.

%package -n %{libname}
Summary:	Shared library for using D-Bus
Group:		System/Libraries

%description -n %{libname}
D-Bus shared library.

%package -n %{devname}
Summary:	Libraries and headers for D-Bus
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Provides:	%{name}-devel = %{EVRD}

%description -n %{devname}
Headers and static libraries for D-Bus.

%package x11
Summary:	X11-requiring add-ons for D-Bus
Group:		System/Servers
Requires:	%{name}-daemon = %{EVRD}

%description x11
D-Bus contains some tools that require Xlib to be installed, those are
in this separate package so server systems need not install X.

%package doc
Summary:	Developer documentation for D-BUS
Group:		Books/Computer books
Conflicts:	%{devname} < 1.2.20

%description doc
This package contains developer documentation for D-Bus along with
other supporting documentation such as the introspect dtd file.

%prep
%setup -q
%patch2 -p1 -b .clang~
#only disable in cooker to detect buggy programs
#patch3 -p1 -b .disable_fatal_warning_on_check
%patch5 -p1 -b .nodocs~
%patch6 -p1
%patch7 -p1

%build
%serverbuild_hardened
COMMON_ARGS=" --enable-user-session --enable-systemd --with-systemdsystemunitdir=%{_unitdir} \
	--with-systemduserunitdir=%{_userunitdir} --enable-inotify --enable-libaudit --disable-selinux \
	--with-system-pid-file=%{_rundir}/messagebus.pid  \
	--with-system-socket=%{_rundir}/dbus/system_bus_socket \
	--libexecdir=%{_libexecdir}/dbus-%{api} --disable-static"

%configure \
	$COMMON_ARGS \
	--enable-libaudit \
	--disable-tests \
	--disable-asserts \
%ifnarch riscv64
	--enable-doxygen-docs \
	--enable-xml-docs \
%endif
	--enable-x11-autolaunch \
	--with-x \
	--disable-verbose-mode

%make_build

%install
%make_install

# Obsolete, but still widely used, for drop-in configuration snippets.
install --directory %{buildroot}%{_sysconfdir}/dbus-%{api}/session.d
install --directory %{buildroot}%{_sysconfdir}/dbus-%{api}/system.d
install --directory %{buildroot}%{_datadir}/dbus-1/interfaces

# (tpg) needed for dbus-uuidgen
mkdir -p %{buildroot}%{_var}/lib/dbus
mkdir -p %{buildroot}/run/dbus

# Delete upstream units
rm -f %{buildroot}%{_unitdir}/dbus.{socket,service}
rm -f %{buildroot}%{_unitdir}/sockets.target.wants/dbus.socket
rm -f %{buildroot}%{_unitdir}/multi-user.target.wants/dbus.service
rm -f %{buildroot}%{_userunitdir}/dbus.{socket,service}
rm -f %{buildroot}%{_userunitdir}/sockets.target.wants/dbus.socket

# Install downstream units
install -Dp -m755 %{SOURCE2} %{buildroot}%{_sysconfdir}/X11/xinit/xinitrc.d/00-start-message-bus.sh
install -Dp -m644 %{SOURCE3} %{buildroot}%{_unitdir}/dbus.socket
install -Dp -m644 %{SOURCE4} %{buildroot}%{_unitdir}/dbus-daemon.service
install -Dp -m644 %{SOURCE5} %{buildroot}%{_userunitdir}/dbus.socket
install -Dp -m644 %{SOURCE6} %{buildroot}%{_userunitdir}/dbus-daemon.service

install -d %{buildroot}%{_presetdir}
cat > %{buildroot}%{_presetdir}/86-%{name}-common.preset << EOF
enable dbus.socket
EOF

%pre daemon
# create dbus user and group
getent group messagebus >/dev/null || groupadd -f -g messagebus -r messagebus
if ! getent passwd messagebus >/dev/null ; then
    if ! getent passwd messagebus >/dev/null ; then
    useradd -r -u messagebus -g messagebus -d '/' -s /sbin/nologin -c "System message bus" messagebus
    else
    useradd -r -g messagebus -d '/' -s /sbin/nologin -c "System message bus" messagebus
    fi
fi
exit 0

%post common
%systemd_post dbus.socket
%systemd_user_post dbus.socket

%post daemon
%systemd_post dbus-daemon.service
%systemd_user_post dbus-daemon.service

%preun common
%systemd_preun dbus.socket
%systemd_user_preun dbus.socket

%preun daemon
%systemd_preun dbus-daemon.service
%systemd_user_preun dbus-daemon.service

%postun common
%systemd_postun dbus.socket
%systemd_user_postun dbus.socket

%postun daemon
%systemd_postun dbus-daemon.service
%systemd_user_postun dbus-daemon.service

%triggerin -- setup
if [ $1 -ge 2 -o $2 -ge 2 ]; then

    if ! getent group messagebus >/dev/null 2>&1; then
	/usr/sbin/groupadd -r messagebus 2>/dev/null || :
    fi

    if ! getent passwd messagebus >/dev/null 2>&1; then
	/usr/sbin/useradd -r -c "system user for %{name}" -g messagebus -s /sbin/nologin -d / messagebus 2>/dev/null ||:
    fi
fi

%files common
%dir %{_sysconfdir}/dbus-%{api}
%dir %{_sysconfdir}/dbus-%{api}/session.d
%dir %{_sysconfdir}/dbus-%{api}/system.d
%dir %{_datadir}/dbus-%{api}
%config(noreplace) %{_sysconfdir}/dbus-%{api}/*.conf
%{_presetdir}/86-%{name}-common.preset
%{_datadir}/dbus-%{api}/system-services
%{_datadir}/dbus-%{api}/services
%{_datadir}/dbus-%{api}/interfaces
%{_datadir}/dbus-%{api}/session.conf
%{_datadir}/dbus-%{api}/system.conf
%{_sysusersdir}/dbus.conf
%{_unitdir}/dbus.socket
%{_userunitdir}/dbus.socket

%files daemon
%ghost %dir %{_rundir}/%{name}
%dir %{_localstatedir}/lib/dbus/
%{_bindir}/dbus-daemon
%{_bindir}/dbus-cleanup-sockets
%{_bindir}/dbus-run-session
%{_bindir}/dbus-test-tool
%ifnarch riscv64
%{_mandir}/man1/dbus-cleanup-sockets.1*
%{_mandir}/man1/dbus-daemon.1*
%{_mandir}/man1/dbus-run-session.1*
%{_mandir}/man1/dbus-test-tool.1*
%endif
%dir %{_libexecdir}/dbus-%{api}
# See doc/system-activation.txt in source tarball for the rationale
# behind these permissions
%attr(4750,root,messagebus) %{_libexecdir}/dbus-1/dbus-daemon-launch-helper
%{_tmpfilesdir}/dbus.conf
%{_unitdir}/dbus-daemon.service
%{_userunitdir}/dbus-daemon.service

%files -n %{libname}
%{_libdir}/*dbus-%{api}*.so.%{major}*

%files -n %{devname}
%{_libdir}/libdbus-%{api}.so
%{_libdir}/dbus-1.0/include/
%{_libdir}/pkgconfig/dbus-%{api}.pc
%{_includedir}/dbus-1.0/
%{_libdir}/cmake/DBus1/*.cmake

%files x11
%{_sysconfdir}/X11/xinit/xinitrc.d/00-start-message-bus.sh
%{_bindir}/dbus-launch
%ifnarch riscv64
%{_mandir}/man1/dbus-launch.1*
%endif

%files tools
%{_bindir}/dbus-send
%{_bindir}/dbus-monitor
%{_bindir}/dbus-update-activation-environment
%{_bindir}/dbus-uuidgen
%ifnarch riscv64
%{_mandir}/man1/dbus-monitor.1*
%{_mandir}/man1/dbus-send.1*
%{_mandir}/man1/dbus-update-activation-environment.1*
%{_mandir}/man1/dbus-uuidgen.1*
%endif

%files doc
%doc COPYING NEWS ChangeLog
%doc doc/introspect.dtd doc/introspect.xsl doc/system-activation.txt
%{_docdir}/%{name}/*
%{_datadir}/xml/dbus-%{api}/*.dtd
