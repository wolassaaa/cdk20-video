$ErrorActionPreference = 'Stop'
$base = Join-Path (Split-Path -Parent $PSScriptRoot) '视频内容稿\教师要求补齐版'
$word = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    foreach ($edition in @('简中','繁中')) {
        $doc = $null
        try {
            $docx = Join-Path $base ('视频内容稿_英文加' + $edition + '.docx')
            $pdf = Join-Path $base ('视频内容稿_英文加' + $edition + '.pdf')
            $doc = $word.Documents.Open($docx, $false, $false)
            $doc.Fields.Update() | Out-Null
            foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
            $doc.Repaginate()
            foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() }
            $doc.Save()
            $doc.ExportAsFixedFormat($pdf, 17)
            Write-Output ($edition + ' PAGES=' + $doc.ComputeStatistics(2) + ' TOC=' + $doc.TablesOfContents.Count)
        } finally {
            if ($null -ne $doc) { $doc.Close(0); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) | Out-Null }
        }
    }
} finally {
    if ($null -ne $word) { $word.Quit(); [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) | Out-Null }
}
