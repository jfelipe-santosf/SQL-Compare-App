import difflib
import tkinter as tk
from tkinter import scrolledtext

text1 = """DROP TABLE IF EXISTS #temp
DROP TABLE IF EXISTS #value01
DROP TABLE IF EXISTS #value02
DECLARE @strAlphaNumeric VARCHAR(500);
DECLARE @originalPath VARCHAR(500);
DECLARE @DataPath VARCHAR(500);

SELECT @originalPath = [path]
FROM   sys.traces
WHERE  id = 2;

SET @strAlphaNumeric = @originalPath

DECLARE @intAlpha INT

SET @intAlpha = Patindex('%[^0-9]%', @strAlphaNumeric)

WHILE @intAlpha > 0
  BEGIN
      SET @strAlphaNumeric = Stuff(@strAlphaNumeric, @intAlpha, 1, '')
      SET @intAlpha = Patindex('%[^0-9]%', @strAlphaNumeric)
  END

SELECT @strAlphaNumeric AS [Value01]
INTO   #value01;

SELECT @DataPath = Replace(Replace(@originalPath, '.trc', ''), @strAlphaNumeric, '')
FROM   #value01

DECLARE @path      VARCHAR(MAX) = (SELECT @DataPath
                  + Cast([Value01] - 1 AS VARCHAR(MAX))
                  + '.trc'AS [Value01]
           FROM   tempdb..#value01),
        @StartTime DATETIME

--Set @StartTime = CONVERT (date, GETDATE());
SET @StartTime = Dateadd(MINUTE, -6, Getdate());

SELECT --TOP 100
Min (StartTime)                                        [min Chamada],
Max (StartTime)                                         [Utima Chamada],
ApplicationName,
ObjectName,
Count(ObjectName)                                       [Qtd - Chamadas],
Count(ObjectName) * Avg (CPU)                           AS [Media Total de CPU],           
Count(ObjectName) * Avg (Reads)                         AS [Media Total de Reads],
Avg (READS)                                             [Media Leitura Logica],
Min(Cast(Duration / 1000 / 1000.00 AS NUMERIC(15, 3)))  [Menor tempo de Exec]
Max(Cast(Duration / 1000 / 1000.00 AS NUMERIC(15, 3)))  [Maior tempo de Exec],
Round(Avg(Cast(Duration / 1000 / 1000.00 AS FLOAT)), 3) [Media de tempo do Exec - ms],
Avg (CPU)                                               [Media Consumo de CPU],
Max (RowCounts)                                         [Maior Qtd Linhas],
DatabaseName,
hostname
FROM   ::fn_trace_gettable (@path, DEFAULT)
WHERE  StartTime >= @StartTime
--WHERE StartTime BETWEEN '2024-12-20 19:20:00.000' AND '2024-12-20 19:26:00.000'
--AND DatabaseName = 'fb_servicesystem'
       AND ObjectName NOT IN ( 'sp_executesql', 'sp_prepexec', 'sp_readrequest', 'sp_readrequest', 'sp_reset_connection' )
and objectname = 'GetBoletoOutActionCollectionConcessionaireToSettlement'
GROUP  BY ObjectName,
          ApplicationName,
          DatabaseName,
          hostname
ORDER  BY 5 DESC
OPTION (RECOMPILE) 
"""

text2 = """DROP TABLE IF EXISTS #temp
DROP TABLE IF EXISTS #value01
DROP TABLE IF EXISTS #value02
DECLARE @strAlphaNumeric VARCHAR(500);
DECLARE @originalPath VARCHAR(500);
DECLARE @DataPath VARCHAR(500);

SELECT @originalPath = [path]
FROM   sys.traces
WHERE  id = 2;

SET @strAlphaNumeric = @originalPath

DECLARE @intAlpha INT

SET @intAlpha = Patindex('%[^0-9]%', @strAlphaNumeric)

WHILE @intAlpha > 0
  BEGIN
      SET @strAlphaNumeric = Stuff(@strAlphaNumeric, @intAlpha, 1, '')
      SET @intAlpha = Patindex('%[^0-9]%', @strAlphaNumeric)
  END

SELECT @strAlphaNumeric AS [Value01]
INTO   #value01;

SELECT @DataPath = Replace(Replace(@originalPath, '.trc', ''), @strAlphaNumeric, '')
FROM   #value01

DECLARE @path      VARCHAR(MAX) = (SELECT @DataPath
                  + Cast([Value01] - 1 AS VARCHAR(MAX))
                  + '.trc'AS [Value01]
           FROM   tempdb..#value01),
        @StartTime DATETIME

--Set @StartTime = CONVERT (date, GETDATE());
SET @StartTime = Dateadd(MINUTE, -6, Getdate());

SELECT --TOP 100
Min (StartTime)                                         [min Chamada],
Max (StartTime)                                         [Ultima Chamada],
ApplicationName,
ObjectName,
Count(ObjectName)                                       [Qtd - Chamadas],
Count(ObjectName) * Avg (CPU)                           AS [Media Total de CPU],           
Count(ObjectName) * Avg (Reads)                         AS [Media Total de Reads],
Avg (READS)                                             [Media Leitura Logica],
Min(Cast(Duration / 1000 / 1000.00 AS NUMERIC(15, 3)))  [Menor tempo de Exec],
Max(Cast(Duration / 1000 / 1000.00 AS NUMERIC(15, 3)))  [Maior tempo de Exec],
Round(Avg(Cast(Duration / 1000 / 1000.00 AS FLOAT)), 3) [Media de tempo do Exec - ms],
Avg (CPU)                                               [Media Consumo de CPU],
Max (RowCounts)                                         [Maior Qtd Linhas],
DatabaseName,
hostname
FROM   ::fn_trace_gettable (@path, DEFAULT)
WHERE  StartTime >= @StartTime
--WHERE StartTime BETWEEN '2024-12-20 19:20:00.000' AND '2024-12-20 19:26:00.000'
--AND DatabaseName = 'fb_servicesystem'
       AND ObjectName NOT IN ( 'sp_executesql', 'sp_prepexec', 'sp_readrequest', 'sp_readrequest', 'sp_reset_connection' )
and objectname = 'GetBoletoOutActionCollectionConcessionaireToSettlement'
GROUP  BY ObjectName,
          ApplicationName,
          DatabaseName,
          hostname
ORDER  BY 5 DESC
OPTION (RECOMPILE) 
"""

lines1 = text1.splitlines()
lines2 = text2.splitlines()

matcher = difflib.SequenceMatcher(None, lines1, lines2)
opcodes = matcher.get_opcodes()

root = tk.Tk()
root.title("Comparação lado a lado com todas as linhas")

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

txt1 = scrolledtext.ScrolledText(frame, width=50, height=30, font=("Consolas", 12))
txt2 = scrolledtext.ScrolledText(frame, width=50, height=30, font=("Consolas", 12))
txt1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
txt2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Cores para destaque
color_removed = "misty rose"
color_added = "pale green"
color_changed = "light goldenrod"
color_equal = "white"

def insert_line(txt, line, tag=None):
    txt.insert(tk.END, line + "\n", tag)

for tag, i1, i2, j1, j2 in opcodes:
    if tag == "equal":
        # linhas iguais - insere normalmente
        for line1, line2 in zip(lines1[i1:i2], lines2[j1:j2]):
            insert_line(txt1, line1, "equal")
            insert_line(txt2, line2, "equal")
    elif tag == "replace":
        # linhas modificadas - marca com amarelo
        for line1 in lines1[i1:i2]:
            insert_line(txt1, line1, "changed")
        for line2 in lines2[j1:j2]:
            insert_line(txt2, line2, "changed")
    elif tag == "delete":
        # linhas removidas do texto 1
        for line1 in lines1[i1:i2]:
            insert_line(txt1, line1, "removed")
        # texto 2 sem linhas correspondentes — insere linhas vazias para alinhar
        for _ in range(i2 - i1):
            insert_line(txt2, "", "equal")
    elif tag == "insert":
        # linhas adicionadas no texto 2
        # texto 1 sem linhas correspondentes — insere linhas vazias para alinhar
        for _ in range(j2 - j1):
            insert_line(txt1, "", "equal")
        for line2 in lines2[j1:j2]:
            insert_line(txt2, line2, "added")

# Configuração das tags de cor
txt1.tag_config("removed", background=color_removed)
txt2.tag_config("added", background=color_added)
txt1.tag_config("changed", background=color_changed)
txt2.tag_config("changed", background=color_changed)
txt1.tag_config("equal", background=color_equal)
txt2.tag_config("equal", background=color_equal)

txt1.config(state=tk.DISABLED)
txt2.config(state=tk.DISABLED)



root.mainloop()
