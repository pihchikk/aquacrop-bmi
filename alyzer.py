import os
from pathlib import Path

class ProjectStructure:
    def __init__(self, root_path='.'):
        self.root_path = Path(root_path).resolve()
        self.structure = {}
        
    def build_structure(self, path=None, current_package=''):
        if path is None:
            path = self.root_path
            
        structure = {}
        
        for item in sorted(path.iterdir()):
            if item.name.startswith('.'):
                continue
                
            if item.is_file():
                # Python files
                if item.suffix == '.py':
                    module_name = item.stem
                    if current_package:
                        full_import = f"{current_package}.{module_name}"
                    else:
                        full_import = module_name
                    structure[item.name] = {
                        'type': 'python',
                        'import': full_import,
                        'emoji': '🐍'
                    }
                
                # Config files
                elif self.is_config_file(item.name):
                    structure[item.name] = {
                        'type': 'config',
                        'config_type': self.get_config_type(item.name),
                        'emoji': self.get_config_emoji(item.name)
                    }
                    
            elif item.is_dir():
                init_file = item / '__init__.py'
                if init_file.exists():
                    if current_package:
                        new_package = f"{current_package}.{item.name}"
                    else:
                        new_package = item.name
                    
                    structure[item.name] = {
                        'type': 'package',
                        'import': new_package,
                        'emoji': '📦',
                        'contents': self.build_structure(item, new_package)
                    }
                else:
                    # Check if directory has any relevant files
                    has_relevant_files = any(
                        child.suffix in {'.py', '.toml', '.yaml', '.yml', '.json'} 
                        or self.is_config_file(child.name)
                        for child in item.rglob('*') if child.is_file()
                    )
                    
                    if has_relevant_files:
                        structure[item.name] = {
                            'type': 'directory',
                            'emoji': '📁',
                            'contents': self.build_structure(item, current_package)
                        }
        
        return structure
    
    def is_config_file(self, filename):
        config_extensions = {'.toml', '.yaml', '.yml', '.json', '.ini', '.cfg'}
        important_files = {'pyproject.toml', 'requirements.txt', 'setup.py'}
        ext = Path(filename).suffix.lower()
        return ext in config_extensions or filename in important_files
    
    def get_config_type(self, filename):
        if filename == 'pyproject.toml':
            return 'pyproject'
        elif filename.endswith('.toml'):
            return 'toml'
        elif filename.endswith(('.yaml', '.yml')):
            return 'yaml'
        elif filename.endswith('.json'):
            return 'json'
        else:
            return 'config'
    
    def get_config_emoji(self, filename):
        if filename == 'pyproject.toml':
            return '🎯'
        elif filename == 'requirements.txt':
            return '📦'
        elif 'docker' in filename.lower():
            return '🐳'
        elif filename in ['setup.py', 'setup.cfg']:
            return '🔧'
        else:
            ext = Path(filename).suffix.lower()
            return {
                '.toml': '⚙️', '.yaml': '⚙️', '.yml': '⚙️', 
                '.json': '📊', '.ini': '⚙️', '.cfg': '⚙️'
            }.get(ext, '📄')
    
    def print_structure(self, structure=None, indent=0, is_last=True):
        if structure is None:
            structure = self.structure
            
        items = list(structure.items())
        
        for i, (name, info) in enumerate(items):
            is_last_item = i == len(items) - 1
            prefix = '    ' * indent + ('└── ' if is_last_item else '├── ')
            emoji = info.get('emoji', '📄')
            
            if info['type'] == 'package':
                print(f"{prefix}{emoji} {name}/ (package)")
                print(f"{'    ' * (indent + 1)}# import {info['import']}")
                if 'contents' in info:
                    self.print_structure(info['contents'], indent + 1, is_last_item)
                    
            elif info['type'] == 'directory':
                print(f"{prefix}{emoji} {name}/")
                if 'contents' in info:
                    self.print_structure(info['contents'], indent + 1, is_last_item)
                    
            elif info['type'] == 'python':
                print(f"{prefix}{emoji} {name}")
                print(f"{'    ' * (indent + 1)}# from {info['import']} import ...")
                
            elif info['type'] == 'config':
                print(f"{prefix}{emoji} {name}")
                print(f"{'    ' * (indent + 1)}# {info['config_type']} config file")
    
    def analyze(self):
        self.structure = self.build_structure()
        print(f"📊 Complete Project Structure: {self.root_path}")
        print("=" * 60)
        self.print_structure()

# Usage
analyzer = ProjectStructure('.')
analyzer.analyze()