# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.38 - 2025-04-29

### Added

- Add field `dataset_metadata.use_category.url` to file

### Removed

- Remove field `dataset_metadata.use_category.id` from file

## 0.37 - 2025-04-11

### Fixed

- Fix missing dataset response mapping in `get_datasets_by_ids`

## 0.36 - 2025-04-02

### Added

- Include `pas_compatible_file` and `non_pas_compatible_file` dataset fields

## Changed

- `get_file2dataset_ids` now accepts a list of storage identifiers and only retrieves files from PAS storage service
- `delete_files` accepts a list of file objects allowing any identifiers to be used for files

## Fixed

- Support new syntax for `preservation__state` dataset search parameter

## 0.35 - 2025-02-26

### Added

- `get_dataset_file` method

### Fixed

- Duplicate file detection was fixed in in `post_file`, and the method was renamed as `post_files`
- Fix fetching datasets that contain "hidden" metadata

### Removed

- Support for Metax V2
- Support for password authentication
- CLI, and methods that were required only for CLI

## 0.34 - 2025-02-10

### Added

- Support for Metax V3 as required by the FDDPS services
- Add Metax V3 methods
  - `set_pas_package_created`
  - `get_file_format_versions`
  - `get_dataset_directory`
  - `unlock_dataset` and `lock_dataset`
  - `copy_dataset_to_pas_catalog` method for copying dataset to PAS catalog.
- Add `api_version` configuration parameter

## 0.33 - 2025-01-14

### Added

- `response_mapper` module.
- `set_contract` method for updating the contract of a dataset.

### Changed

- file, directory files, dataset and contract metadata responses from `metax-access` are formatted such that only fields used by services using metax-access are returned. The mapping is done in `response_mapper` module.

- `null` values are included to the responses of the `metax-access`.

## 0.32 - 2024-11-26

### Added

- Normalize file inserts & updates to Metax V3 format
- Add missing fields during V3 -> V2 normalization
  - `checksum.checked`
  - `file_uploaded`

### Fixed

- `storage_identifier` is normalized correctly as external file identifier instead of storage service identifier

## 0.31 - 2024-10-25

### Added

- `get_directory_id`returns an identifier of a directory.
- All methods, retrieving data from Metax, return Mtax V3 format data.

## 0.30 - 2024-09-27

### Changed

- `directory` CLI command retrieves the metadata and the content of a directory by the path and the project id of a directory. Accessing a directory with the directory ID is no longer supported. The command's flag `--files` was changed to `--content`

### Removed

- Methods `get_directory` and `get_directory_files` were removed. Directory identifiers will be removed entirely in Metax V3.
- Unused methods `set_xml`, `get_xml`, `delete_dataset_files` and `get_dataset_filetypes` removed.
