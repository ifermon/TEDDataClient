from flask import Flask
from flask import request
from flask import Response
import xml.etree.ElementTree as ET
import time

app = Flask(__name__)

DATA_SERVER_IP = 'http://192.168.0.221'

@app.route('/', methods=['POST', 'GET'])
def hello_world():
	print "Hello there"
	return 'Hello World!'

@app.route('/activation', methods=['POST', 'GET'])
def activate():
	# Need the sleep otherwise TED errors out
	time.sleep(2) 
	xml_response = """
			<ted5000ActivationResponse>
				<PostServer>{0}</PostServer>
				<UseSSL>F</UseSSL>
				<PostPort>5000</PostPort>
				<PostURL>/post_readings</PostURL>
				<AuthToken>1234</AuthToken>
				<PostRate>1</PostRate>
				<HighPrec>T</HighPrec>
				<SSLKey>NOT IMPLEMENTED</SSLKey>
			</ted5000ActivationResponse>""".format(DATA_SERVER_IP)
	resp = Response(xml_response, mimetype='text/xml')
	print resp
	return resp

@app.route('/post_readings', methods=['POST'])
def get_readings():
	"""
	print "Hello <{0}>".format(time.time())
	print "req = {0}".format(request)
	print "data = {0}".format(request.data)
	print "values = {0}".format(request.values)
	print "headers = {0}".format(request.headers)
	"""

	root = ET.fromstring(request.data)
	"""
	print "root {0}".format(root)
	print "tag {0}".format(root.tag)
	print "text {0}".format(root.text)
	print "tail {0}".format(root.tail)
	print "attrib {0}".format(root.attrib)
	print "Printing iter():"
	"""
	for e in root.iter('MTU'):
		if e.attrib['type'] == '2':
			print "Found solar!! <{0}>".format(e)
			for se in e.iter('cumulative'):
				print "sub item {0}".format(se)
				print "sub attrib {0}".format(se.attrib)
				print "Time {0}".format(time.gmtime(int(se.attrib['timestamp'])))
	root.clear()
	return Response("Success", mimetype='text/xml')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
