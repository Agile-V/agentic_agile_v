#!/usr/bin/env python3
"""
Interface Contract Validator for Agentic Agile-V

Validates that implementation matches task interface examples exactly.
Catches API incompatibilities before tests run.

This is the CRITICAL validator that prevents the most common failure mode:
implementing an API that doesn't match the task's usage examples.

Usage:
    python scripts/validate_interface_contracts.py --task tasks/AAV-001/task_description.md --implementation src/module.py
    python scripts/validate_interface_contracts.py --task-id AAV-001

Exit codes:
    0: All interface contracts validated successfully
    1: Interface incompatibility detected
    2: Invalid input or usage error

Inspired by: Agile-V Skills quality-gates (Interface Validation Gate)
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any


def parse_task_examples(task_path: Path) -> dict[str, list[dict[str, Any]]]:
    """
    Parse task description to extract API usage examples.
    
    Returns:
        dict: {
            'ClassName': [
                {'call': 'ClassName(arg1, arg2)', 'args': [...], 'kwargs': {...}},
                ...
            ]
        }
    """
    if not task_path.exists():
        raise FileNotFoundError(f"Task description not found: {task_path}")
    
    with open(task_path) as f:
        content = f.read()
    
    examples = {}
    
    # Extract code blocks
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', content, re.DOTALL)
    
    for block in code_blocks:
        # Look for instantiation patterns: ClassName(...)
        # Common patterns:
        #   Message(topic="test", payload={...})
        #   router = WebSocketRouter(max_connections=10)
        #   connection.send(data)
        
        # Find all function/class calls
        calls = re.findall(r'(\w+)\((.*?)\)', block, re.DOTALL)
        
        for class_name, args_str in calls:
            # Skip obvious method calls (lowercase first letter)
            if class_name and class_name[0].islower() and '.' not in class_name:
                continue
            
            if class_name not in examples:
                examples[class_name] = []
            
            # Parse arguments
            try:
                # Try to parse as Python expression
                call_expr = f"{class_name}({args_str})"
                examples[class_name].append({
                    'call': call_expr.strip(),
                    'raw_args': args_str.strip()
                })
            except:
                # If parsing fails, store raw
                examples[class_name].append({
                    'call': f"{class_name}({args_str})",
                    'raw_args': args_str.strip()
                })
    
    return examples


def load_implementation(impl_path: Path) -> Any:
    """
    Dynamically load implementation module.
    
    Returns:
        module: Loaded Python module
    """
    if not impl_path.exists():
        raise FileNotFoundError(f"Implementation not found: {impl_path}")
    
    spec = importlib.util.spec_from_file_location("implementation", impl_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load implementation: {impl_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module


def extract_class_signature(module: Any, class_name: str) -> dict[str, Any] | None:
    """
    Extract __init__ signature for a class.
    
    Returns:
        dict: {
            'required': ['arg1', 'arg2'],
            'optional': {'arg3': default_value, ...},
            'all': ['arg1', 'arg2', 'arg3', ...]
        }
    """
    if not hasattr(module, class_name):
        return None
    
    cls = getattr(module, class_name)
    
    import inspect
    try:
        sig = inspect.signature(cls)
        
        required = []
        optional = {}
        all_params = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            all_params.append(param_name)
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            else:
                optional[param_name] = param.default
        
        return {
            'required': required,
            'optional': optional,
            'all': all_params
        }
    except:
        return None


def validate_call_compatibility(class_name: str, example_call: str, signature: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validate that an example call is compatible with implementation signature.
    
    Returns:
        (is_valid, error_message)
    """
    # Parse the example call to extract arguments
    # Example: "Message(topic='test', payload={'data': 1})"
    
    # Extract args from call
    match = re.search(rf'{class_name}\((.*?)\)$', example_call, re.DOTALL)
    if not match:
        return True, None  # Can't parse, skip validation
    
    args_str = match.group(1).strip()
    
    # Count positional and keyword arguments
    if not args_str:
        # No arguments in example
        positional_count = 0
        keyword_args = set()
    else:
        # Simple heuristic: count commas not inside brackets/parens
        # and check for = signs for kwargs
        
        # Split by commas (simplified - doesn't handle nested structures perfectly)
        parts = []
        depth = 0
        current = []
        
        for char in args_str:
            if char in '({[':
                depth += 1
            elif char in ')}]':
                depth -= 1
            elif char == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
                continue
            current.append(char)
        
        if current:
            parts.append(''.join(current).strip())
        
        # Classify as positional or keyword
        positional_count = 0
        keyword_args = set()
        
        for part in parts:
            if '=' in part and not any(x in part for x in ['==', '!=', '<=', '>=']):
                # Keyword argument
                key = part.split('=')[0].strip()
                keyword_args.add(key)
            else:
                # Positional argument
                positional_count += 1
    
    # Check if call would work with implementation signature
    required = signature['required']
    all_params = signature['all']
    
    # Check: all required parameters must be satisfied
    # by either positional args or keyword args
    
    unsatisfied_required = []
    for i, req_param in enumerate(required):
        # Satisfied by positional arg?
        if i < positional_count:
            continue
        # Satisfied by keyword arg?
        if req_param in keyword_args:
            continue
        # Not satisfied
        unsatisfied_required.append(req_param)
    
    if unsatisfied_required:
        return False, f"Example call missing required parameter(s): {', '.join(unsatisfied_required)}"
    
    # Check: no extra required parameters in implementation
    example_provides = positional_count + len(keyword_args)
    if len(required) > example_provides:
        extra_required = required[example_provides:]
        return False, f"Implementation requires parameter(s) not in example: {', '.join(extra_required)}"
    
    return True, None


def validate_interfaces(task_path: Path, impl_path: Path) -> bool:
    """
    Main validation: check implementation matches task examples.
    
    Returns:
        bool: True if all validations pass
    """
    print(f"\n{'='*70}")
    print("Interface Contract Validation")
    print(f"{'='*70}")
    print(f"Task: {task_path}")
    print(f"Implementation: {impl_path}")
    print(f"{'─'*70}\n")
    
    # Parse task examples
    try:
        examples = parse_task_examples(task_path)
        print(f"📋 Found {len(examples)} class(es) with usage examples\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to parse task examples: {e}\n", file=sys.stderr)
        return False
    
    # Load implementation
    try:
        module = load_implementation(impl_path)
        print("✅ Implementation loaded successfully\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to load implementation: {e}\n", file=sys.stderr)
        return False
    
    # Validate each class
    all_valid = True
    validation_count = 0
    
    for class_name, calls in examples.items():
        print(f"🔍 Validating {class_name}:")
        
        # Get implementation signature
        signature = extract_class_signature(module, class_name)
        
        if signature is None:
            print("   ⚠️  Class not found in implementation or signature unavailable")
            print("      This may be OK if it's defined elsewhere\n")
            continue
        
        print(f"   Required params: {signature['required']}")
        print(f"   Optional params: {list(signature['optional'].keys())}")
        
        # Validate each example call
        for call_info in calls:
            example_call = call_info['call']
            is_valid, error_msg = validate_call_compatibility(
                class_name, example_call, signature
            )
            
            validation_count += 1
            
            if is_valid:
                print(f"   ✅ {example_call[:60]}..." if len(example_call) > 60 else f"   ✅ {example_call}")
            else:
                print(f"   ❌ {example_call[:60]}..." if len(example_call) > 60 else f"   ❌ {example_call}")
                print(f"      {error_msg}")
                all_valid = False
        
        print()
    
    # Summary
    print(f"{'─'*70}")
    
    if all_valid:
        print(f"✅ PASS: All {validation_count} interface contract(s) validated")
        print(f"{'='*70}\n")
        return True
    else:
        print("❌ FAIL: Interface incompatibility detected")
        print("\n⚠️  CRITICAL: Implementation API doesn't match task examples.")
        print("   This will cause TypeErrors or missing argument errors at runtime.")
        print("\n🔧 Resolution:")
        print("   Option 1: Make missing parameters optional with defaults")
        print("   Option 2: Adjust implementation to match task examples")
        print("   Option 3: Update task description if examples are wrong")
        print("\n📊 Evidence:")
        print("   - Agentic Agile-V v2.1: Made sender_id required → 8 tests ERROR")
        print("   - Agile-V Skills v2.1: Interface validation caught this → 100% pass")
        print(f"{'='*70}\n")
        return False


def find_task_and_implementation(task_id: str, search_root: Path = Path('.')) -> tuple[Path | None, Path | None]:
    """
    Auto-discover task description and implementation for a task ID.
    
    Returns:
        (task_path, impl_path) or (None, None) if not found
    """
    # Look for task description
    task_patterns = [
        search_root / f"tasks/{task_id}/task_description.md",
        search_root / f"tasks/{task_id}/TASK.md",
        search_root / f"tasks/{task_id}/README.md",
    ]
    
    task_path = None
    for pattern in task_patterns:
        if pattern.exists():
            task_path = pattern
            break
    
    # Look for implementation (common patterns)
    impl_patterns = [
        search_root / f"tasks/{task_id}/implementation/*.py",
        search_root / "src/*.py",
        search_root / "*.py",
    ]
    
    impl_path = None
    for pattern in impl_patterns:
        matches = list(pattern.parent.glob(pattern.name)) if '*' in str(pattern) else [pattern]
        if matches and matches[0].exists():
            impl_path = matches[0]
            break
    
    return task_path, impl_path


def main():
    parser = argparse.ArgumentParser(
        description="Validate interface contracts for Agentic Agile-V tasks"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--task-id",
        help="Task ID (auto-discovers task and implementation paths)"
    )
    group.add_argument(
        "--task",
        help="Path to task description file"
    )
    
    parser.add_argument(
        "--implementation",
        help="Path to implementation file (required with --task)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.task_id:
            # Auto-discover paths
            task_path, impl_path = find_task_and_implementation(args.task_id)
            
            if task_path is None:
                print(f"\n❌ ERROR: Could not find task description for {args.task_id}\n", file=sys.stderr)
                sys.exit(2)
            
            if impl_path is None:
                print(f"\n❌ ERROR: Could not find implementation for {args.task_id}\n", file=sys.stderr)
                sys.exit(2)
        else:
            # Use provided paths
            if not args.implementation:
                parser.error("--implementation required when using --task")
            
            task_path = Path(args.task)
            impl_path = Path(args.implementation)
        
        # Validate
        is_valid = validate_interfaces(task_path, impl_path)
        
        # Exit with appropriate code
        sys.exit(0 if is_valid else 1)
        
    except (FileNotFoundError, ImportError, ValueError) as e:
        print(f"\n❌ ERROR: {e}\n", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
