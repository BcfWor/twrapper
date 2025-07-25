import asyncio
import websockets
import json
import subprocess
import os
import sys

with open('config.json') as f:
    config = json.load(f)

HOST = config['host']
PORT = config['port']
EXEC_PATH = config['exec_path']
DATADIR = config['datadir']
CWD = config['cwd']
NO_LOGGING = config.get('no_logging', False)

print(f"twrapper listening on {HOST}:{PORT} (no-logging={NO_LOGGING})")
print(f"exec_path={EXEC_PATH}\ndatadir={DATADIR}\ncwd={CWD}")

processes = {}

async def stream_output(proc, logfile, name):
    if NO_LOGGING:
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode(errors='replace')
            print(f"[{name}][{proc.pid}] {text}", end='')
    else:
        with open(logfile, 'a') as f:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode(errors='replace')
                f.write(text)
                f.flush()
                print(f"[{name}][{proc.pid}] {text}", end='')

def kill_later(pid, duration, name):
    async def _kill():
        await asyncio.sleep(duration * 3600)
        proc = processes.get(pid)
        if proc and proc.returncode is None:
            try:
                proc.kill()
                print(f"[auto-kill] name={name} pid={pid} after {duration}h")
            except Exception as e:
                print(f"[auto-kill-error] name={name} pid={pid} error={e}")
    asyncio.create_task(_kill())

async def ws_handler(websocket):
    async for message in websocket:
        print(f"[request] {message}")
        try:
            data = json.loads(message)
            if data.get('action') == 'start_server':
                params = data.get('params', {})
                xml_path = params.get('xml_path')
                duration = params.get('duration')
                log_path = params.get('log_path')
                datadir = params.get('datadir', DATADIR)
                exec_path = params.get('exec_path', EXEC_PATH)
                cwd = params.get('cwd', CWD)
                name = params.get('name', os.path.basename(xml_path) if xml_path else f'server_{len(processes)+1}')
                if not xml_path:
                    await websocket.send(json.dumps({'status': 'error', 'msg': 'Missing xml_path'}))
                    continue
                cmd = [exec_path, f'--server-config={xml_path}', '--network-console']
                env = os.environ.copy()
                env['SUPERTUXKART_DATADIR'] = datadir
                try:
                    proc = await asyncio.create_subprocess_exec(*cmd, cwd=cwd, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
                    processes[proc.pid] = proc
                    if not log_path:
                        log_path = f"/tmp/servers/{name}_{proc.pid}.log"
                    print(f"[start] name={name} pid={proc.pid} cmd={' '.join(cmd)} log={log_path if not NO_LOGGING else 'NOLOG'}")
                    asyncio.create_task(stream_output(proc, log_path, name))
                    if duration:
                        try:
                            duration = float(duration)
                            kill_later(proc.pid, duration, name)
                        except Exception as e:
                            print(f"[duration-error] {e}")
                    await websocket.send(json.dumps({'status': 'ok', 'pid': proc.pid, 'log': log_path if not NO_LOGGING else None}))
                except Exception as e:
                    await websocket.send(json.dumps({'status': 'error', 'msg': str(e)}))
            else:
                await websocket.send(json.dumps({'status': 'error', 'msg': 'Unknown action'}))
        except Exception as e:
            await websocket.send(json.dumps({'status': 'error', 'msg': f'Invalid request: {e}'}))

async def main():
    async with websockets.serve(ws_handler, HOST, PORT):
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
