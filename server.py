'''
# Implementacao de um servidor web escrito em Python
# Autor: Rafael F. Dias 
# Disciplina: Laboratório de Sistemas Operacionais
# Professor: Miguel Xavier
# Data: 10-04-2023 
# Versao: 1.0
#  Licenca: GPL-2.0
# Requisitos: python3
'''

import http.server
import subprocess

# Retrieve memory usage information from /proc/meminfo
def get_meminfo():
    cmd = '''
        memtotal=$(awk 'NR==1 {printf \"%0.f\", $2/1000}' /proc/meminfo) && 
        memfree=$(awk 'NR==2 {printf \"%0.f\", ($1-$2)/1000}' /proc/meminfo) &&
        memused=$(( $memtotal - $memfree )) &&
        printf "%s,%s" "$memtotal" "$memused"
    '''
    p = subprocess.Popen(['sh', '-c', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise RuntimeError(f'Error running command: {cmd}.\n{stderr.decode()}')
    mem_str = stdout.decode().strip()
    memused, memtotal = mem_str.split(',')
    mem_str = f"Mem used: {memused}\nTotal mem: {memtotal} Mb"
    return mem_str

class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
    
        if self.path == '/':
            # Retrieve CPU usage information from /proc/stat
            with open('/proc/stat', 'r') as f:
                cpu_stats = f.readline().strip().split()[1:]
                cpu_total = sum(map(int, cpu_stats))
                cpu_idle = int(cpu_stats[3])
                cpu_usage = 100.0 - cpu_idle / cpu_total * 100.0

            # Retrieve memory usage information from /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                mem_stats = dict(map(str.strip, line.split(':'))
                                 for line in f.readlines()[:3])
                mem_total = int(mem_stats['MemTotal'].split()[0])
                mem_free = int(mem_stats['MemFree'].split()[0])
                mem_usage = 100.0 - mem_free / mem_total * 100.0
                
            get_uptime = subprocess.check_output(['sh', '-c', 'awk \'{sub(/\..*/,"") ; print $1 }\' /proc/uptime'])
            uptime_str = get_uptime.decode().strip()
            
            #get date and time of system
            get_datetime = subprocess.check_output(['sh', '-c', 'date "+%Y-%m-%d %H:%M:%S"'])
            datetime_str = get_datetime.decode().strip()
            
            get_cpu_model = subprocess.check_output(['sh', '-c', 'awk -F: \'/model name/ {print $2}\' /proc/cpuinfo | sed -n \'1p\''])
            cpu_model_str = get_cpu_model.decode().strip()

            get_cpu_speed = subprocess.check_output(['sh', '-c', 'awk -F: \'/cpu MHz/ {print $2}\' /proc/cpuinfo | sed -n \'1p\''])
            cpu_speed_str = get_cpu_speed.decode().strip()

            cpuinfo_str = f"CPU Model: {cpu_model_str}\nCPU Speed: {cpu_speed_str} MHz"
            
            #get_cpu_usage = subprocess.check_output(['sh', '-c', 'top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk \'{print 100 - $1}\''])
            #cpu_usage_str = get_cpu_usage.decode().strip()

            memo_str = get_meminfo()
            
            get_version = subprocess.check_output(['sh', '-c', 'cat /proc/version'])
            version_str = get_version.decode().strip()
            
            get_proclist = subprocess.check_output(['sh', '-c', 'for i in /proc/[0-9]*/stat; do awk \'{gsub(/[()]/,""); printf "%s->%s,\\n", $1, $2}\' "$i"; done'])
            proclist_str = get_proclist.decode().strip()
            
            # Write the response content
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(
                f"<html><body> \
                <ul> \
                <h1>Date and time: {datetime_str}</h1> \
                <h1>CPU Usage: {cpu_usage:.2f}%</h1> \
                <h1>Memory Usage: {mem_usage:.2f}%</h1>\
                <h1>System Up Time: {uptime_str} seconds</h1> \
                <h1>Current Cpu info : {cpuinfo_str}</h1> \
                <h1>{memo_str}</h1> \
                <h1>System version : {version_str}</h1> \
                <h1>Process list and name: {proclist_str}</h1> \
                </ul> \
                </body>\
                </html>".encode())
        else:
            # Return a 404 error for all other paths
            self.send_error(404)

PORT = 8700
httpd = http.server.HTTPServer(('', PORT), MyHandler)
print(f"Serving on port {PORT}")
httpd.serve_forever()

