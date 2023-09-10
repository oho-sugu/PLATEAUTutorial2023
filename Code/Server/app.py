from flask import Flask,request
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from datetime import datetime,date,timedelta
import json
import jwt
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/placeplateau'
db = SQLAlchemy(app)

with open ('testgeospatialapi-165ee1b61a8f.json','r') as f:
    service_account_info = json.load(f)

private_key = service_account_info['private_key']
client_email = service_account_info['client_email']

class PlaceData(db.Model):
    __tablename__ = 'placedata'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.String)
    side = db.Column(db.Integer)
    created_at = db.Column(db.Time)
    geom = db.Column(Geometry('POLYGON'))
    area = db.Column(db.Float(5,False,3))

    def getdict(self):
        return {"id":self.id,
                "userid":self.userid,
                "side":self.side,
                "created_at":str(self.created_at),
                "geom":to_shape(self.geom).wkt,
                "area":self.area}

@app.route('/')
def hello():
    return 'PlacePLATEAU API SERVER'

@app.route('/getarea')
def getArea():
    today = date.today()
    placedatas = db.session.query(PlaceData).where(PlaceData.created_at >= today).order_by(PlaceData.id)
    datas = []
    for placedata in placedatas:
        print(placedata.id)
        datas.append(placedata.getdict())
    return json.dumps(datas)

@app.route('/makearea', methods=['POST'])
def makeArea():
    data = request.json

    lastid=data['lastid']
    newarea=data['newarea']

    placedatas = db.session.query(PlaceData).where(PlaceData.created_at >= today).order_by(PlaceData.id)
    datas = []
    for placedata in placedatas:
        print(placedata.id)
        datas.append(placedata.getdict())
    return json.dumps(datas)

@app.route('/token', methods=['GET'])
def token():
    data = request.args.get('key','')
    if data != 'password':
        return 'error'

    current_time = datetime.now()
    expiration_time = current_time + timedelta(hours=1)

    payload = {
        'iss': client_email,
        'sub': client_email,
        'iat': int(current_time.timestamp()),
        'exp': int(expiration_time.timestamp()),
        'aud': 'https://arcore.googleapis.com/',
    }

    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

if __name__ == '__main__':
    app.run(host='0.0.0.0')
