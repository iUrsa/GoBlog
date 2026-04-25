#!/usr/bin/env python3
"""
GoBlog - 静态博客生成器
"""

import click
import sys
from pathlib import Path
from generator import GoBlogGenerator
from watcher import watch_content


@click.command()
@click.option('--content', '-c', default='./content', 
              type=click.Path(exists=True), help='内容目录')
@click.option('--output', '-o', default='./public', 
              type=click.Path(), help='输出目录')
@click.option('--watch', '-w', is_flag=True, help='监听文件变化')
@click.option('--clean', is_flag=True, help='清空输出目录')
@click.option('--drafts', is_flag=True, help='包含草稿文章')
def main(content, output, watch, clean, drafts):
    """GoBlog - 静态博客生成器"""
    
    content_path = Path(content)
    output_path = Path(output)
    
    # 创建生成器实例
    generator = GoBlogGenerator(content_path, output_path, include_drafts=drafts)
    
    if clean and output_path.exists():
        click.echo(f"正在清空 {output_path}...")
        import shutil
        shutil.rmtree(output_path)
    
    try:
        # 加载配置和内容
        click.echo("📖 正在加载配置...")
        generator.load_config()
        
        click.echo("📝 正在加载文章...")
        generator.load_content()
        
        if watch:
            click.echo(f"🔍 正在监听 {content_path} 目录变化...")
            click.echo("按 Ctrl+C 停止监听")
            watch_content(generator, content_path)
        else:
            # 生成站点
            click.echo("🏗️  正在生成网站...")
            generator.generate()
            click.echo(f"\n✨ 网站生成成功！输出目录：{output_path.absolute()}")
            click.echo(f"   本地预览：cd {output_path} && python -m http.server 8080")
            click.echo(f"   然后访问：http://localhost:8080")
            
    except Exception as e:
        click.echo(f"❌ 错误：{e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
