import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Config:
    """博客配置"""
    title: str = "我的博客"
    description: str = "一只个人博客"
    author: str = "作者"
    base_url: str = "https://example.com"
    language: str = "zh"
    
    @classmethod
    def load(cls, config_path: Path) -> 'Config':
        """从 JSON 文件加载配置"""
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save(self, config_path: Path):
        """保存配置到 JSON 文件"""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
