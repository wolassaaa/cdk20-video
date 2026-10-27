$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $PSScriptRoot
$docx = Join-Path $base 'AI辅助肝癌候选分子发现内容手册.docx'
$pdf = Join-Path $base 'AI辅助肝癌候选分子发现内容手册.pdf'
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($docx, $false, $true)
    $doc.Repaginate()
    $pages = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($pdf, 17)
    Write-Output ('WORD_EXPORT_PAGES=' + $pages)
    Write-Output ('PDF_CREATED=' + $pdf)
} finally {
    if ($null -ne $doc) { $doc.Close(0); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) | Out-Null }
    if ($null -ne $word) { $word.Quit(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null }
}
