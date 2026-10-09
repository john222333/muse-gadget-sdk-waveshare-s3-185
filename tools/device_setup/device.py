# SPDX-License-Identifier: Apache-2.0
"""Flash a public bundle and provision personal settings locally over USB."""
import argparse, getpass, hashlib, json, pathlib, subprocess, sys, time
import serial
from serial.tools import list_ports

def port_name(requested):
    if requested: return requested
    ports=[p.device for p in list_ports.comports() if p.vid==0x303A and p.pid==0x1001]
    if len(ports)!=1: raise SystemExit('Specify --port; found '+str(len(ports))+' ESP USB ports.')
    return ports[0]

def manifest_files(folder):
    root=folder.resolve(); manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if manifest['chip']!='esp32s3' or manifest['board']!='waveshare-s3-185': raise ValueError('Wrong board bundle')
    files=[]
    for entry in manifest['files']:
        path=(root/entry['file']).resolve()
        if root not in path.parents: raise ValueError('Invalid bundle path')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']: raise ValueError('Bundle checksum failed')
        files.extend([entry['offset'],str(path)])
    return files

def flash(args):
    files=manifest_files(args.bundle)
    base=[sys.executable,'-m','esptool','--chip','esp32s3','--port',port_name(args.port),'--baud','460800']
    if args.erase: subprocess.run(base+['erase-flash'],check=True)
    subprocess.run(base+['write-flash','--flash-mode','dio','--flash-size','16MB','--flash-freq','80m']+files,check=True)
    print('Flash complete. Run configure, then pair and set Wi-Fi in the Muse phone app.')

def send_config(port,values):
    command=('>user.config='+json.dumps(values,ensure_ascii=True,separators=(',',':'))+'\n').encode()
    if len(command)>1024: raise ValueError('Configuration exceeds device serial limit')
    link=serial.Serial();link.port=port;link.baudrate=115200;link.timeout=.2;link.dtr=False;link.rts=False
    link.open()
    try:
        time.sleep(1);link.reset_input_buffer()
        for start in range(0,len(command),64):
            link.write(command[start:start+64]);link.flush();time.sleep(.03)
        deadline=time.monotonic()+10;pending=b''
        while time.monotonic()<deadline:
            pending+=link.read(4096)
            if b'@user.config saved;' in pending:
                link.write(b'>user.reboot\n');link.flush();time.sleep(.5)
                print('Settings saved; restarting. Personal settings were not written to this computer.')
                return
            if b'@user.config invalid' in pending: raise ValueError('Device rejected configuration')
        raise TimeoutError('No configuration acknowledgement. Close serial monitor and check the installed firmware.')
    finally: link.close()

def configure(args):
    values={}
    token=getpass.getpass('Muse SDK token (hidden; Enter keeps existing): ').strip()
    if token:values['sdk_token']=token
    values['relay_ip']=input('Computer relay IPv4 (Enter for direct/router networking): ').strip()
    values['tts_url']=input('Speech API URL (Enter disables text-to-speech): ').strip()
    values['tts_key']=getpass.getpass('Speech API bearer key (hidden; Enter for none): ').strip()
    values['phone_audio']=input('Play new phone Muse replies on this board? [Y/n]: ').strip().lower()!='n'
    send_config(port_name(args.port),values)

def main():
    parser=argparse.ArgumentParser(description='Waveshare S3 1.85 direct flash and USB configuration')
    sub=parser.add_subparsers(dest='mode',required=True)
    f=sub.add_parser('flash');f.add_argument('--port');f.add_argument('--bundle',type=pathlib.Path,default=pathlib.Path(__file__).absolute().parent/'firmware');f.add_argument('--erase',action='store_true',help='Erase old firmware, Wi-Fi and pairing first')
    c=sub.add_parser('configure');c.add_argument('--port')
    args=parser.parse_args()
    try: flash(args) if args.mode=='flash' else configure(args)
    except (ValueError,TimeoutError,serial.SerialException) as error:raise SystemExit(str(error))
if __name__=='__main__':main()
