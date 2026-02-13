# PopKit Error Codes

This file is generated from `packages/shared-py/popkit_shared/utils/error_codes.py`.

## Quick Reference

| Code                            | Severity | Category           | Message                                                |
| ------------------------------- | -------- | ------------------ | ------------------------------------------------------ |
| `E001_JSON_PARSE`               | critical | JSON/Input Parsing | Invalid JSON syntax in input                           |
| `E002_INVALID_SCHEMA`           | high     | JSON/Input Parsing | JSON structure doesn't match expected schema           |
| `E003_MALFORMED_INPUT`          | high     | JSON/Input Parsing | Input data is malformed or corrupted                   |
| `E004_ENCODING_ERROR`           | high     | JSON/Input Parsing | Input encoding error (invalid UTF-8 or character set)  |
| `E101_FILE_NOT_FOUND`           | high     | File I/O           | Required file not found                                |
| `E102_PERMISSION_DENIED`        | high     | File I/O           | Permission denied accessing file or directory          |
| `E103_FILE_READ_ERROR`          | high     | File I/O           | Failed to read file contents                           |
| `E104_FILE_WRITE_ERROR`         | high     | File I/O           | Failed to write to file                                |
| `E106_DIRECTORY_NOT_FOUND`      | high     | File I/O           | Required directory not found                           |
| `E108_FILE_LOCKED`              | high     | File I/O           | File is locked by another process                      |
| `E202_CONNECTION_REFUSED`       | high     | Network/API        | Connection refused by remote server                    |
| `E203_API_ERROR`                | high     | Network/API        | API request failed with error response                 |
| `E205_DNS_RESOLUTION_FAILED`    | high     | Network/API        | Failed to resolve hostname                             |
| `E301_REPO_NOT_FOUND`           | high     | Git Operations     | Git repository not found                               |
| `E302_MERGE_CONFLICT`           | high     | Git Operations     | Git merge conflict detected                            |
| `E303_DETACHED_HEAD`            | high     | Git Operations     | Git repository is in detached HEAD state               |
| `E305_BRANCH_NOT_FOUND`         | high     | Git Operations     | Git branch not found                                   |
| `E307_PUSH_REJECTED`            | high     | Git Operations     | Git push rejected by remote                            |
| `E501_DB_CONNECTION_FAILED`     | critical | Database           | Failed to connect to database                          |
| `E502_QUERY_ERROR`              | high     | Database           | Database query execution failed                        |
| `E503_TRANSACTION_FAILED`       | high     | Database           | Database transaction failed or rolled back             |
| `E505_SCHEMA_MISMATCH`          | critical | Database           | Database schema doesn't match expected structure       |
| `E601_TOOL_FAILED`              | high     | Tool Execution     | Tool execution failed                                  |
| `E603_INVALID_ARGS`             | high     | Tool Execution     | Invalid arguments provided to tool                     |
| `E604_TOOL_NOT_FOUND`           | high     | Tool Execution     | Required tool or command not found                     |
| `E606_TOOL_CRASHED`             | high     | Tool Execution     | Tool crashed or terminated unexpectedly                |
| `E701_INVALID_CONFIG`           | high     | Configuration      | Invalid configuration                                  |
| `E702_CONFIG_NOT_FOUND`         | high     | Configuration      | Configuration file not found                           |
| `E703_CONFIG_PARSE_ERROR`       | high     | Configuration      | Failed to parse configuration file                     |
| `E705_CONFIG_VALIDATION_FAILED` | high     | Configuration      | Configuration validation failed                        |
| `E801_PLUGIN_LOAD_FAILED`       | high     | Plugin/Extension   | Failed to load plugin or extension                     |
| `E803_PLUGIN_CONFLICT`          | high     | Plugin/Extension   | Plugin conflict detected                               |
| `E805_PLUGIN_INIT_FAILED`       | high     | Plugin/Extension   | Plugin initialization failed                           |
| `E901_ASSERTION_FAILED`         | critical | System/Internal    | Internal assertion failed                              |
| `E902_UNEXPECTED_STATE`         | critical | System/Internal    | System reached unexpected state                        |
| `E904_RESOURCE_EXHAUSTED`       | critical | System/Internal    | System resources exhausted                             |
| `I905_MAINTENANCE_MODE`         | info     | System/Internal    | System is in maintenance mode                          |
| `S401_DESTRUCTIVE_CMD`          | critical | Safety/Security    | Potentially destructive command blocked                |
| `S402_CREDENTIAL_LEAK`          | critical | Safety/Security    | Potential credential or secret detected                |
| `S403_INSECURE_OPERATION`       | high     | Safety/Security    | Operation uses insecure method or protocol             |
| `S405_UNVERIFIED_SOURCE`        | high     | Safety/Security    | Operation involves unverified or untrusted source      |
| `W005_DEPRECATED_FORMAT`        | medium   | JSON/Input Parsing | Input uses deprecated format                           |
| `W105_FILE_TOO_LARGE`           | medium   | File I/O           | File size exceeds recommended limits                   |
| `W107_DISK_SPACE_LOW`           | medium   | File I/O           | Low disk space detected                                |
| `W201_NETWORK_TIMEOUT`          | medium   | Network/API        | Network request timed out                              |
| `W204_RATE_LIMIT`               | medium   | Network/API        | API rate limit exceeded                                |
| `W206_SSL_CERTIFICATE_WARNING`  | medium   | Network/API        | SSL certificate verification issue                     |
| `W304_UNCOMMITTED_CHANGES`      | medium   | Git Operations     | Uncommitted changes detected                           |
| `W306_BEHIND_REMOTE`            | medium   | Git Operations     | Local branch is behind remote                          |
| `W404_SECURITY_WARNING`         | medium   | Safety/Security    | Potential security concern detected                    |
| `W406_DEPRECATED_SECURITY`      | medium   | Safety/Security    | Using deprecated security method                       |
| `W504_SLOW_QUERY`               | medium   | Database           | Database query is running slowly                       |
| `W602_TOOL_TIMEOUT`             | medium   | Tool Execution     | Tool execution timed out                               |
| `W605_TOOL_VERSION_OLD`         | medium   | Tool Execution     | Tool version is outdated                               |
| `W702_MISSING_FIELD`            | medium   | Configuration      | Optional configuration field missing                   |
| `W704_CONFIG_OVERRIDE`          | low      | Configuration      | Configuration value overridden by environment variable |
| `W802_VERSION_MISMATCH`         | medium   | Plugin/Extension   | Plugin version incompatibility detected                |
| `W804_PLUGIN_DEPRECATED`        | medium   | Plugin/Extension   | Plugin is deprecated                                   |
| `W903_RESOURCE_WARNING`         | medium   | System/Internal    | System resource usage warning                          |

## Notes

- `E`: blocking error
- `W`: non-blocking warning
- `S`: safety/security violation
- `I`: informational status
