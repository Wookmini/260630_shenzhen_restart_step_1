$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open('C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\작업장소 (영수증 보관)\2026-05\심천지사 전도금 정산 양식_2026-05.xlsx')
$wb.Save()
$wb.Close($true)
$excel.Quit()
