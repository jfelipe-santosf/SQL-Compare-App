import difflib

class CompareProcedureSchema:
    def __init__(self):
        self.matcher = None
        self.opcodes = None
        
    def compare(self, text1, text2):
        """
        Compare two texts and return formatted versions with diff markers
        
        Args:
            text1 (str): First text to compare
            text2 (str): Second text to compare
            
        Returns:
            tuple: (formatted_text1, formatted_text2) with diff markers
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        self.matcher = difflib.SequenceMatcher(None, lines1, lines2)
        self.opcodes = self.matcher.get_opcodes()
        
        result1 = []
        result2 = []
        
        for tag, i1, i2, j1, j2 in self.opcodes:
            if tag == "equal":
                for l1, l2 in zip(lines1[i1:i2], lines2[j1:j2]):
                    result1.append(f"  {l1}")
                    result2.append(f"  {l2}")
            elif tag == "replace":
                for l1 in lines1[i1:i2]:
                    result1.append(f"||{l1}")
                for l2 in lines2[j1:j2]:
                    result2.append(f"||{l2}")
            elif tag == "delete":
                for l1 in lines1[i1:i2]:
                    result1.append(f"--{l1}")
                for _ in range(i2 - i1):
                    result2.append("")
            elif tag == "insert":
                for _ in range(j2 - j1):
                    result1.append("")
                for l2 in lines2[j1:j2]:
                    result2.append(f"++{l2}")
        
        return "\n".join(result1), "\n".join(result2)

    def get_ratio(self):
        """
        Get similarity ratio between the compared texts
        
        Returns:
            float: Similarity ratio (0.0 to 1.0)
        """
        if self.matcher:
            return self.matcher.ratio()
        return 0.0

    def get_opcodes(self):
        """
        Get the opcodes describing how to transform text1 into text2
        
        Returns:
            list: List of opcodes if comparison has been done, None otherwise
        """
        return self.opcodes