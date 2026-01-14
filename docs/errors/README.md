# PopKit Error Codes Reference

This directory contains documentation for all PopKit error codes. Each error has a dedicated page with detailed explanations, common causes, and resolution steps.

## Quick Reference

| Code | Description | Severity | Category |
|------|-------------|----------|----------|
| [E001](E001_JSON_PARSE.md) | Invalid JSON syntax in input | Critical | JSON/Input Parsing |
| [E002](E002_INVALID_SCHEMA.md) | JSON structure doesn't match expected schema | High | JSON/Input Parsing |
| [E003](E003_MALFORMED_INPUT.md) | Input data is malformed or corrupted | High | JSON/Input Parsing |
| [E004](E004_ENCODING_ERROR.md) | Input encoding error (invalid UTF-8) | High | JSON/Input Parsing |
| [W005](W005_DEPRECATED_FORMAT.md) | Input uses deprecated format | Medium | JSON/Input Parsing |
| [E101](E101_FILE_NOT_FOUND.md) | Required file not found | High | File I/O |
| [E102](E102_PERMISSION_DENIED.md) | Permission denied accessing file | High | File I/O |
| [E103](E103_FILE_READ_ERROR.md) | Failed to read file contents | High | File I/O |
| [E104](E104_FILE_WRITE_ERROR.md) | Failed to write to file | High | File I/O |
| [W105](W105_FILE_TOO_LARGE.md) | File size exceeds recommended limits | Medium | File I/O |
| [E106](E106_DIRECTORY_NOT_FOUND.md) | Required directory not found | High | File I/O |
| [W107](W107_DISK_SPACE_LOW.md) | Low disk space detected | Medium | File I/O |
| [E108](E108_FILE_LOCKED.md) | File is locked by another process | High | File I/O |
| [W201](W201_NETWORK_TIMEOUT.md) | Network request timed out | Medium | Network/API |
| [E202](E202_CONNECTION_REFUSED.md) | Connection refused by remote server | High | Network/API |
| [E203](E203_API_ERROR.md) | API request failed with error response | High | Network/API |
| [W204](W204_RATE_LIMIT.md) | API rate limit exceeded | Medium | Network/API |
| [E205](E205_DNS_RESOLUTION_FAILED.md) | Failed to resolve hostname | High | Network/API |
| [W206](W206_SSL_CERTIFICATE_WARNING.md) | SSL certificate verification issue | Medium | Network/API |
| [E301](E301_REPO_NOT_FOUND.md) | Git repository not found | High | Git Operations |
| [E302](E302_MERGE_CONFLICT.md) | Git merge conflict detected | High | Git Operations |
| [E303](E303_DETACHED_HEAD.md) | Git repository in detached HEAD state | High | Git Operations |
| [W304](W304_UNCOMMITTED_CHANGES.md) | Uncommitted changes detected | Medium | Git Operations |
| [E305](E305_BRANCH_NOT_FOUND.md) | Git branch not found | High | Git Operations |
| [W306](W306_BEHIND_REMOTE.md) | Local branch is behind remote | Medium | Git Operations |
| [E307](E307_PUSH_REJECTED.md) | Git push rejected by remote | High | Git Operations |
| [S401](S401_DESTRUCTIVE_CMD.md) | Potentially destructive command blocked | Critical | Safety/Security |
| [S402](S402_CREDENTIAL_LEAK.md) | Potential credential or secret detected | Critical | Safety/Security |
| [S403](S403_INSECURE_OPERATION.md) | Operation uses insecure method | High | Safety/Security |
| [W404](W404_SECURITY_WARNING.md) | Potential security concern detected | Medium | Safety/Security |
| [S405](S405_UNVERIFIED_SOURCE.md) | Unverified or untrusted source | High | Safety/Security |
| [W406](W406_DEPRECATED_SECURITY.md) | Using deprecated security method | Medium | Safety/Security |
| [E501](E501_DB_CONNECTION_FAILED.md) | Failed to connect to database | Critical | Database |
| [E502](E502_QUERY_ERROR.md) | Database query execution failed | High | Database |
| [E503](E503_TRANSACTION_FAILED.md) | Database transaction failed | High | Database |
| [W504](W504_SLOW_QUERY.md) | Database query running slowly | Medium | Database |
| [E505](E505_SCHEMA_MISMATCH.md) | Database schema mismatch | Critical | Database |
| [E601](E601_TOOL_FAILED.md) | Tool execution failed | High | Tool Execution |
| [W602](W602_TOOL_TIMEOUT.md) | Tool execution timed out | Medium | Tool Execution |
| [E603](E603_INVALID_ARGS.md) | Invalid arguments provided to tool | High | Tool Execution |
| [E604](E604_TOOL_NOT_FOUND.md) | Required tool or command not found | High | Tool Execution |
| [W605](W605_TOOL_VERSION_OLD.md) | Tool version is outdated | Medium | Tool Execution |
| [E606](E606_TOOL_CRASHED.md) | Tool crashed unexpectedly | High | Tool Execution |
| [E701](E701_INVALID_CONFIG.md) | Invalid configuration | High | Configuration |
| [W702](W702_MISSING_FIELD.md) | Optional configuration field missing | Medium | Configuration |
| [E702](E702_CONFIG_NOT_FOUND.md) | Configuration file not found | High | Configuration |
| [E703](E703_CONFIG_PARSE_ERROR.md) | Failed to parse configuration file | High | Configuration |
| [W704](W704_CONFIG_OVERRIDE.md) | Config overridden by environment variable | Low | Configuration |
| [E705](E705_CONFIG_VALIDATION_FAILED.md) | Configuration validation failed | High | Configuration |
| [E801](E801_PLUGIN_LOAD_FAILED.md) | Failed to load plugin | High | Plugin/Extension |
| [W802](W802_VERSION_MISMATCH.md) | Plugin version incompatibility | Medium | Plugin/Extension |
| [E803](E803_PLUGIN_CONFLICT.md) | Plugin conflict detected | High | Plugin/Extension |
| [W804](W804_PLUGIN_DEPRECATED.md) | Plugin is deprecated | Medium | Plugin/Extension |
| [E805](E805_PLUGIN_INIT_FAILED.md) | Plugin initialization failed | High | Plugin/Extension |
| [E901](E901_ASSERTION_FAILED.md) | Internal assertion failed | Critical | System/Internal |
| [E902](E902_UNEXPECTED_STATE.md) | System reached unexpected state | Critical | System/Internal |
| [W903](W903_RESOURCE_WARNING.md) | System resource usage warning | Medium | System/Internal |
| [E904](E904_RESOURCE_EXHAUSTED.md) | System resources exhausted | Critical | System/Internal |
| [I905](I905_MAINTENANCE_MODE.md) | System is in maintenance mode | Info | System/Internal |

## Error Categories

### Critical (Blocking)
Errors that block execution and require immediate attention.
- [E001](E001_JSON_PARSE.md) - JSON parsing error
- [S401](S401_DESTRUCTIVE_CMD.md) - Destructive command blocked
- [S402](S402_CREDENTIAL_LEAK.md) - Credential leak detected
- [E501](E501_DB_CONNECTION_FAILED.md) - Database connection failed
- [E505](E505_SCHEMA_MISMATCH.md) - Database schema mismatch
- [E901](E901_ASSERTION_FAILED.md) - Internal assertion failed
- [E902](E902_UNEXPECTED_STATE.md) - Unexpected system state
- [E904](E904_RESOURCE_EXHAUSTED.md) - Resources exhausted

### High Severity (Blocking)
Issues that block execution but may have workarounds.
- [E002](E002_INVALID_SCHEMA.md) - Invalid JSON schema
- [E003](E003_MALFORMED_INPUT.md) - Malformed input data
- [E004](E004_ENCODING_ERROR.md) - Encoding error
- [E101-E108](E101_FILE_NOT_FOUND.md) - File I/O errors
- [E202-E205](E202_CONNECTION_REFUSED.md) - Network errors
- [E301-E307](E301_REPO_NOT_FOUND.md) - Git operation errors
- [S403-S405](S403_INSECURE_OPERATION.md) - Security issues
- [E502-E503](E502_QUERY_ERROR.md) - Database errors
- [E601-E606](E601_TOOL_FAILED.md) - Tool execution errors
- [E701-E705](E701_INVALID_CONFIG.md) - Configuration errors
- [E801-E805](E801_PLUGIN_LOAD_FAILED.md) - Plugin errors

### Warnings (Non-blocking)
Issues that don't block execution but should be addressed.
- [W005](W005_DEPRECATED_FORMAT.md) - Deprecated format
- [W105](W105_FILE_TOO_LARGE.md) - File too large
- [W107](W107_DISK_SPACE_LOW.md) - Low disk space
- [W201](W201_NETWORK_TIMEOUT.md) - Network timeout
- [W204](W204_RATE_LIMIT.md) - Rate limit exceeded
- [W206](W206_SSL_CERTIFICATE_WARNING.md) - SSL warning
- [W304](W304_UNCOMMITTED_CHANGES.md) - Uncommitted changes
- [W306](W306_BEHIND_REMOTE.md) - Behind remote
- [W404](W404_SECURITY_WARNING.md) - Security warning
- [W406](W406_DEPRECATED_SECURITY.md) - Deprecated security
- [W504](W504_SLOW_QUERY.md) - Slow database query
- [W602](W602_TOOL_TIMEOUT.md) - Tool timeout
- [W605](W605_TOOL_VERSION_OLD.md) - Old tool version
- [W702-W704](W702_MISSING_FIELD.md) - Configuration warnings
- [W802-W804](W802_VERSION_MISMATCH.md) - Plugin warnings
- [W903](W903_RESOURCE_WARNING.md) - Resource warning

### Informational
Status updates and non-critical information.
- [I905](I905_MAINTENANCE_MODE.md) - Maintenance mode
- [W704](W704_CONFIG_OVERRIDE.md) - Config override info

## By Hook Type

### Session Hooks
- [E001](E001_JSON_PARSE.md) - JSON parsing
- [W201](W201_NETWORK_TIMEOUT.md) - Network timeout
- [E701](E701_INVALID_CONFIG.md) - Invalid configuration
- [E801](E801_PLUGIN_LOAD_FAILED.md) - Plugin load failure

### Pre-Tool-Use
- [S401](S401_DESTRUCTIVE_CMD.md) - Destructive command
- [S402](S402_CREDENTIAL_LEAK.md) - Credential leak
- [S403](S403_INSECURE_OPERATION.md) - Insecure operation
- [E002](E002_INVALID_SCHEMA.md) - Invalid schema
- [E603](E603_INVALID_ARGS.md) - Invalid tool arguments

### Post-Tool-Use
- [E601](E601_TOOL_FAILED.md) - Tool execution failure
- [W602](W602_TOOL_TIMEOUT.md) - Tool timeout
- [E606](E606_TOOL_CRASHED.md) - Tool crash

### Git Hooks
- [E301-E307](E301_REPO_NOT_FOUND.md) - All git operation errors
- [W304](W304_UNCOMMITTED_CHANGES.md) - Uncommitted changes warning
- [W306](W306_BEHIND_REMOTE.md) - Behind remote warning

## Searching Errors

**By code:** Search for the exact error code (e.g., E001, W201, S401)
**By keyword:** Search error descriptions in this directory
**By category:** Use the category filters above
**By severity:** Filter by Critical, High, Medium, Low, Info

## Contributing Error Codes

When adding new error codes:
1. Add code to `ErrorRegistry` in `packages/shared-py/popkit_shared/utils/error_codes.py`
2. Run `python packages/shared-py/scripts/generate_error_docs.py` to create markdown file
3. Fill in detailed description, causes, and examples in the generated file
4. Update this README with new code (run script again to regenerate)

## Error Code Format

Error codes follow the format: `[PREFIX][NUMBER]_[NAME]`

**Prefixes:**
- `E` - Error (blocking)
- `W` - Warning (non-blocking)
- `S` - Safety violation (blocking)
- `I` - Info (informational)

**Number Ranges:**
- 001-099: JSON/Input Parsing
- 100-199: File I/O
- 200-299: Network/API
- 300-399: Git Operations
- 400-499: Safety/Security
- 500-599: Database
- 600-699: Tool Execution
- 700-799: Configuration
- 800-899: Plugin/Extension
- 900-999: System/Internal

## Related Documentation

- [PopKit Error Code System (Issue #104)](https://github.com/jrc1883/popkit-claude/issues/104)
- [Hook Standards](../../CLAUDE.md#hook-standards)
- [Error Code Implementation](../../packages/shared-py/popkit_shared/utils/error_codes.py)
- [Error Code Tests](../../packages/shared-py/popkit_shared/tests/test_error_codes.py)

---

**Total Error Codes**: 59
**Last Updated**: 2026-01-14 (Phase 3 - Issue #104)
