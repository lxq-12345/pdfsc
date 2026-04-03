#!/usr/bin/env python3
"""
PDF Smart Converter - CLI Entry Point

主程序入口，负责命令行参数解析和工作流调度
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import ConfigManager, ModelCapabilities
from converter import Converter
from detector import PDFDetector
from extractor import TextExtractor
from image_handler import ImageProcessor
from logger import create_logger
from metadata import FrontmatterGenerator
from validator import HallucinationDetector, MarkdownValidator


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        prog='pdfsc',
        description="PDF Smart Converter - AI-Powered PDF to Markdown Transformation",
        epilog="For more information, visit: https://github.com/yourusername/pdfsc"
    )

    parser.add_argument('--version', action='version', version='pdfsc 0.1.0')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # convert 命令
    convert_parser = subparsers.add_parser('convert', help='Convert a single PDF to Markdown')
    convert_parser.add_argument('input', help='Input PDF file path')
    convert_parser.add_argument('--output', help='Output directory (default: ./output)')
    convert_parser.add_argument('--config', help='Configuration file path')
    convert_parser.add_argument('--mode', choices=['full', 'restore-only', 'enhance-only'],
                                help='Conversion mode')
    convert_parser.add_argument('--image-mode', choices=['disabled', 'description-only', 'extract'],
                                help='Image handling mode')
    convert_parser.add_argument('--offline', action='store_true',
                                help='Enable strict offline mode (no external model calls)')
    convert_parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    # convert-batch 命令
    batch_parser = subparsers.add_parser('convert-batch', help='Convert multiple PDFs in a directory')
    batch_parser.add_argument('input_dir', help='Input directory containing PDF files')
    batch_parser.add_argument('--output', help='Output directory (default: ./output)')
    batch_parser.add_argument('--config', help='Configuration file path')
    batch_parser.add_argument('--offline', action='store_true',
                              help='Enable strict offline mode (no external model calls)')
    batch_parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    # verify 命令
    verify_parser = subparsers.add_parser('verify', help='Verify output Markdown format')
    verify_parser.add_argument('input', help='Input Markdown file or directory')

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='Show conversion statistics')
    stats_parser.add_argument('input_dir', help='Output directory to analyze')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 加载配置（三层）
    try:
        config_manager = ConfigManager()
        config_manager.load_default()

        if hasattr(args, 'config') and args.config:
            config_manager.load_user(args.config)

        config_manager.load_cli_overrides(args)

        # 初始化日志
        logger = create_logger(config_manager)
        logger.info(f"PDF Smart Converter v0.1.0")
        logger.info(f"Command: {args.command}")

        # 显示模型能力和自动降级提示
        maybe_apply_capability_guard(config_manager, logger)

        # 显示配置信息（仅verbose模式）
        if hasattr(args, 'verbose') and args.verbose:
            logger.debug(f"Configuration loaded successfully")
            logger.debug(f"Output directory: {config_manager.get('paths.output_md')}")
            logger.debug(f"Conversion mode: {config_manager.get('conversion.mode')}")
            logger.debug(f"Image mode: {config_manager.get('images.mode')}")

        # 执行命令
        if args.command == 'convert':
            run_convert(args, config_manager, logger)
        elif args.command == 'convert-batch':
            run_convert_batch(args, config_manager, logger)
        elif args.command == 'verify':
            run_verify(args, logger)
        elif args.command == 'stats':
            run_stats(args, logger)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def run_convert(args, config, logger):
    """执行单文件转换"""
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    if input_path.suffix.lower() != '.pdf':
        raise ValueError(f"仅支持 PDF 文件: {input_path}")

    output_root = Path(config.get('paths.output_md', './output'))
    start_index = int(config.get('naming.index_start', 1))

    result = convert_single_pdf(
        pdf_path=input_path,
        output_root=output_root,
        config=config,
        logger=logger,
        index=start_index,
    )

    logger.info("转换完成")
    if result.get('raw_path'):
        logger.info(f"Raw 输出: {result['raw_path']}")
    if result.get('final_path'):
        logger.info(f"Final 输出: {result['final_path']}")


def run_convert_batch(args, config, logger):
    """执行批量转换"""
    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    output_root = Path(config.get('paths.output_md', './output'))
    recursive = bool(config.get('batch.recursive', False))
    pattern = config.get('batch.file_pattern', '*.pdf')
    start_index = int(config.get('naming.index_start', 1))

    pdf_files = collect_pdf_files(input_dir, recursive=recursive, pattern=pattern)
    if not pdf_files:
        logger.warning(f"未找到 PDF 文件: {input_dir}")
        return

    success_count = 0
    results = []

    for offset, pdf_path in enumerate(pdf_files):
        current_index = start_index + offset
        try:
            result = convert_single_pdf(
                pdf_path=pdf_path,
                output_root=output_root,
                config=config,
                logger=logger,
                index=current_index,
            )
            results.append(result)
            success_count += 1
            logger.info(f"[{success_count}/{len(pdf_files)}] 已转换: {pdf_path.name}")
        except Exception as exc:
            logger.error(f"转换失败: {pdf_path.name} -> {exc}")

    logger.info(f"批量转换完成：成功 {success_count}/{len(pdf_files)}")

    # 批量汇总报告
    if results:
        reports_dir = output_root / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        summary_path = reports_dir / f"batch_summary_{_today()}.md"
        _write_batch_summary(summary_path, results, success_count, len(pdf_files))
        logger.info(f"批量报告已生成: {summary_path}")


def run_verify(args, logger):
    """执行格式验证"""
    target = Path(args.input)
    if not target.exists():
        raise FileNotFoundError(f"验证目标不存在: {target}")

    validator = MarkdownValidator(spec_file=str(PROJECT_ROOT / 'skills' / 'Markdown转换规范.md'))
    files = [target] if target.is_file() else sorted(target.rglob('*.md'))

    if not files:
        logger.warning("未找到可验证的 Markdown 文件")
        return

    failed_count = 0
    for md_file in files:
        content = md_file.read_text(encoding='utf-8')
        result = validator.validate(content)
        status = '通过' if result['valid'] else '未通过'
        logger.info(f"{md_file}: {status}，评分 {result['score']}/10")
        if not result['valid']:
            failed_count += 1
            for err in result['errors']:
                logger.error(f"  - {err}")
            for warn in result['warnings']:
                logger.warning(f"  - {warn}")

    logger.info(f"验证完成：总计 {len(files)} 个文件，未通过 {failed_count} 个")


def run_stats(args, logger):
    """显示统计信息"""
    output_dir = Path(args.input_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        raise FileNotFoundError(f"目录不存在: {output_dir}")

    all_md = list(output_dir.rglob('*.md'))
    raw_md = [f for f in all_md if f.name.endswith('_raw.md')]
    final_md = [f for f in all_md if not f.name.endswith('_raw.md')]

    total_size_mb = sum(f.stat().st_size for f in all_md) / (1024 * 1024) if all_md else 0.0

    logger.info("转换统计")
    logger.info(f"- 目录: {output_dir}")
    logger.info(f"- Markdown总数: {len(all_md)}")
    logger.info(f"- Raw文件数: {len(raw_md)}")
    logger.info(f"- Final文件数: {len(final_md)}")
    logger.info(f"- 总大小: {total_size_mb:.2f} MB")


def maybe_apply_capability_guard(config, logger):
    """在 CLI 层面提前提示模型能力，必要时降级图片模式。"""
    provider = config.get('api.provider')
    model = config.get('api.model')

    if not provider or not model:
        logger.warning('未配置 API provider/model，后续将使用本地回退模式。')
        return

    registry = ModelCapabilities()
    registry.load_registry(PROJECT_ROOT / 'config' / 'model_capabilities.yml')

    unknown_vision = bool(config.get('api.unknown_model_vision', False))
    desc = registry.describe(provider, model, unknown_vision=unknown_vision)

    logger.info(
        f"模型能力：provider={desc['provider']} model={desc['model']} "
        f"known={desc['known']} vision={desc['vision']}"
    )

    image_mode = config.get('images.mode', 'disabled')
    if image_mode != 'disabled' and not desc['vision']:
        config.set('images.mode', 'disabled')
        logger.warning(
            f"当前模型 {model} 不支持视觉，已将 images.mode 自动降级为 disabled。"
        )


def convert_single_pdf(pdf_path, output_root, config, logger, index):
    """转换单个 PDF，输出 raw/final 文件。"""
    detector = PDFDetector()
    analysis = detector.analyze(str(pdf_path))
    pdf_type = analysis['type']

    logger.info(f"检测类型: {pdf_path.name} -> {pdf_type}")

    with TextExtractor(str(pdf_path)) as extractor:
        extracted = extractor.extract_structure()

    metadata_generator = FrontmatterGenerator()
    frontmatter = metadata_generator.generate(str(pdf_path))
    metadata = parse_frontmatter(frontmatter)
    metadata['frontmatter'] = frontmatter.strip()
    metadata['source_pdf'] = pdf_path.name
    metadata['pdf_type'] = pdf_type

    converter = Converter(config=config, logger=logger, pdf_type=pdf_type)
    mode = config.get('conversion.mode', 'full')
    save_intermediate = bool(config.get('conversion.save_intermediate', True))

    restore_markdown = None
    final_markdown = None

    if mode == 'restore-only':
        restore_markdown = converter.convert_restore(extracted, metadata)
    elif mode == 'enhance-only':
        restore_markdown = converter.convert_restore(extracted, metadata)
        final_markdown = converter.convert_enhance(restore_markdown, metadata)
    else:
        restore_markdown, final_markdown = converter.convert_full(extracted, metadata)

    # 图片处理（C2阶段）
    image_mode = config.get('images.mode', 'disabled')
    if image_mode != 'disabled':
        doc_index = str(index).zfill(2)
        images_dir = output_root / 'images'
        with ImageProcessor(pdf_path, images_dir, doc_index) as img_proc:
            min_width = int(config.get('images.min_width', 100))
            if restore_markdown:
                restore_markdown = img_proc.process(
                    restore_markdown, image_mode=image_mode, min_width=min_width
                )
            if final_markdown:
                final_markdown = img_proc.process(
                    final_markdown, image_mode=image_mode, min_width=min_width
                )
        logger.info(f"图片处理完成（模式：{image_mode}）")

    base_name = build_output_basename(pdf_path.stem, index, config)
    raw_dir = output_root / 'markdown' / 'raw'
    final_dir = output_root / 'markdown' / 'final'
    raw_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    raw_path = None
    final_path = None

    if restore_markdown and (save_intermediate or mode == 'restore-only'):
        raw_path = raw_dir / f"{base_name}_raw.md"
        raw_path.write_text(restore_markdown, encoding='utf-8')

    if final_markdown:
        final_path = final_dir / f"{base_name}.md"
        final_path.write_text(final_markdown, encoding='utf-8')

    # 质量检测报告
    reports_dir = output_root / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = None

    if restore_markdown and final_markdown:
        report_lines = [
            f"# 转换质量报告 - {pdf_path.name}",
            f"\n**转换日期**：{_today()}\n",
        ]

        # 格式验证
        validator = MarkdownValidator()
        val_result = validator.validate(final_markdown)
        report_lines.append(validator.generate_report(val_result))

        # 数字幻觉检测
        detector = HallucinationDetector()
        hal_result = detector.detect(restore_markdown, final_markdown)
        report_lines.append(detector.generate_report(hal_result, pdf_name=pdf_path.name))

        report_content = '\n'.join(report_lines)
        report_path = reports_dir / f"{base_name}_quality_report.md"
        report_path.write_text(report_content, encoding='utf-8')

        risk = hal_result['risk_level']
        logger.info(
            f"质量报告已生成: {report_path.name} "
            f"（格式验证={val_result['score']}/10，幻觉风险={risk}）"
        )

    return {
        'pdf': str(pdf_path),
        'type': pdf_type,
        'raw_path': str(raw_path) if raw_path else None,
        'final_path': str(final_path) if final_path else None,
        'report_path': str(report_path) if report_path else None,
        'validation_score': val_result['score'] if restore_markdown and final_markdown else None,
        'hallucination_risk': hal_result['risk_level'] if restore_markdown and final_markdown else None,
    }


def _today():
    """返回今日日期字符串 YYYY-MM-DD。"""
    from datetime import date
    return date.today().isoformat()


def _write_batch_summary(summary_path, results, success_count, total_count):
    """写入批量转换汇总报告。"""
    lines = [
        '# 批量转换汇总报告',
        '',
        f"**日期**：{_today()}",
        f"**总计**：{success_count}/{total_count} 成功",
        '',
        '## 各文件结果',
        '',
        '| 文件 | 类型 | 格式评分 | 幻觉风险 | 报告 |',
        '|------|------|---------|---------|------|',
    ]
    for r in results:
        pdf_name = Path(r['pdf']).name
        pdf_type = r.get('type', '-')
        score = f"{r['validation_score']}/10" if r.get('validation_score') is not None else '-'
        risk = r.get('hallucination_risk', '-') or '-'
        report = Path(r['report_path']).name if r.get('report_path') else '-'
        lines.append(f"| {pdf_name} | {pdf_type} | {score} | {risk} | {report} |")

    summary_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def collect_pdf_files(input_dir, recursive=False, pattern='*.pdf'):
    """收集 PDF 文件列表。"""
    if recursive:
        return sorted(p for p in input_dir.rglob(pattern) if p.is_file())
    return sorted(p for p in input_dir.glob(pattern) if p.is_file())


def parse_frontmatter(frontmatter_text):
    """从 frontmatter 字符串解析 metadata。"""
    lines = frontmatter_text.strip().splitlines()
    if len(lines) < 3 or lines[0].strip() != '---':
        return {}

    end_idx = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            end_idx = idx
            break

    if end_idx is None:
        return {}

    payload = '\n'.join(lines[1:end_idx])
    return yaml.safe_load(payload) or {}


def build_output_basename(pdf_stem, index, config):
    """按配置模板生成输出文件基名。"""
    template = config.get('naming.template', '{index}_{title}.md')
    if template.endswith('.md'):
        template = template[:-3]

    digits = int(config.get('naming.index_digits', 2))
    index_text = str(index).zfill(digits)
    title_text = sanitize_filename(pdf_stem)

    basename = template.format(index=index_text, title=title_text)
    return sanitize_filename(basename).strip('_')


def sanitize_filename(text):
    """清理文件名非法字符。"""
    sanitized = re.sub(r'[<>:"/\\|?*]+', '_', text)
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('._')


if __name__ == '__main__':
    main()
