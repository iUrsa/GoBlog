import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import Config
from parser import PostParser, Post


class GoBlogGenerator:
    """静态博客生成器"""
    
    def __init__(self, content_dir: Path, output_dir: Path, include_drafts: bool = False):
        self.content_dir = Path(content_dir)
        self.output_dir = Path(output_dir)
        self.include_drafts = include_drafts
        
        # 初始化组件
        self.parser = PostParser(include_drafts=include_drafts)
        
        # 初始化 Jinja2 模板引擎
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # 注册自定义过滤器
        self.env.filters['slugify'] = self.slugify
        
        # 数据存储
        self.config: Optional[Config] = None
        self.posts: List[Post] = []
        self.notes: List[Post] = []
        self.topics: Dict[str, List[Post]] = defaultdict(list)
        self.series: Dict[str, List[Post]] = defaultdict(list)
    
    def load_config(self):
        """加载站点配置"""
        config_path = self.content_dir / 'config.json'
        self.config = Config.load(config_path)
    
    def load_content(self):
        """加载所有内容"""
        # 加载文章
        posts_dir = self.content_dir / 'posts'
        if posts_dir.exists():
            self._load_from_directory(posts_dir, is_note=False)
        
        # 加载笔记
        notes_dir = self.content_dir / 'notes'
        if notes_dir.exists():
            self._load_from_directory(notes_dir, is_note=True)
        
        # 排序文章（按日期倒序）
        self.posts.sort(key=lambda p: p.date, reverse=True)
        self.notes.sort(key=lambda p: p.date, reverse=True)
        
        print(f"   已加载 {len(self.posts)} 篇文章，{len(self.notes)} 条笔记")
    
    def _load_from_directory(self, directory: Path, is_note: bool = False):
        """从目录加载内容"""
        for md_file in directory.rglob('*.md'):
            post = self.parser.parse(md_file)
            if post:
                if is_note:
                    self.notes.append(post)
                else:
                    self.posts.append(post)
                    
                    # 按主题分类
                    for topic in post.topics:
                        self.topics[topic].append(post)
                    
                    # 按系列分类
                    if post.series:
                        self.series[post.series].append(post)
    
    def generate(self):
        """生成整个站点"""
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制静态文件
        self._copy_static_files()
        
        # 生成页面
        self._generate_index()
        self._generate_writing()
        self._generate_topics()
        self._generate_series()
        self._generate_notes()
        self._generate_posts()
        self._generate_feed()
        
        print("✅ 网站生成成功！")
    
    def _copy_static_files(self):
        """复制静态资源"""
        static_dir = Path(__file__).parent / 'static'
        if static_dir.exists():
            shutil.copytree(static_dir, self.output_dir, dirs_exist_ok=True)
            print("📁 已复制静态文件")
    
    def _render_template(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.env.get_template(template_name)
        return template.render(config=self.config, **kwargs)
    
    def _write_file(self, file_path: Path, content: str):
        """写入文件"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_index(self):
        """生成首页"""
        # 获取最近的文章（前5篇）
        recent_posts = self.posts[:5]
        
        # 获取主题列表（按文章数排序，取前5）
        topic_list = [
            {'name': name, 'slug': self.slugify(name), 'count': len(posts)}
            for name, posts in self.topics.items()
        ]
        topic_list.sort(key=lambda x: x['count'], reverse=True)
        topic_list = topic_list[:5]
        
        # 获取系列列表（取前3）
        series_list = [
            {'name': name, 'slug': self.slugify(name), 'count': len(posts)}
            for name, posts in self.series.items()
        ]
        series_list.sort(key=lambda x: x['count'], reverse=True)
        series_list = series_list[:3]
        
        content = self._render_template(
            'index.html',
            recent_posts=recent_posts,
            topics=topic_list,
            series=series_list,
            notes=self.notes[:5]
        )
        self._write_file(self.output_dir / 'index.html', content)
        print("📄 已生成首页")
    
    def _generate_writing(self):
        """生成文章列表页"""
        content = self._render_template('writing.html', posts=self.posts)
        self._write_file(self.output_dir / 'writing.html', content)
        print("📄 已生成文章列表")
    
    def _generate_topics(self):
        """生成主题索引页"""
        topic_list = [
            {'name': name, 'slug': self.slugify(name), 'count': len(posts)}
            for name, posts in self.topics.items()
        ]
        topic_list.sort(key=lambda x: x['count'], reverse=True)
        
        content = self._render_template('topics.html', topics=topic_list)
        self._write_file(self.output_dir / 'topics.html', content)
        print("📄 已生成分类页面")
        
        # 生成每个主题的页面
        topics_dir = self.output_dir / 'topics'
        for name, posts in self.topics.items():
            posts.sort(key=lambda p: p.date, reverse=True)
            content = self._render_template(
                'topic.html',
                topic={'name': name, 'slug': self.slugify(name)},
                posts=posts
            )
            self._write_file(topics_dir / f"{self.slugify(name)}.html", content)
        
        if self.topics:
            print(f"📄 已生成 {len(self.topics)} 个分类页面")
    
    def _generate_series(self):
        """生成系列索引页"""
        series_list = []
        for name, posts in self.series.items():
            posts.sort(key=lambda p: p.date)
            series_list.append({
                'name': name,
                'slug': self.slugify(name),
                'posts': posts,
                'count': len(posts)
            })
        series_list.sort(key=lambda x: x['count'], reverse=True)
        
        content = self._render_template('series.html', series=series_list)
        self._write_file(self.output_dir / 'series.html', content)
        print("📄 已生成系列列表")
        
        # 生成每个系列的页面
        series_dir = self.output_dir / 'series'
        for name, posts in self.series.items():
            posts.sort(key=lambda p: p.date)
            content = self._render_template(
                'series_detail.html',
                series={'name': name, 'slug': self.slugify(name)},
                posts=posts
            )
            self._write_file(series_dir / f"{self.slugify(name)}.html", content)
        
        if self.series:
            print(f"📄 已生成 {len(self.series)} 个系列页面")
    
    def _generate_notes(self):
        """生成笔记页"""
        if not self.notes:
            return
        
        content = self._render_template('notes.html', notes=self.notes)
        self._write_file(self.output_dir / 'notes.html', content)
        print("📄 已生成笔记页面")
    
    def _generate_posts(self):
        """生成所有文章详情页"""
        for post in self.posts:
            # 按日期创建目录结构
            year = post.date.strftime('%Y')
            month = post.date.strftime('%m')
            post_dir = self.output_dir / 'writing' / year / month
            content = self._render_template('post.html', post=post)
            self._write_file(post_dir / f"{post.slug}.html", content)
        
        for note in self.notes:
            note_dir = self.output_dir / 'notes'
            content = self._render_template('post.html', post=note)
            self._write_file(note_dir / f"{note.slug}.html", content)
        
        print(f"📄 已生成 {len(self.posts)} 篇文章和 {len(self.notes)} 条笔记")
    
    def _generate_feed(self):
        """生成 RSS Feed"""
        # 取最近20篇文章
        recent_posts = self.posts[:20]
        
        content = self._render_template('feed.xml', posts=recent_posts)
        self._write_file(self.output_dir / 'feed.xml', content)
        print("📄 已生成 RSS 订阅源")
    
    @staticmethod
    def slugify(text: str) -> str:
        """生成 URL slug"""
        import re
        # 转换为小写，替换空格为连字符
        slug = text.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug
