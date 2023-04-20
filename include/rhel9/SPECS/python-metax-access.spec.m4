# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT
%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           python-metax-access
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Metax Access Library
Group:          Applications/Archiving
License:        LGPLv3+
URL:            https://digitalpreservation.fi/
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  %{py3_dist pip}
BuildRequires:  %{py3_dist wheel}
BuildRequires:  %{py3_dist setuptools}
BuildRequires:  %{py3_dist setuptools_scm}
BuildRequires:  %{py3_dist pytest}
BuildRequires:  %{py3_dist sphinx}
BuildRequires:  %{py3_dist requests_mock}

%global _description %{expand:
Metax access library
}

%description %_description

%package -n python3-metax-access
Summary:    %{summary}
%description -n python3-metax-access %_description

%prep
%autosetup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build
export SETUPTOOLS_SCM_PRETEND_VERSION=%{file_version}
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files metax_access

cp %{_prefix}/etc/metax.cfg %{_sysconfdir}/metax.cfg

%files -n python3-metax-access -f %{pyproject_files}
%{_bindir}/metax_access
%config %{_sysconfdir}/metax.cfg
%license LICENSE
%doc README.rst

# TODO: For now changelog must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog
