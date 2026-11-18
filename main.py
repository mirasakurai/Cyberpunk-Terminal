#!/usr/bin/env python

import sys
import os

# add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui import main

if __name__ == "__main__":
    main()
