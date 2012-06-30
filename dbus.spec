%define	major	3
%define	api	1
%define	libname %mklibname dbus- %{api} %{major}
%define	devname %mklibname -d dbus- %{api}

%define enable_test 0
%define enable_verbose 0

%define git_url git://git.freedesktop.org/git/dbus/dbus

Summary:	D-Bus message bus
Name:		dbus
Version:	1.6.2
Release:	2
License:	GPLv2+ or AFL
Group:		System/Servers
URL:		http://www.freedesktop.org/Software/dbus
Source0:	http://dbus.freedesktop.org/releases/dbus/%{name}-%{version}.tar.gz
Source1:	doxygen_to_devhelp.xsl
# (fc) 0.20-1mdk fix start/stop order (fd.o bug #11491), starts after network
Patch0:		dbus-initscript.patch
# (fc) 1.0.2-5mdv disable fatal warnings on check (fd.o bug #13270)
Patch3:		dbus-1.0.2-disable_fatal_warning_on_check.patch
# (bor) synchronize dbus.service with dbus.target so dependencies work
Patch7:		dbus-1.6.2-dbus.service-before-dbus.target.patch

BuildRequires:	docbook-dtd412-xml
BuildRequires:	doxygen
BuildRequires:	libtool
BuildRequires:	xmlto
BuildRequires:	expat-devel >= 2.0.1
BuildRequires:	pkgconfig(glib-2.0)
BuildRequires:	pkgconfig(libcap-ng)
BuildRequires:	pkgconfig(x11)
BuildRequires:	pkgconfig(libsystemd-daemon) >= 32
BuildRequires:	pkgconfig(libsystemd-login) >= 32
BuildRequires:	pkgconfig(systemd)
Requires(post):	systemd-units
Requires(post):	systemd-sysvinit
Requires(preun):	systemd-units
Requires(postun):	systemd-units
Requires(pre):	rpm-helper
Requires(preun):	rpm-helper
Requires(post):	rpm-helper
Requires(postun):	rpm-helper
Requires(post):	chkconfig >= 1.3.37-3
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
Requires:	%{libname} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}
Conflicts:	%{_lib}dbus-1_0-devel < 1.4.14
Obsoletes:	%{_lib}dbus-1_3-devel < 1.4.14

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
%patch0 -p1 -b .initscript
#only disable in cooker to detect buggy programs
#patch3 -p1 -b .disable_fatal_warning_on_check
%patch7 -p1 -b .after_dbus_target

%build
#needed for correct localstatedir location 
%define _localstatedir %{_var}

COMMON_ARGS="--enable-systemd --with-systemdsystemunitdir=/lib/systemd/system --disable-selinux --with-system-pid-file=%{_var}/run/messagebus.pid --with-system-socket=%{_var}/run/dbus/system_bus_socket --with-session-socket-dir=/tmp --libexecdir=/%{_lib}/dbus-%{api}" 

#### Build once with tests to make check
%if %{enable_test}
%configure2_5x \
	$COMMON_ARGS \
	--enable-tests=yes \
	--enable-verbose-mode=yes \
	--enable-asserts=yes \
	--disable-doxygen-docs \
	--disable-xml-docs

DBUS_VERBOSE=1 %make

make check

#### Clean up and build again
make clean
%endif

%configure2_5x \
	$COMMON_ARGS \
	--disable-tests \
	--disable-asserts \
	--enable-doxygen-docs \
	--enable-xml-docs \
	--enable-userdb-cache \
%if %enable_verbose
	--enable-verbose-mode=yes
%else
	--enable-verbose-mode=no
%endif

%make

doxygen Doxyfile

xsltproc -o dbus.devhelp %{SOURCE1} doc/api/xml/index.xml

%check
make check

%install
%makeinstall_std

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

cp dbus.devhelp %{buildroot}%{_datadir}/devhelp/books/dbus
cp doc/dbus-specification.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp doc/dbus-faq.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp doc/dbus-tutorial.html %{buildroot}%{_datadir}/devhelp/books/dbus
cp doc/api/html/* %{buildroot}%{_datadir}/devhelp/books/dbus/api

%pre
%_pre_useradd messagebus / /sbin/nologin
%_pre_groupadd daemon messagebus

%post
if [ "$1" = "1" ]; then 
    /usr/bin/dbus-uuidgen --ensure
    /bin/systemctl enable dbus.service >/dev/null 2>&1 || :
fi

%postun
%_postun_groupdel daemon messagebus
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart dbus.service >/dev/null 2>&1 || :
fi

%preun
if [ $1 = 0 ]; then
    /bin/systemctl --no-reload dbus.service > /dev/null 2>&1 || :
    /bin/systemctl stop dbus.service > /dev/null 2>&1 || :
fi

%triggerun -- dbus < 1.4.16-1
/bin/systemctl enable dbus.service >/dev/null 2>&1
/sbin/chkconfig --del messagebus >/dev/null 2>&1 || :
/bin/systemctl try-restart dbus.service >/dev/null 2>&1 || :

%triggerpostun -- dbus < 1.2.4.4permissive-2mdv
/sbin/chkconfig --level 7 messagebus reset

%files
%doc COPYING NEWS
%dir %{_sysconfdir}/dbus-%{api}
%config(noreplace) %{_sysconfdir}/dbus-%{api}/*.conf
%{_sysconfdir}/rc.d/init.d/*
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

%files -n %{libname}
/%{_lib}/*dbus-%{api}*.so.%{major}*

%files -n %devname
%doc ChangeLog 
%{_libdir}/libdbus-%{api}.a
%{_libdir}/libdbus-%{api}.so
%{_libdir}/dbus-1.0/include/
%{_libdir}/pkgconfig/dbus-%{api}.pc
%{_includedir}/dbus-1.0/

%files x11
%{_sysconfdir}/X11/xinit.d/*
%{_bindir}/dbus-launch
%{_bindir}/dbus-monitor

%files doc
%doc doc/introspect.dtd doc/introspect.xsl doc/system-activation.txt
%doc %{_datadir}/devhelp/books/dbus
