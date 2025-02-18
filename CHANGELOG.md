# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added

- `post_file` and `post_files` methods for submitting a single and multiple files

### Fixed

- Fix duplicate file detection in `post_file` and `post_files`

### Removed

- Support for Metax V2

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
