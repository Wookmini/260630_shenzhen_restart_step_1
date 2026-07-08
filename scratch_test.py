import sys, os, subprocess
filepath = r'c:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\_시스템_코어\batch_processor.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Make template_data empty to bypass old overrides during test
content = content.replace('if os.path.exists(template_path):', 'if False:')

# bypass excel save to avoid PermissionError
content = content.replace('export_to_excel(results, month_label=month_str, output_path=excel_path)', '# export_to_excel(...)')

# Save as test processor
test_filepath = filepath.replace('batch_processor.py', 'batch_processor_test.py')
with open(test_filepath, 'w', encoding='utf-8') as f:
    f.write(content)

subprocess.run([sys.executable, test_filepath, '2026-06'])
