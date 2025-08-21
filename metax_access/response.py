"""
Metax V3 response data structures

These do not match exactly with data models defined for Metax V3, as some
fields do not either exist in Metax V3 yet or need to be included anyway in
some way to ensure applications remain functional during V2 -> V3 migration
period.

For underlying data models, see:

https://metax-v3.fd-staging.csc.fi/v3/swagger/
"""
from typing import TypedDict, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    # Type checkers need to support NotRequired
    from typing_extensions import Required
else:
    # Python 3.9 does not have Required. Use an alias instead.
    Required = Union


class MetaxPrefLabel(TypedDict):
    en: str
    fi: str


class MetaxFileDatasetMetadataEntry(TypedDict, total=False):
    id: Optional[str]
    url: Optional[str]
    in_schema: Optional[str]
    pref_label: Optional[MetaxPrefLabel]


class MetaxFileDatasetMetadata(TypedDict, total=False):
    title: Optional[str]
    file_type: Optional[MetaxFileDatasetMetadataEntry]
    use_category: Optional[MetaxFileDatasetMetadataEntry]


class MetaxFileFormatVersion(TypedDict, total=False):
    pref_label: Optional[MetaxPrefLabel]
    file_format: Optional[str]      # MIME type
    format_version: Optional[str]


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
