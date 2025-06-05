import difflib
from typing import List, Tuple

class CompareProcedureSchema:
    def compare_procedure(self, source: str, target: str):
        """
        Compare two SQL procedures and return their differences.
        
        Args:
            source: Source procedure body
            target: Target procedure body
            
        Returns:
            Tuple of (source_diff, target_diff) with prefixed lines indicating differences
        """
        # Normalize both procedure bodies
        source_lines = self._normalize_lines(source)
        target_lines = self._normalize_lines(target)
        
        # Perform the comparison
        source_diff, target_diff = self._diff_lines(source_lines, target_lines)
        
        return source_diff, target_diff
    
    def _normalize_lines(self, text: str) -> List[str]:
        """
        Normalize SQL procedure text by:
        - Splitting into lines
        - Removing empty lines
        - Removing comments
        - Converting to lowercase
        - Stripping whitespace
        
        Args:
            text: SQL procedure body
            
        Returns:
            List of normalized lines
        """
        if not text:
            return []
            
        lines = []
        for line in text.splitlines():
            # Strip whitespace and convert to lowercase
            line = line.strip().casefold()
            
            # Skip empty lines and comments
            if not line or line.startswith(('--', '#')):
                continue
                
            lines.append(line)
            
        return lines
    
    def _diff_lines(self, source_lines: List[str], target_lines: List[str]) -> Tuple[List[str], List[str]]:
        """
        Compare normalized lines from source and target procedures.
        
        Args:
            source_lines: Normalized lines from source procedure
            target_lines: Normalized lines from target procedure
            
        Returns:
            Tuple of (source_diff, target_diff) with prefixed lines
        """
        # Initialize difflib SequenceMatcher for more accurate comparison
        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        
        # Initialize result lists
        source_diff = []
        target_diff = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are identical in both
                for line in source_lines[i1:i2]:
                    source_diff.append(f"  {line}")
                for line in target_lines[j1:j2]:
                    target_diff.append(f"  {line}")
            elif tag == 'delete':
                # Lines only in source
                for line in source_lines[i1:i2]:
                    source_diff.append(f"++ {line}")
            elif tag == 'insert':
                # Lines only in target
                for line in target_lines[j1:j2]:
                    target_diff.append(f"-- {line}")
            elif tag == 'replace':
                # Lines differ between source and target
                for line in source_lines[i1:i2]:
                    source_diff.append(f"|| {line}")
                for line in target_lines[j1:j2]:
                    target_diff.append(f"|| {line}")
        
        return source_diff, target_diff