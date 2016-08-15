#!/usr/bin/python
#==========================================================
# LANG : Python
# NAME : sydi-linux.py
# AUTHORS : Patrick Ogenstad (patrick.ogenstad@netsafe.se)
#           Patrik Kullman (patrik.kullman@netsafe.se)
#			Hassan Khraim   ()khraimh@hotmail.com)
# VERSION : 0.2
# DATE : 2005-04-19
# UPDATE : 2016-08-16
# Description : Creates a basic documentation for a Linux
# system, which you can use as a starting point.
#
# COMMENTS : 
#
# UPDATES : http://sydi.sourceforge.net/
#
# Running the script: ./sydi-linux.py
#
# Feedback: Please send feedback to patrick.ogenstad@netsafe.se
#                                   patrik.kullman@netsafe.se
#
# LICENSE :
# Copyright (c) 2004-2005, Patrick Ogenstad
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  * Neither the name SYDI nor the names of its contributors may be used
#    to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#==========================================================
#==========================================================

import sys, os, re, time, subprocess, itertools
from ctypes import *
nScriptVersion = 0.2

def checkversion(nVersion):
	import httplib
	conn = httplib.HTTPConnection("sydi.sourceforge.net")
	conn.request("GET", "/versions.php?package=sydi-linux")
	r1 = conn.getresponse()
	if r1.status == 200:
		data1 = r1.read()
		if nVersion < data1:
			print "A New version of SYDI-Linux has been released: " + data1
			print "Download it at http://sydi.sourceforge.net"
		else:
			print "You have the latest version"
	else:
		print "Unable to connect to server, verify that you are connected to the internet or try again later"
	conn.close()

class Sockaddr(Structure):
    _fields_ = [('sa_family', c_ushort), ('sa_data', c_char * 14)]

class Ifa_Ifu(Union):
    _fields_ = [('ifu_broadaddr', POINTER(Sockaddr)),
                ('ifu_dstaddr', POINTER(Sockaddr))]

class Ifaddrs(Structure):
    pass

Ifaddrs._fields_ = [('ifa_next', POINTER(Ifaddrs)), ('ifa_name', c_char_p),
                    ('ifa_flags', c_uint), ('ifa_addr', POINTER(Sockaddr)),
                    ('ifa_netmask', POINTER(Sockaddr)), ('ifa_ifu', Ifa_Ifu),
                    ('ifa_data', c_void_p)]


def get_interfaces():
    libc = CDLL('libc.so.6')
    libc.getifaddrs.restype = c_int
    ifaddr_p = pointer(Ifaddrs())
    ret = libc.getifaddrs(pointer((ifaddr_p)))
    interfaces = set()
    head = ifaddr_p
    while ifaddr_p:
        interfaces.add(ifaddr_p.contents.ifa_name)
        ifaddr_p = ifaddr_p.contents.ifa_next
    libc.freeifaddrs(head) 
    return interfaces

def getNetworkAdapters():
	adapters =[]
	interfaces =get_interfaces()
	for interface in interfaces:
		#adapters['name']=interface
		#adapters['ipaddress']=getAdapterinfo(interface,'inet')
		#adapters['mac']=getAdapterinfo(interface,'link') 
		#adapters['gateway']=getGatewayInfo()
		#groups.append({'name': cgroup, 'xml': '<group name="'+cgroup+'" id="'+gid+'" />'})
		mac=getAdapterinfo(interface,'link')
		gateway=getGatewayInfo()
		ipaddress=getAdapterinfo(interface,'inet')
		adapters.append({'name':interface,'ipaddress' :ipaddress,'mac':mac,'gateway':gateway})
        return  adapters

def getAdapterinfo(interface,att):
        attrib =subprocess.Popen('/sbin/ip add show '+ interface +' | grep ' + att +  ' |sed \'s/\s\+/\ /g\' |cut -d\' \' -f3,-1',shell=True,stdout=subprocess.PIPE)
        (attribinfo,err) =attrib.communicate()
	return attribinfo.strip()
	
def getGatewayInfo():
        attrib =subprocess.Popen('ip route  show |  grep  default | cut -d\' \' -f3',shell=True,stdout=subprocess.PIPE)
        (gateway,err) =attrib.communicate()
	return gateway.strip()

def getDNSServersInfo():
       dns =[]
       p =subprocess.Popen('cat /etc/resolv.conf |grep -v "^#"|grep nameserver| cut -d\' \' -f2',shell=True,stdout=subprocess.PIPE)
       (output,err) =p.communicate()
       p_status=p.wait()
       for line in output.splitlines():
        	dns.append({'nameserver': line.strip()})
       return dns

def getSwapinfo():
        reSwaps =[]
        swapInfo =[]

        p =subprocess.Popen(' swapon -s |awk \'{ print $1"," $2 "," $3 "," $4"," $5}\'',shell=True,stdout=subprocess.PIPE)
        (output,err) =p.communicate()
	p_status=p.wait()
        swapInfo= output.splitlines()


        #driveInfo.pop(0)
        header=swapInfo[0].split(',')
        swapInfo.pop(0)
        count =0
        for i in swapInfo:
                drives =i.split(',')
                reSwaps.append({})
                count =(len(reSwaps) -1)
                drivestr=""
                for h in range(0,len( header)):
                        drivestr +=  ' '+ header[h].replace('%','Per') +'="'+ drives[h] +'" '

                reSwaps[count]['xml'] = '<swap' + drivestr +"/>"

        return reSwaps


def getCPUInfo():
	cpuinfo = file("/proc/cpuinfo")
	proc = {}
	for line in cpuinfo:
		try:
			key,value = re.split(":", line)
		except:
			break

		key = key.strip()
		value = value.strip()
		if key == "processor":
			proc['num'] = int(value)+1
		elif key == "vendor_id":
			proc['id'] = value
		elif key == "model name":
			proc['name'] = value
		elif key == "cpu family":
			proc['family'] = value
		elif key == "model":
			proc['model'] = value
		elif key == "stepping":
			proc['stepping'] = value
		elif key == "cpu MHz":
			proc['mhz'] = value
		elif key == "cache size":
			proc['cache'] = re.split(" ", value)[0]
	cpuinfo.close()
	proc['xml'] = '<processor count="' + str(proc['num']) + '" name="' + proc['name'] + '"'
	proc['xml'] += ' description="' + proc['id'] + " Family " + proc['family'] + " Model " + proc['model'] + " Stepping " + proc['stepping'] + '"'
	proc['xml'] += ' speed="' + proc['mhz'] + '" l2cachesize="' + proc['cache'] + '" />'
	return proc


def getHostInfo():
	host = {}
	hostfd = file("/proc/sys/kernel/hostname")
	host['name'] = hostfd.next().strip()
	hostfd.close()
	domainfd = file("/proc/sys/kernel/domainname")
	host['domain'] = domainfd.next().strip()
	host['oslanguage']=getOSConfiguration()
	domainfd.close()
	return host


def getOSConfiguration():
	computerLang =subprocess.Popen('/usr/bin/locale |grep "^LANG"| cut -d \'=\' -f 2',shell=True,stdout=subprocess.PIPE)
	(computerLang,err) =computerLang.communicate()
	return computerLang


#dmidecode	
# 0	BIOS
# 1	System
# 2 	Base Board
# 3	Chassis
# 4	Processor 
# ....
def getOSBios(request):
	computerBios =subprocess.Popen('/usr/sbin/dmidecode '+ request ,shell=True,stdout=subprocess.PIPE)
	(BIOSINfo,err)=computerBios.communicate()
	return BIOSINfo.strip()
	
	
def getBIOSInfo():
	bios = {}
	bios['version']= getOSBios(' --type 0|grep SMBIOS')
	bios['smbiosversion']= getOSBios(' --type 0|grep \'BIOS Revision\'')
	bios['smbiosmajorversion']=getOSBios(' --type 0|grep \'Firmware Revision\'')
	bios['bioscharacteristics']= getOSBios(' --type 0')
	return bios
	
def getInstalledPackages(platforminfo):
	if (platforminfo['distribution'] == "gentoo"):
		return getDistGentooInstPkgs()
	if (platforminfo['distribution'] == "redhat"):
		return getDistRedhatInstPkgs()
	return ""

def getLocalGroups():
	group = file("/etc/group")
	groups = []
	for i in group:
		groupline = i.strip()
		cgroup = groupline.split(":")[0]
		gid = groupline.split(":")[2]
		members =groupline.split(":")[3]
		groups.append({'name': cgroup, 'xml': '<group name="'+cgroup+'" id="'+gid+'" members="' + members + '" />'})
		
	return groups


def getLocalUsers():
	passwd = file("/etc/passwd")
	users = []
	for i in passwd:
		passwdline = i.strip()
		user = passwdline.split(":")[0]
		uid = passwdline.split(":")[2]
		group = passwdline.split(":")[3]
		fullname = passwdline.split(":")[4]
		home = passwdline.split(":")[5]
		shell = passwdline.split(":")[6]
		users.append({'name': user, 'xml': '<user name="'+user+'" id="'+uid+'" fullname="'+ fullname +'"  group="'+ group +'"  shell="'+ shell +'" home="'+ home +'" />'})
	return users


def getMemInfo():
	meminfo = file("/proc/meminfo")
	mem = {}
	for line in meminfo:
		try:
			key,value = re.split(":", line)
		except:
			break

		value = value.strip()

		if key == "MemTotal":
			mem['total'] = int(re.split(" ", value)[0])/1024
		elif key == "SwapTotal":
			mem['swap'] = int(re.split(" ", value)[0])/1024

	return mem

def getPlatformInfo():
	global osUname
	platform = {}
	platform['ostype'] = osUname[0]
	platform['osrelease'] = osUname[2]
	if os.path.isfile("/etc/gentoo-release"):
		platform['distribution'] = "gentoo"
	elif os.path.isfile("/etc/redhat-release"):
		platform['distribution'] = "redhat"
	else:
		platform['distribution'] = "unknown"

	return platform

def getServices(platforminfo):
	if (platforminfo['distribution'] == "gentoo"):
		return getDistGentooServices()
	elif (platforminfo['distribution'] == "redhat"):
		return getDistRedhatServices()
	return ""


def getTimezone():
	timezone = {}
	timezone['timezone'] = time.tzname[0]
	timezone['xml'] = '<regional timezone="' + timezone['timezone'] + '" />'
	return timezone

# Start Gentoo Specifics	
def getDistGentooServices():
	services = {}
	retServices = []
	services['all'] = os.listdir("/etc/init.d/")
	services['boot'] = os.listdir("/etc/runlevels/boot/")
	services['/etc/'] = os.listdir("/etc/initdefault")
	services['started'] = os.listdir("/var/lib/init.d/started/")
	services['exclude'] = ['reboot.sh', 'shutdown.sh', 'halt.sh', 'functions.sh', 'depscan.sh', 'runscript.sh']
	services['all'].sort()
	for i in services['all']:
		if i not in services['exclude'] and os.access("/etc/init.d/" + i, os.X_OK):
			retServices.append({})
			count = (len(retServices)-1)
			if i in services['started']:
				started = "True"
			else:
				started = "False"
			if i in services['boot']:
				startmode = "Auto"
				runlevel = "boot"
			elif i in services['default']:
				startmode = "Auto"
				runlevel = "default"
			else:
				startmode = "Manual"
				runlevel = "(none)"
			retServices[count]['name'] = i
			retServices[count]['started'] = started
			retServices[count]['startmode'] = startmode
			retServices[count]['runlevel'] = runlevel
			retServices[count]['xml'] = '<service name="' + i + '" startmode="' + startmode + '"'
			retServices[count]['xml'] += ' started="' + started + '" runlevel="' + runlevel + '" />'
	return retServices

def getRedHatRunLevel():
        p =subprocess.Popen('/sbin/runlevel',shell=True,stdout=subprocess.PIPE)
        (output,err) =p.communicate()
        p_status=p.wait()
        (dd,runlevel)=output.split()
        return runlevel


def getRedHatServices(runlevel):
        retServices = []
        cmd= '/sbin/chkconfig --list |grep "' +  runlevel + ':on"'
        p =subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        (output,err) =p.communicate()
        p_status=p.wait()
        for line in output.splitlines():
                #print line
                fields =line.split()
                if(len(fields) > 3):
                        retServices.append([fields[0],fields[(int(runlevel)+1)]])
                        #print retServices


        return retServices

def getRedHatServicesNew(comm):
    	cmd =''
#	rpmSystemd =subprocess.Popen('rpm -q systemd',shell=True,stdout=subprocess.PIPE)
#	(output0,err) =rpmSystemd.communicate()
    	if os.path.isfile('/usr/bin/systemctl'):
    		cmd= 'systemctl list-unit-files --type=service --no-legend' + comm
	else: #initV
    		cmd= '/sbin/chkconfig --list' + comm
	p =subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
	(output,err) =p.communicate()
	p_status=p.wait()
	return output.splitlines()

def getConnectionsTCP():
	retConnections =[]
	cmd= 'netstat -vatnp |grep LISTEN |awk \'{print $1","$4","$5","$7}\''
	p =subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
	(output,err) =p.communicate()
	p_status=p.wait()
	return output.splitlines()

def getConnectionsUDP():
        retConnections =[]
        cmd= 'netstat -vaunp |grep udp |awk \'{print $1"," $4","$5","$6}\''
        p =subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        (output,err) =p.communicate()
        p_status=p.wait()
        return output.splitlines()


def getRoutTable():
        reRoute =[]
        routetable =[]
        cmd  ='/sbin/route -n'
        for i in os.popen(cmd):
                routetable.append(i.strip())

        routetable.pop(0)
        header=routetable[0].split()
        routetable.pop(0)
        count =0
        for i in routetable:
                routes =i.split()
                reRoute.append({})
                count =(len(reRoute) -1)
                routst=""
                for h in range(0,len( header)):
                        routst +=  ' '+ header[h] +'="'+ routes[h] +'" '

                reRoute[count]['xml'] = '<networkroute' + routst + "/>"

        return reRoute

def getDrivesInfo():
        reDrives =[]
        driveInfo =[]
        cmd  ='df -hlP  -x tmpfs -x devtmpfs | grep -v ^none|awk \'{ print $1"," $2 "," $3 "," $4","$5","$6}\''
        p =subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        (output,err) =p.communicate()
        p_status=p.wait()
        driveInfo= output.splitlines()


        #driveInfo.pop(0)
        header=driveInfo[0].split(',')
        driveInfo.pop(0)
        count =0
        for i in driveInfo:
                drives =i.split(',')
                reDrives.append({})
                count =(len(reDrives) -1)
                drivestr=""
                for h in range(0,len( header)):
                        drivestr +=  ' '+ header[h].replace('%','Per') +'="'+ drives[h] +'" '

                reDrives[count]['xml'] = '<drive' + drivestr +"/>"

        return reDrives

def getAllConnections():
	connections = {}
	retConnectionTcp = []
	retConnectionUDP = []
        connections =  getConnectionsTCP()
	retConnectionTcp = getConnections(connections)
        connections  =  getConnectionsUDP()
	retConnectionUDP= getConnections(connections)
	return retConnectionTcp +retConnectionUDP
	 


#Proto Recv-Q Send-Q Local Address               Foreign Address             State       PID/Program name
def getConnections(connections):
        retConnections = []
	runlevelglobal  =  getConnectionsTCP()
        connections.sort()
        for i in  connections:
		retConnections.append({})
                count = (len(retConnections)-1)
		(proto,localAddress,foreignAddress,pid_programName) =i.split(',')
                retConnections[count]['Proto'] = proto 
                retConnections[count]['localAddress'] = localAddress 
                retConnections[count]['foreignAddress'] = foreignAddress
                retConnections[count]['pid_programName'] = pid_programName
                retConnections[count]['xml'] = '<Socket protocal="' + proto + '" localAddress="' + localAddress + '"'
                retConnections[count]['xml'] += '  foreignAddress="' + foreignAddress + '" pid_programName="' + pid_programName + '"/>' 
        return retConnections

# Start Redhat Specifics
def getDistRedhatServices():
        services = {}
        retServices = []
	rpmSystemd =subprocess.Popen('/usr/bin/systemctl get-default',shell=True,stdout=subprocess.PIPE)
	(output0,err) =rpmSystemd.communicate()
	runlevelglobal =output0.rstrip()
        services['all'] =  getRedHatServicesNew('|awk \'{print $1}\'')
        services['autostart'] = getRedHatServicesNew( '| egrep -v \'(disabled|static)\'|grep enabled |awk \'{print $1}\'')
        services['all'].sort()
        for i in services['all']:

                retServices.append({})
                count = (len(retServices)-1)
                if i in services['autostart']:
                        startmode = "Auto"
                        runlevel = runlevelglobal
                else:
			startmode = "Manual"
                        runlevel = "(none)"
                retServices[count]['name'] = i
                retServices[count]['startmode'] = startmode
                retServices[count]['runlevel'] = runlevel
                retServices[count]['xml'] = '<service name="' + i + '" startmode="' + startmode + '"'
                retServices[count]['xml'] += ' startname="' + runlevel + '" />'
        return retServices



def getDistGentooInstPkgs():
	package = []
	for i in os.popen('qpkg -I -v -nc'):
		package.append(i.strip())
	package.sort()
	instPackages = []
	emergeLog = file("/var/log/emerge.log")
	installTimes = {}
	for i in emergeLog:
		if re.match('(\d+):  ::: completed emerge \((\d+) of (\d+)\) (\S+) to /', i):
			installTimes[i.split(" ")[-3]] = i.split(":")[0]

	for i in package:
		if i.split("-")[-1][0] == "r":
			splitby = -2
		else:
			splitby = -1
		
		version = i.split("-")[splitby:]
		version = "-".join(version)
		name = i.split("-")[:splitby]
		name = "-".join(name)
		try:
			installdate = int(installTimes[name + "-" + version])
			installdate = time.strftime("%Y-%m-%d", time.localtime(installdate))
		except:
			installdate = "N/A"
		
		instPackages.append({"name": name, "version": version, "xml": '<portageapplication productname="'+name+'" version="'+version+'" installdate="'+str(installdate)+'" />'})
	return instPackages

def getDistRedhatInstPkgs():
        package = []
        for i in os.popen('rpm -qa --queryformat \'%{name},%{ARCH},%{version},%{installtime:date}\n \''):
                package.append(i.strip())

	package.sort()
	instPackages = []

        for i in package:
		pacinfo =i.split(',')
		if len(pacinfo) > 3:
			(name,arch,version,installdate)=pacinfo
                	instPackages.append({"name": name, "version": version, "xml": '<portageapplication productname="'+name+'" arch="'+arch+'"  version="'+version+'" installdate="'+installdate+'" />'})
        return instPackages



# End Gentoo Specifics

def unsupportedExit():
	print "This machine (" + os.name + "/" + sys.platform + ") isn't supported yet."
	print "Exiting.."

	
def writeXML(outputFile):
	global gendate, platforminfo, hostinfo, cpuinfo, services, installed_packages, localUsers, localGroups,localroute,biosInfo,networkInfo,dnsInfo,swapinfo
	xmlFile = file(outputFile, "w+")
	xmlFile.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
	xmlFile.write('<computer>\n')
	xmlFile.write(' <generated script="sydi-linux" version="0.1" scantime="' + gendate + '" />\n')
	xmlFile.write(' <system name="' + hostinfo['name'] + '" />\n')
	xmlFile.write(' <operatingsystem name="' + platforminfo['ostype'] + ' ' + platforminfo['osrelease'] + '" />\n')

	xmlFile.write(' <distribution name="' + platforminfo['distribution'] +'" />\n')
	xmlFile.write(' <osconfiguration osname="' + hostinfo['name'] + '" domainname="'+ hostinfo['domain'] +'"  />\n')
	xmlFile.write(' <bios version="' + biosInfo['version'] + '" smbiosversion="'+ biosInfo['smbiosversion'] +'" smbiosmajorversion="'+  biosInfo['smbiosmajorversion']+'"  >\n')
	xmlFile.write(' 	<bioscharacteristics name="'+biosInfo['bioscharacteristics']+'" />\n')
	xmlFile.write(' </bios>\n')
			
	xmlFile.write(' <roles>\n')
	xmlFile.write(' </roles>\n')
	xmlFile.write(' <storage>\n')
	xmlFile.write(' 	<drives>\n')
	for i in drives:
		xmlFile.write('  ' + i['xml'] + '\n')
        xmlFile.write(' 	</drives>\n')
        xmlFile.write(' </storage>\n')
        xmlFile.write(' <network>\n')
	for i in networkInfo:
        	xmlFile.write('   <adapter description="' + i['name'] + '" macaddress="' + i['mac'] + '">\n')
                xmlFile.write('		<ip address="' + i['ipaddress'] + '" subnetmask="" />\n')
                xmlFile.write('		<gateway address="' + i['gateway'] + '" />\n')
		for j in dnsInfo:
        	        xmlFile.write('		<dnsserver address="' + j['nameserver'] + '" />\n')
        	xmlFile.write('   </adapter>\n')
        xmlFile.write(' </network>\n')
        
	xmlFile.write(' ' + cpuinfo['xml'] + '\n')
	xmlFile.write(' <memory totalsize="' + str(meminfo['total']) + '" swapsize="' + str(meminfo['swap']) + '" >\n')
#	xmlFile.write(' <swaps>\n')
	for i in swapinfo:
		xmlFile.write( '        ' + i['xml']  + '\n')
#	xmlFile.write(' </swaps>\n')
	xmlFile.write(' </memory>\n')
	xmlFile.write(' <installedapplications>\n')
	for i in installed_packages:
		xmlFile.write('  ' + i['xml'] + '\n')
	xmlFile.write(' </installedapplications>\n')
	xmlFile.write(' <localgroups>\n')
	for i in localGroups:
		xmlFile.write('  ' + i['xml'] + '\n')
	xmlFile.write(' </localgroups>\n')
	xmlFile.write(' <localusers>\n')
	for i in localUsers:
		xmlFile.write('  ' + i['xml'] + '\n')
	xmlFile.write(' </localusers>\n')
	xmlFile.write(' ' + timezone['xml'] + '\n')
	xmlFile.write(' <Sockets>\n')
	for i in connections:
		xmlFile.write('  ' + i['xml'] + '\n')
	xmlFile.write(' </Sockets>\n')
	xmlFile.write(' <services>\n')
	for i in services:
		xmlFile.write('  ' + i['xml'] + '\n')
	xmlFile.write(' </services>\n')
	xmlFile.write(' <network>\n')
	for i in localroute:
		xmlFile.write('  ' + i['xml'] + '\n')
	xmlFile.write(' </network>\n')
	xmlFile.write('</computer>\n')
	xmlFile.close()
	

platform = ""

if os.name == "posix":
	# Running POSIX - good
	if sys.platform == "linux2":
		# Running Linux - very good !
		platform = "Linux"
	else:
		unsupportedExit()
else:
	unsupportedExit()

osUname = os.uname()
hostinfo = getHostInfo()
biosInfo = getBIOSInfo()
dnsInfo= getDNSServersInfo()
networkInfo=getNetworkAdapters()
defaultOutputFile = hostinfo['name'] + ".xml"

gendate = time.strftime("%Y-%m-%d %H:%M:%S")
cpuinfo = getCPUInfo()
meminfo = getMemInfo()
swapinfo =getSwapinfo()
timezone = getTimezone()
platforminfo = getPlatformInfo()
services = getServices(platforminfo)
installed_packages = getInstalledPackages(platforminfo)
connections = getAllConnections()
drives =getDrivesInfo()
localUsers = getLocalUsers()
localGroups = getLocalGroups()
localroute = getRoutTable()

writeXML(defaultOutputFile)


