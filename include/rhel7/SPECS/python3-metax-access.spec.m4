# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT
%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           python3-metax-access
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Metax Access Library
Group:          Applications/Archiving
License:        LGPLv3+
URL:            http://www.csc.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Requires:       python3
Requires:       python36-lxml
Requires:       python36-requests
Requires:       python36-click
BuildRequires:  python3-setuptools
BuildRequires:  python36-setuptools_scm
BuildRequires:  python36-pytest
BuildRequires:  python3-sphinx
BuildRequires:  python36-pytest-catchlog
BuildRequires:  python3-requests-mock

%description
Metax access library


%prep
%setup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build

%pre

%install
rm -rf $RPM_BUILD_ROOT
make install PREFIX="%{_prefix}" DESTDIR="%{buildroot}" SETUPTOOLS_SCM_PRETEND_VERSION=%{file_version}

# Rename executable to prevent naming collision with Python 2 RPM
sed -i 's/\/bin\/metax_access$/\/bin\/metax_access-3/g' INSTALLED_FILES

mv %{buildroot}%{_bindir}/metax_access %{buildroot}%{_bindir}/metax_access-3

%post

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root,-)
%config /etc/metax.cfg


# TODO: For now changelog must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog
