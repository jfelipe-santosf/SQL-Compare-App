from TextComparer import TextComparer
# Example usage
comparer = TextComparer()

text1 = """linha 1 comum
linha 2 modificada que é muito longa para testar o scroll horizontal
linha 3
linha 4"""

text2 = """linha 1 comum
linha 2 original que também é muito longa para testar o scroll horizontal
linha 3 alterada
linha 5"""

result1, result2 = comparer.compare(text1, text2)

print("Text 1 with differences:")
print(result1)
print("\nText 2 with differences:")
print(result2)

print("\nSimilarity ratio:", comparer.get_ratio())