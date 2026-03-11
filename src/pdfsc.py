#!/usr/bin/env python3
"""
PDF Smart Converter - CLI Entry Point

主程序入口，负责命令行参数解析和工作流调度
"""

import sys
import argparse


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="PDF Smart Converter - AI-Powered PDF to Markdown Transformation"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # convert 命令
    convert_parser = subparsers.add_parser('convert', help='Convert a single PDF to Markdown')
    convert_parser.add_argument('input', help='Input PDF file path')
    convert_parser.add_argument('--output', default='./output', help='Output directory')
    convert_parser.add_argument('--config', help='Configuration file path')
    convert_parser.add_argument('--mode', default='full', choices=['full', 'restore-only', 'enhance-only'])
    convert_parser.add_argument('--image-mode', default='disabled', choices=['disabled', 'description-only', 'extract'])
    convert_parser.add_argument('--verbose', action='store_true', help='Verbose output')

    # convert-batch 命令
    batch_parser = subparsers.add_parser('convert-batch', help='Convert multiple PDFs in a directory')
    batch_parser.add_argument('input_dir', help='Input directory containing PDF files')
    batch_parser.add_argument('--output', default='./output', help='Output directory')

    # verify 命令
    verify_parser = subparsers.add_parser('verify', help='Verify output Markdown format')
    verify_parser.add_argument('input', help='Input Markdown file')

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='Show conversion statistics')
    stats_parser.add_argument('input_dir', help='Output directory to analyze')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    print(f"[INFO] Command: {args.command}")
    print("[INFO] Implementation pending...")


if __name__ == '__main__':
    main()
