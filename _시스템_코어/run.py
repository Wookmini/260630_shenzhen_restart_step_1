import os
import sys

def main():
    print("="*50)
    print("  심천지사 전도금 정산 자동화 시스템 - 배치 처리")
    print("="*50)
    print()
    month = input("작업할 정산 월을 입력하세요 (예: 2026-06): ").strip()
    
    if not month:
        print("월이 입력되지 않았습니다. 프로그램이 종료됩니다.")
        return
        
    print(f"\n[{month}] 월 데이터를 처리합니다. 잠시만 기다려주세요...\n")
    
    # 배치 프로세서 실행
    exit_code = os.system(f"python _시스템_코어/batch_processor.py {month}")
    
    print("\n" + "="*50)
    if exit_code == 0:
        print("처리가 완료되었습니다. (위쪽에 에러 메시지가 없는지 확인하세요)")
    else:
        print(f"오류가 발생했습니다. (종료 코드: {exit_code})")
    print("="*50)

if __name__ == "__main__":
    main()
