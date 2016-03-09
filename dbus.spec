%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}

%bcond_with test
%bcond_with verbose

%define git_url git://git.freedesktop.org/git/dbus/dbus

Summary:	D-Bus message bus
Name:		dbus
Version:	1.10.8
Release:	1
License:	GPLv2+ or AFL
Group:		System/Servers
Url:		http://www.freedesktop.org/Software/dbus
Source0:	http://dbus.freedesktop.org/releases/dbus/%{name}-%{version}.tar.gz
Source1:	doxygen_to_devhelp.xsl
Patch2:		dbus-1.8.14-headers-clang.patch
# (fc) 1.0.2-5mdv disable fatal warnings on check (fd.o bug #13270)
Patch3:		dbus-1.0.2-disable_fatal_warning_on_check.patch
Patch4:		dbus-daemon-bindir.patch
Patch5:		dbus-1.8.0-fix-disabling-of-xml-docs.patch

BuildRequires:	asciidoc
BuildRequires:	docbook2x
BuildRequires:	docbook-dtd412-xml
BuildRequires:	doxygen
BuildRequires:	libtool
BuildRequires:	xmlto
BuildRequires:	pkgconfig(expat)
BuildRequires:	pkgconfig(glib-2.0)
BuildRequires:	pkgconfig(libcap-ng)
BuildRequires:	pkgconfig(sm)
BuildRequires:	pkgconfig(x11)
BuildRequires:	pkgconfig(libsystemd-daemon) >= 32
BuildRequires:	pkgconfig(libsystemd-login) >= 32
BuildRequires:	pkgconfig(libsystemd-journal) >= 32
BuildRequires:	pkgconfig(libsystemd-id128)
BuildRequires:	pkgconfig(systemd)
# To make sure _rundir is defined
BuildRequires:	rpm-build >= 1:5.4.10-79
Requires(post,preun,postun):	rpm-helper >= 0.24.12-11
Provides:	should-restart = system

%description
D-Bus is a system for sending messages between applications. It is
used both for the systemwide message bus service, and as a
per-user-login-session messaging facility.

%package -n %{libname}
Summary:	Shared library for using D-Bus
Group:		System/Libraries

%description -n	%{libname}
D-Bus shared library.

%package -n %{devname}
Summary:	Libraries and headers for D-Bus
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Provides:	%{name}-devel = %{EVRD}

%description -n	%{devname}
Headers and static libraries for D-Bus.

%package x11
Summary:	X11-requiring add-ons for D-Bus
Group:		System/Servers
Requires:	dbus = %{EVRD}

%description x11
D-Bus contains some tools that require Xlib to be installed, those are
in this separate package so server systems need not install X.

%package doc
Summary:	Developer documentation for D-BUS
Group:		Books/Computer books
Suggests:	devhelp
Conflicts:	%{devname} < 1.2.20

%description doc
This package contains developer documentation for D-Bus along with
other supporting documentation such as the introspect dtd file.

%prep
%setup -q
%patch2 -p1 -b .clang~
#only disable in cooker to detect buggy programs
#patch3 -p1 -b .disable_fatal_warning_on_check
%patch4 -p1 -b .daemon_bindir~
%patch5 -p1 -b .nodocs~
if test -f autogen.sh; then env NOCONFIGURE=1 ./autogen.sh; else autoreconf -v -f -i; fi

%build
%serverbuild_hardened
COMMON_ARGS=" --enable-user-session --enable-systemd --with-systemdsystemunitdir=%{_unitdir} \
	--with-systemduserunitdir=%{_userunitdir} --bindir=/bin --enable-libaudit --disable-selinux \
	--with-system-pid-file=%{_rundir}/messagebus.pid --exec-prefix=/ \
	--with-system-socket=%{_rundir}/dbus/system_bus_socket \
	--libexecdir=/%{_lib}/dbus-%{api} --with-init-scripts=redhat --disable-static"

export CONFIGURE_TOP="$PWD"

#### Build once with tests to make check
%if %{with test}
# (tpg) enable verbose mode by default --enable-verbose-mode
mkdir -p tests
pushd tests
%configure \
	$COMMON_ARGS \
	--enable-libaudit \
	--enable-verbose-mode \
	--enable-tests \
	--enable-asserts \
	--enable-x11-autolaunch \
	--with-x \
	--disable-doxygen-docs \
	--disable-xml-docs

DBUS_VERBOSE=1 %make
popd
%endif

mkdir -p shared
pushd shared
%configure \
	$COMMON_ARGS \
	--enable-libaudit \
	--disable-tests \
	--disable-asserts \
	--enable-doxygen-docs \
	--enable-xml-docs \
	--enable-x11-autolaunch \
	--with-x \
%if %{with verbose}
	--enable-verbose-mode
%else
	--disable-verbose-mode
%endif

%make
doxygen Doxyfile

xsltproc -o dbus.devhelp %{SOURCE1} doc/api/xml/index.xml
popd

%check
%if %{with test}
%make -C tests check
%endif
%make -C shared check

%install
%makeinstall_std -C shared

# move lib to /, because it might be needed by hotplug script, before
# /usr is mounted
mkdir -p %{buildroot}/%{_lib} %{buildroot}%{_bindir}

mv %{buildroot}%{_libdir}/*dbus-1*.so.* %{buildroot}/%{_lib}
ln -sf /%{_lib}/libdbus-%{api}.so.%{major} %{buildroot}%{_libdir}/libdbus-%{api}.so

# create directory
mkdir %{buildroot}%{_datadir}/dbus-%{api}/interfaces

# Make sure that when somebody asks for D-Bus under the name of the
# old SysV script, that he ends up with the standard dbus.service name
# now.
ln -s dbus.service %{buildroot}%{_unitdir}/messagebus.service

#add devhelp compatible helps
mkdir -p %{buildroot}%{_datadir}/devhelp/books/dbus
mkdir -p %{buildroot}%{_datadir}/devhelp/books/dbus/api

# (tpg) needed for dbus-uuidgen
mkdir -p %{buildroot}%{_var}/lib/dbus

cp shared/dbus.devhelp %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/dbus-specification.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/dbus-faq.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/dbus-tutorial.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/api/html/* %{buildroot}%{_datadir}/devhelp/books/dbus/api

# (tpg) remove old initscript
rm -r %{buildroot}%{_sysconfdir}/rc.d/init.d/*

mkdir -p %{buildroot}%{_tmpfilesdir}
cat > %{buildroot}%{_tmpfilesdir}/dbus.conf << EOF
d /run/dbus 755 - - -
EOF

%post
/bin/dbus-uuidgen --ensure
/bin/systemctl --global enable dbus.socket >/dev/null 2>&1 || :
/bin/systemctl --user enable dbus.socket >/dev/null 2>&1 || :
/bin/systemctl --user start dbus.socket >/dev/null 2>&1 || :
/bin/systemctl --global enable dbus.service >/dev/null 2>&1 || :
/bin/systemctl --user enable dbus.service >/dev/null 2>&1 || :
/bin/systemctl --user start dbus.service >/dev/null 2>&1 || :

%postun
%_postun_groupdel messagebus

%triggerin -- setup
if [ $1 -ge 2 -o $2 -ge 2 ]; then

    if ! getent group messagebus >/dev/null 2>&1; then
	/usr/sbin/groupadd -r messagebus 2>/dev/null || :
    fi

    if ! getent passwd messagebus >/dev/null 2>&1; then
	/usr/sbin/useradd -r -c "system user for %{name}" -g messagebus -s /sbin/nologin -d / messagebus 2>/dev/null ||:
    fi
fi

%triggerun -- dbus < 1.7.10-2
# User sessions are new in 1.7.10
/bin/systemctl --user --global enable dbus.socket >/dev/null 2>&1 || :
/bin/systemctl --user --global enable dbus.service >/dev/null 2>&1 || :

#(proyvind): most likely overkill in complexity, but trying to *really*
#            make sure not to break (running) dbus this time...
%triggerprein -- dbus < 1:1.8.0-2
if [ -L /run/dbus ]; then
    rm -f /run/dbus
fi
if [ -d %{_localstatedir}/run/dbus ]; then
   if [ -d /run/dbus ]; then
      if [ -S /run/dbus/system_bus_socket ]; then 
          rm -rf %{_localstatedir}/run/dbus
      else
          rm -rf /run/dbus
          mv %{_localstatedir}/run/dbus /run/
      fi
   else
      mv %{_localstatedir}/run/dbus /run/
   fi
   ln -sf /run/dbus %{_localstatedir}/run/dbus
fi

%triggerun -- dbus < 1.4.16-1
/bin/systemctl enable dbus.service >/dev/null 2>&1
/sbin/chkconfig --del messagebus >/dev/null 2>&1 || :
/bin/systemctl try-restart dbus.service >/dev/null 2>&1 || :

%triggerpostun -- dbus < 1.2.4.4permissive-2mdv
/sbin/chkconfig --level 7 messagebus reset

%files
%dir %{_sysconfdir}/dbus-%{api}
%config(noreplace) %{_sysconfdir}/dbus-%{api}/*.conf
%dir %{_libdir}/dbus-1.0
%dir %{_var}/lib/dbus
%{_tmpfilesdir}/dbus.conf
/bin/dbus-cleanup-sockets
/bin/dbus-daemon
/bin/dbus-monitor
/bin/dbus-run-session
/bin/dbus-send
/bin/dbus-uuidgen
/bin/dbus-test-tool
/bin/dbus-update-activation-environment
%{_mandir}/man*/*
%dir %{_datadir}/dbus-%{api}
%{_datadir}/dbus-%{api}/system-services
%{_datadir}/dbus-%{api}/services
%{_datadir}/dbus-%{api}/interfaces
%{_datadir}/dbus-%{api}/session.conf
%{_datadir}/dbus-%{api}/system.conf
# See doc/system-activation.txt in source tarball for the rationale
# behind these permissions
%dir /%{_lib}/dbus-%{api}
%attr(4750,root,messagebus) /%{_lib}/dbus-%{api}/dbus-daemon-launch-helper
%{_unitdir}/dbus.service
%{_unitdir}/messagebus.service
%{_unitdir}/dbus.socket
%{_unitdir}/dbus.target.wants/dbus.socket
%{_unitdir}/multi-user.target.wants/dbus.service
%{_unitdir}/sockets.target.wants/dbus.socket
%{_userunitdir}/dbus.service
%{_userunitdir}/dbus.socket
%{_userunitdir}/sockets.target.wants/dbus.socket

%files -n %{libname}
/%{_lib}/*dbus-%{api}*.so.%{major}*

%files -n %{devname}
%doc ChangeLog
%{_libdir}/libdbus-%{api}.so
%{_libdir}/dbus-1.0/include/
%{_libdir}/pkgconfig/dbus-%{api}.pc
%{_includedir}/dbus-1.0/

%files x11
/bin/dbus-launch

%files doc
%doc COPYING NEWS
%doc doc/introspect.dtd doc/introspect.xsl doc/system-activation.txt
%{_docdir}/%{name}/*
%doc %{_datadir}/devhelp/books/dbus
