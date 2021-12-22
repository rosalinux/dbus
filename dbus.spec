# dbus is used by wine and steam
%ifarch %{x86_64}
%bcond_without compat32
%else
%bcond_with compat32
%endif

%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}
%define lib32name libdbus-%{api}_%{major}
%define dev32name libdbus-%{api}-devel

%define git_url git://git.freedesktop.org/git/dbus/dbus

Summary:	D-Bus message bus
Name:		dbus
Version:	1.13.18
Release:	9
License:	GPLv2+ or AFL
Group:		System/Servers
Url:		http://www.freedesktop.org/Software/dbus
Source0:	http://dbus.freedesktop.org/releases/dbus/%{name}-%{version}.tar.xz
Source1:	dbus.sysusers
Source2:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/00-start-message-bus.sh
Source3:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus.socket
Source4:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus-daemon.service
Source5:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus.user.socket
Source6:	https://src.fedoraproject.org/rpms/dbus/raw/master/f/dbus-daemon.user.service
Patch1:		0001-tools-Use-Python3-for-GetAllMatchRules.patch
Patch2:		dbus-1.8.14-headers-clang.patch
# (fc) 1.0.2-5mdv disable fatal warnings on check (fd.o bug #13270)
#Patch3:		dbus-1.0.2-disable_fatal_warning_on_check.patch
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
%ifarch %{x86_64}
BuildRequires:	lib64unwind1.0
%endif
BuildRequires:	systemd-rpm-macros
# To make sure _rundir is defined
BuildRequires:	rpm-build >= 1:5.4.10-79
Requires:	dbus-broker >= 16
%if %{with compat32}
BuildRequires:	devel(libSM)
BuildRequires:	devel(libX11)
BuildRequires:	devel(libexpat)
%endif

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
# So services can use Requires: dbus to work with either
# dbus-daemon or dbus-broker
Provides:	dbus = %{EVRD}
%{?systemd_requires}
Requires:	dbus-common = %{EVRD}
Requires:	%{libname} = %{EVRD}
Requires:	dbus-tools = %{EVRD}
%systemd_requires
Requires(pre):	systemd

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
Requires:	(%{name}-daemon = %{EVRD} or dbus-broker)

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

%if %{with compat32}
%package -n %{lib32name}
Summary:	Shared library for using D-Bus (32-bit)
Group:		System/Libraries

%description -n %{lib32name}
D-Bus shared library.

%package -n %{dev32name}
Summary:	Libraries and headers for D-Bus (32-bit)
Group:		Development/C
Requires:	%{lib32name} = %{EVRD}
Requires:	%{devname} = %{EVRD}

%description -n %{dev32name}
Headers and static libraries for D-Bus.
%endif

%prep
%autosetup -p1
autoreconf -fi

export CONFIGURE_TOP="$(pwd)"
%if %{with compat32}
mkdir build32
cd build32
# We use --disable-modular-tests to avoid dragging in
# a glib2.0 dependency -- glib2.0 depends on dbus, and
# circular dependencies are ugly
%configure32 \
	--disable-selinux \
	--disable-systemd \
	--disable-modular-tests \
	--enable-x11-autolaunch
cd ..
%endif

mkdir build
cd build
%serverbuild_hardened
COMMON_ARGS="--disable-static --enable-user-session --enable-systemd --with-systemdsystemunitdir=%{_unitdir} \
	--with-systemduserunitdir=%{_userunitdir} --enable-inotify --enable-libaudit --disable-selinux \
	--with-system-pid-file=%{_rundir}/messagebus.pid  \
	--with-system-socket=%{_rundir}/dbus/system_bus_socket \
	--libexecdir=%{_libexecdir}/dbus-%{api}"

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
cd ..

# Build an X11-less version of dbus-launch (e.g. for Wayland sessions)
mkdir build-nox
cd build-nox
%serverbuild_hardened
COMMON_ARGS="--disable-static --enable-user-session --enable-systemd --with-systemdsystemunitdir=%{_unitdir} \
	--with-systemduserunitdir=%{_userunitdir} --enable-inotify --enable-libaudit --disable-selinux \
	--with-system-pid-file=%{_rundir}/messagebus.pid  \
	--with-system-socket=%{_rundir}/dbus/system_bus_socket \
	--libexecdir=%{_libexecdir}/dbus-%{api}"

%configure \
	$COMMON_ARGS \
	--disable-verbose-mode \
	--disable-tests \
	--disable-asserts \
	--enable-doxygen-docs \
	--enable-xml-docs \
	--disable-x11-autolaunch \
	--without-x

%build
%if %{with compat32}
%make_build -C build32
%endif
%make_build -C build-nox

%install
%if %{with compat32}
%make_install -C build32
# We don't need the 32-bit version
rm -rf %{buildroot}%{_libexecdir}
%endif
%make_install -C build-nox
cp build-nox/tools/.libs/dbus-launch %{buildroot}%{_bindir}/dbus-launch-nox

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
install -Dp -m644 %{SOURCE1} %{buildroot}%{_sysusersdir}/dbus.conf

install -d %{buildroot}%{_presetdir}
cat > %{buildroot}%{_presetdir}/86-%{name}-common.preset << EOF
enable dbus-daemon.service
enable dbus.socket
EOF

%pre daemon
%sysusers_create_package %{name} %{SOURCE1}

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
%{_unitdir}/dbus.socket
%{_userunitdir}/dbus.socket

%files daemon
%ghost %dir %{_rundir}/%{name}
%dir %{_localstatedir}/lib/dbus/
%{_sysusersdir}/dbus.conf
%{_bindir}/dbus-daemon
%{_bindir}/dbus-cleanup-sockets
%{_bindir}/dbus-run-session
%{_bindir}/dbus-test-tool
%ifnarch riscv64
%doc %{_mandir}/man1/dbus-cleanup-sockets.1*
%doc %{_mandir}/man1/dbus-daemon.1*
%doc %{_mandir}/man1/dbus-run-session.1*
%doc %{_mandir}/man1/dbus-test-tool.1*
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
%doc %{_mandir}/man1/dbus-launch.1*
%endif

%files tools
%{_bindir}/dbus-launch-nox
%{_bindir}/dbus-send
%{_bindir}/dbus-monitor
%{_bindir}/dbus-update-activation-environment
%{_bindir}/dbus-uuidgen
%ifnarch riscv64
%doc %{_mandir}/man1/dbus-monitor.1*
%doc %{_mandir}/man1/dbus-send.1*
%doc %{_mandir}/man1/dbus-update-activation-environment.1*
%doc %{_mandir}/man1/dbus-uuidgen.1*
%endif

%files doc
%doc COPYING NEWS
%doc doc/introspect.dtd doc/introspect.xsl doc/system-activation.txt
%{_docdir}/%{name}/*
%{_datadir}/xml/dbus-%{api}/*.dtd

%if %{with compat32}
%files -n %{lib32name}
%{_prefix}/lib/libdbus-1.so.*

%files -n %{dev32name}
%{_prefix}/lib/cmake/DBus1
%{_prefix}/lib/dbus-1.0/include/dbus/dbus-arch-deps.h
%{_prefix}/lib/libdbus-1.so
%{_prefix}/lib/pkgconfig/dbus-1.pc
%endif
