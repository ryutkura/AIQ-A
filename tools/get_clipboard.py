import os
import sys
from PIL import ImageGrab

def main():
    # クリップボードから画像を取得
    img = ImageGrab.grabclipboard()
    
    if img:
        out_path = '_temp_clipboard.png'
        # 一時ファイルとして保存
        img.save(out_path)
        print(f"SUCCESS: Image successfully saved to {out_path}")
    else:
        print("ERROR: No image found in the clipboard. Please make sure you copied an image.")
        sys.exit(1)

if __name__ == '__main__':
    main()
