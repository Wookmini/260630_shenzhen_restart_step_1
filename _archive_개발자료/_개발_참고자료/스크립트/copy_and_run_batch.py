import os
import shutil
import sys
import subprocess

SRC_DIR = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\과거 참고데이터\26년 5월\5월 스캔본_재정비\엑셀 대응"
DEST_ROOT = r"C:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\작업장소 (영수증 보관)\2026-05"

# PDF filename (digits only or range) to Assignee directory
ASSIGNEE_MAP = {
    "01": "심천지사",
    "02": "Zhang Liang",
    "03": "Zhang Liang",
    "04": "심천지사",
    "05": "심천지사",
    "06": "심천지사",
    "07": "심천지사",
    "08": "심천지사",
    "09": "심천지사",
    "10": "심천지사",
    "11": "심천지사",
    "12": "심천지사",
    "13": "신순연",
    "14": "신순연",
    "15": "신순연",
    "16": "신순연",
    "17": "신순연",
    "18": "신순연",
    "19": "Zhang Liang",
    "20": "Zhang Liang",
    "21": "Zhang Liang",
    "22": "Zhang Liang",
    "23": "Zhang Liang",
    "24": "Zhang Liang",
    "25": "Zhang Liang",
    "26": "Lin Wei Jian",
    "27": "Lin Wei Jian",
    "28": "Lin Wei Jian",
    "29": "Lin Wei Jian",
    "30": "Lin Wei Jian",
    "31": "Piao Mei Ling",
    "32": "Piao Mei Ling",
    "33": "Piao Mei Ling",
    "34": "Piao Mei Ling",
    "35": "Piao Mei Ling",
    "36": "Piao Mei Ling",
    "37": "Piao Mei Ling",
    "38": "권유석",
    "39": "권유석",
    "40": "권유석",
    "41": "Xiong Feng",
    "42": "Xiong Feng",
    "43": "Xiong Feng",
    "44": "Xiong Feng",
    "45": "Xiong Feng",
    "46": "Chen Guo Liang",
    "47": "Chen Guo Liang",
    "48": "Chen Guo Liang",
    "49": "Chen Guo Liang",
    "50": "Liu Ming Liang",
    "51": "Liu Ming Liang",
    "52": "Liu Ming Liang",
    "53": "Liu Ming Liang",
    "54": "Chen Feng Ju",
    "55": "Chen Feng Ju",
    "56": "Chen Feng Ju",
    "57": "Chen Feng Ju",
    "58": "김명관",
    "59": "김명관",
    "60": "김명관",
    "61-62": "심천지사"
}

def setup_and_run():
    # Clean recreate destination dir
    if os.path.exists(DEST_ROOT):
        print(f"Cleaning existing directory: {DEST_ROOT}")
        shutil.rmtree(DEST_ROOT)
    
    os.makedirs(DEST_ROOT, exist_ok=True)
    
    # Copy files
    for pdf_name in os.listdir(SRC_DIR):
        if not pdf_name.endswith('.pdf'):
            continue
            
        base = os.path.splitext(pdf_name)[0]
        assignee = ASSIGNEE_MAP.get(base, "심천지사")
        
        assignee_dir = os.path.join(DEST_ROOT, assignee)
        os.makedirs(assignee_dir, exist_ok=True)
        
        src_path = os.path.join(SRC_DIR, pdf_name)
        dest_path = os.path.join(assignee_dir, pdf_name)
        
        print(f"Copying {pdf_name} to {assignee} folder...")
        shutil.copy2(src_path, dest_path)
        
    print("Files copied successfully. Running batch_processor...")
    
    # Run batch_processor.py 2026-05
    cmd = [sys.executable, "batch_processor.py", "2026-05"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # We run subprocess and pipe the output directly to stdout/stderr in real-time
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    
    # Read stdout line by line
    for line in process.stdout:
        print(line, end="")
    
    # Read remaining stderr
    stderr_output = process.stderr.read()
    if stderr_output:
        print("STDERR:")
        print(stderr_output)

if __name__ == "__main__":
    setup_and_run()
