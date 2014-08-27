import sys, os

DEBUG   = False 
ROOT    = os.path.dirname(os.path.abspath(__file__))
INTERP  = '/home/kargrz/virtualenvs/py2.7/bin/python'  # fix 'USERNAME'
sys.path.insert(1,ROOT)
if sys.executable != INTERP:
   os.execl(INTERP, INTERP, *sys.argv)

from monstermash import app as application
