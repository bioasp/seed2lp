from . import color
from ._version import __version__


def print_logo():
    """Print the seed2lp ASCII banner.

    Must be called explicitly (e.g. once from __main__.main()) rather than
    run as an import-time side effect: on platforms where multiprocessing
    defaults to the "spawn" start method (macOS, Windows), every worker
    process re-imports this package from scratch, so a module-level print
    here would render the banner once per spawned process instead of once
    per run.
    """
    print(color.cyan_light+color.bold+"""           
                       _   ___    _   
  ___   ___   ___   __| | |_  \  | | _ __  
 / __| / _ \ / _ \ / _` |   ) |  | || '_ \ 
 \__ \|  __/|  __/| (_| |  / /_  | || |_) |
 |___/ \___| \___| \__,_| |____| |_|| .__/    
                                    |_|         
      """+color.reset)
