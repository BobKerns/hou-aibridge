"""
Retrieval system for accessing collected Houdini static data.
Provides efficient access to subsets of the data based on queries.
"""

from pathlib import Path
import sqlite3
from typing import Any
import json

from zabob.common.analysis_db import analysis_db

class DataRetriever:
    """
    Class for retrieving data from the analysis database.
    Provides methods to query different aspects of the collected data.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_module_functions(self, module_pattern: str, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get functions matching a module name pattern.

        Args:
            module_pattern: SQL LIKE pattern to match parent module names
            limit: Maximum number of results to return

        Returns:
            list of dictionaries containing function information
        """
        with analysis_db(db_path=self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT name, parent_name, docstring, type
                FROM houdini_module_data
                WHERE type IN ('function', 'method')
                AND parent_name LIKE ?
                ORDER BY parent_name, name
                LIMIT ?
            """

            cursor.execute(query, (module_pattern, limit))

            results = []
            for row in cursor.fetchall():
                name, parent_name, docstring, type_name = row

                # Get signature information if available
                signature_query = """
                    SELECT parameters, return_type, is_overload, overload_index
                    FROM function_signatures
                    WHERE func_name = ? AND parent_name = ?
                    ORDER BY is_overload, overload_index
                """

                cursor.execute(signature_query, (name, parent_name))
                signatures = []

                for sig_row in cursor.fetchall():
                    params_json, return_type, is_overload, overload_index = sig_row
                    try:
                        parameters = json.loads(params_json)
                    except (json.JSONDecodeError, TypeError):
                        parameters = []

                    signatures.append({
                        "parameters": parameters,
                        "return_type": return_type,
                        "is_overload": bool(is_overload),
                        "overload_index": overload_index
                    })

                results.append({
                    "name": name,
                    "module": parent_name,
                    "type": type_name,
                    "docstring": docstring,
                    "signatures": signatures
                })

            return results

    def get_node_type_info(self, node_pattern: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get node types matching a pattern.

        Args:
            node_pattern: SQL LIKE pattern to match node type names
            limit: Maximum number of results to return

        Returns:
            list of dictionaries containing node type information
        """
        with analysis_db(db_path=self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT n.name, n.category, n.description, n.icon, n.version
                FROM houdini_node_types n
                WHERE n.name LIKE ?
                ORDER BY n.category, n.name
                LIMIT ?
            """

            cursor.execute(query, (node_pattern, limit))

            results = []
            for row in cursor.fetchall():
                name, category, description, icon, version = row

                # Get parameters for this node type
                param_query = """
                    SELECT name, label, data_type, default_value, menu_items, help
                    FROM houdini_parm_templates
                    WHERE node_type_name = ? AND node_type_category = ?
                """

                cursor.execute(param_query, (name, category))
                parameters = []

                for param_row in cursor.fetchall():
                    param_name, label, data_type, default_value, menu_items, help_text = param_row

                    try:
                        if menu_items:
                            menu_items = json.loads(menu_items)
                    except (json.JSONDecodeError, TypeError):
                        menu_items = []

                    parameters.append({
                        "name": param_name,
                        "label": label,
                        "type": data_type,
                        "default": default_value,
                        "menu_items": menu_items,
                        "help": help_text
                    })

                results.append({
                    "name": name,
                    "category": category,
                    "description": description,
                    "icon": icon,
                    "version": version,
                    "parameters": parameters
                })

            return results

    def get_function_signatures(self, func_pattern: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get function signatures matching a pattern.

        Args:
            func_pattern: SQL LIKE pattern to match function names
            limit: Maximum number of results to return

        Returns:
            list of dictionaries containing function signature information
        """
        with analysis_db(db_path=self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT fs.func_name, fs.parent_name, fs.parameters, fs.return_type,
                       fs.is_overload, fs.overload_index, fs.file_path, fs.line_number,
                       hmd.docstring
                FROM function_signatures fs
                LEFT JOIN houdini_module_data hmd
                    ON fs.func_name = hmd.name AND fs.parent_name = hmd.parent_name
                WHERE fs.func_name LIKE ?
                ORDER BY fs.parent_name, fs.func_name, fs.is_overload, fs.overload_index
                LIMIT ?
            """

            cursor.execute(query, (func_pattern, limit))

            results = []
            for row in cursor.fetchall():
                func_name, parent_name, params_json, return_type, is_overload, overload_index, file_path, line_number, docstring = row

                try:
                    parameters = json.loads(params_json)
                except (json.JSONDecodeError, TypeError):
                    parameters = []

                results.append({
                    "name": func_name,
                    "module": parent_name,
                    "parameters": parameters,
                    "return_type": return_type,
                    "is_overload": bool(is_overload),
                    "overload_index": overload_index,
                    "file_path": file_path,
                    "line_number": line_number,
                    "docstring": docstring
                })

            return results

    def get_related_items(self, item_name: str, max_depth: int = 2) -> dict[str, Any]:
        """
        Get items related to the specified item within a certain relationship depth.

        Args:
            item_name: Name of the item to find relationships for
            max_depth: Maximum depth of relationships to traverse

        Returns:
            dictionary containing the item and its related items
        """
        with analysis_db(db_path=self.db_path) as conn:
            cursor = conn.cursor()

            # First, find the specified item
            query = """
                SELECT name, type, datatype, docstring, parent_name, parent_type
                FROM houdini_module_data
                WHERE name = ?
            """

            cursor.execute(query, (item_name,))
            item_row = cursor.fetchone()

            if not item_row:
                return {"error": f"Item '{item_name}' not found"}

            name, type_name, datatype, docstring, parent_name, parent_type = item_row

            result = {
                "name": name,
                "type": type_name,
                "datatype": datatype,
                "docstring": docstring,
                "parent": {
                    "name": parent_name,
                    "type": parent_type
                } if parent_name else None,
                "children": [],
                "siblings": []
            }

            # Get child items
            if max_depth > 0:
                child_query = """
                    SELECT name, type, datatype, docstring
                    FROM houdini_module_data
                    WHERE parent_name = ?
                """

                cursor.execute(child_query, (name,))

                def make_child(child_row):
                    child_name, child_type, child_datatype, child_docstring = child_row

                    child_item = {
                        "name": child_name,
                        "type": child_type,
                        "datatype": child_datatype,
                        "docstring": child_docstring
                    }

                    # Recursively get children of children if depth allows
                    if max_depth > 1:
                        child_item["children"] = self._get_children(cursor, child_name, max_depth - 1)
                    return child_item

                result["children"] = [
                    make_child(child_row)
                    for child_row in cursor.fetchall()
                ]

            # Get sibling items (other items with the same parent)
            if parent_name:
                sibling_query = """
                    SELECT name, type, datatype, docstring
                    FROM houdini_module_data
                    WHERE parent_name = ? AND name != ?
                    LIMIT 20
                """

                cursor.execute(sibling_query, (parent_name, name))

                def make_sibling(sibling_row):
                    sibling_name, sibling_type, sibling_datatype, sibling_docstring = sibling_row
                    return {
                        "name": sibling_name,
                        "type": sibling_type,
                        "datatype": sibling_datatype,
                        "docstring": sibling_docstring
                    }

                result["siblings"] = [
                    make_sibling(sibling_row)
                    for sibling_row in cursor.fetchall()
                ]

            return result

    def _get_children(self, cursor: sqlite3.Cursor, parent_name: str, depth: int) -> list[dict[str, Any]]:
        """
        Helper method to recursively get children of an item.

        Args:
            cursor: Database cursor
            parent_name: Name of the parent item
            depth: Remaining depth to traverse

        Returns:
            list of dictionaries containing child items
        """
        if depth <= 0:
            return []

        query = """
            SELECT name, type, datatype, docstring
            FROM houdini_module_data
            WHERE parent_name = ?
        """

        cursor.execute(query, (parent_name,))

        children = []
        for row in cursor.fetchall():
            name, type_name, datatype, docstring = row

            child = {
                "name": name,
                "type": type_name,
                "datatype": datatype,
                "docstring": docstring
            }

            if depth > 1:
                child["children"] = self._get_children(cursor, name, depth - 1)

            children.append(child)

        return children
