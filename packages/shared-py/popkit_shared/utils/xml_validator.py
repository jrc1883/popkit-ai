#!/usr/bin/env python3
"""
XML Validation Utility for PopKit

Provides schema-based validation for PopKit's XML context system.
Supports both lxml (full XSD validation) and ElementTree (well-formedness).
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import lxml for XSD validation (optional dependency)
try:
    from lxml import etree as lxml_etree

    HAS_LXML = True
except ImportError:
    HAS_LXML = False
    logger.debug("lxml not available, XSD validation will be limited to well-formedness checks")

# Schema cache for performance
_SCHEMA_CACHE = {}


def get_schema_path(schema_type: str) -> Path:
    """
    Returns path to XSD schema file.

    Args:
        schema_type: One of 'problem', 'project', 'findings', 'workflow'

    Returns:
        Path to the XSD schema file

    Raises:
        ValueError: If schema_type is invalid
    """
    schema_map = {
        "problem": "problem-context.xsd",
        "project": "project-context.xsd",
        "findings": "findings.xsd",
        "workflow": "workflow.xsd",
    }

    if schema_type not in schema_map:
        raise ValueError(
            f"Invalid schema_type: {schema_type}. Must be one of: {', '.join(schema_map.keys())}"
        )

    # Get schema directory (same directory as this file, then ../schemas/)
    current_file = Path(__file__)
    schema_dir = current_file.parent.parent / "schemas"
    schema_file = schema_dir / schema_map[schema_type]

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    return schema_file


def is_well_formed_xml(xml_string: str) -> tuple[bool, str | None]:
    """
    Checks if XML is well-formed (parseable by ElementTree).

    This is a lightweight check that ensures:
    - Valid XML syntax
    - Properly closed tags
    - Valid nesting
    - No duplicate attributes

    Args:
        xml_string: XML content to validate

    Returns:
        Tuple of (is_well_formed, error_message)
        - is_well_formed: True if XML is parseable
        - error_message: None if valid, error description if invalid
    """
    if not xml_string or not xml_string.strip():
        return False, "Empty XML string"

    try:
        ET.fromstring(xml_string)
        return True, None
    except ET.ParseError as e:
        return False, f"XML parsing error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during XML parsing: {str(e)}"


def validate_xml_structure(xml_string: str, expected_root: str) -> bool:
    """
    Quick validation of root element without full schema check.

    This is faster than full schema validation and useful for
    quick sanity checks before more expensive validation.

    Args:
        xml_string: XML content to validate
        expected_root: Expected root element name (e.g., 'problem-context')

    Returns:
        True if root element matches, False otherwise
    """
    try:
        root = ET.fromstring(xml_string)
        return root.tag == expected_root
    except Exception:
        return False


def validate_xml_against_schema(xml_string: str, schema_type: str) -> tuple[bool, str | None]:
    """
    Validates XML string against XSD schema.

    This function attempts full XSD validation if lxml is available.
    If lxml is not available, it falls back to well-formedness checking
    and basic structure validation.

    Args:
        xml_string: XML content to validate
        schema_type: One of 'problem', 'project', 'findings', 'workflow'

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if XML is valid against schema
        - error_message: None if valid, error description if invalid

    Raises:
        ValueError: If schema_type is invalid
        FileNotFoundError: If schema file doesn't exist
    """
    # First check well-formedness
    is_well_formed, error = is_well_formed_xml(xml_string)
    if not is_well_formed:
        return False, f"Not well-formed XML: {error}"

    # Get expected root element based on schema type
    root_map = {
        "problem": "problem-context",
        "project": "project",
        "findings": "findings",
        "workflow": "workflow",
    }
    expected_root = root_map.get(schema_type)

    # Quick structure check
    if expected_root and not validate_xml_structure(xml_string, expected_root):
        return False, f"Root element is not '{expected_root}'"

    # If lxml is not available, we can only do basic checks
    if not HAS_LXML:
        logger.debug(f"lxml not available, skipping full XSD validation for {schema_type}")
        return True, None

    try:
        # Get or load schema
        schema_path = get_schema_path(schema_type)

        # Check cache
        if schema_path not in _SCHEMA_CACHE:
            with open(schema_path, "rb") as f:
                schema_doc = lxml_etree.parse(f)
                _SCHEMA_CACHE[schema_path] = lxml_etree.XMLSchema(schema_doc)

        schema = _SCHEMA_CACHE[schema_path]

        # Parse and validate XML
        xml_doc = lxml_etree.fromstring(xml_string.encode("utf-8"))

        if schema.validate(xml_doc):
            return True, None
        else:
            # Collect validation errors
            errors = []
            for error in schema.error_log:
                errors.append(f"Line {error.line}: {error.message}")

            error_message = "; ".join(errors[:3])  # Limit to first 3 errors
            if len(schema.error_log) > 3:
                error_message += f" (and {len(schema.error_log) - 3} more errors)"

            return False, error_message

    except ValueError:
        # Invalid schema_type
        raise
    except FileNotFoundError:
        # Schema file not found
        raise
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def clear_schema_cache():
    """Clears the schema cache. Useful for testing or after schema updates."""
    global _SCHEMA_CACHE
    _SCHEMA_CACHE.clear()
    logger.debug("Schema cache cleared")


# Convenience functions for specific schema types


def validate_problem_xml(xml_string: str) -> tuple[bool, str | None]:
    """Validates problem-context XML."""
    return validate_xml_against_schema(xml_string, "problem")


def validate_project_xml(xml_string: str) -> tuple[bool, str | None]:
    """Validates project XML."""
    return validate_xml_against_schema(xml_string, "project")


def validate_findings_xml(xml_string: str) -> tuple[bool, str | None]:
    """Validates findings XML."""
    return validate_xml_against_schema(xml_string, "findings")


def validate_workflow_xml(xml_string: str) -> tuple[bool, str | None]:
    """Validates workflow XML."""
    return validate_xml_against_schema(xml_string, "workflow")
