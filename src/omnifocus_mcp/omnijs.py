"""OmniJS script execution utilities for OmniFocus.

OmniJS (JavaScript running inside OmniFocus) provides access to features
not available via AppleScript, such as:
- flattenedTasks, flattenedProjects, flattenedFolders globals
- Perspective.BuiltIn.* constants
- Perspective.Custom.all collection
- Task.Status and Project.Status enums
"""

import asyncio
import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

# Directory containing JavaScript scripts
SCRIPTS_DIR = Path(__file__).parent / "scripts"

# Static JXA wrapper that executes parameterized OmniJS scripts
JXA_WRAPPER = """function run() {
    try {
        const app = Application('OmniFocus');
        app.includeStandardAdditions = true;
        const wrappedScript = "(function(params) { " + scriptContent + " })(" + JSON.stringify(params) + ");";
        return app.evaluateJavascript(wrappedScript);
    } catch (e) {
        return JSON.stringify({error: e.message});
    }
}"""


def escape_for_jxa(script: str) -> str:
    """
    Escape an OmniJS script for embedding in JXA backticks.

    Args:
        script: The OmniJS script to escape

    Returns:
        Escaped script safe for JXA template literal
    """
    return script.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")


def create_jxa_wrapper(omnijs_script: str) -> str:
    """
    Create a JXA (JavaScript for Automation) wrapper that executes
    an OmniJS script inside OmniFocus.

    Args:
        omnijs_script: The OmniJS script to execute

    Returns:
        JXA script that will run the OmniJS in OmniFocus
    """
    escaped_script = escape_for_jxa(omnijs_script)

    return f"""function run() {{
    try {{
        const app = Application('OmniFocus');
        app.includeStandardAdditions = true;

        // Run the OmniJS script in OmniFocus and capture the output
        const result = app.evaluateJavascript(`{escaped_script}`);

        // Return the result (usually JSON string)
        return result;
    }} catch (e) {{
        return JSON.stringify({{ error: e.message }});
    }}
}}"""


async def execute_omnijs(script: str) -> dict[str, Any]:
    """
    Execute an OmniJS script inside OmniFocus via JXA wrapper.

    This function:
    1. Escapes the script for JXA backticks
    2. Wraps in JXA that calls app.evaluateJavascript()
    3. Writes to a temp file
    4. Executes via osascript -l JavaScript
    5. Parses and returns the JSON result

    Args:
        script: The OmniJS script to execute. Should return a JSON string.

    Returns:
        Parsed JSON result from the script

    Raises:
        RuntimeError: If script execution fails
    """
    jxa_script = create_jxa_wrapper(script)

    # Write to temp file
    fd, temp_path = tempfile.mkstemp(suffix=".js", prefix="omnijs_")
    try:
        os.write(fd, jxa_script.encode("utf-8"))
        os.close(fd)

        # Execute via osascript
        proc = await asyncio.create_subprocess_exec(
            "osascript",
            "-l",
            "JavaScript",
            temp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip() or "Unknown error"
            raise RuntimeError(f"OmniJS execution failed: {error_msg}")

        # Parse JSON result
        result_str = stdout.decode().strip()
        if not result_str:
            return {"error": "Empty result from OmniJS"}

        try:
            return json.loads(result_str)
        except json.JSONDecodeError:
            # If it's not JSON, return the raw result
            return {"result": result_str, "raw": True}

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


async def execute_omnijs_raw(script: str) -> str:
    """
    Execute an OmniJS script and return the raw string result.

    Use this when the script doesn't return JSON.

    Args:
        script: The OmniJS script to execute

    Returns:
        Raw string result from the script

    Raises:
        RuntimeError: If script execution fails
    """
    jxa_script = create_jxa_wrapper(script)

    # Write to temp file
    fd, temp_path = tempfile.mkstemp(suffix=".js", prefix="omnijs_")
    try:
        os.write(fd, jxa_script.encode("utf-8"))
        os.close(fd)

        # Execute via osascript
        proc = await asyncio.create_subprocess_exec(
            "osascript",
            "-l",
            "JavaScript",
            temp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip() or "Unknown error"
            raise RuntimeError(f"OmniJS execution failed: {error_msg}")

        return stdout.decode().strip()

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


@lru_cache(maxsize=32)
def load_script(name: str) -> str:
    """
    Load a JavaScript script from the scripts directory.

    Scripts are cached after first load for performance.

    Args:
        name: Script name without .js extension (e.g., 'list_perspectives')
              Can include subdirectory (e.g., 'common/status_maps')

    Returns:
        The script content as a string

    Raises:
        FileNotFoundError: If the script file doesn't exist
    """
    script_path = SCRIPTS_DIR / f"{name}.js"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    return script_path.read_text(encoding="utf-8")


async def execute_omnijs_with_params(script_name: str, params: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a parameterized OmniJS script inside OmniFocus.

    This function uses osascript -e flags to avoid temp files entirely.
    The script receives parameters as a 'params' object.

    Args:
        script_name: Name of the script in scripts/ directory (without .js)
        params: Parameters to pass to the script as a dict

    Returns:
        Parsed JSON result from the script

    Raises:
        RuntimeError: If script execution fails
        FileNotFoundError: If script file doesn't exist
    """
    script_content = load_script(script_name)

    # Build osascript command with -e flags
    # Three -e arguments: params definition, script content, JXA wrapper
    proc = await asyncio.create_subprocess_exec(
        "osascript",
        "-l",
        "JavaScript",
        "-e",
        f"var params = {json.dumps(params)};",
        "-e",
        f"var scriptContent = {json.dumps(script_content)};",
        "-e",
        JXA_WRAPPER,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error_msg = stderr.decode().strip() or "Unknown error"
        raise RuntimeError(f"OmniJS execution failed: {error_msg}")

    # Parse JSON result
    result_str = stdout.decode().strip()
    if not result_str:
        return {"error": "Empty result from OmniJS"}

    try:
        return json.loads(result_str)
    except json.JSONDecodeError:
        # If it's not JSON, return the raw result
        return {"result": result_str, "raw": True}
