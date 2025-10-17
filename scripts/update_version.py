#!/usr/bin/env python3
"""
Version History Management Script
Automatically updates version history and tracks changes.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

class VersionManager:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.version_file = self.project_root / "docs" / "VERSION.md"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        
    def get_current_version(self) -> str:
        """Get the current version from VERSION.md."""
        try:
            if not self.version_file.exists():
                return "0.0.0"
                
            content = self.version_file.read_text()
            version_match = re.search(r'### v(\d+\.\d+\.\d+)', content)
            if version_match:
                return version_match.group(1)
            return "0.0.0"
        except Exception:
            return "0.0.0"
    
    def get_next_version(self, change_type: str = "patch") -> str:
        """Get the next version number based on change type."""
        current_version = self.get_current_version()
        major, minor, patch = map(int, current_version.split('.'))
        
        if change_type == "major":
            return f"{major + 1}.0.0"
        elif change_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"
    
    def get_changed_files(self) -> List[str]:
        """Get list of changed files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            return []
        except Exception:
            return []
    
    def categorize_changes(self, files: List[str]) -> Dict[str, List[str]]:
        """Categorize changed files by type."""
        categories = {
            "backend": [],
            "frontend": [],
            "docs": [],
            "tests": [],
            "scripts": [],
            "config": [],
            "other": []
        }
        
        for file_path in files:
            if not file_path:
                continue
                
            if file_path.startswith("backend/"):
                categories["backend"].append(file_path)
            elif file_path.startswith("frontend/"):
                categories["frontend"].append(file_path)
            elif file_path.startswith("docs/"):
                categories["docs"].append(file_path)
            elif file_path.startswith("tests/"):
                categories["tests"].append(file_path)
            elif file_path.startswith("scripts/"):
                categories["scripts"].append(file_path)
            elif file_path.endswith((".yaml", ".yml", ".json", ".toml", ".env")):
                categories["config"].append(file_path)
            else:
                categories["other"].append(file_path)
                
        return categories
    
    def get_change_description(self, files: List[str]) -> str:
        """Generate a description of changes based on files."""
        categories = self.categorize_changes(files)
        
        descriptions = []
        
        if categories["backend"]:
            descriptions.append(f"Backend changes ({len(categories['backend'])} files)")
        if categories["frontend"]:
            descriptions.append(f"Frontend changes ({len(categories['frontend'])} files)")
        if categories["docs"]:
            descriptions.append(f"Documentation updates ({len(categories['docs'])} files)")
        if categories["tests"]:
            descriptions.append(f"Test updates ({len(categories['tests'])} files)")
        if categories["scripts"]:
            descriptions.append(f"Script updates ({len(categories['scripts'])} files)")
        if categories["config"]:
            descriptions.append(f"Configuration changes ({len(categories['config'])} files)")
        if categories["other"]:
            descriptions.append(f"Other changes ({len(categories['other'])} files)")
            
        return "; ".join(descriptions)
    
    def determine_change_type(self, files: List[str]) -> str:
        """Determine the change type based on files changed."""
        categories = self.categorize_changes(files)
        
        # Check for breaking changes
        breaking_patterns = [
            r"migration",
            r"breaking",
            r"deprecat",
            r"remove",
            r"delete"
        ]
        
        for file_path in files:
            for pattern in breaking_patterns:
                if re.search(pattern, file_path.lower()):
                    return "major"
        
        # Check for new features
        feature_patterns = [
            r"feature",
            r"new",
            r"add",
            r"implement"
        ]
        
        for file_path in files:
            for pattern in feature_patterns:
                if re.search(pattern, file_path.lower()):
                    return "minor"
        
        # Default to patch
        return "patch"
    
    def update_version_history(self, change_type: str = "patch", description: str = "", files: List[str] = None) -> str:
        """Update the version history with new changes."""
        if files is None:
            files = self.get_changed_files()
            
        if not description:
            description = self.get_change_description(files)
            
        next_version = self.get_next_version(change_type)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Generate version entry
        entry = f"""
### v{next_version} - {today} - {change_type.title()} Release
- **Files Modified**: {', '.join(files) if files else 'No files detected'}
- **Description**: {description}
- **Change Type**: {change_type}
- **Documentation Updated**: {self._get_doc_updates(files)}
- **Breaking Changes**: {self._has_breaking_changes(files)}
- **New Features**: {self._get_new_features(files)}
- **Bug Fixes**: {self._get_bug_fixes(files)}
- **Performance Improvements**: {self._get_performance_improvements(files)}
- **Migration Notes**: {self._get_migration_notes(files)}
"""
        
        # Read existing content
        if self.version_file.exists():
            content = self.version_file.read_text()
        else:
            content = "# Version History\n\n"
        
        # Insert new entry after the header
        lines = content.split('\n')
        insert_index = 2  # After "# Version History" and empty line
        
        # Insert the new entry
        entry_lines = entry.strip().split('\n')
        for i, line in enumerate(entry_lines):
            lines.insert(insert_index + i, line)
        
        # Write updated content
        updated_content = '\n'.join(lines)
        self.version_file.write_text(updated_content)
        
        return next_version
    
    def _get_doc_updates(self, files: List[str]) -> str:
        """Get documentation files that were updated."""
        doc_files = [f for f in files if f.startswith("docs/")]
        if doc_files:
            return ', '.join(doc_files)
        return "None detected"
    
    def _has_breaking_changes(self, files: List[str]) -> str:
        """Check if there are breaking changes."""
        breaking_files = [f for f in files if any(word in f.lower() for word in ['migration', 'breaking', 'deprecat', 'remove'])]
        if breaking_files:
            return f"Yes: {', '.join(breaking_files)}"
        return "No"
    
    def _get_new_features(self, files: List[str]) -> str:
        """Get new features based on files."""
        feature_files = [f for f in files if any(word in f.lower() for word in ['feature', 'new', 'add', 'implement'])]
        if feature_files:
            return f"Detected in: {', '.join(feature_files)}"
        return "None detected"
    
    def _get_bug_fixes(self, files: List[str]) -> str:
        """Get bug fixes based on files."""
        fix_files = [f for f in files if any(word in f.lower() for word in ['fix', 'bug', 'error', 'issue'])]
        if fix_files:
            return f"Detected in: {', '.join(fix_files)}"
        return "None detected"
    
    def _get_performance_improvements(self, files: List[str]) -> str:
        """Get performance improvements based on files."""
        perf_files = [f for f in files if any(word in f.lower() for word in ['performance', 'optimize', 'speed', 'memory'])]
        if perf_files:
            return f"Detected in: {', '.join(perf_files)}"
        return "None detected"
    
    def _get_migration_notes(self, files: List[str]) -> str:
        """Get migration notes based on files."""
        migration_files = [f for f in files if 'migration' in f.lower()]
        if migration_files:
            return f"See: {', '.join(migration_files)}"
        return "None required"
    
    def generate_changelog(self) -> str:
        """Generate a changelog from version history."""
        if not self.version_file.exists():
            return "No version history found."
            
        content = self.version_file.read_text()
        
        # Extract version entries
        entries = re.findall(r'### v(\d+\.\d+\.\d+) - (\d{4}-\d{2}-\d{2}) - (.+?)\n(.*?)(?=\n### v|\Z)', content, re.DOTALL)
        
        changelog = "# Changelog\n\n"
        
        for version, date, change_type, details in entries:
            changelog += f"## [{version}] - {date}\n\n"
            
            # Parse details
            lines = details.strip().split('\n')
            for line in lines:
                if line.startswith('- **'):
                    # Format as changelog entry
                    key = line.split('**')[1].rstrip(':')
                    value = line.split('**: ')[1] if '**: ' in line else line.split('**:')[1]
                    changelog += f"### {key}\n{value}\n\n"
            
            changelog += "---\n\n"
        
        return changelog

def main():
    """Main function to manage version history."""
    if len(sys.argv) < 2:
        print("Usage: python update_version.py <change_type> [description]")
        print("Change types: major, minor, patch")
        sys.exit(1)
    
    change_type = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else ""
    
    if change_type not in ["major", "minor", "patch"]:
        print("Error: Change type must be major, minor, or patch")
        sys.exit(1)
    
    manager = VersionManager()
    
    print(f"🔄 Updating version history for {change_type} release...")
    
    # Update version history
    new_version = manager.update_version_history(change_type, description)
    
    print(f"✅ Version updated to v{new_version}")
    print(f"📝 Version history updated in {manager.version_file}")
    
    # Generate changelog
    changelog = manager.generate_changelog()
    manager.changelog_file.write_text(changelog)
    print(f"📋 Changelog generated: {manager.changelog_file}")

if __name__ == "__main__":
    main()
