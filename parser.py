import frontmatter
import markdown
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


@dataclass
class Post:
    """博客文章"""
    title: str
    slug: str
    date: datetime
    content: str = ""
    html_content: str = ""
    description: str = ""
    topics: List[str] = field(default_factory=list)
    series: Optional[str] = None
    updated: Optional[datetime] = None
    draft: bool = False
    file_path: Optional[Path] = None
    
    def to_dict(self):
        """转换为字典"""
        return {
            'title': self.title,
            'slug': self.slug,
            'date': self.date,
            'updated': self.updated,
            'description': self.description,
            'topics': self.topics,
            'series': self.series,
            'draft': self.draft,
            'html_content': self.html_content
        }


class MarkdownRenderer:
    """Markdown 渲染器，支持代码高亮"""
    
    def __init__(self):
        # 配置 Markdown 扩展
        self.md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.meta',
            'markdown.extensions.smarty',
            'markdown.extensions.nl2br',
        ])
    
    def render(self, content: str) -> str:
        """渲染 Markdown 为 HTML"""
        # 自定义代码块处理
        # 这里简化处理，实际可以集成 Pygments
        rendered = self.md.convert(content)
        self.md.reset()
        return rendered


class PostParser:
    """文章解析器"""
    
    def __init__(self, include_drafts: bool = False):
        self.renderer = MarkdownRenderer()
        self.include_drafts = include_drafts
    
    def parse(self, file_path: Path) -> Optional[Post]:
        """解析单个 Markdown 文件"""
        try:
            # 使用 python-frontmatter 解析
            post_data = frontmatter.load(file_path)
            
            # 提取 Frontmatter
            title = post_data.get('title', file_path.stem)
            slug = post_data.get('slug', file_path.stem)
            date = post_data.get('date')
            
            # 处理日期
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            elif not date:
                # 使用文件修改时间
                date = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # 处理更新日期
            updated = post_data.get('updated')
            if isinstance(updated, str):
                updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            
            # 提取标签
            topics = post_data.get('topics', [])
            if isinstance(topics, str):
                topics = [t.strip() for t in topics.split(',')]
            
            # 创建文章对象
            post = Post(
                title=title,
                slug=slug,
                date=date,
                updated=updated,
                description=post_data.get('description', ''),
                topics=topics,
                series=post_data.get('series', None),
                draft=post_data.get('draft', False),
                file_path=file_path
            )
            
            # 渲染内容
            post.html_content = self.renderer.render(post_data.content)
            
            # 检查是否为草稿
            if post.draft and not self.include_drafts:
                return None
                
            return post
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
