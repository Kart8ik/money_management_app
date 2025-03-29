
import logging
from flask import Flask, render_template, redirect, request,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

categories = ['Total', 'Budget', 'Food', 'Rent', 'Utilities', 'Transportation','Education', 'Healthcare', 'Subscriptions']

def current_time_without_ms():
    return datetime.utcnow().replace(microsecond=0)

class money(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(200), nullable=False)
    date_made = db.Column(db.DateTime, default=current_time_without_ms)

    def __repr__(self) -> str:
        return f'expense-{self.sno}-{self.amount}'

class summary(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, default=0)

    def __repr__(self) -> str:
        return 'summary updated'

with app.app_context():
    logger.debug("Creating all tables...")
    db.create_all()
    logger.debug("Tables created successfully.")

@app.route('/data')
def get_data():
    groups = summary.query.all()
    data = {
        "labels": [group.category for group in groups if group.category!='Total' and group.category!='Budget'],
        "values": [group.amount for group in groups if group.category!='Total' and group.category!='Budget']
    }
    return jsonify(data)

@app.route('/', methods=['GET', 'POST'])
def home():
    logger.debug("Home route accessed.")
    if summary.query.count() == 0:
        logger.debug("Summary table is empty, initializing categories...")
        for category in categories:
            group = summary(category=category)
            db.session.add(group)
            db.session.commit()
        logger.debug("Summary table initialized.")
    all_spend = money.query.all()
    return render_template('index.html', all_spend=all_spend)

@app.route('/addspend', methods=['GET', 'POST'])
def addspend():
    logger.debug("Add spend route accessed.")
    if request.method=='POST':
        amount=request.form['amount']
        desc=request.form['desc']
        category=request.form['inlineRadioOptions']
        spend=money(amount=amount,desc=desc,category=category)
        if spend.desc=='':
            db.session.commit()
        else:
            group=summary.query.filter_by(category=category).first()
            total=summary.query.filter_by(category='Total').first()
            group.amount=(group.amount)+int(amount)
            total.amount=(total.amount)+int(amount)
            db.session.add_all([spend,group,total])
            db.session.commit()
    if summary.query.count() == 0:
        logger.debug("Summary table is empty, initializing categories...")
        for category in categories:
            group = summary(category=category)
            db.session.add(group)
            db.session.commit()
        logger.debug("Summary table initialized.")
    all_spend=money.query.all()
    return render_template('index.html',all_spend=all_spend)

@app.route('/delete/<int:sno>', methods=['GET', 'POST'])
def delete(sno):
    logger.debug(f"Delete route accessed for sno: {sno}")
    spend = money.query.filter_by(sno=sno).first()
    group = summary.query.filter_by(category=spend.category).first()
    total=summary.query.filter_by(category='Total').first()
    group.amount=(group.amount)-int(spend.amount)
    total.amount=(total.amount)-int(spend.amount)
    db.session.add_all([group,total])
    db.session.delete(spend)
    db.session.commit()
    logger.debug(f"Deleted spend: {spend}")
    return redirect('/')

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    logger.debug(f"Update route accessed for sno: {sno}")
    if request.method == 'POST':
        amount = request.form['amount']
        desc = request.form['desc']
        category = request.form['inlineRadioOptions']
        spend = money.query.filter_by(sno=sno).first()
        group = summary.query.filter_by(category=spend.category).first()
        total=summary.query.filter_by(category='Total').first()
        group.amount=(group.amount)-int(spend.amount)
        total.amount=(total.amount)-int(spend.amount)
        db.session.add(group)
        spend.amount = amount
        spend.desc = desc
        spend.category = category
        groupnew = summary.query.filter_by(category=spend.category).first()
        groupnew.amount=(groupnew.amount)+int(spend.amount)
        total.amount=(total.amount)+int(spend.amount)
        db.session.add_all([spend,groupnew,total])
        db.session.commit()
        logger.debug(f"Updated spend: {spend}")
        return redirect('/')
    spend = money.query.filter_by(sno=sno).first()
    return render_template('update.html', spend=spend)

@app.route('/graphs',methods=['POST','GET'])
def graphs():
    if request.method=='POST':
        budget=request.form['budget']
        group=summary.query.filter_by(category='Budget').first()
        group.amount=budget
        db.session.add(group)
        db.session.commit()
    logger.debug("Graphs route accessed.")
    groups=summary.query.all()
    Total=summary.query.filter_by(category='Total').first()
    Budget=summary.query.filter_by(category='Budget').first()
    return render_template('graphs.html',groups=groups,total=int(Total.amount),budget=int(Budget.amount))

@app.route('/reset',methods=['POST','GET'])
def reset():
    db.drop_all()
    db.create_all()
    return redirect('/')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
