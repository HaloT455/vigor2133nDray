#!/usr/bin/env python3
"""Read-only, local 3.3V TTL serial logging; NEVER sends a byte or performs flashing."""
from __future__ import annotations
import argparse,os,select,termios,time
from pathlib import Path
BAUD={9600:termios.B9600,57600:termios.B57600,115200:termios.B115200}

def capture(port:Path,out:Path,baud:int,duration:int):
    if baud not in BAUD or not 1<=duration<=600:raise ValueError('Invalid baud/duration')
    if out.exists() or out.is_symlink():raise FileExistsError('Refusing to overwrite log')
    fd=os.open(port,os.O_RDONLY|os.O_NOCTTY|os.O_NONBLOCK)
    try:
        attr=termios.tcgetattr(fd)
        attr[0]=termios.IGNPAR;attr[1]=0;attr[2]=termios.CS8|termios.CREAD|termios.CLOCAL
        attr[3]=0;attr[4]=BAUD[baud];attr[5]=BAUD[baud]
        attr[6][termios.VMIN]=0;attr[6][termios.VTIME]=0
        termios.tcsetattr(fd,termios.TCSANOW,attr)
        target_fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            until=time.monotonic()+duration
            total=0
            while time.monotonic()<until and total<8*1024*1024:
                ready,_,_=select.select([fd],[],[],max(0,min(1,until-time.monotonic())))
                if not ready:continue
                try:chunk=os.read(fd,32768)
                except BlockingIOError:continue
                if chunk:
                    os.write(target_fd,chunk);total+=len(chunk)
        finally:os.close(target_fd)
    finally:os.close(fd)
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=Path,required=True)
    p.add_argument('--baud',type=int,choices=sorted(BAUD),default=115200)
    p.add_argument('--seconds',type=int,default=45)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();capture(a.port,a.out,a.baud,a.seconds)
    print('Saved private serial capture:',a.out)
    print('Contains potentially sensitive identifiers: redact before sharing. No commands sent.')
if __name__=='__main__':main()
