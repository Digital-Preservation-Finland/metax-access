"""
Metax V3 response data structures

These do not match exactly with data models defined for Metax V3, as some
fields do not either exist in Metax V3 yet or need to be included anyway in
some way to ensure applications remain functional during V2 -> V3 migration
period.

For underlying data models, see:

https://metax.fd-staging.csc.fi/v3/swagger/
"""
from collections.abc import Sequence
from typing import Any, TypedDict, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    # Type checkers need to support NotRequired
    from typing_extensions import Required
else:
    # Python 3.9 does not have Required. Use an alias instead.
    Required = Union


class MetaxPrefLabel(TypedDict, total=False):
    en: Optional[str]
    fi: Optional[str]
    sv: Optional[str]
    und: Optional[str]


class MetaxFileDatasetMetadataEntry(TypedDict, total=False):
    id: Optional[str]
    url: Optional[str]
    in_schema: Optional[str]
    pref_label: Optional[MetaxPrefLabel]


class MetaxFileDatasetMetadata(TypedDict, total=False):
    title: Optional[str]
    file_type: Optional[MetaxFileDatasetMetadataEntry]
    use_category: Optional[MetaxFileDatasetMetadataEntry]


class MetaxFileFormatVersion(
    MetaxFileDatasetMetadataEntry, TypedDict, total=False
):
    file_format: Required[Optional[str]]      # MIME type
    format_version: Required[Optional[str]]
    deprecated: Optional[str]


class MetaxFileCharacteristics(TypedDict, total=False):
    encoding: Optional[str]        # UTF-8, UTF-16, UTF-32 or ISO-8859-15
    csv_has_header: Optional[bool]
    csv_quoting_char: Optional[str]
    csv_delimiter: Optional[str]
    csv_record_separator: Optional[str]     # LF, CR or CRLF

    file_format_version: Optional[MetaxFileFormatVersion]

    file_created: Optional[str]     # DOES NOT EXIST in V3


class MetaxFile(TypedDict, total=False):
    id: Required[str]                       # UUID
    storage_identifier: Required[str]
    pathname: Required[str]                 # Always starts with '/'
    filename: Required[str]
    size: Required[int]
    checksum: Required[str]                 # '<algo>:<hash>'
    storage_service: Required[str]          # 'pas', 'ida' or 'test'
    csc_project: Required[str]
    frozen: Optional[str]                   # ISO 8601 date
    modified: Optional[str]                 # ISO 8601 date
    removed: Optional[str]                  # ISO 8601 date
    published: Optional[str]                # ISO 8601 date
    dataset_metadata: Optional[MetaxFileDatasetMetadata]
    characteristics: Optional[MetaxFileCharacteristics]
    characteristics_extension: Optional[dict]  # Free-form contents
    pas_process_running: Optional[bool]
    pas_compatible_file: Optional[str]
    non_pas_compatible_file: Optional[str]

    # TODO: Temporary field used during V2-V3 transition. Metax V3 has no
    # file creation date field, but this is still required for V2.
    _file_uploaded: Optional[str]


class MetaxMinFile(TypedDict, total=False):
    id: Required[str]
    filename: Required[str]
    size: Required[str]


class MetaxParentDirectory(TypedDict, total=False):
    storage_service: Optional[str]
    csc_project: Optional[str]
    name: Optional[str]
    pathname: Required[str]
    file_count: Optional[int]
    size: Optional[int]
    created: Optional[str]
    modified: Optional[str]
    dataset_metadata: Optional[Any]
    parent_url: Optional[str]


class MetaxDirectory(TypedDict, total=False):
    storage_service: Optional[str]
    csc_project: Optional[str]
    name: Required[str]
    pathname: Required[str]
    file_count: Required[int]
    size: Required[int]
    created: Optional[str]
    modified: Optional[str]
    dataset_metadata: Optional[Any]
    url: Optional[str]


class MetaxDirectoryFiles(TypedDict):
    directory: Optional[MetaxParentDirectory]
    files: Sequence[MetaxMinFile]
    directories: Sequence[MetaxDirectory]


class MetaxContractOrganization(TypedDict):
    name: str
    organization_identifier: str


class DateRange(TypedDict, total=False):
    start_date: Required[str]
    end_date: Optional[str]
    temporal_coverage: Optional[Any]


class MetaxContact(TypedDict):
    name: str
    email: str
    phone: str


class RelatedService(TypedDict):
    identifier: str
    name: str


class MetaxDataFieldBase(TypedDict):
    pref_label: MetaxPrefLabel


class MetaxDataField(MetaxDataFieldBase, TypedDict, total=False):
    id: Optional[str]
    in_scheme: Optional[str]
    url: Required[Optional[str]]


class MetaxUrlField(TypedDict):
    url: str


class MetaxContract(TypedDict, total=False):
    id: Required[str]
    title: Required[MetaxPrefLabel]
    description: Required[MetaxPrefLabel]
    quota: Required[int]
    created: Required[str]
    modified: Optional[str]
    organization: Required[MetaxContractOrganization]
    validity: Required[DateRange]
    contact: Required[Sequence[MetaxContact]]
    related_service: Required[Sequence[RelatedService]]
    removed: Optional[bool]


class MetaxLicense(TypedDict, total=False):
    id: Optional[str]
    pref_label: Required[Optional[MetaxPrefLabel]]
    custom_url: Optional[str]
    description: Optional[MetaxPrefLabel]
    title: Optional[MetaxPrefLabel]
    url: Required[str]


class MetaxAccessRights(TypedDict, total=False):
    available: Optional[str]
    description: Optional[MetaxPrefLabel]
    license: Required[Sequence[MetaxLicense]]


class MetaxPerson(TypedDict, total=False):
    name: Required[str]
    external_identifier: Required[Optional[str]]
    email: Optional[str]


class MetaxOrganization(TypedDict):
    pref_label: MetaxPrefLabel
    url: str
    external_identifier: str
    parent: Optional[MetaxDataFieldBase]


class MetaxActor(TypedDict, total=False):
    roles: Sequence[str]
    person: Optional[MetaxPerson]
    organization: Optional[MetaxOrganization]


class MetaxFileSet(TypedDict):
    csc_project: Optional[str]
    total_files_size: Required[int]
    total_files_count: Required[int]


class MetaxMetadataOwner(TypedDict, total=False):
    id: Optional[str]
    user: Required[str]
    organization: Required[str]


class MetaxPreservationDatasetVersion(TypedDict):
    id: Optional[str]
    persistent_identifier: Optional[str]
    preservation_state: Optional[str]


class MetaxPreservation(TypedDict, total=False):
    state: Required[int]
    description: Required[Optional[MetaxPrefLabel]]
    reason_description: Required[Optional[MetaxPrefLabel]]
    dataset_version: Optional[MetaxPreservationDatasetVersion]
    contract: Required[Optional[str]]


class MetaxProvenance(TypedDict, total=False):
    title: Required[MetaxPrefLabel]
    temporal: Optional[DateRange]
    description: Required[MetaxPrefLabel]
    event_outcome: Optional[MetaxDataField]
    outcome_description: Required[MetaxPrefLabel]
    lifecycle_event: Optional[MetaxDataFieldBase]


class MetaxSpatial(TypedDict):
    geographic_name: str


class MetaxDataset(TypedDict, total=False):
    id: Required[str]
    access_rights: Required[Optional[MetaxAccessRights]]
    actors: Required[Sequence[MetaxActor]]
    bibliographic_citations: Optional[Any]
    cumulative_state: Optional[int]
    data_catalog: Required[Optional[str]]
    description: Required[Optional[MetaxPrefLabel]]
    field_of_science: Required[Sequence[MetaxDataFieldBase]]
    fileset: Required[MetaxFileSet]
    generate_pid_on_publish: Optional[str]
    infrastructure: Optional[Sequence[Any]]
    issued: Required[Optional[str]]
    keyword: Required[Sequence[str]]
    language: Required[Sequence[MetaxUrlField]]
    metadata_owner: Required[MetaxMetadataOwner]
    other_identifiers: Optional[Sequence[Any]]
    persistent_identifier: Required[Optional[str]]
    preservation: Required[MetaxPreservation]
    projects: Optional[Sequence[Any]]
    provenance: Required[Sequence[MetaxProvenance]]
    relation: Optional[Sequence[Any]]
    remote_resources: Optional[Sequence[Any]]
    spatial: Required[Sequence[MetaxSpatial]]
    state: Optional[str]
    temporal: Optional[Sequence[DateRange]]
    theme: Required[Sequence[MetaxDataFieldBase]]
    title: Required[MetaxPrefLabel]
    created: Required[str]
    cumulation_started: Optional[str]
    cumulation_ended: Optional[str]
    deprecated: Optional[str]
    removed: Optional[str]
    modified: Required[str]
    dataset_versions: Optional[Sequence["MetaxDataset"]]
    published_revision: Optional[int]
    draft_revision: Optional[int]
    draft_of: Optional[str]
    next_draft: Optional[str]
    version: Required[int]
    api_version: Optional[int]
    metadata_repository: Optional[str]
