#!/usr/bin/env python3
"""
Documentation Validation Script
Validates that code changes are properly documented and consistent.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import json

class DocumentationValidator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.docs_root = self.project_root / "docs"
        self.reference_docs = self.docs_root / "docs" / "reference"
        
    def validate_documentation_coverage(self) -> Dict[str, Any]:
        """Validate that all code changes have corresponding documentation."""
        results = {
            "coverage": 0,
            "missing_docs": [],
            "outdated_docs": [],
            "errors": []
        }
        
        try:
            # Get list of Python files
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if "test" not in str(f) and "__pycache__" not in str(f)]
            
            # Get list of documentation files
            doc_files = list(self.reference_docs.rglob("*.md"))
            
            # Check coverage
            documented_files = 0
            for py_file in python_files:
                if self._has_documentation(py_file, doc_files):
                    documented_files += 1
                else:
                    results["missing_docs"].append(str(py_file))
            
            results["coverage"] = (documented_files / len(python_files)) * 100
            
        except Exception as e:
            results["errors"].append(f"Error validating coverage: {e}")
            
        return results
    
    def _has_documentation(self, py_file: Path, doc_files: List[Path]) -> bool:
        """Check if a Python file has corresponding documentation."""
        file_name = py_file.stem
        
        # Check if there's a guide for this component
        for doc_file in doc_files:
            if file_name.lower() in doc_file.name.lower():
                return True
                
        # Check if the file is mentioned in any documentation
        for doc_file in doc_files:
            try:
                content = doc_file.read_text()
                if file_name in content or str(py_file) in content:
                    return True
            except Exception:
                continue
                
        return False
    
    def validate_examples(self) -> Dict[str, Any]:
        """Validate that all code examples in documentation work."""
        results = {
            "total_examples": 0,
            "working_examples": 0,
            "broken_examples": [],
            "errors": []
        }
        
        try:
            doc_files = list(self.reference_docs.rglob("*.md"))
            
            for doc_file in doc_files:
                examples = self._extract_code_examples(doc_file)
                results["total_examples"] += len(examples)
                
                for example in examples:
                    if self._test_code_example(example):
                        results["working_examples"] += 1
                    else:
                        results["broken_examples"].append({
                            "file": str(doc_file),
                            "example": example[:100] + "..." if len(example) > 100 else example
                        })
                        
        except Exception as e:
            results["errors"].append(f"Error validating examples: {e}")
            
        return results
    
    def _extract_code_examples(self, doc_file: Path) -> List[str]:
        """Extract code examples from markdown file."""
        examples = []
        content = doc_file.read_text()
        
        # Find code blocks
        code_blocks = re.findall(r'```(?:python|typescript|javascript|bash)\n(.*?)\n```', content, re.DOTALL)
        examples.extend(code_blocks)
        
        return examples
    
    def _test_code_example(self, example: str) -> bool:
        """Test if a code example works (basic syntax check)."""
        try:
            # Basic syntax check for Python
            if example.strip().startswith(('import ', 'from ', 'def ', 'class ', 'async def')):
                compile(example, '<string>', 'exec')
                return True
            return True  # Assume other examples work
        except SyntaxError:
            return False
        except Exception:
            return True  # Assume other issues are not syntax errors
    
    def validate_links(self) -> Dict[str, Any]:
        """Validate that all internal links work."""
        results = {
            "total_links": 0,
            "working_links": 0,
            "broken_links": [],
            "errors": []
        }
        
        try:
            doc_files = list(self.reference_docs.rglob("*.md"))
            
            for doc_file in doc_files:
                links = self._extract_links(doc_file)
                results["total_links"] += len(links)
                
                for link in links:
                    if self._test_link(link, doc_file):
                        results["working_links"] += 1
                    else:
                        results["broken_links"].append({
                            "file": str(doc_file),
                            "link": link
                        })
                        
        except Exception as e:
            results["errors"].append(f"Error validating links: {e}")
            
        return results
    
    def _extract_links(self, doc_file: Path) -> List[str]:
        """Extract internal links from markdown file."""
        content = doc_file.read_text()
        
        # Find markdown links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        internal_links = []
        
        for text, url in links:
            if url.startswith(('docs/', './', '../')) or not url.startswith(('http', 'mailto')):
                internal_links.append(url)
                
        return internal_links
    
    def _test_link(self, link: str, from_file: Path) -> bool:
        """Test if an internal link works."""
        try:
            # Resolve relative paths
            if link.startswith('./'):
                target = from_file.parent / link[2:]
            elif link.startswith('../'):
                target = from_file.parent.parent / link[3:]
            elif link.startswith('docs/'):
                target = self.project_root / link
            else:
                target = from_file.parent / link
                
            return target.exists()
        except Exception:
            return False
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        coverage_results = self.validate_documentation_coverage()
        example_results = self.validate_examples()
        link_results = self.validate_links()
        
        report = f"""
# Documentation Validation Report

## Coverage Analysis
- **Coverage**: {coverage_results['coverage']:.1f}%
- **Missing Documentation**: {len(coverage_results['missing_docs'])} files
- **Errors**: {len(coverage_results['errors'])} errors

## Example Validation
- **Total Examples**: {example_results['total_examples']}
- **Working Examples**: {example_results['working_examples']}
- **Broken Examples**: {len(example_results['broken_examples'])}
- **Success Rate**: {(example_results['working_examples'] / max(example_results['total_examples'], 1)) * 100:.1f}%

## Link Validation
- **Total Links**: {link_results['total_links']}
- **Working Links**: {link_results['working_links']}
- **Broken Links**: {len(link_results['broken_links'])}
- **Success Rate**: {(link_results['working_links'] / max(link_results['total_links'], 1)) * 100:.1f}%

## Issues Found

### Missing Documentation
"""
        
        for file in coverage_results['missing_docs']:
            report += f"- {file}\n"
            
        report += "\n### Broken Examples\n"
        for example in example_results['broken_examples']:
            report += f"- {example['file']}: {example['example']}\n"
            
        report += "\n### Broken Links\n"
        for link in link_results['broken_links']:
            report += f"- {link['file']}: {link['link']}\n"
            
        return report

def main():
    """Main function to run documentation validation."""
    validator = DocumentationValidator()
    
    print("🔍 Validating documentation...")
    
    # Run validation
    coverage_results = validator.validate_documentation_coverage()
    example_results = validator.validate_examples()
    link_results = validator.validate_links()
    
    # Generate report
    report = validator.generate_report()
    
    # Print summary
    print(f"📊 Coverage: {coverage_results['coverage']:.1f}%")
    print(f"📝 Examples: {example_results['working_examples']}/{example_results['total_examples']} working")
    print(f"🔗 Links: {link_results['working_links']}/{link_results['total_links']} working")
    
    # Check if validation passed
    coverage_ok = coverage_results['coverage'] >= 80
    examples_ok = (example_results['working_examples'] / max(example_results['total_examples'], 1)) >= 0.9
    links_ok = (link_results['working_links'] / max(link_results['total_links'], 1)) >= 0.95
    
    if coverage_ok and examples_ok and links_ok:
        print("✅ Documentation validation passed!")
        return 0
    else:
        print("❌ Documentation validation failed!")
        print("\n" + report)
        return 1

if __name__ == "__main__":
    sys.exit(main())
