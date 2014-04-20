%define	api	1
%define	major	3
%define	libname	%mklibname dbus- %{api} %{major}
%define	devname	%mklibname -d dbus- %{api}

%bcond_with	test
%bcond_with	verbose

%define git_url git://git.freedesktop.org/git/dbus/dbus

%bcond_without uclibc

Summary:	D-Bus message bus
Name:		dbus
Version:	1.8.0
Release:	1
# forgive me, need to quickly get around ABF issues.. :|
Epoch:		1
License:	GPLv2+ or AFL
Group:		System/Servers
Url:		http://www.freedesktop.org/Software/dbus
Source0:	http://dbus.freedesktop.org/releases/dbus/%{name}-%{version}.tar.gz
Source1:	doxygen_to_devhelp.xsl
# (fc) 1.0.2-5mdv disable fatal warnings on check (fd.o bug #13270)
Patch3:		dbus-1.0.2-disable_fatal_warning_on_check.patch
Patch4:		dbus-daemon-bindir.patch
Patch5:		dbus-1.8.0-fix-disabling-of-xml-docs.patch
Patch6:	 	0001-name-test-Don-t-run-test-autolaunch-if-we-don-t-have.patch

BuildREquires:	asciidoc
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
BuildRequires:	pkgconfig(systemd)
%if %{with uclibc}
BuildRequires:	uClibc-devel >= 0.9.33.2-9
%endif

Requires(pre):	shadow-utils
Requires(preun,post,postun):	rpm-helper
Provides:	should-restart = system

%description
D-Bus is a system for sending messages between applications. It is
used both for the systemwide message bus service, and as a
per-user-login-session messaging facility.

%if %{with uclibc}
%package -n	uclibc-%{name}
Summary:	D-Bus message bus (uClibc linked)
Group:		System/Servers
Requires:	%{name} = %{EVRD}

%description -n	uclibc-%{name}
D-Bus is a system for sending messages between applications. It is
used both for the systemwide message bus service, and as a
per-user-login-session messaging facility.
%endif

%package -n %{libname}
Summary:	Shared library for using D-Bus
Group:		System/Libraries

%description -n	%{libname}
D-Bus shared library.

%if %{with uclibc}
%package -n	uclibc-%{libname}
Summary:	Shared library for using D-Bus (uClibc linked)
Group:		System/Libraries

%description -n	uclibc-%{libname}
D-Bus shared library.
%endif

%package -n %{devname}
Summary:	Libraries and headers for D-Bus
Group:		Development/C
Requires:	%{libname} = %{EVRD}
%if %{with uclibc}
Requires:	uclibc-%{libname} = %{EVRD}
%endif
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
#only disable in cooker to detect buggy programs
#patch3 -p1 -b .disable_fatal_warning_on_check
%patch4 -p1 -b .daemon_bindir~
%patch5 -p1 -b .nodocs~
%patch6 -p1 -b .noautolaunchtest~
if test -f autogen.sh; then env NOCONFIGURE=1 ./autogen.sh; else autoreconf -v -f -i; fi

%build
%serverbuild_hardened
COMMON_ARGS="--enable-systemd --with-systemdsystemunitdir=%{_unitdir} \
	--bindir=/bin --enable-libaudit --disable-selinux \
	--with-system-pid-file=%{_var}/run/messagebus.pid --exec-prefix=/ \
	--with-system-socket=%{_var}/run/dbus/system_bus_socket \
	--libexecdir=/%{_lib}/dbus-%{api} --with-init-scripts=redhat"

export CONFIGURE_TOP="$PWD"
%if %{with uclibc}
mkdir -p uclibc
pushd uclibc
%configure2_5x \
	CC=%{uclibc_cc} \
	CFLAGS="%{uclibc_cflags}" \
	$COMMON_ARGS \
	--with-sysroot=%{uclibc_root} \
	--bindir=%{uclibc_root}/bin \
	--exec-prefix=%{uclibc_root} \
	--libexecdir=%{uclibc_root}/%{_lib}/dbus-%{api} \
	--disable-libaudit \
	--disable-tests \
	--disable-asserts \
	--disable-doxygen-docs \
	--disable-xml-docs \
	--disable-x11-autolaunch \
	--without-x \
%if %{with verbose}
	--enable-verbose-mode
%else
	--disable-verbose-mode
%endif
# ugly hack to get rid of library search dir passed..
for i in `find -name Makefile`; do
	sed -e 's#-L%{_libdir}##g' -i $i
done
%make
popd
%endif

#### Build once with tests to make check
%if %{with test}
# (tpg) enable verbose mode by default --enable-verbose-mode
mkdir -p tests
pushd tests
%configure2_5x \
	$COMMON_ARGS \
	--enable-libaudit \
	--enable-verbose-mode \
	--enable-tests \
	--enable-asserts \
	--disable-doxygen-docs \
	--disable-xml-docs

DBUS_VERBOSE=1 %make
popd
%endif

mkdir -p shared
pushd shared
%configure2_5x \
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
%if %{with uclibc}
%makeinstall_std -C uclibc
install -d %{buildroot}%{uclibc_root}{/%{_lib},%{_libdir}}
mv %{buildroot}%{_libdir}/libdbus-%{api}.so.%{major}* %{buildroot}%{uclibc_root}/%{_lib}
ln -srf %{buildroot}%{uclibc_root}/%{_lib}/libdbus-%{api}.so.%{major}.* %{buildroot}%{uclibc_root}%{_libdir}/libdbus-%{api}.so

%endif

%makeinstall_std -C shared

# move lib to /, because it might be needed by hotplug script, before
# /usr is mounted
mkdir -p %{buildroot}/%{_lib} %{buildroot}%{_localstatedir}/lib/dbus %{buildroot}%{_bindir}

mv %{buildroot}%{_libdir}/*dbus-1*.so.* %{buildroot}/%{_lib} 
ln -sf /%{_lib}/libdbus-%{api}.so.%{major} %{buildroot}%{_libdir}/libdbus-%{api}.so

mv %{buildroot}/bin/dbus-launch %{buildroot}%{_bindir}/dbus-launch
mkdir -p %{buildroot}%{_sysconfdir}/X11/xinit.d
cat << EOF > %{buildroot}%{_sysconfdir}/X11/xinit.d/30dbus
# to be sourced
if [ -z "\$DBUS_SESSION_BUS_ADDRESS" ]; then
  eval \`%{_bindir}/dbus-launch --exit-with-session --sh-syntax\`
fi
EOF

chmod 755 %{buildroot}%{_sysconfdir}/X11/xinit.d/30dbus

# create directory
mkdir %{buildroot}%{_datadir}/dbus-%{api}/interfaces

# Make sure that when somebody asks for D-Bus under the name of the
# old SysV script, that he ends up with the standard dbus.service name
# now.
ln -s dbus.service %{buildroot}%{_unitdir}/messagebus.service

#add devhelp compatible helps
mkdir -p %{buildroot}%{_datadir}/devhelp/books/dbus
mkdir -p %{buildroot}%{_datadir}/devhelp/books/dbus/api

cp shared/dbus.devhelp %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/dbus-specification.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/dbus-faq.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/dbus-tutorial.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/api/html/* %{buildroot}%{_datadir}/devhelp/books/dbus/api

# (tpg) remove old initscript
rm -r %{buildroot}%{_sysconfdir}/rc.d/init.d/*

# systemd user session bits
mkdir -p %{buildroot}%{_prefix}/lib/systemd/user
cat >%{buildroot}%{_prefix}/lib/systemd/user/dbus.service <<'EOF'
[Unit]
Description=D-Bus User Message Bus
Requires=dbus.socket

[Service]
ExecStart=/usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile --systemd-activation
ExecReload=/usr/bin/dbus-send --print-reply --session --type=method_call --dest=org.freedesktop.DBus / org.freedesktop.DBus.ReloadConfig

[Install]
WantedBy=default.target
EOF
cat >%{buildroot}%{_prefix}/lib/systemd/user/dbus.socket <<'EOF'
[Unit]
Description=D-Bus User Message Bus Socket
Before=sockets.target

[Socket]
ListenStream=/run/user/%U/dbus/user_bus_socket

[Install]
WantedBy=default.target
EOF

%pre
# (cg) Do not require/use rpm-helper helper macros... we must do this manually
# to avoid dep loops during install
/usr/sbin/groupadd -r messagebus 2>/dev/null || :
/usr/sbin/useradd -r -c "system user for %{name}" -g messagebus -s /sbin/nologin -d / messagebus 2>/dev/null ||:

%post
/bin/rm -rf /var/run/dbus
/bin/ln -s /run/dbus /var/run/
if [ "$1" = "1" ]; then
    /usr/bin/dbus-uuidgen --ensure
    /bin/systemctl enable dbus.service >/dev/null 2>&1 || :
    /bin/systemctl --user --global enable dbus.socket >/dev/null 2>&1 || :
    /bin/systemctl --user --global enable dbus.service >/dev/null 2>&1 || :
fi
%_post_service %{name} %{name}.service

%postun
%_postun_groupdel messagebus
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart dbus.service >/dev/null 2>&1 || :
fi

%preun
if [ $1 = 0 ]; then
    /bin/systemctl --no-reload dbus.service > /dev/null 2>&1 || :
    /bin/systemctl stop dbus.service > /dev/null 2>&1 || :
fi

%triggerun -- dbus < 1.7.10-2
# User sessions are new in 1.7.10
/bin/systemctl --user --global enable dbus.socket >/dev/null 2>&1 || :
/bin/systemctl --user --global enable dbus.service >/dev/null 2>&1 || :

%triggerun -- dbus < 1.6.18-1
/bin/rm -rf /var/run/dbus
/bin/ln -s /run/dbus /var/run/

%triggerun -- dbus < 1.4.16-1
/bin/systemctl enable dbus.service >/dev/null 2>&1
/sbin/chkconfig --del messagebus >/dev/null 2>&1 || :
/bin/systemctl try-restart dbus.service >/dev/null 2>&1 || :

%triggerpostun -- dbus < 1.2.4.4permissive-2mdv
/sbin/chkconfig --level 7 messagebus reset

%files
%dir %{_sysconfdir}/dbus-%{api}
%config(noreplace) %{_sysconfdir}/dbus-%{api}/*.conf
%dir %{_sysconfdir}/dbus-%{api}/system.d
%dir %{_sysconfdir}/dbus-%{api}/session.d
%dir %{_var}/run/dbus
%dir %{_localstatedir}/lib/dbus
%dir %{_libdir}/dbus-1.0
/bin/dbus-cleanup-sockets
/bin/dbus-daemon
/bin/dbus-monitor
/bin/dbus-run-session
/bin/dbus-send
/bin/dbus-uuidgen
%{_mandir}/man*/*
%dir %{_datadir}/dbus-%{api}
%{_datadir}/dbus-%{api}/system-services
%{_datadir}/dbus-%{api}/services
%{_datadir}/dbus-%{api}/interfaces
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
%{_prefix}/lib/systemd/user/dbus.*

%if %{with uclibc}
%files -n uclibc-%{name}
%{uclibc_root}/bin/dbus-cleanup-sockets
%{uclibc_root}/bin/dbus-daemon
%{uclibc_root}/bin/dbus-launch
%{uclibc_root}/bin/dbus-monitor
%{uclibc_root}/bin/dbus-run-session
%{uclibc_root}/bin/dbus-send
%{uclibc_root}/bin/dbus-uuidgen
%dir %{uclibc_root}/%{_lib}/dbus-%{api}
%attr(4750,root,messagebus) %{uclibc_root}/%{_lib}/dbus-%{api}/dbus-daemon-launch-helper
%endif

%files -n %{libname}
/%{_lib}/*dbus-%{api}*.so.%{major}*

%if %{with uclibc}
%files -n uclibc-%{libname}
%{uclibc_root}/%{_lib}/libdbus-%{api}.so.%{major}*
%endif

%files -n %{devname}
%doc ChangeLog
%{_libdir}/libdbus-%{api}.so
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libdbus-%{api}.so
%endif
%{_libdir}/dbus-1.0/include/
%{_libdir}/pkgconfig/dbus-%{api}.pc
%{_includedir}/dbus-1.0/

%files x11
%{_sysconfdir}/X11/xinit.d/*
%{_bindir}/dbus-launch

%files doc
%doc COPYING NEWS
%doc doc/introspect.dtd doc/introspect.xsl doc/system-activation.txt
%{_docdir}/%{name}/*
%doc %{_datadir}/devhelp/books/dbus
