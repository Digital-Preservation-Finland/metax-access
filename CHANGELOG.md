# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 0.0.0 - 2024-07-08

### Changed

- `directory` CLI command retrieves the metadata and the content of a directory by the path and the project id of a directory. Accessing a directory with the dirctory ID is no longer supported.

### Removed

- Methods `get_directory` and `get_directory_files` were removed due the deprecation of the directory's id value.
- Unused methods `set_xml`, `get_xml`, `delete_dataset_files` and `get_dataset_filetypes` removed.