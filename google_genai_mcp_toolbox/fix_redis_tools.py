#!/usr/bin/env python3
"""
Script to convert Redis tools from operation/key_pattern format to commands format
"""

import re

def fix_redis_tools(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern to match Redis tools with operation and key_pattern
    pattern = r'(\s+)(\w+[-\w]*):(\s+kind: redis\s+source: memorystore-redis\s+description: [^\n]+\n)(\s+)operation: (set|get|delete)(\s+parameters:(?:\s+- name: \w+\s+type: \w+\s+description: [^\n]+\n)*)\s+key_pattern: "([^"]+)"'

    def replace_redis_tool(match):
        indent = match.group(1)
        tool_name = match.group(2)
        header = match.group(3)
        param_indent = match.group(4)
        operation = match.group(5)
        parameters = match.group(6)
        key_pattern = match.group(7)

        # Convert key_pattern variables from {var} to $var format
        redis_key = key_pattern.replace('{', '$').replace('}', '')

        if operation == 'set':
            # For SET operations, we need to extract the value parameter
            # Look for the second parameter (usually the value to set)
            param_lines = parameters.strip().split('\n')
            value_param = None
            for line in param_lines:
                if 'name:' in line and 'session_id' not in line:
                    value_param = line.split('name:')[1].strip()
                    break

            if value_param:
                command = f'      - [SET, "{redis_key}", "${value_param}"]'
            else:
                # Fallback - try to infer from common patterns
                if 'rag_context' in key_pattern:
                    command = f'      - [SET, "{redis_key}", "$rag_context"]'
                elif 'requirements_analyzed' in key_pattern:
                    command = f'      - [SET, "{redis_key}", "$raw_response"]'
                elif 'test_cases' in key_pattern:
                    command = f'      - [SET, "{redis_key}", "$test_cases_data"]'
                elif 'feedback' in key_pattern:
                    command = f'      - [SET, "{redis_key}", "$feedback_data"]'
                elif 'analysis' in key_pattern:
                    command = f'      - [SET, "{redis_key}", "$analysis_content"]'
                else:
                    command = f'      - [SET, "{redis_key}", "$value"]'

        elif operation == 'get':
            command = f'      - [GET, "{redis_key}"]'
        elif operation == 'delete':
            command = f'      - [DEL, "{redis_key}"]'

        # Remove ttl line if present
        parameters = re.sub(r'\s+ttl: -1 # Permanent cache.*\n', '', parameters)

        result = f"{indent}{tool_name}:{header}{param_indent}commands:\n{command}{parameters}"
        return result

    # Apply the replacement
    content = re.sub(pattern, replace_redis_tool, content, flags=re.MULTILINE | re.DOTALL)

    with open(file_path, 'w') as f:
        f.write(content)

    print("Fixed Redis tools format")

if __name__ == "__main__":
    fix_redis_tools("/Users/mv/Documents/genai-exchange/agents/google_genai_mcp_toolbox/tools.yaml")