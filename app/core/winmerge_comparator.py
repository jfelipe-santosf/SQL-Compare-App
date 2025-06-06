import difflib
from typing import Optional, Tuple, List, Dict, Any, Union
from enum import Enum
import re


class DiffAlgorithm(Enum):
    """Algoritmos de comparação disponíveis."""
    DEFAULT = "default"
    MINIMAL = "minimal"  # Similar ao algoritmo Myers
    NONE = "none"       # Comparação linha por linha sem alinhamento
    QUICK = "quick"     # Comparação rápida


class IgnoreOptions:
    """Opções para ignorar diferenças durante a comparação."""
    
    def __init__(self):
        self.ignore_whitespace = False
        self.ignore_case = False
        self.ignore_blank_lines = False
        self.ignore_line_endings = False
        self.ignore_regex_patterns: List[str] = []
        
    def should_ignore_line(self, line: str) -> bool:
        """Verifica se uma linha deve ser ignorada baseada nas opções."""
        if self.ignore_blank_lines and not line.strip():
            return True
            
        for pattern in self.ignore_regex_patterns:
            if re.match(pattern, line):
                return True
                
        return False
    
    def normalize_line(self, line: str) -> str:
        """Normaliza uma linha baseada nas opções de ignore."""
        normalized = line
        
        if self.ignore_line_endings:
            normalized = normalized.rstrip('\r\n')
            
        if self.ignore_whitespace:
            normalized = ' '.join(normalized.split())
            
        if self.ignore_case:
            normalized = normalized.lower()
            
        return normalized


class DiffBlock:
    """Representa um bloco de diferença encontrado."""
    
    def __init__(self, block_type: str, left_start: int, left_end: int, 
                 right_start: int, right_end: int, 
                 left_lines: List[str] = None, right_lines: List[str] = None):
        self.type = block_type  # 'equal', 'replace', 'delete', 'insert'
        self.left_start = left_start
        self.left_end = left_end
        self.right_start = right_start
        self.right_end = right_end
        self.left_lines = left_lines or []
        self.right_lines = right_lines or []
        
    def __repr__(self):
        return f"DiffBlock({self.type}, L{self.left_start}-{self.left_end}, R{self.right_start}-{self.right_end})"


class WinMergeLikeComparator:
    """
    Comparador de textos inspirado no WinMerge com algoritmos avançados de diferenciação.
    
    Implementa características similares ao WinMerge:
    - Múltiplos algoritmos de comparação
    - Opções para ignorar diferenças
    - Detecção de blocos movidos
    - Alinhamento inteligente de linhas
    - Visualização lado a lado
    """
    
    def __init__(self, algorithm: DiffAlgorithm = DiffAlgorithm.DEFAULT):
        self.algorithm = algorithm
        self.ignore_options = IgnoreOptions()
        self.diff_blocks: List[DiffBlock] = []
        self.similarity_ratio = 0.0
        
    def set_ignore_options(self, **options):
        """Configura opções para ignorar diferenças."""
        for key, value in options.items():
            if hasattr(self.ignore_options, key):
                setattr(self.ignore_options, key, value)
    
    def _preprocess_lines(self, lines: List[str]) -> Tuple[List[str], List[int]]:
        """
        Pré-processa linhas aplicando opções de ignore.
        Retorna linhas processadas e mapeamento para índices originais.
        """
        processed_lines = []
        line_mapping = []
        
        for i, line in enumerate(lines):
            if not self.ignore_options.should_ignore_line(line):
                normalized = self.ignore_options.normalize_line(line)
                processed_lines.append(normalized)
                line_mapping.append(i)
                
        return processed_lines, line_mapping
    
    def _myers_like_diff(self, lines1: List[str], lines2: List[str]) -> List[DiffBlock]:
        """
        Implementa um algoritmo similar ao algoritmo de Myers usado pelo WinMerge.
        Baseado na Longest Common Subsequence (LCS) para melhor alinhamento.
        """
        # Usar SequenceMatcher com heurística para melhor performance
        matcher = difflib.SequenceMatcher(
            isjunk=None, 
            a=lines1, 
            b=lines2,
            autojunk=False
        )
        
        blocks = []
        opcodes = matcher.get_opcodes()
        
        for tag, i1, i2, j1, j2 in opcodes:
            left_lines = lines1[i1:i2] if i1 < i2 else []
            right_lines = lines2[j1:j2] if j1 < j2 else []
            
            block = DiffBlock(
                block_type=tag,
                left_start=i1,
                left_end=i2,
                right_start=j1,
                right_end=j2,
                left_lines=left_lines,
                right_lines=right_lines
            )
            blocks.append(block)
            
        return blocks
    
    def _none_algorithm_diff(self, lines1: List[str], lines2: List[str]) -> List[DiffBlock]:
        """
        Algoritmo 'none' - comparação linha por linha sem alinhamento automático.
        Similar à opção 'none' do WinMerge.
        """
        blocks = []
        max_lines = max(len(lines1), len(lines2))
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else None
            line2 = lines2[i] if i < len(lines2) else None
            
            if line1 is None:
                # Inserção
                block = DiffBlock('insert', i, i, i, i+1, [], [line2])
            elif line2 is None:
                # Deleção
                block = DiffBlock('delete', i, i+1, i, i, [line1], [])
            elif line1 == line2:
                # Igual
                block = DiffBlock('equal', i, i+1, i, i+1, [line1], [line2])
            else:
                # Substituição
                block = DiffBlock('replace', i, i+1, i, i+1, [line1], [line2])
                
            blocks.append(block)
            
        return blocks
    
    def _quick_diff(self, lines1: List[str], lines2: List[str]) -> List[DiffBlock]:
        """
        Algoritmo rápido para comparação básica.
        Otimizado para performance em arquivos grandes.
        """
        if lines1 == lines2:
            return [DiffBlock('equal', 0, len(lines1), 0, len(lines2), lines1, lines2)]
        
        # Usar comparação simples sem heurísticas complexas
        matcher = difflib.SequenceMatcher(
            isjunk=lambda x: len(x.strip()) == 0,  # Ignorar linhas vazias como junk
            a=lines1,
            b=lines2,
            autojunk=True
        )
        
        blocks = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            block = DiffBlock(
                block_type=tag,
                left_start=i1,
                left_end=i2,
                right_start=j1,
                right_end=j2,
                left_lines=lines1[i1:i2],
                right_lines=lines2[j1:j2]
            )
            blocks.append(block)
            
        return blocks
    
    def _detect_moved_blocks(self, blocks: List[DiffBlock]) -> List[DiffBlock]:
        """
        Detecta blocos de texto que foram movidos (similar ao WinMerge).
        Esta é uma implementação simplificada da detecção de blocos movidos.
        """
        # TODO: Implementar detecção de blocos movidos mais sofisticada
        # Por agora, retorna os blocos originais
        return blocks
    
    def compare(self, text1: str, text2: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Compara dois textos usando o algoritmo selecionado e opções de ignore.
        
        Args:
            text1 (str): Primeiro texto para comparar
            text2 (str): Segundo texto para comparar
            
        Returns:
            tuple: (formatted_text1, formatted_text2) com marcadores de diferença,
                   ou (None, None) se não houver diferenças
        """
        if not isinstance(text1, str) or not isinstance(text2, str):
            raise TypeError("Ambos os argumentos devem ser strings")
        
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        # Pré-processar linhas se necessário
        if any([self.ignore_options.ignore_whitespace,
                self.ignore_options.ignore_case,
                self.ignore_options.ignore_blank_lines,
                self.ignore_options.ignore_regex_patterns]):
            processed_lines1, mapping1 = self._preprocess_lines(lines1)
            processed_lines2, mapping2 = self._preprocess_lines(lines2)
        else:
            processed_lines1, processed_lines2 = lines1, lines2
            mapping1 = list(range(len(lines1)))
            mapping2 = list(range(len(lines2)))
        
        # Escolher algoritmo
        if self.algorithm == DiffAlgorithm.MINIMAL:
            self.diff_blocks = self._myers_like_diff(processed_lines1, processed_lines2)
        elif self.algorithm == DiffAlgorithm.NONE:
            self.diff_blocks = self._none_algorithm_diff(processed_lines1, processed_lines2)
        elif self.algorithm == DiffAlgorithm.QUICK:
            self.diff_blocks = self._quick_diff(processed_lines1, processed_lines2)
        else:  # DEFAULT
            self.diff_blocks = self._myers_like_diff(processed_lines1, processed_lines2)
        
        # Detectar blocos movidos
        self.diff_blocks = self._detect_moved_blocks(self.diff_blocks)
        
        # Calcular similaridade
        matcher = difflib.SequenceMatcher(None, processed_lines1, processed_lines2)
        self.similarity_ratio = matcher.ratio()
        
        # Verificar se há diferenças
        if not self.has_differences():
            return None, None
        
        # Gerar saída formatada
        return self._format_output(lines1, lines2)
    
    def _format_output(self, original_lines1: List[str], 
                      original_lines2: List[str]) -> Tuple[str, str]:
        """
        Formata a saída com marcadores visuais similares ao WinMerge.
        """
        result1 = []
        result2 = []
        
        for block in self.diff_blocks:
            if block.type == "equal":
                for line in block.left_lines:
                    result1.append(f"  {line}")
                for line in block.right_lines:
                    result2.append(f"  {line}")
                    
            elif block.type == "replace":
                # Marcador especial para substituições (similar ao WinMerge)
                for line in block.left_lines:
                    result1.append(f"~ {line}")
                for line in block.right_lines:
                    result2.append(f"~ {line}")
                    
                # Balancear se necessário
                len_diff = len(block.left_lines) - len(block.right_lines)
                if len_diff > 0:
                    result2.extend([""] * len_diff)
                elif len_diff < 0:
                    result1.extend([""] * abs(len_diff))
                    
            elif block.type == "delete":
                for line in block.left_lines:
                    result1.append(f"- {line}")
                    result2.append("")
                    
            elif block.type == "insert":
                for line in block.right_lines:
                    result1.append("")
                    result2.append(f"+ {line}")
        
        return "\n".join(result1), "\n".join(result2)
    
    def has_differences(self) -> bool:
        """Verifica se foram encontradas diferenças."""
        return any(block.type != 'equal' for block in self.diff_blocks)
    
    def get_similarity_ratio(self) -> float:
        """Retorna a taxa de similaridade entre os textos."""
        return self.similarity_ratio
    
    def get_diff_blocks(self) -> List[DiffBlock]:
        """Retorna a lista de blocos de diferença."""
        return self.diff_blocks.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas detalhadas da comparação.
        Similar às estatísticas do WinMerge.
        """
        stats = {
            'total_blocks': len(self.diff_blocks),
            'equal_blocks': 0,
            'different_blocks': 0,
            'added_lines': 0,
            'deleted_lines': 0,
            'modified_lines': 0,
            'similarity_ratio': self.similarity_ratio,
            'algorithm_used': self.algorithm.value
        }
        
        for block in self.diff_blocks:
            if block.type == 'equal':
                stats['equal_blocks'] += 1
            else:
                stats['different_blocks'] += 1
                
            if block.type == 'insert':
                stats['added_lines'] += len(block.right_lines)
            elif block.type == 'delete':
                stats['deleted_lines'] += len(block.left_lines)
            elif block.type == 'replace':
                stats['modified_lines'] += max(len(block.left_lines), len(block.right_lines))
        
        return stats
    
    def generate_unified_diff(self, text1: str, text2: str, 
                            filename1: str = "file1", filename2: str = "file2",
                            context: int = 3) -> str:
        """
        Gera diff no formato unificado (similar ao diff -u do Unix).
        """
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            lines1, lines2,
            fromfile=filename1,
            tofile=filename2,
            n=context
        )
        
        return ''.join(diff)
    
    def generate_side_by_side_html(self, text1: str, text2: str,
                                  filename1: str = "Left", filename2: str = "Right") -> str:
        """
        Gera uma visualização HTML lado a lado similar ao WinMerge.
        """
        result = self.compare(text1, text2)
        if result == (None, None):
            return f"""
            <html>
            <head><title>Comparison Results</title></head>
            <body>
            <h2>Files are identical</h2>
            <p>{filename1} and {filename2} have no differences.</p>
            </body>
            </html>
            """
        
        formatted1, formatted2 = result
        lines1 = formatted1.split('\n')
        lines2 = formatted2.split('\n')
        
        html_content = f"""
        <html>
        <head>
            <title>File Comparison</title>
            <style>
                body {{ font-family: 'Courier New', monospace; font-size: 12px; }}
                .container {{ display: flex; }}
                .column {{ flex: 1; margin: 5px; border: 1px solid #ccc; }}
                .header {{ background-color: #f0f0f0; padding: 5px; font-weight: bold; }}
                .line {{ padding: 2px 5px; border-bottom: 1px solid #eee; }}
                .equal {{ background-color: white; }}
                .modified {{ background-color: #ffffcc; }}
                .added {{ background-color: #ccffcc; }}
                .deleted {{ background-color: #ffcccc; }}
                .empty {{ background-color: #f5f5f5; color: #999; }}
            </style>
        </head>
        <body>
            <h2>File Comparison Results</h2>
            <div class="container">
                <div class="column">
                    <div class="header">{filename1}</div>
        """
        
        for line in lines1:
            css_class = self._get_line_css_class(line)
            display_line = line[2:] if len(line) > 2 else line  # Remove marker
            html_content += f'<div class="line {css_class}">{self._escape_html(display_line)}</div>\n'
        
        html_content += f"""
                </div>
                <div class="column">
                    <div class="header">{filename2}</div>
        """
        
        for line in lines2:
            css_class = self._get_line_css_class(line)
            display_line = line[2:] if len(line) > 2 else line  # Remove marker
            html_content += f'<div class="line {css_class}">{self._escape_html(display_line)}</div>\n'
        
        html_content += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _get_line_css_class(self, line: str) -> str:
        """Determina a classe CSS baseada no marcador da linha."""
        if not line:
            return "empty"
        
        marker = line[:2]
        if marker == "  ":
            return "equal"
        elif marker == "~ ":
            return "modified"
        elif marker == "+ ":
            return "added"
        elif marker == "- ":
            return "deleted"
        else:
            return "equal"
    
    def _escape_html(self, text: str) -> str:
        """Escapa caracteres HTML."""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# EXEMPLO DE USO AVANÇADO
if __name__ == "__main__":
    # Criar comparador com algoritmo Myers-like
    comparator = WinMergeLikeComparator(DiffAlgorithm.MINIMAL)
    
    # Configurar opções de ignore (similar ao WinMerge)
    comparator.set_ignore_options(
        ignore_whitespace=True,
        ignore_case=False,
        ignore_blank_lines=True
    )
    
    text1 = """Primeira linha
Segunda linha   
Terceira linha
Quarta linha original
Quinta linha"""
    
    text2 = """Primeira linha
Segunda linha
Terceira linha modificada
Nova linha inserida
Quinta linha"""
    
    # Comparar textos
    result = comparator.compare(text1, text2)
    
    if result != (None, None):
        print("=== COMPARAÇÃO WINMERGE-LIKE ===")
        formatted1, formatted2 = result
        
        print("\n=== ARQUIVO 1 ===")
        print(formatted1)
        
        print("\n=== ARQUIVO 2 ===")
        print(formatted2)
        
        print(f"\n=== ESTATÍSTICAS ===")
        stats = comparator.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        print(f"\n=== BLOCOS DE DIFERENÇA ===")
        for block in comparator.get_diff_blocks():
            print(block)
        
        # Gerar diff unificado
        print(f"\n=== DIFF UNIFICADO ===")
        unified = comparator.generate_unified_diff(text1, text2, "original.txt", "modified.txt")
        print(unified)
        
    else:
        print("Arquivos são idênticos!")