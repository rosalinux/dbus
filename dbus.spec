%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}

%define enable_test 0
%define enable_verbose 0

%define git_url git://git.freedesktop.org/git/dbus/dbus

%bcond_without uclibc

Summary:	D-Bus message bus
Name:		dbus
Version:	1.6.18
Release:	3
License:	GPLv2+ or AFL
Group:		System/Servers
Url:		http://www.freedesktop.org/Software/dbus
Source0:	http://dbus.freedesktop.org/releases/dbus/%{name}-%{version}.tar.gz
Source1:	doxygen_to_devhelp.xsl
# (fc) 1.0.2-5mdv disable fatal warnings on check (fd.o bug #13270)
Patch3:		dbus-1.0.2-disable_fatal_warning_on_check.patch
# (bor) synchronize dbus.service with dbus.target so dependencies work
Patch7:		dbus-1.6.2-dbus.service-before-dbus.target.patch

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
BuildRequires:	pkgconfig(systemd)
%if %{with uclibc}
BuildRequires:	uClibc-devel >= 0.9.33.2-9
%endif

Requires(post,preun,postun):	systemd-units
Requires(post):	systemd-sysvinit
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
Requires:	%{libname} = %{version}-%{release}
%if %{with uclibc}
Requires:	uclibc-%{libname} = %{version}-%{release}
%endif
Provides:	%{name}-devel = %{version}-%{release}

%description -n	%{devname}
Headers and static libraries for D-Bus.

%package x11
Summary:	X11-requiring add-ons for D-Bus
Group:		System/Servers
Requires:	dbus = %{version}-%{release}

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
%patch7 -p1 -b .after_dbus_target

%build
%serverbuild_hardened
#needed for correct localstatedir location
%define _localstatedir %{_var}

COMMON_ARGS="--enable-systemd --with-systemdsystemunitdir=/lib/systemd/system \
    --enable-libaudit --disable-selinux --with-system-pid-file=/run/messagebus.pid \
    --with-system-socket=/run/dbus/system_bus_socket --libexecdir=/%{_lib}/dbus-%{api}"

export CONFIGURE_TOP=$PWD
%if %{with uclibc}
mkdir -p uclibc
pushd uclibc
%configure2_5x \
	CC=%{uclibc_cc} \
	CFLAGS="%{uclibc_cflags}" \
	$COMMON_ARGS \
	--with-sysroot=%{uclibc_root} \
	--bindir=%{uclibc_root}%{_bindir} \
	--disable-libaudit \
	--disable-static \
	--disable-tests \
	--disable-asserts \
	--disable-doxygen-docs \
	--disable-xml-docs \
	--enable-userdb-cache \
%if %{enable_verbose}
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
%if %{enable_test}
# (tpg) enable verbose mode by default --enable-verbose-mode
mkdir -p test
pushd test
%configure2_5x \
	$COMMON_ARGS \
	--enable-libaudit \
	--disable-static \
	--enable-verbose-mode \
	--enable-tests=yes \
	--enable-verbose-mode=yes \
	--enable-asserts \
	--disable-doxygen-docs \
	--disable-xml-docs

DBUS_VERBOSE=1 %make

make check
popd
%endif

mkdir -p shared
pushd shared
%configure2_5x \
	$COMMON_ARGS \
	--enable-libaudit \
	--disable-static \
	--disable-tests \
	--disable-asserts \
	--enable-doxygen-docs \
	--enable-xml-docs \
	--enable-userdb-cache \
%if %enable_verbose
	--enable-verbose-mode
%else
	--disable-verbose-mode
%endif

%make
doxygen Doxyfile

xsltproc -o dbus.devhelp %{SOURCE1} doc/api/xml/index.xml
popd

%check
make -C shared check

%install
%if %{with uclibc}
%makeinstall_std -C uclibc
install -d %{buildroot}%{uclibc_root}{/%{_lib},%{_libdir}}
mv %{buildroot}%{_libdir}/libdbus-%{api}.so.%{major}* %{buildroot}%{uclibc_root}/%{_lib}
ln -srf %{buildroot}%{uclibc_root}/%{_lib}/libdbus-%{api}.so.%{major}.* %{buildroot}%{uclibc_root}%{_libdir}/libdbus-%{api}.so

rm -f %{buildroot}%{uclibc_root}%{_bindir}/dbus-{launch,monitor}
%endif

%makeinstall_std -C shared

# move lib to /, because it might be needed by hotplug script, before
# /usr is mounted
mkdir -p %{buildroot}/%{_lib} %{buildroot}%{_var}/lib/dbus

mv %{buildroot}%{_libdir}/*dbus-1*.so.* %{buildroot}/%{_lib} 
ln -sf ../../%{_lib}/libdbus-%{api}.so.%{major} %{buildroot}%{_libdir}/libdbus-%{api}.so

mkdir -p %{buildroot}%{_sysconfdir}/X11/xinit.d
cat << EOF > %{buildroot}%{_sysconfdir}/X11/xinit.d/30dbus
# to be sourced
if [ -z "\$DBUS_SESSION_BUS_ADDRESS" ]; then
  eval \`/usr/bin/dbus-launch --exit-with-session --sh-syntax\`
fi
EOF

chmod 755 %{buildroot}%{_sysconfdir}/X11/xinit.d/30dbus

# create directory
mkdir %{buildroot}%{_datadir}/dbus-%{api}/interfaces

# Make sure that when somebody asks for D-Bus under the name of the
# old SysV script, that he ends up with the standard dbus.service name
# now.
ln -s dbus.service %{buildroot}/lib/systemd/system/messagebus.service

#add devhelp compatible helps
mkdir -p %{buildroot}%{_datadir}/devhelp/books/dbus
mkdir -p %{buildroot}%{_datadir}/devhelp/books/dbus/api

cp shared/dbus.devhelp %{buildroot}%{_datadir}/devhelp/books/dbus
cp doc/dbus-specification.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp doc/dbus-faq.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp doc/dbus-tutorial.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp shared/doc/api/html/* %{buildroot}%{_datadir}/devhelp/books/dbus/api

# (tpg) remove old initscript
rm -rf %{buildroot}%{_sysconfdir}/rc.d/init.d/*

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
%dir %{_var}/lib/dbus
%dir %{_libdir}/dbus-1.0
%{_bindir}/dbus-daemon
%{_bindir}/dbus-send
%{_bindir}/dbus-cleanup-sockets
%{_bindir}/dbus-uuidgen
%{_mandir}/man*/*
%dir %{_datadir}/dbus-%{api}
%{_datadir}/dbus-%{api}/system-services
%{_datadir}/dbus-%{api}/services
%{_datadir}/dbus-%{api}/interfaces
# See doc/system-activation.txt in source tarball for the rationale
# behind these permissions
%dir /%{_lib}/dbus-%{api}
%attr(4750,root,messagebus) /%{_lib}/dbus-%{api}/dbus-daemon-launch-helper
/lib/systemd/system/dbus.service
/lib/systemd/system/messagebus.service
/lib/systemd/system/dbus.socket
/lib/systemd/system/dbus.target.wants/dbus.socket
/lib/systemd/system/multi-user.target.wants/dbus.service
/lib/systemd/system/sockets.target.wants/dbus.socket

%if %{with uclibc}
%files -n uclibc-%{name}
%{uclibc_root}%{_bindir}/dbus-daemon
%{uclibc_root}%{_bindir}/dbus-send
%{uclibc_root}%{_bindir}/dbus-cleanup-sockets
%{uclibc_root}%{_bindir}/dbus-uuidgen
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
%{_bindir}/dbus-monitor

%files doc
%doc COPYING NEWS
%doc doc/introspect.dtd doc/introspect.xsl doc/system-activation.txt
%{_docdir}/%{name}/*
%doc %{_datadir}/devhelp/books/dbus
