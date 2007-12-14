%define expat_version           2.0.1

%define lib_major 3
%define lib_api 1
%define lib_name %mklibname dbus- %{lib_api} %{lib_major}
%define develname %mklibname -d dbus- %lib_api

%define enable_test 0

Summary: D-Bus message bus
Name: dbus
Version: 1.1.2
Release: %mkrel 4
URL: http://www.freedesktop.org/Software/dbus
Source0: http://dbus.freedesktop.org/releases/dbus/%{name}-%{version}.tar.gz
Source1: doxygen_to_devhelp.xsl
# (fc) 0.20-1mdk fix start/stop order, add pinit support (fd.o bug #11491)
Patch0: dbus-0.91-initscript.patch
# (fc) 1.0.1-1mdv add inotify support (fd.o bug #13268)
Patch1: dbus-1.0.0-inotify.patch
# (fc) 1.0.1-1mdv fix dnotify detection of new config file (fd.o bug #13269)
Patch2: dbus-1.0.0-fixfilecreation.patch
# (fc) 1.0.2-5mdv disable fatal warnings on check (fd.o bug #13270)
Patch3: dbus-1.0.2-disable_fatal_warning_on_check.patch
# (fc) 1.1.2-1mdv fix aborting (fd.o bug #12430) (Fedora)
Patch4: dbus-1.1.2-no-abort.patch
# (fc) 1.1.2-1mdv fix PIE usage (git)
Patch5: dbus-pie.patch
# (fc) 1.1.2-1mdv generate xml doc (Fedora)
Patch6: dbus-1.0.1-generate-xml-docs.patch

License: GPLv2+ or AFL
Group: System/Servers
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: libx11-devel
BuildRequires: expat-devel >= %{expat_version}
BuildRequires: xmlto docbook-dtd412-xml
BuildRequires: doxygen
BuildRequires: libtool
Requires(pre): rpm-helper
Requires(preun): rpm-helper
Requires(post): rpm-helper
Requires(postun): rpm-helper
Requires(post): %{lib_name} >= %{version}-%{release}

%description
D-Bus is a system for sending messages between applications. It is
used both for the systemwide message bus service, and as a
per-user-login-session messaging facility.

%package -n %{lib_name}
Summary: Shared library for using D-Bus
Group: System/Libraries
Requires: dbus >= %{version}

%description -n %{lib_name}
D-Bus shared library.

%package -n %develname
Summary: Libraries and headers for D-Bus
Group: Development/C
Requires: %{name} = %{version}
Requires: %{lib_name} = %{version}
Provides: lib%{name}-1-devel = %{version}-%{release}
Provides: lib%{name}-devel = %{version}-%{release}
Provides: %{name}-devel = %{version}-%{release}
Conflicts: %{_lib}dbus-1_0-devel
Obsoletes: %mklibname -d dbus- 1 3

%description -n %develname

Headers and static libraries for D-Bus.

%package x11
Summary: X11-requiring add-ons for D-Bus
Group: System/Servers
Requires: dbus = %{version}

%description x11
D-Bus contains some tools that require Xlib to be installed, those are
in this separate package so server systems need not install X.

%prep
%setup -q 
%patch0 -p1 -b .initscript
%patch1 -p1 -b .inotify
%patch2 -p1 -b .fixfilecreation
#only disable in cooker to detect buggy programs
#patch3 -p1 -b .disable_fatal_warning_on_check
%patch4 -p1 -b .no-abort
%patch5 -p1 -b .pie
%patch6 -p1 -b .xmldoc

#needed by patch1 & 5
aclocal-1.10
automake-1.10
autoheader
autoconf

%build

#needed for correct localstatedir location 
%define _localstatedir %{_var}

COMMON_ARGS="--disable-selinux --with-system-pid-file=%{_var}/run/messagebus.pid --with-system-socket=%{_var}/run/dbus/system_bus_socket --with-session-socket-dir=/tmp --libexecdir=/%{_lib}/dbus-%{lib_api}"

#### Build once with tests to make check
%if %{enable_test}
%configure2_5x $COMMON_ARGS --enable-tests=yes --enable-verbose-mode=yes --enable-asserts=yes  --disable-doxygen-docs --disable-xml-docs

DBUS_VERBOSE=1 %make
make check

#### Clean up and build again 
make clean
%endif 

# leave verbose mode so people can debug their apps but make sure to
# turn it off on stable releases with --disable-verbose-mode
%configure2_5x $COMMON_ARGS --disable-tests --disable-asserts --enable-doxygen-docs --enable-xml-docs
%make

doxygen Doxyfile

xsltproc -o dbus.devhelp %{SOURCE1} doc/api/xml/index.xml

%check
make check

%install
rm -rf %{buildroot}

%makeinstall_std

# move lib to /, because it might be needed by hotplug script, before
# /usr is mounted
mkdir -p $RPM_BUILD_ROOT/%{_lib} %buildroot%{_var}/lib/dbus
mv $RPM_BUILD_ROOT%{_libdir}/*dbus-1*.so.* $RPM_BUILD_ROOT/%{_lib} 
ln -sf ../../%{_lib}/libdbus-%{lib_api}.so.%{lib_major} $RPM_BUILD_ROOT%{_libdir}/libdbus-%{lib_api}.so

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/X11/xinit.d
cat << EOF > $RPM_BUILD_ROOT%{_sysconfdir}/X11/xinit.d/30dbus
# to be sourced
eval \`/usr/bin/dbus-launch --exit-with-session --sh-syntax\`
EOF
chmod 755 $RPM_BUILD_ROOT%{_sysconfdir}/X11/xinit.d/30dbus

# create directory
mkdir $RPM_BUILD_ROOT%{_datadir}/dbus-%{lib_api}/interfaces

#add devhelp compatible helps
mkdir -p $RPM_BUILD_ROOT%{_datadir}/devhelp/books/dbus
mkdir -p $RPM_BUILD_ROOT%{_datadir}/devhelp/books/dbus/api

cp dbus.devhelp $RPM_BUILD_ROOT%{_datadir}/devhelp/books/dbus
cp doc/dbus-specification.html $RPM_BUILD_ROOT%{_datadir}/devhelp/books/dbus
cp doc/dbus-faq.html $RPM_BUILD_ROOT%{_datadir}/devhelp/books/dbus
cp doc/dbus-tutorial.html $RPM_BUILD_ROOT%{_datadir}/devhelp/books/dbus
cp doc/api/html/* $RPM_BUILD_ROOT%{_datadir}/devhelp/books/dbus/api

#remove unpackaged file
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la

%clean
rm -rf %{buildroot}

%pre
%_pre_useradd messagebus / /sbin/nologin
%_pre_groupadd daemon messagebus

%post -n %{lib_name} -p /sbin/ldconfig
%postun -n %{lib_name} -p /sbin/ldconfig

%post
%_post_service messagebus

%postun
%_postun_userdel messagebus
%_postun_groupdel daemon messagebus

%preun
%_preun_service messagebus

%triggerpostun -- dbus < 0.21-4mdk
/sbin/chkconfig --del messagebus
/sbin/chkconfig --add messagebus

%files
%defattr(-,root,root)

%doc COPYING NEWS

%dir %{_sysconfdir}/dbus-%{lib_api}
%config(noreplace) %{_sysconfdir}/dbus-%{lib_api}/*.conf
%{_sysconfdir}/rc.d/init.d/*
%dir %{_sysconfdir}/dbus-%{lib_api}/system.d
%dir %{_sysconfdir}/dbus-%{lib_api}/session.d
%dir %{_var}/run/dbus
%dir %{_var}/lib/dbus
%dir %{_libdir}/dbus-1.0
%{_bindir}/dbus-daemon
%{_bindir}/dbus-send
%{_bindir}/dbus-cleanup-sockets
%{_bindir}/dbus-uuidgen
%{_mandir}/man*/*
%dir %{_datadir}/dbus-%{lib_api}
%dir %{_datadir}/dbus-%{lib_api}/services
%dir %{_datadir}/dbus-%{lib_api}/interfaces
# See doc/system-activation.txt in source tarball for the rationale
# behind these permissions
%attr(4750,root,messagebus) /%{_lib}/dbus-%{lib_api}/dbus-daemon-launch-helper

%files -n %{lib_name}
%defattr(-,root,root)
/%{_lib}/*dbus-%{lib_api}*.so.%{lib_major}*

%files -n %develname
%defattr(-,root,root)
%doc doc/*
%{_libdir}/libdbus-%{lib_api}.a
%{_libdir}/libdbus-%{lib_api}.so
%{_libdir}/dbus-1.0/include
%{_libdir}/pkgconfig/dbus-%{lib_api}.pc
%{_includedir}/dbus-1.0
%doc %{_datadir}/devhelp/books/dbus

%files x11
%defattr(-,root,root)
%{_sysconfdir}/X11/xinit.d/*
%{_bindir}/dbus-launch
%{_bindir}/dbus-monitor
