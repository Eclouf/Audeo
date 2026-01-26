#!/usr/bin/env python3
"""
Script CLI Python pour convertir des options yt-dlp CLI en dict API Python.
Utilisation: python convert_yt_opts.py [--full] [options yt-dlp...]
Exemple: python convert_yt_opts.py --audio-format mp3 --embed-thumbnail
"""

import os
import sys

# Ajout du chemin pour yt-dlp si nécessaire (adaptez si besoin)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yt_dlp
from yt_dlp.options import create_parser

def parse_patched_options(opts):
    patched_parser = create_parser()
    patched_parser.defaults.update({
        'ignoreerrors': False,
        'retries': 0,
        'fragment_retries': 0,
        'extract_flat': False,
        'concat_playlist': 'never',
        'update_self': False,
    })
    original_create_parser = yt_dlp.options.create_parser
    yt_dlp.options.create_parser = lambda: patched_parser
    try:
        return yt_dlp.parse_options(opts)
    finally:
        yt_dlp.options.create_parser = original_create_parser

default_opts = parse_patched_options([]).ydl_opts

def cli_to_api(opts, cli_defaults=False):
    parser_func = yt_dlp.parse_options if cli_defaults else parse_patched_options
    opts_parsed = parser_func(opts).ydl_opts
    diff = {k: v for k, v in opts_parsed.items() if default_opts.get(k) != v}
    if 'postprocessors' in diff:
        default_pps = default_opts.get('postprocessors', [])
        diff['postprocessors'] = [pp for pp in diff['postprocessors']
                                  if pp not in default_pps]
    return diff

if __name__ == '__main__':
    from pprint import pprint

    full_defaults = len(sys.argv) > 1 and sys.argv[1] == '--full'
    args_start = 2 if full_defaults else 1
    options = sys.argv[args_start:]

    if not options:
        print("Usage: python convert_yt_opts.py [--full] [options yt-dlp...]")
        print("  --full : Inclut les defaults CLI complets")
        sys.exit(1)

    print('\nOptions CLI passées:')
    print(' '.join(options))
    print('\nTraduction en API (diff des patched defaults):')
    pprint(cli_to_api(options))
    print('\nAvec defaults CLI complets:')
    pprint(cli_to_api(options, cli_defaults=True))
