import difflib
import re
from typing import List, Tuple, Optional
from enum import Enum, auto
from dataclasses import dataclass

class DifferenceType(Enum):
    IDENTICAL = auto()
    MODIFIED = auto()
    ADDED = auto()
    REMOVED = auto()

@dataclass
class DiffResult:
    line_content: str
    diff_type: DifferenceType
    source_line: Optional[int] = None
    target_line: Optional[int] = None

class CompareProcedureSchema:
    def __init__(self, ignore_whitespace: bool = True, ignore_comments: bool = True):
        self.ignore_whitespace = ignore_whitespace
        self.ignore_comments = ignore_comments
        self._comment_pattern = re.compile(r'--.*?$|/\*.*?\*/|#.*?$', re.DOTALL | re.MULTILINE)
        self._whitespace_pattern = re.compile(r'\s+')

    def compare_procedure(self, source: str, target: str) -> Tuple[List[str], List[str]]:
        """
        Compara dois procedimentos SQL e retorna diferenças formatadas como strings
        
        Args:
            source: Código fonte do procedimento
            target: Código alvo do procedimento
            
        Returns:
            Tupla com (diferenças_origem, diferenças_destino) como strings prefixadas
            ou (None, None) se não houver diferenças significativas
        """
        source_diff, target_diff = self._detailed_compare(source, target)
        
        # Verifica se há diferenças significativas
        has_diff = any(
            diff.diff_type != DifferenceType.IDENTICAL 
            for diff in source_diff + target_diff
        )
        
        if not has_diff:
            return None, None
            
        return (
            [self._format_diff(diff) for diff in source_diff],
            [self._format_diff(diff) for diff in target_diff]
        )

    def _detailed_compare(self, source: str, target: str) -> Tuple[List[DiffResult], List[DiffResult]]:
        """Comparação detalhada que retorna objetos DiffResult"""
        # Preserva as quebras de linha originais
        source_lines = source.splitlines()
        target_lines = target.splitlines()
        
        # Normaliza para comparação (sem modificar as linhas originais)
        norm_source = [self._normalize_line(line) for line in source_lines if line.strip()]
        norm_target = [self._normalize_line(line) for line in target_lines if line.strip()]
        
        matcher = difflib.SequenceMatcher(None, norm_source, norm_target, autojunk=False)
        source_diff = []
        target_diff = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for i in range(i1, i2):
                    source_diff.append(DiffResult(
                        source_lines[i], 
                        DifferenceType.IDENTICAL, 
                        i+1, j1+(i-i1)+1
                    ))
                for j in range(j1, j2):
                    target_diff.append(DiffResult(
                        target_lines[j], 
                        DifferenceType.IDENTICAL, 
                        i1+(j-j1)+1, j+1
                    ))
            elif tag == 'delete':
                for i in range(i1, i2):
                    source_diff.append(DiffResult(
                        source_lines[i], 
                        DifferenceType.REMOVED, 
                        i+1
                    ))
            elif tag == 'insert':
                for j in range(j1, j2):
                    target_diff.append(DiffResult(
                        target_lines[j], 
                        DifferenceType.ADDED, 
                        None, j+1
                    ))
            elif tag == 'replace':
                for i in range(i1, i2):
                    source_diff.append(DiffResult(
                        source_lines[i], 
                        DifferenceType.MODIFIED, 
                        i+1
                    ))
                for j in range(j1, j2):
                    target_diff.append(DiffResult(
                        target_lines[j], 
                        DifferenceType.MODIFIED, 
                        None, j+1
                    ))

        return source_diff, target_diff

    def _normalize_line(self, line: str) -> str:
        """Normaliza uma única linha para comparação"""
        if self.ignore_comments:
            line = self._comment_pattern.sub('', line)
        line = line.strip()
        if self.ignore_whitespace:
            line = self._whitespace_pattern.sub(' ', line)
        return line.lower()

    def _format_diff(self, diff: DiffResult) -> str:
        """Formata um DiffResult para string com prefixo"""
        prefixes = {
            DifferenceType.IDENTICAL: '  ',
            DifferenceType.REMOVED: '--',
            DifferenceType.ADDED: '++',
            DifferenceType.MODIFIED: '||'
        }
        return f"{prefixes.get(diff.diff_type, '  ')} {diff.line_content}"