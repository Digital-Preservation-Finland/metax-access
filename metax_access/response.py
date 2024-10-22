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


class MetaxFileDatasetMetadata(TypedDict):
    title: Optional[str]
    file_type: Optional[str]
    use_category: Optional[str]


class MetaxFileFormatVersion(TypedDict):
    pref_label: Optional[str]
    file_format: Optional[str]      # MIME type
    format_version: Optional[str]


class MetaxFileCharacteristics(TypedDict):
    encoding: Optional[str]        # UTF-8, UTF-16, UTF-32 or ISO-8859-15
    csv_has_header: Optional[bool]
    csv_quoting_char: Optional[str]
    csv_delimiter: Optional[str]
    csv_record_separator: Optional[str]     # LF, CR or CRLF

    file_format_version: Optional[MetaxFileFormatVersion]

    file_created: Optional[str]     # DOES NOT EXIST in V3


class MetaxFile(TypedDict, total=False):
    id: Required[str]                       # UUID
    storage_identifier: Optional[str]
    pathname: Required[str]                 # Always starts with '/'
    filename: Required[str]
    size: Required[int]
    checksum: Required[str]                 # '<algo>:<hash>'
    storage_service: Required[str]          # 'pas', 'ida' or 'test'
    csc_project: Required[str]
    frozen: Optional[str]                   # ISO 8601 date
    modified: Required[str]                                # ISO 8601 date
    removed: Optional[str]                  # ISO 8601 date
    published: Optional[str]                # ISO 8601 date
    dataset_metadata: Optional[MetaxFileDatasetMetadata]
    characteristics: Optional[MetaxFileCharacteristics]
    characteristics_extension: Optional[dict]  # Free-form contents
