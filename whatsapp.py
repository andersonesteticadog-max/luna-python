import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from luna.whatsapp.webhook import main

if __name__ == "__main__":
    main()
