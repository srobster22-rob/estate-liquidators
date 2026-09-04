# crop.py out.png in.png x y w h  -- a 1:1 crop, so detail survives the viewer's downscale
import struct,zlib,sys
def readpng(p):
    d=open(p,'rb').read(); pos=8; w=h=0; idat=b''
    while pos<len(d):
        ln=struct.unpack('>I',d[pos:pos+4])[0]; t=d[pos+4:pos+8]; c=d[pos+8:pos+8+ln]
        if t==b'IHDR': w,h,bd,ct=struct.unpack('>IIBB',c[:10]); assert bd==8 and ct in (2,6), (bd,ct); bpp=3 if ct==2 else 4
        elif t==b'IDAT': idat+=c
        elif t==b'IEND': break
        pos+=12+ln
    raw=zlib.decompress(idat); stride=w*bpp; rows=[]; prev=bytearray(stride); i=0
    for y in range(h):
        f=raw[i]; i+=1; cur=bytearray(raw[i:i+stride]); i+=stride
        if f==1:
            for x in range(bpp,stride): cur[x]=(cur[x]+cur[x-bpp])&255
        elif f==2:
            for x in range(stride): cur[x]=(cur[x]+prev[x])&255
        elif f==3:
            for x in range(stride): cur[x]=(cur[x]+((cur[x-bpp] if x>=bpp else 0)+prev[x])//2)&255
        elif f==4:
            for x in range(stride):
                a=cur[x-bpp] if x>=bpp else 0; b=prev[x]; c=prev[x-bpp] if x>=bpp else 0
                pa=abs(b-c); pb=abs(a-c); pc=abs(a+b-2*c)
                pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c); cur[x]=(cur[x]+pr)&255
        rows.append(bytes(cur)); prev=cur
    return w,h,bpp,rows
def writepng(p,w,h,rows):
    raw=b''.join(b'\0'+r for r in rows)
    def ch(t,c): return struct.pack('>I',len(c))+t+c+struct.pack('>I',zlib.crc32(t+c)&0xffffffff)
    open(p,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw,6))+ch(b'IEND',b''))
out,inp,x,y,w,h=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:7])
W,H,bpp,rows=readpng(inp); x=max(0,min(x,W-w)); y=max(0,min(y,H-h))
res=[]
for r in rows[y:y+h]:
    row=bytearray()
    for px in range(x,x+w): row+=r[px*bpp:px*bpp+3]
    res.append(bytes(row))
writepng(out,w,h,res)
