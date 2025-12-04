
#!/usr/bin/env python3
"""
GPIO config helper used by shell scripts.

Usage:
    gpio_config_tool.py list <config.json>    # prints all available fields per relay
    gpio_config_tool.py validate <config.json> # validates JSON structure, exits 0 on success
"""
import sys
import json
from pathlib import Path

def load_config(path):
    p = Path(path)
    if not p.exists():
        print(f"config file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with p.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"invalid json: {e}", file=sys.stderr)
        sys.exit(3)

def cmd_list(path):
    cfg = load_config(path)
    relays = cfg.get('relays')
    if not isinstance(relays, dict):
        print('missing or invalid "relays" object', file=sys.stderr)
        sys.exit(4)
    for key, v in relays.items():
        fields = []
        if 'pin' in v: fields.append(f"pin={v['pin']}")
        if 'path' in v: fields.append(f"path={v['path']}")
        if 'chip' in v: fields.append(f"chip={v['chip']}")
        if 'line' in v: fields.append(f"line={v['line']}")
        if 'active' in v: fields.append(f"active={v['active']}")
        if fields:
            print(" ".join(fields))
        else:
            print(f"relay {key} missing required fields", file=sys.stderr)

def cmd_validate(path):
    cfg = load_config(path)
    relays = cfg.get('relays')
    if not isinstance(relays, dict):
        print('invalid structure: relays must be a dict', file=sys.stderr)
        return 5
    for key, v in relays.items():
        has_pin_path_active = 'pin' in v and 'path' in v and 'active' in v
        has_chip_line_active = 'chip' in v and 'line' in v and 'active' in v
        if not (has_pin_path_active or has_chip_line_active):
            print(f'relay {key} must have either pin+path+active or chip+line+active', file=sys.stderr)
            return 6
    return 0

def usage():
    print(__doc__.strip(), file=sys.stderr)

def main(argv):
    if len(argv) < 3:
        usage()
        return 2
    cmd = argv[1]
    path = argv[2]
    if cmd == 'list':
        cmd_list(path)
        return 0
    if cmd in ('validate', 'check'):
        return cmd_validate(path)
    usage()
    return 2

if __name__ == '__main__':
    sys.exit(main(sys.argv))
