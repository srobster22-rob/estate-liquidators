import struct,zlib,sys
def readpng(p):
    d=open(p,'rb').read(); pos=8; w=h=0; idat=b''
    while pos<len(d):
        ln=struct.unpack('>I',d[pos:pos+4])[0]; t=d[pos+4:pos+8]; c=d[pos+8:pos+8+ln]
        if t==b'IHDR': w,h,bd,ct=struct.unpack('>IIBB',c[:10])
        if t==b'IDAT': idat+=c
        pos+=12+ln
    raw=zlib.decompress(idat); bpp=4 if ct==6 else 3; stride=w*bpp; rows=[]; prev=bytearray(stride); i=0
    for y in range(h):
        f=raw[i]; i+=1; line=bytearray(raw[i:i+stride]); i+=stride
        for x in range(stride):
            a=line[x-bpp] if x>=bpp else 0; b=prev[x]; c=prev[x-bpp] if x>=bpp else 0
            if f==1: line[x]=(line[x]+a)&255
            elif f==2: line[x]=(line[x]+b)&255
            elif f==3: line[x]=(line[x]+(a+b)//2)&255
            elif f==4:
                pa=abs(b-c); pb=abs(a-c); pc=abs(a+b-2*c); pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c); line[x]=(line[x]+pr)&255
        rows.append(bytes(line)); prev=line
    return w,h,bpp,rows
def writepng(p,w,h,rows):
    raw=b''.join(b'\x00'+r for r in rows)
    def chunk(t,c): return struct.pack('>I',len(c))+t+c+struct.pack('>I',zlib.crc32(t+c)&0xffffffff)
    open(p,'wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
import os
out=sys.argv[1]; frames=sys.argv[2:]; scale=int(os.environ.get("SCALE","2"))
imgs=[readpng(f) for f in frames]; w,h,bpp,_=imgs[0]; rows=[]
for y in range(0,h,scale):
    row=b''
    for (w2,h2,bpp2,rs) in imgs:
        r=rs[y]
        for x in range(0,w2,scale): row+=r[x*bpp2:x*bpp2+3]+b'\xff'
    rows.append(row)
writepng(out,(w//scale)*len(imgs),len(rows),rows); print(out)
